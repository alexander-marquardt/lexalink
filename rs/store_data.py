# -*- coding: utf-8 -*- 

################################################################################
# LexaLink Copyright information - do not remove this copyright notice
# Copyright (C) 2012 
#
# Lexalink - a free social network and dating website platform for the Google App Engine. 
#
# Original author: Alexander Marquardt
# Documentation and additional information: http://www.LexaLink.com
# Git source code repository: https://github.com/lexalink/LexaLink.git 
#
# Please consider contributing your enhancements and modifications to the LexaLink community, 
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
################################################################################


from os import environ

from google.appengine.api import images
from google.appengine.ext import db 
from google.appengine.api import taskqueue
from google.appengine.api import memcache

import re, logging, datetime, pickle, StringIO, os

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse,\
     HttpResponseNotAllowed, HttpResponseBadRequest, HttpResponseServerError
from django.core.validators import email_re
from django.utils.html import strip_tags
from django.utils import simplejson
from django.utils.translation import ugettext
from django.utils import translation

import settings
from constants import *
from utils import passhash, compute_captcha_bypass_string, \
     put_userobject, requires_login, ajax_call_requires_login
from models import PhotoModel,  InitiateContactModel, \
     UserModel, SpamMailStructures
from user_profile_main_data import UserSpec
from user_profile_details import UserProfileDetails
import mailbox
import email_utils
import captcha
import queries
import backup_data, error_reporting
import login_utils, utils, sharding, utils_top_level, models
import constants, models, localizations, text_fields, site_configuration
import friend_bazaar_specific_code
from rs.import_search_engine_overrides import *


NUM_REPORTS_FOR_UNACCEPTABLE_PROFILE = 3 # how many times does a profile have to be marked as unacceptable before we generate a warning

#############################################
def store_search_preferences(request):
    # This funcion stores search parameters, and re-directs to the search generator function.
    # future default search values will reflect the users current selection.
    
    # Note: it might "look bad" to be passing in data in a "GET", however this is necessary in order
    # for the back button to function correctly in IE. Additionally, since we are using ajax (get with 
    # a random value appended in order to ensure no caching) to 
    # reload the updated search preferences, this essentially functions like a POST for our purposes.
    
    userobject = utils_top_level.get_userobject_from_request(request)

    if request.method != 'GET':
        # user has done something strange -- raise exception
        raise Exception("store_search_preferences expected a GET and got something else")
    else:
        # Remember the search settings, so that the next time the user performs a search
        # their default settings are the same.
        search_preferences2_object = userobject.search_preferences2
        
        # This function should only be called 
        assert(search_preferences2_object != None)
        
        # set search preferences to the values received in the GET.
        for search_preference in UserSpec.search_fields:
            value = request.GET.get(search_preference,'----')
            setattr(search_preferences2_object, search_preference, value)
        
        search_preferences2_object.user_has_done_a_search = True
        # Write the new search parameters as the default for future searches.
        search_preferences2_object.put()
    
    request.session.modified = True

        
    
def store_photo_options(request, owner_uid, is_admin_photo_review = False, review_action_dict = {}):
    # recieves to POST from the "edit_photos" call, and stores to the appropriate data structure.
    # then re-direct back to the user profile.
    # - uid - id of current user
    # 
    # If this is called by the administrator/photo review - then we deal with only one photo at a time
    # meaning that there are no lists of photo keys etc. posted to this function.
    #
    # if is_admin_photo_review is True, then we will not write the userobject to the database, but we
    # *will* write the userobject.unique_last_login_offset_ref to the database to reflect any 
    # changes that may have occured with respect to the number of photos that the current user
    # has associated with their profile. This is necssary for cases when the administrator modifies
    # or removes photos associated with a given profile.
    #
    # review_action_dict is a dictionary that will contain one of the following values:
    # is_profile : ref_key *or* is_private : ref_key *or* delete : ref_key
    # were the first dictionary key tell the action, and the ref_key refers to the photo that we
    # are modifying.

    # What I do here is notvery elegant.. loop over all photos associated with a particular
    # profile and check if any values have changed due to the posted data. If changed
    # then write the photo to the database.
    
    try:
        #logging.debug("Entering store_photo_options")
        if not is_admin_photo_review:
            assert(owner_uid == request.session['userobject_str'])
            userobject = utils_top_level.get_userobject_from_request(request)
        else:
            # this has been called by the administrator while reviewing photos - the session
            # does not contain the current userobject reference.
            userobject = utils_top_level.get_object_from_string(owner_uid)
    
        if request.method != 'POST':
            return HttpResponseBadRequest()
        
        is_profile_key = ''
        is_private_list_of_keys = []
        delete_photo_list_of_keys = []
        
        if not is_admin_photo_review:
            is_profile_key = request.POST.get('is_profile', '') #only one photo is profile, so not a list
            is_private_list_of_keys = request.POST.getlist('is_private')
            delete_photo_list_of_keys = request.POST.getlist('delete_photo')
        else:
            # since the administrative review functionality sends one photo key at a time, we fake previously existing
            # structures that were posting lists of values. 
            if review_action_dict.has_key('is_profile'):
                is_profile_key = review_action_dict['is_profile']
            if review_action_dict.has_key('is_private'):
                is_private_list_of_keys.append(review_action_dict['is_private'])
            if review_action_dict.has_key('delete'):
                delete_photo_list_of_keys.append(review_action_dict['delete'])
                        
        # Loop over all photos, and mark them appropriately based on the inputs. 

        all_user_photo_keys = PhotoModel.all(keys_only = True).filter('parent_object =', userobject).fetch(MAX_NUM_PHOTOS)  
        for photo_key in all_user_photo_keys:
            photo_key_str = str(photo_key)
            photo_object = db.get(photo_key)
            
            if photo_key_str in delete_photo_list_of_keys:
                db.delete(photo_key)
            else:
                if photo_key_str in is_private_list_of_keys:
                    if not photo_object.is_private:
                        photo_object.is_private = True
                        photo_object.is_profile = False
                        utils.put_object(photo_object)
                else:
                    if not is_admin_photo_review:
                        # if this is a photo review, we should never be marking photos as profile or as normal .. 
                        # but additionally, this code is invalid for admin reviews, since it assumes that all user photos
                        # that is not in the list of private photos are public photos - but this list only contains
                        # a single element when we call this function from the reviewers page.
                        if photo_key_str in is_profile_key:
                            if not photo_object.is_profile:
                                photo_object.is_profile = True
                                photo_object.is_private = False
                                utils.put_object(photo_object)

                        else: # it is just a normal photo
                            if photo_object.is_private or photo_object.is_profile:
                                photo_object.is_private = False
                                photo_object.is_profile = False
                                utils.put_object(photo_object)
                
                
        # Do *not* try to combine this loop with the previous for loop - it is necessary that all photo_objects
        # are updated before we start to check if they are private, public, etc.
        has_private_photos = has_public_photos = has_profile_photo = False
        for photo_key in all_user_photo_keys:
            photo_key_str = str(photo_key)
            photo_object = db.get(photo_key) 
            if photo_object: # make sure not deleted
                if photo_object.is_profile:
                    has_profile_photo = True
                    has_public_photos = True
                elif photo_object.is_private:
                    has_private_photos = True
                else: 
                    has_public_photos = True
                

        # update the offsets for displaying the user with higher (or lower) priority in the search results.
        userobject.unique_last_login_offset_ref.has_profile_photo_offset = has_profile_photo
        userobject.unique_last_login_offset_ref.has_public_photo_offset = has_public_photos
        userobject.unique_last_login_offset_ref.has_private_photo_offset = has_private_photos
        logging.debug("Writing unique_last_login_offset for %s has_profile_photo = %s has_public_photos = %s has_private_photos = %s" % (
            userobject.username, has_profile_photo, has_public_photos, has_private_photos))
        userobject.unique_last_login_offset_ref.put()
    
        if not is_admin_photo_review:
            (userobject.unique_last_login, userobject.unique_last_login_offset_ref) = \
             login_utils.get_or_create_unique_last_login(userobject, userobject.username)
            put_userobject(userobject)       
           
        utils.invalidate_user_summary_memcache(owner_uid) 
        return HttpResponse('Success')
    
    except:
        error_reporting.log_exception(logging.critical, request = request)       
        return HttpResponse('Error')            
    
#############################################
@requires_login
def store_about_user(request, owner_uid):
    # recieves to POST from the "edit_about_user" call, and stores to the appropriate data structure.
    # then re-direct back to the user profile.
    try:
        assert(owner_uid == request.session['userobject_str'])
        userobject = utils_top_level.get_userobject_from_request(request)

        text = request.POST.get('about_user', '')
        
        # make sure that the user isnt trying to do an html/javascript injection
        text = strip_tags(text)

        if len(text) > ABOUT_USER_MIN_DESCRIPTION_LEN:
            userobject.has_about_user = True
        else:
            userobject.has_about_user = False
       
        if text:
            userobject.about_user = text[:ABOUT_USER_MAX_DESCRIPTION_LEN]
            # break long words into smaller words
            userobject.about_user = utils.break_long_words(userobject.about_user, constants.MAX_CHARS_PER_WORD)            
        else:
            userobject.about_user = "----"
            

            
        userobject.unique_last_login_offset_ref.has_about_user_offset = True
        userobject.unique_last_login_offset_ref.put()
        (userobject.unique_last_login, userobject.unique_last_login_offset_ref) = \
         login_utils.get_or_create_unique_last_login(userobject, userobject.username)
        
        
        put_userobject(userobject)  
            
        return HttpResponse('Success')
    
    except:
        error_reporting.log_exception(logging.critical, request = request)       
        return HttpResponse('Error')   


#############################################
def verify_email_address_is_valid_and_send_confirmation(request, userobject, email_address):
    

    # email_re is a built-in django regular expression that can be checked against for validity of email
    # address. 
    if email_re.match(email_address):
        assert(userobject != None)
        is_valid=True
        countdown_time = 5 # give few seconds to make sure userobject has had time to propagate through servers (especially if this is a new registration) 
                           # this is necessary because the task-queue could otherwise start in parallel with the writing of the userobject, which could 
                           # cause a failure due to to email address not yet being stored properly.
        taskqueue.add(queue_name = 'mail-queue',  countdown = countdown_time, url='/rs/admin/send_confirmation_email/',\
                      params = {'uid': str(userobject.key()), 'email_address':email_address, 'remoteip': os.environ['REMOTE_ADDR'],
                                'lang_code' : request.LANGUAGE_CODE})
    else:
        is_valid=False
    return is_valid


#############################################
def update_when_to_send_next_notification_after_profile_modification(userobject):
    
    # update the when_to_send_next_notification to reflect the newly selected value in both the mail and contact
    # counter objects. Also, allows us to "disable" the message queuing for this user (meaning that the date for sending
    # a message notification is set to infinity) - Note: Other parts of the code could overwrite this value if they don't also
    # verify that the email address is valid.  (we don't check the userobject here, because it hasn't yet been updated with the 
    # new value)

    hours_between_message_notifications = utils.get_hours_between_notifications(userobject, constants.hours_between_message_notifications)
    hours_between_new_contacts_notifications = utils.get_hours_between_notifications(userobject, constants.hours_between_new_contacts_notifications)
    
    db.run_in_transaction (utils.when_to_send_next_notification_txn, userobject.unread_mail_count_ref.key(), \
                           hours_between_message_notifications)
    
    db.run_in_transaction (utils.when_to_send_next_notification_txn, userobject.new_contact_counter_ref.key(), \
                           hours_between_new_contacts_notifications)       
    
    
    
#############################################
@ajax_call_requires_login
def store_email_options(request, owner_uid):
    
    assert(owner_uid == request.session['userobject_str'])
    userobject = utils_top_level.get_userobject_from_request(request)
    
    # for historical reasons email_options is a list that typically contains a single value
    post = request.POST.getlist('email_options')
    
    if post:
        # set the new email_options value on the userobject
        setattr(userobject, 'email_options', post)
        put_userobject(userobject)  
        update_when_to_send_next_notification_after_profile_modification(userobject)
    
    return HttpResponse('Success')


def store_email_address(request, owner_uid):

    try:
        assert(owner_uid == request.session['userobject_str'])
        userobject = utils_top_level.get_userobject_from_request(request)
        # remove blank spaces from the email address -- to make it more likely to be acceptable
        posted_email = request.POST.get('email_address','')
        posted_email = posted_email.replace(' ', '')
        
        # make it lowercase so we can find it when we query 
        posted_email =posted_email.lower()
        email_is_valid = False
        
        unique_last_login_offset_ref = userobject.unique_last_login_offset_ref

        if posted_email:
            email_is_valid = \
                verify_email_address_is_valid_and_send_confirmation(request, userobject, posted_email)
            userobject.email_address_is_valid = email_is_valid
            
            if  email_is_valid:
                unique_last_login_offset_ref.has_email_address_offset = True
                userobject.email_address = posted_email                
                logging.info("User %s has modified their email address %s to %s" % (
                    userobject.username, userobject.email_address, posted_email))
           
                
        
        # if user clears the field, a blank value will not be written to 
        # the database, so, set it back to the default "----" so that it
        # will overwrite the previously stored address. If an invalid email address 
        # is entered, treat it the same as a clearing.
        if not email_is_valid: # if post == "" or if an invalid email is entered
            userobject.email_address = "----" 
            logging.warning("User %s erased their email address %s" % (userobject.username, userobject.email_address))
            userobject.email_address_is_valid = False
            unique_last_login_offset_ref.has_email_address_offset = False
        
        unique_last_login_offset_ref.put()
        put_userobject(userobject)  
            
        # in all cases if the email is cahnged we should updated the message queuing values - this is in case we go from
        # having a valid email to invalid or vice-versa -- we could explicity check for this is this becomes a bottleneck
        update_when_to_send_next_notification_after_profile_modification(userobject)
        return HttpResponse('Success')
    
    except:
        error_reporting.log_exception(logging.critical, request = request)       
        return HttpResponse('Error')       
    
    
def store_current_status(request, owner_uid):
    # stores the users "headline" 
    
    try:
        assert(owner_uid == request.session['userobject_str'])
        userobject = utils_top_level.get_userobject_from_request(request)
        current_status = request.POST.get('current_status','')      
        
        # make sure that they don't try to store a value that is larger than the field size
        current_status= current_status[:field_formats['status_field_length']]
        current_status = strip_tags(utils.break_long_words(current_status, constants.MAX_CHARS_PER_WORD))
        userobject.current_status_update_time = datetime.datetime.now()
        if current_status == "":
            current_status = "----" 
        
        userobject.current_status = current_status
        put_userobject(userobject)  
        return HttpResponse('Success')

    except:
        error_reporting.log_exception(logging.critical, request = request)       
        return HttpResponse('Error')      
            
def copy_principal_user_data_fields_into_ix_lists(userobject):

    try:
        for field in UserSpec.principal_user_data + ['region', 'sub_region',]:
            
            val = getattr(userobject, field)
            ix_field_name = field + "_ix_list"
            ix_list = [u'----',]
            if val:
                ix_list.append(val)
            setattr(userobject, ix_field_name, ix_list)   
    except:
        error_message = "Unknown error userobject: %s" % (repr(userobject))
        error_reporting.log_exception(logging.critical, error_message = error_message)

        
def re_compute_for_sale_to_buy_ix_list(userobject, parent_ix_list_name): 
    # Used in Friend, for computing ix_lists that are necessary for search queries    
    # Returns True if the lists are stored correctly (ie. they are not longer than the cutoff value)
    # and returns False if the lists have violated a constraint.
    
    try:
        ix_list_length = 0
        
        ix_field_name =  parent_ix_list_name + "_ix_list"
        ix_list = ["----",]
        # loop over all the to_buy or for_sale child fields, and add the values into the ix_list
        for category in friend_bazaar_specific_code.categories_label_dict.keys():
            
            field_name = '%s_%s' % (parent_ix_list_name, category)
            field_list = getattr(userobject, field_name)

            # By construction, 'prefer_no_say' is only allowed if there are no other values present in the list.
            if field_list[0] != 'prefer_no_say':                
                # add the category name to the list
                ix_list.append(field_name)
                # now copy all the values within the category into the ix_list
                ix_list  += field_list
                ix_list_length += len(field_list)
            
        if settings.DEBUG:
            # make sure that the ix_list is clean (no extra prefer_no_say or ---- values)
            assert(not "prefer_no_say" in ix_list)
            assert(not "----" in ix_list[1:]) # note, we ignore the first value since it *should* be set to "----"
            
        # we  cut-off the list since it exceeds the maximum allowed (we don't want people selecting every single activity)
        if ix_list_length > constants.MAX_CHECKBOX_VALUES_IN_COMBINED_IX_LIST:
            error_reporting.log_exception(logging.critical, error_message = "Long ix_list length %s for user %s\nlist=%s" % (
                ix_list_length, userobject.username, ix_list,))
            return False
        else:            
            setattr(userobject, ix_field_name, ix_list)
            return True
        
    except:
        error_message = "Unknown error userobject: %s" % (repr(userobject))
        error_reporting.log_exception(logging.critical, error_message = error_message)
        return False
        
        
for_sale_pattern = re.compile(r'for_sale.*')        
to_buy_pattern = re.compile(r'to_buy.*')

@ajax_call_requires_login
def store_generic_checkbox_option_list(request, option_name, owner_uid):
    
    prepend_dont_care_to_list = False
    parent_ix_list_name = None
    
    try:
        if settings.BUILD_NAME == "Language":
            # This is necessary for ensuring that the languages and languages_to_learn contain "----" which is necessary for
            # ensuring that all profiles show up in "dont_care" searches.
            prepend_dont_care_to_list = True
            
        if settings.BUILD_NAME == "Friend":
            # we must copy the list into the appropriate for_sale_ix_list, or to_buy_ix_list (depending on if this is a for_sale or to_buy sub-list)
            if for_sale_pattern.match(option_name):
                parent_ix_list_name = "for_sale"
            #elif to_buy_pattern.match(option_name):
                #parent_ix_list_name = "to_buy"
            else: 
                assert(0)
            
        fields_to_store = [option_name,]
        http_return = store_data(request, fields_to_store, owner_uid, is_a_list = True, prepend_dont_care_to_list = prepend_dont_care_to_list,
                                 parent_ix_list_name = parent_ix_list_name)
        
    except:
        error_reporting.log_exception(logging.critical, request = request)      
        http_return = HttpResponse('Error')
        
    return http_return
    
@ajax_call_requires_login
def store_data(request, fields_to_store, owner_uid, is_a_list = False, update_title = False, is_signup_fields = False, 
               prepend_dont_care_to_list = False, parent_ix_list_name = None):
    # recieves to POST from the "edit_xxxx" call, and stores to the appropriate data structure.
    # then re-direct back to the user profile.
    # - uid - id of current user
    # - fields_to_store - data fields that are passed in in the current post
    # - is_a_list - if the post contains data from a checkbox, it should be processed as
    #               a list. 
    # - prepend_dont_care_to_list: we add a value of "----" to the list, which will be used in search queries where the condition is "don't care"
    # - parent_ix_list_name: "for_sale" or "to_buy" - indicates that this list will be added to a larger ix_list that is used for
    #                         efficiently searching through profiles specified in the search box.
    
    try:
        userobject_ok_to_write = True
        assert(owner_uid == request.session['userobject_str'])
        userobject = utils_top_level.get_userobject_from_request(request)
        
        if request.method != 'POST':
            return HttpResponseBadRequest()
        
        for field in fields_to_store:
                       
            post_val = ""
            if not is_a_list:
                post_val = request.POST.get(field,'')
            else: # it is a list of values that will be stored in a single variable (array)
                post_val = request.POST.getlist(field)
                              
                # check if one of the values is "prefer_no_say", and if there are other values, then
                # remove this and leave on the other values in the list.
                if len(post_val) > 1:
                    try:
                        idx = post_val.index('prefer_no_say')
                        del post_val[idx]
                    except:
                        # did not find 'prefer_no_say' value, just pass
                        pass
                    
                if len(post_val) == 0:
                    # if the post is an empty list, then set the value of the list to 'prefer_no_say'. This ensures that
                    # an empty list will over-ride the currenly stored list.
                    if  (settings.BUILD_NAME == "Language" and (field == 'languages' or field=='languages_to_learn')):
                        # if build is Language and the field is languages or languages_to_learn, then don't set the value here
                        # since 'prefer_no_say' is invalid for these fields.
                        pass
                    else:
                        # for all other checkbox fields, prefer_no_say is a valid value, and a good indicator that the user has 
                        # passed in an empty list.
                        post_val = ['prefer_no_say',]
                    
                    
                if prepend_dont_care_to_list:
                    # this is necessary for us to be able to do queries on the current field, for which we want to show *all* users irregardless
                    # of their setting for the current field.
                    post_val = [u"----",] + post_val
                    
            if field == 'country' or field == 'native_language' or field == 'friend_currency':
                # do not allow them to set their country, native_language, or currency to undefined value
                # These are the fields that have a ---- seperating the "important" values from the rest. 
                if post_val == '----':
                    # by setting to '', it will not be written to the userobject.
                    post_val = ''
                
            if settings.BUILD_NAME == "Language":
                if field == "native_language":
                    # Ensure that their new native language is added into the list of languages.
                    if post_val not in userobject.languages:
                        userobject.languages.append(post_val)
                if field == "languages":
                    # Do not allow the user to save a languages list that does not include their native_language
                    # if they try to post a list that does not contain their native language, add it back in.
                    if userobject.native_language not in post_val:
                        post_val.append(userobject.native_language)
                        
                
            if post_val:
                # set the value on the userobject
                setattr(userobject, field, post_val)
                 
                # The following piece of code is used for computing the unique_last_login value, which allows us to display
                # profiles sorted based on whatever weighting we have given to the different critera (eg. if they have a photo,
                # that could move their profile up by 2 days, and if they have an email address that could move it up by 8 hours, etc.).
                # Ultimately, the value is written into the "unique_last_login" value contained on the userobject.
                # update the value for has_xxx_offset (if the value has changed -- since database
                # writes are expensive.
                unique_last_login_offset_ref = userobject.unique_last_login_offset_ref
                has_offset_name = "has_" + field + "_offset"
                
                # make sure that the database has the current field defined -- some fields such as 
                # email options, etc.. might be post_valed to the current function, but do not have values
                # defined in the login_offset data structure.
                if hasattr(unique_last_login_offset_ref, has_offset_name):
                    offset_is_set = getattr(unique_last_login_offset_ref, has_offset_name)
                    if not offset_is_set:
                        setattr(unique_last_login_offset_ref, has_offset_name, True)
                        unique_last_login_offset_ref.put()
                        (userobject.unique_last_login, userobject.unique_last_login_offset_ref) = \
                         login_utils.get_or_create_unique_last_login(userobject, userobject.username)
 
                
        if is_signup_fields:
            # copy the current field into the search index list for the current field
            copy_principal_user_data_fields_into_ix_lists(userobject)
            
        if parent_ix_list_name:
            userobject_ok_to_write = re_compute_for_sale_to_buy_ix_list(userobject, parent_ix_list_name)

        if userobject_ok_to_write:
            put_userobject(userobject)
            return HttpResponse('Success')
        else:
            error_message = 'Unable to store data to userobject'
            error_reporting.log_exception(logging.critical, error_message=error_message)
            return HttpResponse(error_message)
       
    except:
        error_message="Unable to store data for user - check POST"
        error_reporting.log_exception(logging.critical, error_message=error_message, request = request)       
        return HttpResponse('Error')


#############################################
@ajax_call_requires_login
def store_change_password_fields(request, owner_uid):

    assert(owner_uid == request.session['userobject_str'])
    userobject = utils_top_level.get_userobject_from_request(request)
    
    password_change_is_valid = False
    
    if request.method != 'POST':
        return HttpResponseBadRequest()
    else:
        current_password = request.POST.get('current_password','')
        new_password = request.POST.get('new_password', '')
        verify_new_password = request.POST.get('verify_new_password','')
        
        # Authenticate the original password
        if passhash(current_password) == userobject.password:
            if new_password == verify_new_password and new_password != "":
                password_change_is_valid = True
               
        userobject.change_password_is_valid = password_change_is_valid
        userobject.password_attempted_change_date = datetime.datetime.now()             

            
    #only overwrite the password if the post was a valid password change
    if password_change_is_valid:
        setattr(userobject, 'password', passhash(new_password))
        
    # write the object in all cases, because state information about the attempted password
    # change is written into the userobject. We use the attempted_password_change time in the
    # ajax function "load_change_password_fields" -- we should fix this in the future, and 
    # NOT write the userobject, unless a successful password change has occured -- we can eaily
    # pass the status back to the client and process with javascript as opposed to server side
    # tracking of this status (this is written like this because when I first started coding I didn't know
    # any javascript). 
    put_userobject(userobject)  
    
    return HttpResponse('Success')


###########################################################################
def  reset_new_contact_or_mail_counter_notification_settings(object_ref_key):
    # resets the date_of_last_notification on the object to the current time. This can be used for both "new_contact_counter" and "unread_mail_count"
            
    def txn(new_contact_counter_ref_key):

        counter_obj = db.get(object_ref_key)
        counter_obj.date_of_last_notification = datetime.datetime.now()
        counter_obj.num_new_since_last_notification = 0
        counter_obj.when_to_send_next_notification = datetime.datetime.max
        counter_obj.when_to_send_next_notification_string = str(counter_obj.when_to_send_next_notification)
        counter_obj.put()
    
    db.run_in_transaction(txn, object_ref_key)
    

    
    
###########################################################################

def  modify_new_contact_counter(new_contact_counter_ref_key, action_for_contact_count, value,
                                hours_between_notifications, update_notification_times):
    # updates the new_contact_counter_obj value based on the value passed in. Must
    # be run in a transaction to ensure that only a single update can take place at a time.
    # This value is used for tracking number of kisses, winks, keys, received by a user since their
    # last login. 
            
    def txn(new_contact_counter_ref_key, action_for_contact_count, value):

        new_contact_counter_obj = db.get(new_contact_counter_ref_key)
        current_count = getattr(new_contact_counter_obj, action_for_contact_count)
        current_count += value
        setattr(new_contact_counter_obj, action_for_contact_count, current_count)
        
        if update_notification_times:
            new_contact_counter_obj.num_new_since_last_notification += value

            if value > 0:
                # only update notification settings if the user has received a new
                # contact (not one that is delted)
                if hours_between_notifications != None:
                    new_contact_counter_obj.when_to_send_next_notification = \
                                           new_contact_counter_obj.date_of_last_notification + \
                                           datetime.timedelta(hours = hours_between_notifications)
                else:
                    new_contact_counter_obj.when_to_send_next_notification = datetime.datetime.max
                                
            if new_contact_counter_obj.num_new_since_last_notification <= 0:
                # this number can go negative if someone gives a kiss, and then takes it away. Not an exception,
                # but it is good to keep it non-negative so that if new contacts are received after old contacts
                # are taken away, this number will still be positive.
                new_contact_counter_obj.num_new_since_last_notification = 0
                
                # don't send a notification if there are no new contacts
                new_contact_counter_obj.when_to_send_next_notification = datetime.datetime.max
            
            new_contact_counter_obj.when_to_send_next_notification_string = str(new_contact_counter_obj.when_to_send_next_notification)  
            
        new_contact_counter_obj.put()
        return new_contact_counter_obj
    
    
    new_contact_counter_obj = db.run_in_transaction(txn, new_contact_counter_ref_key, action_for_contact_count, value)
    return new_contact_counter_obj
                       
###########################################################################
   
def get_or_create_initiate_contact_object(userobject_key, other_userobject_key):
    # either gets or creates a new initiate_contact_object that tracks communication (winks, kisses, keys) between 
    # two users. 

    try:
        initiate_contact_object = utils.get_initiate_contact_object(userobject_key, other_userobject_key, create_if_does_not_exist = True)
        return initiate_contact_object

    except:
        error_reporting.log_exception(logging.critical)
        return None


###########################################################################
        
        
# New HR Datastore
def update_users_have_sent_messages_object_favorite_val(userobject, other_userobject, bool_val):

    try:
        users_have_sent_messages_object = utils.get_have_sent_messages_object(userobject.key(), other_userobject.key())
    
        if users_have_sent_messages_object:
            users_have_sent_messages_object.other_is_favorite = bool_val
            users_have_sent_messages_object.put()
        else:
            # if they have not yet sent messages between them, then do not create this object
            pass
    except:
        error_reporting.log_exception(logging.critical)
                
        
def toggle_chat_friend_status(initiate_contact_object):
    
    # chat_friend_stored will contain a string that indicates the following possible conditions:
    #    None: Neither the viewer or displayed profile have made any request to add to each others chat list
    #    "request_sent": the displayed profile has been sent a request to add to chat contacts
    #    "request_received": the viewer profile has been sent a chat request from the users whose profile is being viewed
    #    "connected": the viewer and displayed profile have agreed to add each other to their chat contacts.

    
    # we are essentially toggeling the chat_friend status, based on the current setting
    
    try:
        if not initiate_contact_object.chat_friend_stored:
            # store a totally new request
            initiate_contact_object.chat_friend_stored = "request_sent"
            chat_request_action_on_receiver = "friend_request"
            counter_modify = 1
        elif initiate_contact_object.chat_friend_stored == "request_sent":
            # remove the request
            initiate_contact_object.chat_friend_stored = None
            chat_request_action_on_receiver = "friend_request"
            counter_modify = -1
            
        elif initiate_contact_object.chat_friend_stored == "request_received":
            # user is responding to a request to "connect" for chat and therefore a click will make them connected
            initiate_contact_object.chat_friend_stored = "connected"
            chat_request_action_on_receiver = "friend_confirmation"
            counter_modify = 1
            
        elif initiate_contact_object.chat_friend_stored == "connected":
            # the user has decided to disconnect from the other user -- however the other users request still remains
            initiate_contact_object.chat_friend_stored = "request_received"
            chat_request_action_on_receiver = "friend_confirmation"
            counter_modify = -1
        else:
            assert(False)
                    
        return (counter_modify, chat_request_action_on_receiver)
    
    except:
        error_reporting.log_exception(logging.critical)
        return (0, None)

###########################################################################
def modify_passive_initiate_contact_object(chat_request_action_on_receiver, add_or_remove, userobject_key, other_userobject_key):
    # chat-request_action_on_receiver is either "friend_request" or "friend_confirmation", 
    # and add_or_remove is either +1 or -1 respectively
    #
    # "passive" initiate contact object means the initiate contact object referring to "other_userobject" kisses,keys,etc.
    # sent to "userobject". (this is the "opposite" of the "active" userobject).
    
    def txn(initiate_contact_object_key):
        # use a transaction to ensure that only a single update to this object will happen at a time.
        initiate_contact_object = db.get(initiate_contact_object_key)
        if chat_request_action_on_receiver == "friend_request":
            if add_or_remove == +1:
                initiate_contact_object.chat_friend_stored = "request_received"
            if add_or_remove == -1:
                initiate_contact_object.chat_friend_stored = None
                
        if chat_request_action_on_receiver == "friend_confirmation":
            if add_or_remove == +1:
                initiate_contact_object.chat_friend_stored = "connected"
            if add_or_remove == -1:
                initiate_contact_object.chat_friend_stored = "request_sent"
            
        initiate_contact_object.chat_friend_stored_date = datetime.datetime.now()
        initiate_contact_object.put()  
    
    # currently this function should only be called for chat_friend requests.
    assert(chat_request_action_on_receiver == "friend_request" or chat_request_action_on_receiver == "friend_confirmation")   
    assert(add_or_remove == +1 or add_or_remove == -1)
    # NOTE: reversed userobjects in the following call to get the "passive" object (the user receiving 
    # the chat request)
    initiate_contact_object = get_or_create_initiate_contact_object(other_userobject_key, userobject_key)
    initiate_contact_object_key = initiate_contact_object.key()    

    try: 
        db.run_in_transaction(txn, initiate_contact_object_key)
        update_bool = True
    except:
        # transaction failed -- object not modified
        update_bool = False
        
    return update_bool

def invalidate_memcache_for_friends_lists(owner_uid):
    # invalidate memcache for chat structures for the user indicated in owner_uid - this ensures that they will 
    # receive a fresh friend list immediately. 
    all_friends_dict_memcache_key = constants.ALL_CHAT_FRIENDS_DICT_MEMCACHE_PREFIX + owner_uid
    memcache.delete(all_friends_dict_memcache_key)
    
    check_friends_online_last_update_memcache_key = constants.CHECK_CHAT_FRIENDS_ONLINE_LAST_UPDATE_MEMCACHE_PREFIX + owner_uid
    memcache.delete(check_friends_online_last_update_memcache_key)
    
    online_contacts_names_dict_memcache_key = constants.ONLINE_CHAT_CONTACTS_INFO_MEMCACHE_PREFIX + owner_uid
    memcache.delete(online_contacts_names_dict_memcache_key)

def modify_active_initiate_contact_object(action, initiate_contact_object, userobject_key, other_userobject_key, override_minimum_delay = False):
    # modifys the initiate_contact_object based on the "action" that the user has taken
    # userobject refers to the user taking the action
    # other_userobject refers to the profile that is being viewed when the action is taken
    #
    # "active" initiate contact object means the initiate contact object referring to "userobject" kisses,keys,etc.
    # sent to "other_userobject". 
    
    try:
        def txn(initiate_contact_object_key, action):
            # use a transaction to ensure that only a single update to this object will happen at a time.
            counter_modify = 0
            chat_request_action_on_receiver = None
            initiate_contact_object = db.get(initiate_contact_object_key)
            action_stored_str = action + "_stored"
            action_stored_date_str = action + "_stored_date"
            
            if action != "chat_friend":
                # Toggle the value, based on the current setting.
                if not getattr(initiate_contact_object, action_stored_str):
                    setattr(initiate_contact_object, action_stored_str, True)
                    counter_modify = 1
                else:
                    setattr(initiate_contact_object, action_stored_str, False)
                    counter_modify = -1
            else:
                # this is a chat_friend request, which requires more complex processing due to
                # the different states that are possible. 
                (counter_modify, chat_request_action_on_receiver) = \
                 toggle_chat_friend_status(initiate_contact_object)
                # invalidate memcache for chat_friend_tracker so that online users will 
                # immediately see their new friends online
                invalidate_memcache_for_friends_lists(str(userobject_key))
                invalidate_memcache_for_friends_lists(str(other_userobject_key))
                
            # Update the set time for bot setting and removing the action
            setattr(initiate_contact_object, action_stored_date_str, datetime.datetime.now())
            initiate_contact_object.put()  
            return (counter_modify, chat_request_action_on_receiver, initiate_contact_object)
        
        
        initiate_contact_object_modified = False
        action_stored_date_str = action + "_stored_date"
        
        initiate_contact_object_key = initiate_contact_object.key()
    
        action_stored_date = getattr(initiate_contact_object, action_stored_date_str)
        # prevent double submission (rapid clicking) -- check the value needs to be set before writing
        if action_stored_date: # make sure not None
            time_since_stored = datetime.datetime.now() - action_stored_date
        else:
            # this is the first time the action is stored, so an infinite amount of time has passed
            # since the last update.
            time_since_stored = datetime.datetime.max - datetime.datetime.now()
        
        counter_modify = 0
        chat_request_action_on_receiver = None
        if time_since_stored > datetime.timedelta(seconds = 1) or override_minimum_delay: # only process if X seconds have passed
            # update the initiate_contact_object inside a transaction
            try: 
                (counter_modify, chat_request_action_on_receiver, initiate_contact_object) = \
                 db.run_in_transaction(txn, initiate_contact_object_key, action)
                initiate_contact_object_modified = True
            except:
                # transaction failed -- object not modified
                initiate_contact_object_modified = False
        else:
            # we do not write the initiate_contact_object since not enough time has passed since the last click
            pass
            
        return (initiate_contact_object, initiate_contact_object_modified, counter_modify, chat_request_action_on_receiver)
    except:
        error_reporting.log_exception(logging.critical)
            
        
@ajax_call_requires_login
def store_initiate_contact(request, to_uid):
    # stores updates to winks, favorites, etc. This is called when users click on the associated icon. 
    

    userobject = utils_top_level.get_userobject_from_request(request)
    userobject_key = userobject.key()
    
    try:
        
        possible_actions = ('wink', 'favorite', 'kiss', 'key', 'chat_friend', 'blocked')
        other_userobject_key = db.Key(to_uid)
        other_userobject = utils_top_level.get_object_from_string(to_uid)
        
        if request.method != 'POST':
            return HttpResponseBadRequest()
        else:          
            action = request.POST.get('section_name', '')
            if action in possible_actions:
                
                initiate_contact_object = get_or_create_initiate_contact_object(userobject_key, other_userobject_key)
                (initiate_contact_object, initiate_contact_object_modified, counter_modify, chat_request_action_on_receiver) =\
                 modify_active_initiate_contact_object(action, initiate_contact_object, userobject_key, other_userobject_key)
                
                if initiate_contact_object_modified:  
                    
                    # first check that the user has not exceeded their quota for the given action
                    request_denied = False
                    if counter_modify > 0:
                        if action == "key":
                            if userobject.new_contact_counter_ref.num_sent_key >= constants.MAX_KEYS_SENT_ALLOWED:
                                response_text = ugettext("""You have exceeded the limit of %(max_keys)s on the number of keys that you can send. 
                                Before sending additional keys, you must take back keys that you have given to other users.""") \
                                              % {'max_keys' : constants.MAX_KEYS_SENT_ALLOWED}
                                request_denied = True
                                
                        if action == "chat_friend":
                            if userobject.client_paid_status or initiate_contact_object.chat_friend_stored != "request_sent":
                                # VIP clients are allowed to have the max number of chat friends OR
                                # we allow people to accept friend requests even after their free limit on friends has been exceeded. 
                                # ... But not to initiate new friend requests,
                                if userobject.new_contact_counter_ref.num_sent_chat_friend >= MAX_CHAT_FRIEND_REQUESTS_ALLOWED:
                                    response_text = ugettext("""You have exceeded the limit of %(max_requests)s on the number of chat friends
                                    that you are allowed to request and/or accept.
                                    Before requesting/accepting additional chat friends, you must remove some of your current chat friends.""") \
                                                  % {'max_requests' : MAX_CHAT_FRIEND_REQUESTS_ALLOWED}
                                    request_denied = True                                
                            
                            else:
                                # This user is neither VIP nor responding to a friend request, therefore they 
                                # only have the free limit of friends
                                if userobject.new_contact_counter_ref.num_sent_chat_friend >= GUEST_NUM_CHAT_FRIEND_REQUESTS_ALLOWED:
                                    
                                    request_denied = True  
                                    
                                    response_text = ugettext("""
                                    You have %(num_sent_chat_friend)s chat friends, which means that
                                    you have exceeded the limit of %(max_guest_requests)s on the number of chat friends
                                    that you are allowed to request. 
                                    You must remove some of your current chat friends before requesting additional chat friends, or
                                    you can ask the other person to invite you to be their chat friend. """) % \
                                        {'num_sent_chat_friend': userobject.new_contact_counter_ref.num_sent_chat_friend ,
                                         'max_guest_requests' : GUEST_NUM_CHAT_FRIEND_REQUESTS_ALLOWED}
                                     
                                    response_text += ugettext("""
                                    Alternatively, if you wish to increase this limit to %(max_requests)s, 
                                    you could consider becoming a VIP member.""")   % \
                                        {'max_requests' : MAX_CHAT_FRIEND_REQUESTS_ALLOWED}

                        if request_denied:
                            # un-do the request (toggle it) by calling the same function again, Note that we override the 
                            # minimum delay between clicks. 
                            (initiate_contact_object, initiate_contact_object_modified, counter_modify, chat_request_action_on_receiver) =\
                             modify_active_initiate_contact_object(action, initiate_contact_object, userobject_key, other_userobject_key, override_minimum_delay = True)
                            return HttpResponse(response_text)
                                    
                    
               
                    # update the counter for the receiver, except for favorites and blocked since these fields 
                    # will never be displayed or available to the "viewed" user.
                    if action != "favorite" and action != 'blocked':
                        if action != "chat_friend":
                            action_for_contact_count = "num_received_" + action + "_since_last_login"
                        else: 
                            #action == "chat_friend"
                            #
                            # Note chat_request_action_on_receiver should be either friend_request or friend_confirmation
                            action_for_contact_count = "num_received_" + chat_request_action_on_receiver + "_since_last_login" 
                            # update the chat_request status on the passive object. 
                            update_bool = modify_passive_initiate_contact_object(chat_request_action_on_receiver, counter_modify, userobject_key, other_userobject_key)
                            if not update_bool:
                                error_reporting.log_exception(logging.critical, 
                                                              error_message = "passive initiate_contact_object failed to update between %s and %s" %
                                                              (userobject.username, other_userobject.username))
                            
                            
                        if counter_modify > 0:
                            hours_between_notifications = utils.get_hours_between_notifications(other_userobject, 
                                                        constants.hours_between_new_contacts_notifications)
                        else: 
                            hours_between_notifications = "NA" # should not be required/accessed
                        
                        # update the *receiver's* counters for kisses, winks, etc.
                        other_userobject.new_contact_counter_ref = modify_new_contact_counter(other_userobject.new_contact_counter_ref.key(), \
                                                   action_for_contact_count, counter_modify, hours_between_notifications, 
                                                   update_notification_times = True)
                        
                        info_message = "Modifying %s on %s by %s" %(action_for_contact_count, other_userobject.username, counter_modify)
                        logging.debug(info_message)
                                                   
                        # if notification for sending the user notification is past due, send it now.
                        if other_userobject.new_contact_counter_ref.when_to_send_next_notification <= datetime.datetime.now():
                            
                            try:
                                # by construction, this should never execute unless the email address is valid - if email address is not
                                # valid, then the date of when_to_send_next_notification should be set to max. 
                                assert(other_userobject.email_address_is_valid)
                                # add a one minute delay before sending the message notification - this means that if the user sends a wink (or whatever)
                                # and quickly changes their mind, the error checking code in the notification function will catch that the 
                                # when_to_send_next_notification time is no longer valid, and the email will be cancelled. 
                                countdown_time = 60

                                taskqueue.add(queue_name = 'fast-queue', countdown = countdown_time, \
                                              url='/rs/admin/send_new_message_notification_email/', params = {
                                                  'uid': str(other_userobject.key())})
                            except:
                                error_reporting.log_exception(logging.critical)
                                
                        if action == "chat_friend" or action == "key":
                            # Update the counters on *owners* "new_contact_counter_ref" object to reflect how many
                            # friend requests or how many keys they have sent. 
                            # For now we only track keys and friend requests
                            sent_action_for_contact_count = "num_sent_" + action
                            modify_new_contact_counter(userobject.new_contact_counter_ref.key(), \
                                                   sent_action_for_contact_count, counter_modify, 
                                                   hours_between_notifications = None, update_notification_times = False)


                    elif action == 'favorite':
                        # we must check if the users have sent messages between them, and if so
                        # must update the users_have_sent_messages (ie. mail) object to reflect that this 
                        # user is now a "favorite". This is necessary due to the dual structure of favorites
                        # which must appear in both the mailbox as well as the contacts lists.
                        if counter_modify == 1:
                            new_action_boolean = True;
                        if counter_modify == -1:
                            new_action_boolean = False
                        if counter_modify == 1 or counter_modify == -1:    
                            update_users_have_sent_messages_object_favorite_val(userobject, other_userobject, new_action_boolean)

            else:
                error_reporting.log_exception(logging.warning, error_message = "unknown action: %s posted" % action)
                                                
            return HttpResponse("OK")
        
        # end if/else request.method != 'POST'
        
    except:
        error_message = "User %s has triggered an exception" % (userobject.username)
        error_reporting.log_exception(logging.critical, error_message = error_message)
        return HttpResponseServerError("Error")
        
    
#############################################

def initialize_and_store_spam_tracker(current_spam_tracker):

    if current_spam_tracker == None:

        spam_tracker = SpamMailStructures()

        spam_tracker.datetime_first_mail_sent_today  = datetime.datetime.now()
        
        spam_tracker.num_mails_sent_today = 0
        spam_tracker.num_mails_sent_total = 0
        
        spam_tracker.num_times_reported_as_spammer_total = 0
        
        spam_tracker.num_times_blocked = 0
        
        spam_tracker.num_times_reported_as_good_today = 0
        spam_tracker.num_times_reported_as_good_total = 0
        
        spam_tracker.number_of_captchass_solved_total = 0         
        
        spam_tracker.put()
        
        return spam_tracker
    else:
        return current_spam_tracker
      

#############################################    


def update_users_have_sent_messages(sender_userobject, receiver_userobject, receiver_has_blocked_sender = False):
    # updates UsersHaveSentMessages model to ensure that all users that have previously had contact
    # will have an entry in the structure. Additionally, this structure will be updated
    # any time a new message is sent between two users, so that the results can be ordered
    # by most the date of most recent contact.
    #
    # Note that for each message, two entries are generated. One with the sender as the "owner",
    # and the other with the receiver as the "owner". This is necessary for queries that will
    # be preformed for the mailbox of a particular "owner".
    
    
    ################################ 
    def txn(sender_userobject_key, receiver_userobject_key, owner_ref, other_ref, 
            is_favorite, receiver_has_blocked_sender):

        return_val = ''
        
        have_sent_messages_obj = utils.get_have_sent_messages_object(owner_ref, other_ref)
        #logging.debug("NEW have_sent_message_object at start of txn: %s" % have_sent_messages_obj)
        if not have_sent_messages_obj:
            have_sent_messages_obj = utils.get_have_sent_messages_object(owner_ref, other_ref, create_if_does_not_exist = True)
            is_new_contact = True
        else:
            is_new_contact = False

        have_sent_messages_obj.owner_ref = owner_ref
        have_sent_messages_obj.other_ref = other_ref                                
        have_sent_messages_obj.last_m_date = datetime.datetime.now()
        have_sent_messages_obj.unique_m_date = "%s_%s" % (datetime.datetime.now(), sender_userobject_key)
        have_sent_messages_obj.mailbox_to_display_this_contact_messages = "inbox"
        have_sent_messages_obj.other_is_favorite = is_favorite
        

        
        # Note: if a user sends a message to themself, this will show up as a received message due to the
        # ordering of the if/else sequence below. This is intentional, so that they can see that the
        # messaging system actually works. 
        
        if receiver_userobject_key == owner_ref:
            # new message has not been read by the receiver yet (cannot have been read yet, because they
            # just received the message)
            have_sent_messages_obj.owner_is_sender = False        
                   
            if not receiver_has_blocked_sender:
                # only increase the unread_contact_counter if the current object is the receiver, and only if this
                # is already marked as read (which means that a new *unread* message should therefore increase
                # the counter).
                if is_new_contact or have_sent_messages_obj.message_chain_has_been_read:
                    return_val = "increase_receiver_unread_contact_count"
                else:
                    return_val = "only_update_when_to_send_next_notification"
            else:
                return_val = '' # do nothing
            
            have_sent_messages_obj.message_chain_has_been_read = False
            
            if receiver_userobject_key == sender_userobject_key:
                # user has sent a message to themselves - however since the "sender_userobject_key == owner_ref" branch 
                # below will never be executed we must increase the num_messages_to_other_sent_today counter here.
                have_sent_messages_obj.num_messages_to_other_sent_today += 1          
            
        elif sender_userobject_key == owner_ref:
            have_sent_messages_obj.owner_is_sender = True
            
            have_sent_messages_obj.num_messages_to_other_sent_today += 1            

            # if the chain has not been read, but the owner is responding .. consider it to have been
            # read anyway, and decrease the unread message counter.
            if not is_new_contact and not have_sent_messages_obj.message_chain_has_been_read:
                return_val = "decrease_sender_unread_contact_count"
                
            # consider that sender has always read the message
            have_sent_messages_obj.message_chain_has_been_read = True


        else:
            raise Exception("Unknown value")
        

        have_sent_messages_obj.put()
        #logging.debug("NEW have_sent_message_object at end of txn: %s" % have_sent_messages_obj)
        #logging.debug("NEW return_val at end of txn: %s" % return_val)
        return return_val # end transaction
    ################################ 

    try:

        receiver_userobject_key = receiver_userobject.key()
        sender_userobject_key = sender_userobject.key()
        
        
        owner_other_ref_def = [(sender_userobject_key, receiver_userobject_key), 
                               (receiver_userobject_key, sender_userobject_key)]
        
    
        for (owner_ref, other_ref) in owner_other_ref_def:
            
            owner_userobject = utils_top_level.get_object_from_string(str(owner_ref))
            other_userobject = utils_top_level.get_object_from_string(str(other_ref))
            
            #try:
                #if owner_ref == sender_userobject_key:
                    #logging.debug("Owner is sender")
                #else:
                    #logging.debug("Other is sender")                        
                #logging.debug("owner_userobject: %s" % owner_userobject.username)
                #logging.debug("other_userobject: %s" % other_userobject.username)
                #logging.debug("sender_userobject unread_count: %s" % sender_userobject.unread_mail_count_ref)
                #logging.debug("receiver_userobject unread_count: %s" % receiver_userobject.unread_mail_count_ref)
                
            #except:
                #error_reporting.log_exception(logging.critical)  
            
            # we need to pull out the initiate_contact_object to check if the other user is a favorite, this is because 
            # favorite status must be marked both on messages, as well as on the initiate_contact_object.
            initiate_contact_object = utils.get_initiate_contact_object(owner_ref, other_ref)
            if initiate_contact_object: 
                is_favorite = initiate_contact_object.favorite_stored
            else:
                is_favorite = False
    
            # update the have_sent_messages object to reflect that these users have now had contact, and that
            # the sender has read the emails between these two users, and the receiver has not read the 
            # emails between these two users. 
            modify_count_string = db.run_in_transaction(txn,  sender_userobject_key, receiver_userobject_key,
                                                        owner_ref, other_ref, is_favorite, receiver_has_blocked_sender)  
            
            # Now, modify the counters that track the number of undread "messages" (from unique contacts)
            # This is done in a transaction to deal with conflicts. Additionally, this is done outside
            # of the previous transaction, because only a single model can be handldled in a single transaction.
            if not modify_count_string:
                pass
            
            elif modify_count_string == "increase_receiver_unread_contact_count":
                
                try:
                    hours_between_notifications = utils.get_hours_between_notifications(receiver_userobject, constants.hours_between_message_notifications)
                    increment_or_decrement_value = 1
                    receiver_userobject.unread_mail_count_ref = \
                                   mailbox.modify_user_unread_contact_count(receiver_userobject.unread_mail_count_ref, increment_or_decrement_value, \
                                                                            hours_between_notifications)
                except:
                    error_message = "User: %s counter exception" % receiver_userobject.username
                    error_reporting.log_exception(logging.error, error_message=error_message)  
                    
            elif modify_count_string == "only_update_when_to_send_next_notification":
                try:
                    hours_between_notifications = utils.get_hours_between_notifications(receiver_userobject, constants.hours_between_message_notifications)
                    increment_or_decrement_value = 0
                    receiver_userobject.unread_mail_count_ref = \
                                   mailbox.modify_user_unread_contact_count(receiver_userobject.unread_mail_count_ref, increment_or_decrement_value, \
                                                                            hours_between_notifications)
                except:
                    error_message = "User: %s counter exception" % receiver_userobject.username
                    error_reporting.log_exception(logging.error, error_message=error_message)  
                    
            elif modify_count_string == "decrease_sender_unread_contact_count":
                try:
                    increment_or_decrement_value = -1
                    sender_userobject.unread_mail_count_ref = \
                                 mailbox.modify_user_unread_contact_count(sender_userobject.unread_mail_count_ref, increment_or_decrement_value, "NA")
                except:
                    error_message = "User: %s counter exception" % sender_userobject.username
                    error_reporting.log_exception(logging.error, error_message=error_message)    
            else:
                raise Exception("Unknown mailbox counter %s" % modify_count_string)
            
            if owner_ref == other_ref:
                # user is sending a message to themself -- no need to loop again.
                break;
    
    except:
        error_reporting.log_exception(logging.critical)   
        return None
    



def store_mail_message(sender_userobject_key, receiver_userobject_key, parent_key, text):
    #
    # stores a MailModel object for the message between two users. 
    
    mail_message = models.MailMessageModel(parent=parent_key)
    mail_message.m_text  = text
    mail_message.m_date = datetime.datetime.now()
    mail_message.unique_m_date =  "%s_%s" % (datetime.datetime.now(), sender_userobject_key)
    mail_message.m_from = sender_userobject_key
    mail_message.m_to =  receiver_userobject_key                  
    mail_message.put()    


def actually_store_send_mail(sender_userobject, to_uid, text):  
    # Called from client directly to store the mail and to update the assocated data structures.
    
    try:
        sender_userobject_key = sender_userobject.key()
        receiver_userobject_key = db.Key(to_uid)
        
        sender_uid = str(sender_userobject_key)
        receiver_uid = str(receiver_userobject_key)
        
        # check to make sure that the receiver has not blocked the sender. If they have been blocked, we still
        # send the message, but immediately move it to the deleted mailbox. We also do NOT want to send any
        # notifications of the new message. Note: we look this up in with in the receivers data structure, since
        # they would have stored the block (as opposed to the sender having blocked the receiver - which is irrelevant
        # right now).
        reverse_initiate_contact_object = utils.get_initiate_contact_object(receiver_userobject_key, sender_userobject_key) 
        if reverse_initiate_contact_object:
            sender_is_blocked = reverse_initiate_contact_object.blocked_stored
        else:
            sender_is_blocked = False
        
        receiver_userobject = utils_top_level.get_object_from_string(receiver_uid)
        # only update the have_sent_messages if the user is not blocked
        update_users_have_sent_messages(sender_userobject, receiver_userobject, sender_is_blocked)

        parent_key = utils.get_fake_mail_parent_entity_key(sender_uid, receiver_uid)
        
        # do not allow extremely huge messages to be sent (to prevent attacks on our storage space)
        text = text[:MAIL_TEXTAREA_CUTOFF_CHARS]
        # make sure that the user hasn't entered a word that is longer than the line width
        text = utils.break_long_words(text, constants.MAX_CHARS_PER_WORD)
        
        store_mail_message(sender_userobject_key, receiver_userobject_key, parent_key, text)

        if not sender_is_blocked:
            # if the time passed since the last notification sent to the user has exceeded their mail preference, then
            # send out the email now. This must come AFTER unread_mail_count is updated.
            if receiver_userobject.unread_mail_count_ref.when_to_send_next_notification <= datetime.datetime.now():
                
                try:
                    # by construction, email_address should be valid if the when_to_send_next_notification value is not "max"
                    assert(receiver_userobject.email_address_is_valid)             
                    taskqueue.add(queue_name = 'fast-queue', url='/rs/admin/send_new_message_notification_email/', params = {
                        'uid': str(receiver_userobject.key())})
                except:
                    error_reporting.log_exception(logging.critical)
                        
        if sender_is_blocked:
            # move this message to the deleted folder in the receivers mailbox
            have_sent_messages_key = utils.get_have_sent_messages_key(receiver_userobject_key, sender_userobject_key)
            mailbox.modify_message(have_sent_messages_key, 'trash')
                    
        return HttpResponse('OK')     

    except: 
        error_reporting.log_exception(logging.critical)   
        return HttpResponse('Error')       
    
#############################################

def determine_if_captcha_is_shown(userobject, have_sent_messages_bool):
    # This function computes the statistics required for determining if this user must filll in  a captcha to send a message
    # It returnns the boolean indicating if a captcha is required, and also returns a string that is used to inform
    # the  user about their currrent spam-sending statistics.
    
    show_captcha = False
    spam_statistics_string = ''
    
    if userobject.client_is_exempt_from_spam_captchas:
        # if this user is paid member, they do not have to see messages about spam, or to solve captchas
        # in the case that someone has indicated that they sent spam. 
        return (show_captcha, spam_statistics_string)

    if not userobject.spam_tracker:
        # if it doesn't exist, create it! (will only be done once in the life of every user..
        # and only for old users that were not initialized correctly -- can remove this
        # code if DB maintenance is done.
        userobject.spam_tracker = initialize_and_store_spam_tracker(userobject.spam_tracker) 
        put_userobject(userobject)  
        
    spam_tracker = userobject.spam_tracker
        

    if spam_tracker.num_times_reported_as_spammer_total > spam_tracker.number_of_captchass_solved_total \
       and not have_sent_messages_bool: 

        # each message that is marked as a SPAM requires that the user enter a captcha.
        show_captcha = True  
      

    # only show spam statistics for profiles that the user has not already had contact with
    if not have_sent_messages_bool:
        
        if spam_tracker.num_mails_sent_total > 0:
            percent_total_spam = float(spam_tracker.num_times_reported_as_spammer_total)/spam_tracker.num_mails_sent_total
        else:
            percent_total_spam = 0
        
        spam_statistics_string += u"""<div><strong>%(spam_stats_string)s</strong>
        %(num_times_reported)s %(of_string)s %(num_mails_sent)s %(sent_string)s (%(percent).0f%%).<br>
        %(if_you_send_spam)s<br><br></div>"""% {
            'spam_stats_string' : ugettext("Statistics of spam sent from your account:"),    
            'of_string' : ugettext("of"), 
            'sent_string' : ugettext("sent"),
            'if_you_send_spam' : ugettext('If you send spam, you will have to write "captchas" before being allowed \
to send more messages. Additionally, if you send a lot of spam, your messages will be sent directly to the spam mailbox.'),
            
            'num_times_reported' : spam_tracker.num_times_reported_as_spammer_total, 
            'num_mails_sent' : spam_tracker.num_mails_sent_total,
            'percent': 100*percent_total_spam}

    
    
    return (show_captcha, spam_statistics_string)


#############################################
def check_captcha(request):
    # verifies if the captcha has been solved correctly.
    
    challenge = request.POST.get('recaptcha_challenge_field')
    response  = request.POST.get('recaptcha_response_field')
    remoteip  = environ['REMOTE_ADDR']
    
    cResponse = captcha.submit(
                   challenge,
                   response,
                   remoteip)
    
    return cResponse.is_valid
            
#############################################    
    
@ajax_call_requires_login
def store_send_mail(request, to_uid, text_post_identifier_string, captcha_bypass_string, have_sent_messages_string):
    # Preforms authentication on the message, and if everything is OK, it 
    # stores the sent mail message into the database 
       
    try:
    
        sender_userobject =  utils_top_level.get_userobject_from_request(request)
        from_uid =  request.session['userobject_str']
        
        response_is_valid = False
            
        # check if the correct code for bypassing the captcha has been passed in.. otherwise, verify that
        # the captcha has been solved before storing anything.
        if captcha_bypass_string == "no_bypass": # I break this portion of the if out for efficiency
            has_captcha = True
        elif captcha_bypass_string != compute_captcha_bypass_string(from_uid, to_uid):
            has_captcha = True
        else: has_captcha = False
        
        if request.method != 'POST':
            # Must be a post for it to work -- this should never actually execute.
            return HttpResponseBadRequest()
        else:
            
            if has_captcha:
                response_is_valid = check_captcha(request)
                # CAPTCHA STUFF
    
            else:
                response_is_valid = True
          
            if response_is_valid:
                text = request.POST.get(text_post_identifier_string, '')
                # make sure that the user isnt trying to do an html/javascript injection
                text = strip_tags(text)
            else:
                # error = cResponse.error_code
                return HttpResponse(ugettext("Captcha is incorrect, try again"))
            
            spam_tracker = sender_userobject.spam_tracker   
            
            
            # If they are trying to send too many messages in a single day, block the extra messages. This is required to prevent
            # "disk-usages attacks" on the database (ie. prevent two users that have previously had contact from sending a million
            # messages between them)
            have_sent_messages_object = utils.get_have_sent_messages_object(from_uid, to_uid)
            

            if have_sent_messages_object and utils.check_if_reset_num_messages_to_other_sent_today(have_sent_messages_object):
                
                have_sent_messages_object.datetime_first_message_to_other_today = datetime.datetime.now()
                have_sent_messages_object.num_messages_to_other_sent_today = 0
                have_sent_messages_object.put()
                
            if not utils.check_if_allowed_to_send_more_messages_to_other_user(have_sent_messages_object):
                error_message = u"%s" % constants.ErrorMessages.num_messages_to_other_in_time_window(constants.NUM_MESSAGES_TO_OTHER_USER_IN_TIME_WINDOW, 
                                                                                                     constants.NUM_HOURS_WINDOW_TO_RESET_MESSAGE_COUNT_TO_OTHER_USER)
                error_reporting.log_exception(logging.warning, error_message=error_message)  
                return HttpResponse(error_message)                    
        
        
    
            # don't allow blank emails to be sent
            if not text:
                return HttpResponse(ugettext("You have not written a message. You must write something before sending it."))
             
            spam_tracker_modified = False
            # don't count messages that are sent to previous contacts in the spam statistics
            if have_sent_messages_string == "have_not_had_contact":
                if spam_tracker.datetime_first_mail_sent_today + datetime.timedelta(hours = NUM_HOURS_TO_RESET_MAIL_COUNT - RESET_MAIL_LEEWAY) <  datetime.datetime.now():
                    
                    spam_tracker.datetime_first_mail_sent_today  = datetime.datetime.now()
                    spam_tracker.num_mails_sent_today = 0
                    
                # Make sure they don't exceed the number of new contacts allowed in a single day. This condition could
                # occur if they open a bunch of windows to different profiles before using their message quota, and then attempting
                # to send messages to each user. 
                
                if not sender_userobject.client_paid_status:
                    num_emails_per_day = MAX_EMAILS_PER_DAY
                else:
                    # VIP member has extra messages allocated
                    num_emails_per_day = constants.vip_num_messages_allowed
                                
            
                if spam_tracker.num_mails_sent_today >= num_emails_per_day:
                    error_message = "You have already sent messages to %(num)s new contacts." % {'num': num_emails_per_day}
                    error_reporting.log_exception(logging.warning, error_message=error_message)  
                    return HttpResponse(error_message)                 
                                    
                # only count the message in the spam tracker if it is to a new person
                spam_tracker.num_mails_sent_today += 1
                spam_tracker_modified = True
                
            # count all messages sent, for statistical reporting of the percentage of times this person 
            # has sent spam.
            spam_tracker.num_mails_sent_total += 1
            
            if has_captcha:
                spam_tracker.number_of_captchass_solved_total += 1
                spam_tracker_modified = True
            
            if spam_tracker_modified:
                spam_tracker.put()
                       
            return_val = actually_store_send_mail(sender_userobject, to_uid, text)

        # Mark the session as modified, which causes a new cookie to be written (with an updated expiry time)
        # Because if they are sending mails (ie they are active) we want to give extra time before session expiry
        # This also reduces the chances of a logout in the middle of sending a mail message.
        request.session.modified = True      
        
        return return_val

    except: 
        error_reporting.log_exception(logging.critical)   
        return HttpResponseServerError(ugettext('Internal error - this error has been logged, and will be investigated immediately')) 


def increase_reporting_or_reporter_unacceptable_count(model_class, userobject_key, increase_or_decrease_count):
    # Function for keeping track of how many times a profile has been marked as unacceptalbe (or how many
    # times a particular user has marked other profiles as unacceptable - depending on the model_class value)
    # We expect model_class to contain either CountReportingProfile or CountUnacceptableProfile
    # and it will update the appropriate counter. 
    
    def txn(profile_reporting_tracker):
        
        if not profile_reporting_tracker:
            profile_reporting_tracker = model_class()
            profile_reporting_tracker.profile_ref = userobject_key   
            
        profile_reporting_tracker.count += increase_or_decrease_count
        
        if model_class == models.CountUnacceptableProfile:
            if profile_reporting_tracker.datetime_first_reported_in_small_time_window + datetime.timedelta(hours = constants.SMALL_TIME_WINDOW_HOURS_FOR_COUNT_UNACCEPTABLE_PROFILE_REPORTS) <  datetime.datetime.now():
                # window has closed, start a new one.
                profile_reporting_tracker.datetime_first_reported_in_small_time_window  = datetime.datetime.now()
                profile_reporting_tracker.num_times_reported_in_small_time_window = 1
            else:
                # within the window - so increase the count
                profile_reporting_tracker.num_times_reported_in_small_time_window += 1
        
        profile_reporting_tracker.put()
        return profile_reporting_tracker 
        
        
        
    query_filter_dict = {}   
    query_filter_dict['profile_ref'] = userobject_key
    
    query = model_class.all()
    for (query_filter_key, query_filter_value) in query_filter_dict.iteritems():
        query = query.filter(query_filter_key, query_filter_value)    
        
    profile_reporting_tracker = query.get()
    profile_reporting_tracker = db.run_in_transaction(txn, profile_reporting_tracker)

    return profile_reporting_tracker
    
    
@ajax_call_requires_login
def store_report_unacceptable_profile(request, display_uid):
    # This function is used for allowing users to notify us if a particular profile should be considered unacceptable. 
    # Once a profile receives a certian number of reports, we will generate a warning, and we will investigate.
    
    try:
        sender_userobject =  utils_top_level.get_userobject_from_request(request)
        owner_uid =  request.session['userobject_str']
        displayed_uid_key = db.Key(display_uid)
        owner_uid_key = db.Key(owner_uid)    
        
        mark_unacceptable_profile = utils.check_if_user_has_denounced_profile(owner_uid, display_uid)
        
        if not mark_unacceptable_profile:
            # if the reporting user has not already denounced the current profile, then we add this information
            # to the database.
            
    
                
            mark_unacceptable_profile = models.MarkUnacceptableProfile()
            mark_unacceptable_profile.displayed_profile = displayed_uid_key
            mark_unacceptable_profile.reporter_profile = owner_uid_key
            mark_unacceptable_profile.put()
            
            increase_or_decrease_count = 1 # we are reporting an unacceptable profile
            response = text_fields.profile_reported
        else:
            # the user has previously denounced the current profile, but is now retracting their complaint -- so, delete the 
            # mark_unacceptable_profile object
            mark_unacceptable_profile.delete()
            increase_or_decrease_count = -1 # we are removing a report of an unacceptable profile
            response = text_fields.profile_unreported
         
        count_reporting_profile = increase_reporting_or_reporter_unacceptable_count(models.CountReportingProfile, owner_uid_key, increase_or_decrease_count)
        
        count_unacceptable_profile = increase_reporting_or_reporter_unacceptable_count(models.CountUnacceptableProfile, displayed_uid_key, increase_or_decrease_count)
        if count_unacceptable_profile.count >= NUM_REPORTS_FOR_UNACCEPTABLE_PROFILE:
            displayed_profile = utils_top_level.get_object_from_string(display_uid)
            error_message = """Profile %s has been reported as unacceptable %s times<br>
            Most recent report by: %s who has reported %s profiles as unacceptable.<br>""" \
                          % (displayed_profile.username, count_unacceptable_profile.count, sender_userobject.username, count_reporting_profile.count)
            email_utils.send_admin_alert_email(error_message)
            logging.critical(error_message)
            
            
        if sender_userobject.creation_date <  datetime.datetime.now() - datetime.timedelta(weeks = 1):
            # only allow users that have been members for over a week to start to eliminate malicious profiles - this prevents someone
            # from signing up a bunch of fake accounts only for the purpose of eliminating other accounts - could also check that the profile
            # has been "active" for additional security - add this in the future.
            
            if count_unacceptable_profile.num_times_reported_in_small_time_window > constants.SMALL_TIME_WINDOW_MAX_UNACCEPTABLE_PROFILE_REPORTS_BEFORE_BAN:
                # if this user has been reported as unacceptable by many users in a short time period, then we ban their account and block their IP
                displayed_profile = utils_top_level.get_object_from_string(display_uid)    
                blocked_ip = displayed_profile.last_login_ip_address
                
                # Note could consider calling batch_jobs.batch_fix_remove_all_users_with_given_ip_or_name to remove all profiles that have
                # ever been accessed from this IP - think about this in the future
                error_message = "Profile %s has been deleted due to reports from other users in the time window" % displayed_profile.username 
                email_utils.send_admin_alert_email(error_message)
                logging.critical(error_message)
                login_utils.delete_or_enable_account_and_generate_response(request, displayed_profile, delete_or_enable = "delete", reason_for_profile_removal = "terms")
                
                # have not yet implemented the code to actually check blocked IPs and block them - this will be done in the future.
                blocked_ip_object = models.TemporarilyBlockedIPAddresses(blocked_ip = blocked_ip)
                blocked_ip_object.put()
        
        return HttpResponse(response)
    except:
        error_reporting.log_exception(logging.critical, request=request, error_message="Unable to report profile as unacceptable")        
        return HttpResponse("Error")
    

def get_alex_userobject():
    # first, query for "Alex" which is the account that will send the welcome message.
    
    
    query = UserModel.gql("WHERE username = :username AND is_real_user = True ORDER BY last_login_string DESC " , 
                          username = constants.ADMIN_USERNAME)
    alex_object = query.get()    
    
    if not alex_object:
        error_reporting.log_exception(logging.critical, error_message="Unable to get ADMIN userobject")
        
    return alex_object
        

#############################################
def welcome_new_user(request):
    
    # sends a welcome message to a new user.
    userobject =  utils_top_level.get_userobject_from_request(request)
    
    alex_object = get_alex_userobject()
    
    if (alex_object):
        # make sure we don't send messages from a backup userobject!
        try:
            to_uid = str(userobject.key())
            if settings.BUILD_NAME != "Language" and settings.BUILD_NAME != "Friend":
                replacement1 = ugettext('"wink" or a "kiss"')
                replacement2 = ugettext('winks, kisses,')
            else:
                replacement1 = ugettext('"greeting"')
                replacement2 = ugettext('greetings')
                
            text = ugettext(
                u"""Welcome to %(app_name)s, and good luck with your search! %(replacement1)s %(replacement2)s""") % {
                    'app_name': settings.APP_NAME, 'replacement1':replacement1, 'replacement2':replacement2}

            actually_store_send_mail(alex_object, to_uid, text)
 
        except:
            error_reporting.log_exception(logging.error, error_message="Unable to send welcome message")
            
            
#############################################
def setup_new_user_defaults_and_structures(userobject, username, lang_code):
    """ set sensible initial defaults for the profile details. 
        Also, sets other defaults that need to be configured upon login.
        lang_code: the langage that the user is viewing the website in.
        native_language: (if set -- currenly only in Language) refers to the native language that the user speaks.
        Note, the user could be viewing the website in English, but be a native speaker of German .. 
        therefore we would mark him initally as speaking both English and German. 
    """
    
    copy_principal_user_data_fields_into_ix_lists(userobject)
    
    userobject.email_options = ['daily_notification_of_new_messages_or_contacts']
    

    for field_name in UserProfileDetails.enabled_checkbox_fields_list:
        setattr(userobject, field_name, ['prefer_no_say' ])
            
    if settings.BUILD_NAME == "Language":
        
        # set language fields to ['----', *language* ], since we know that the user has already specified 
        # a language (only for LikeLangage)
        userobject.languages = [u'----',]
        userobject.languages.append(userobject.native_language)
            
        userobject.languages_to_learn = [u'----',]
        userobject.languages_to_learn.append(userobject.language_to_learn)
    else:
        try:
            # set the languages field to include the language that the user is currently viewing this website in.
            # Note: we don't do this for Language, because viewing/reading in a language is not enough information 
            # for us to determine if the user is tryingto learn the language, or if they speak well enough to teach
            # someone else. Additionally, in Language, we have the user language. Here we are inferring it.
            userobject.languages = []
            userobject.languages.append(localizations.language_code_transaltion[lang_code])
        except:
            error_reporting.log_exception(logging.critical, error_message = "Error, unknown lang_code %s passed in" % lang_code)
            userobject.languages = ['english',]
            

    userobject.last_login =  datetime.datetime.now()
    userobject.last_login_string = str(userobject.last_login)

    userobject.previous_last_login = datetime.datetime.now()
    
    userobject.hash_of_creation_date = utils.passhash(str(userobject.creation_date))
        
    (userobject.unique_last_login, userobject.unique_last_login_offset_ref) = \
     login_utils.get_or_create_unique_last_login(userobject, username)
    
    userobject.unread_mail_count_ref = utils.create_unread_mail_object()
    userobject.new_contact_counter_ref = utils.create_contact_counter_object()
    
    userobject.spam_tracker = initialize_and_store_spam_tracker(userobject.spam_tracker) 
    
    userobject.user_tracker = utils.create_and_return_usertracker()
        
    sharding.increment("number_of_new_users_shard_counter")

    # setup structures for chat
    owner_uid = str(userobject.key()) 

    # userobject will be put in the function that called this. 
    return userobject 
    

def store_new_user_after_verify(request, fake_request=None):
    # Store the user information passed in the request into a userobject.
    # Does some validation to prevent attacks 
    

    error_list = []
            
    try:
        lang_idx = localizations.input_field_lang_idx[request.LANGUAGE_CODE]
        
        if not fake_request:
            login_dict = login_utils.get_login_dict_from_post(request, "signup_fields")
        else:
            fake_request.LANGUAGE_CODE = request.LANGUAGE_CODE
            login_dict = login_utils.get_login_dict_from_post(fake_request, "signup_fields")
    
        error_list += login_utils.error_check_signup_parameters(login_dict, lang_idx)
                    
        # create a dictionary for the "GET string" in case there are errors and we need to re-direct the user back to the login page.
        back_to_login_page_dict = {}       
        for field in UserSpec.signup_fields_to_display_in_order +['sub_region', 'region', 'country', 'password_hashed', 'login_type', 'referring_code']:
            # remember that sub_region, region, can be empty if they have not been specified -- this is assumed by the code that
            # pulls data from ajax calls -- therefore, this should not be considered an error.
            if not fake_request:
                # we use a "fake_request" to allow us to simulate a login when the user clicks on an authorization
                # link in an email that we sent to them.
                field_val = request.REQUEST.get(field, '')
            else:
                field_val = fake_request.REQUEST.get(field, '')
                
            back_to_login_page_dict[field] = field_val    
        url_for_re_signup = "/?%s" % login_utils.generate_get_string_for_passing_login_fields(back_to_login_page_dict)   
        
                    
        if error_list:
            # if there is an error, make them re-do login process (I don't anticipate
            # this happeneing here, since all inputs have been previously verified).
            error_message = repr(error_list)
            error_reporting.log_exception(logging.error, error_message=error_message)
            return (url_for_re_signup)
        
        login_dict['username'] = login_dict['username'].upper()
        username = login_dict['username']
        assert(username)
        password = login_dict['password']
        assert(password)
        # if the username is already registered, and the password is the correct password
        # for the given username, then do not add another user into the database. 
        # Re-direct the user to their home page. --This can happen under normal circumstances
        # if the response to the captcha doesn't arrive before a timeout, and the user has
        # been requested to enter a captcha for a username that has just been registered without
        # the user knowing about it. This can also happen if two users sign-up with the same name
        # at the same moment (before the object is written to the database) -- and if they have 
        # chosen the same password, they will be directed to the same account (this is a possible
        # bug with a one in a billion chance of actually being hit).
        query_filter_dict = {}
        query_filter_dict['username'] = username
        query_filter_dict['password'] = password    
        query_filter_dict['is_real_user'] = True
        query_filter_dict['user_is_marked_for_elimination'] = False
        query_order_string = "-%s" % 'last_login_string'
        query = UserModel.all().order(query_order_string)
        for (query_filter_key, query_filter_value) in query_filter_dict.iteritems():
            query = query.filter(query_filter_key, query_filter_value)
        userobject = query.get()
        
        if userobject:
            # user is already authorized -- send back to login
            return ('/?already_registered=True&username_email=%s&login_type=left_side_fields' % userobject.username)          
        
        # make sure that the user name is not already registered. (this should not happen
        # under normal circumstances, but could possibly happen if someone is hacking our system or if two users have gone through
        # the registration process and attempted to register the same username at the same moment)
        query = UserModel.gql("WHERE username = :username", username = username)
        if query.get():
            error_reporting.log_exception(logging.warning, error_message = 'Registered username encountered in storing user - sending back to main login')       
            return (url_for_re_signup)
    
    except:
        error_reporting.log_exception(logging.critical)   
        return ""

        
    # do not change the order of the following calls. Userobject is written twice because this
    # is necessary to get a database key value. Also, since this is only on signup, efficiency is
    # not an issue.
    
    try:
        # passing in the login_dict to the following declaration will copy the values into the user object.
        userobject = UserModel(**login_dict)
        userobject.is_real_user = True    
        
        userobject.username_combinations_list = utils.get_username_combinations_list(username)
        utils.put_userobject(userobject)
               
        userobject.search_preferences2 = login_utils.create_search_preferences2_object(userobject, request.LANGUAGE_CODE) 
        userobject = setup_new_user_defaults_and_structures(userobject, login_dict['username'], request.LANGUAGE_CODE)

        
        # store indication of email address validity (syntactically valid )
        if login_dict['email_address'] == '----':
            userobject.email_address_is_valid = False
        else:
            userobject.email_address_is_valid = True
            
            if fake_request:
                # if we have entered into this function with a fake request, then we know that the user has entered into the system
                # by clicking on the verification link in an email. Therefore, we can update the user_tracker object with the
                # email address, since we have now confirmed that it is truly verified.
                utils.update_email_address_on_user_tracker(userobject, login_dict['email_address'])
            try:
                assert(verify_email_address_is_valid_and_send_confirmation(request, userobject, login_dict['email_address']))
            except:
                error_reporting.log_exception(logging.warning, error_message = 'Unable to queue confirmation email to %s' % login_dict['email_address'])       
        
                
        userobject.registration_ip_address = environ['REMOTE_ADDR']   
        userobject.last_login_ip_address = environ['REMOTE_ADDR'] 
        userobject.last_login_country_code = request.META.get('HTTP_X_APPENGINE_COUNTRY', None)
        
        utils.put_userobject(userobject)

        login_utils.store_session(request, userobject)
        
        lang_set_in_session = site_configuration.set_language_in_session(request, request.LANGUAGE_CODE)
        assert(lang_set_in_session)    
        
        # create backups of the userobject
        backup_data.update_or_create_userobject_backups(request, userobject)
           
        # send the user a welcome email and key and wink from Alex
        welcome_new_user(request)
    
        owner_uid = str(userobject.key())
        owner_nid = userobject.key().id()
        
    except:
        # if there is any failure in the signup process, clean up all the data stored, and send the user back to the login page with the data that they
        # previously entered.
        try:
            error_message = "Error storing user- cleaning up and sending back to login screen"
            error_reporting.log_exception(logging.critical, request = request, error_message = error_message )   

            utils.delete_sub_object(userobject, 'search_preferences2')
            utils.delete_sub_object(userobject, 'spam_tracker')
            utils.delete_sub_object(userobject, 'unread_mail_count_ref')
            utils.delete_sub_object(userobject, 'new_contact_counter_ref')
            utils.delete_sub_object(userobject.backup_tracker, 'backup_1') # Note: by construction the first backup object is "backup_1"
            utils.delete_sub_object(userobject, 'backup_tracker')
            utils.delete_sub_object(userobject, 'user_tracker')

            try: 
                userobject.delete() # (Finally - remove the userobject)
                error_message = "Deleted userobject: %s : %s" % (userobject.username, repr(userobject))
                error_reporting.log_exception(logging.critical,  error_message = error_message)  

            except: 
                error_message = "Unable to delete userobject: %s : %s" % (userobject.username, repr(userobject))
                error_reporting.log_exception(logging.critical, error_message = error_message)
        except:
            error_reporting.log_exception(logging.critical, request = request, error_message = "Unable to clean up after failed sign-up attempt" ) 
            
        return(url_for_re_signup)

    # log information about this users login time, and IP address
    utils.update_ip_address_on_user_tracker(userobject.user_tracker)

    home_url = reverse("edit_profile_url", kwargs={'display_nid' : owner_nid})  
    logging.info("Registered/Logging in User: %s IP: %s country code: %s - re-directing to edit_profile_url: %s" % (
        userobject.username, os.environ['REMOTE_ADDR'], request.META.get('HTTP_X_APPENGINE_COUNTRY', None), home_url))
    return home_url


def store_new_user_after_verify_email_url(request, username, secret_verification_code):
    # Note, this function is called directly as a URL from a user clicking on an email link. Therefore, 
    # we must direct them directly to a web page (not just returning a URL unlike some of the code that is 
    # communicating with JavaScript code on the client side)
    
    
    authorization_info = login_utils.query_for_authorization_info(username, secret_verification_code)
        
    if authorization_info:
        login_get_dict = pickle.load(StringIO.StringIO(authorization_info.pickled_login_get_dict))
        
        # somewhat of a hack, but we create a fake request object so that we can use common code to process 
        # the user information that was previously submitted.
        class FakeRequest():
            pass
        
        fake_request = FakeRequest()
        fake_request.GET =  fake_request.REQUEST = login_get_dict
        
        response = store_new_user_after_verify(request, fake_request)
        http_response = HttpResponseRedirect(response)
        
        return http_response
    
    else:
        # could happen if the user clicks on the link more than once to authorize their account at some point after
        # we have erased the authorization info.
        warning_message = "Warning: User: %s Code %s  authorization_info not found" % (
            username, secret_verification_code)
        logging.warning(warning_message)
        return HttpResponseRedirect("/?unable_to_verify_user=%s" % username)
    
    error_reporting.log_exception(logging.error, error_message = 'Reached end of function - redirect to /') 
    return HttpResponseRedirect("/")

    
#def store_new_user_after_verify_email_code(request):
    ## receives a request from javascript, which needs to verify if the code matches the stored code for the
    ## given username and email address. This information is entered manually by the user, after they received
    ## an email indicating the code. 
    
    #secret_verification_code = request.POST.get('secret_verification_code')
    #username = request.POST.get('username', '')
    #email_address = request.POST.get('email_address', '')
    
    ## we convert the code to upper case to make it less difficult for users to screw up
    #if secret_verification_code.upper() == utils.compute_secret_verification_code(username, email_address):
        
        #http_response = store_new_user_after_verify(request)
        ## The JS code is expecting either a URL to re-direct to, or a "Fail" status.
        #return HttpResponse(http_response)
        
    ## Send a response of "Fail" so that
    ## we can catch the failed request with javascript, and report an error to the user.
    #return HttpResponse("Fail")


    
def store_new_user_after_verify_captcha(request):
    
    response_is_valid = check_captcha(request)
    
    
    # The JS code is expecting either a URL to re-direct to, or a "Fail" status.
    if response_is_valid: 
        response = store_new_user_after_verify(request)   
        http_response = HttpResponse(response)
        http_response.delete_cookie(constants.REFERRING_COOKIE_CODE)
        return http_response
        
    # otherwise, the captcha was not entered correctly. Send a response of "Fail" so that
    # we can catch the request with javascript, and re-display a new captcha.
    return HttpResponse("Fail")



def check_and_fix_userobject(userobject, lang_code):
    # module that verifies that userobject contains the important variables and sub-objects that are expected
    # by other parts of the code. This detects profiles that have been corrupted and (not stored correctly
    # to the database), and will allow at least partial recovery.
    #
    # Possible enhancement: check not only if the value is not set, but that it is valid -- think carefully before doing this,
    # because a code error with incorrect allowable values could then cause a wipe out valid user data .. 
    
    try:
        is_modified = False
        
        owner_uid = str(userobject.key())
                      
        # define the fields that we want to verify are set, and define the value to assign to them if they are not set.
        # The following values are manditory for all builds. 
        execution_dict = {
            # each dictionary entry indexes a tuple which contains a function pointer, followed by the function parameters that
            # will be passed in to the function. This is necessary to delay execution of the function until it is verified that
            # it needs to be called.
            'new_contact_counter_ref': (utils.create_contact_counter_object, ()),
            'unread_mail_count_ref': (utils.create_unread_mail_object, ()),
            'spam_tracker': (initialize_and_store_spam_tracker, (None,)),
            'search_preferences2' : (login_utils.create_search_preferences2_object, (userobject, lang_code)),
            'last_login': (datetime.datetime.now,()),
            'previous_last_login': (datetime.datetime.now, ()),
            'user_tracker': (utils.create_and_return_usertracker, ()),
            'hash_of_creation_date': (utils.passhash, (str(userobject.creation_date),)),
            'unique_last_login_offset_ref' : (login_utils.create_and_put_unique_last_login_offset_ref, ()),
            'email_options' : (lambda x: x, (['daily_notification_of_new_messages',],)),

        }

        # Some checkbox fields may or may not appear in individual builds, and therefore we have to check the
        # UserProfileDetails.enabled_checkbox_fields_list[] to see if it is necessary to check the field 
        # for correctness.
        
        for field in UserProfileDetails.enabled_checkbox_fields_list:
            if field == 'languages':
                execution_dict[field] = (lambda x: x, ([default_languages_field_value,],))
            else:
                execution_dict[field] = (lambda x: x, (['prefer_no_say',],))
        
        for (field, function_and_args_tuple) in execution_dict.items():
            try:
                if not getattr(userobject, field, None):
                    is_modified = True
                    (func, args) = function_and_args_tuple
                    utils.set_sub_object(userobject, field, func, args)   
            except:
                # This could possibly happen if ther is a dead pointer. If this happens, if will have to be dealt with
                # 
                error_message = "Error with attribute %s on user %s" % (field, userobject.username)
                error_reporting.log_exception(logging.critical, error_message=error_message)    

                
        if is_modified:
            error_message = "Userobject has been repaired and re-written (see logs for what was changed):\n %s" % repr(userobject)
            error_reporting.log_exception(logging.critical, error_message=error_message)            
            utils.put_userobject(userobject)
            
    except:
        error_message = "Critical error in check_and_fix_userobject %s" % repr(userobject)
        error_reporting.log_exception(logging.critical, error_message=error_message)
        
        
        
        