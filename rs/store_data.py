# -*- coding: utf-8 -*- 

################################################################################
# LexaLink Copyright information - do not remove this copyright notice
# Copyright (C) 2012 
#
# Lexalink - a free social network and dating website platform for the Google App Engine. 
#
# Original author: Alexander Marquardt
# Documentation and additional information: http://www.LexaLink.com
# Git source code repository: https://github.com/alexander-marquardt/lexalink 
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


import uuid

from google.appengine.ext import ndb
from google.appengine.api import taskqueue
from google.appengine.api import memcache
from google.appengine.api import users


from django.http import  HttpResponse,\
     HttpResponseBadRequest, HttpResponseServerError
from django.core.validators import email_re
from django.utils.html import strip_tags
from django.utils.translation import ugettext

from constants import *
from utils import put_userobject, requires_login, ajax_call_requires_login
from models import PhotoModel
from user_profile_main_data import UserSpec
from user_profile_details import UserProfileDetails
import email_utils
import login_utils, utils, utils_top_level
import constants, models, text_fields, messages

from rs import vip_render_payment_options
from rs import profile_utils
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
        search_preferences2_object = userobject.search_preferences2.get()
        
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

        
def set_photo_rules_on_userobject(userobject, value_to_set):

    accept_terms_and_rules_object = userobject.accept_terms_and_rules_key.get()
    if accept_terms_and_rules_object.last_photo_rules_accepted != value_to_set:
        # if it is already set don't bother writing to the datastore
        accept_terms_and_rules_object.last_photo_rules_accepted = value_to_set
        accept_terms_and_rules_object.put()
 
    
def store_photo_options(request, owner_uid, is_admin_photo_review = False, review_action_dict = {}):
    # recieves to POST from the "edit_photos" call, and stores to the appropriate data structure.
    # then re-direct back to the user profile.
    # - uid - id of current user
    # 
    # If this is called by the administrator/photo review - then we deal with only one photo at a time
    # meaning that there are no lists of photo keys etc. posted to this function.
    #
    # if is_admin_photo_review is True, then we will not write the userobject to the database.

    # review_action_dict is a dictionary that will contain one of the following values:
    # is_profile : ref_key *or* is_private : ref_key *or* delete : ref_key
    # were the first dictionary key tell the action, and the ref_key refers to the photo that we
    # are modifying.

    # What I do here is notvery elegant.. loop over all photos associated with a particular
    # profile and check if any values have changed due to the posted data. If changed
    # then write the photo to the database.
    
    try:
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
            
            # if the administrator marks a photo as private, or deletes a photo, then we will remind the user 
            # of the photo rules next time they try to upload photos.
            show_photo_rules = False
            if review_action_dict.has_key('is_profile'):
                is_profile_key = review_action_dict['is_profile']
            if review_action_dict.has_key('is_private'):
                is_private_list_of_keys.append(review_action_dict['is_private'])
                show_photo_rules = True
            if review_action_dict.has_key('delete'):
                delete_photo_list_of_keys.append(review_action_dict['delete'])
                show_photo_rules = True
            
            
            if show_photo_rules:
                set_photo_rules_on_userobject(userobject, "not approved by administrator")
                        

        profile_photo_key = None
        public_photos_keys_list = []
        private_photos_keys_list = []
         

        # Loop over all photos, and mark them appropriately based on the inputs. 
        all_user_photo_keys = PhotoModel.query().filter(PhotoModel.parent_object == userobject.key).fetch(MAX_NUM_PHOTOS, keys_only = True)  
        for photo_key in all_user_photo_keys:
            photo_key_str = photo_key.urlsafe()
            photo_object = photo_key.get()
            
            if photo_key_str in delete_photo_list_of_keys:
                photo_key.delete()
                photo_object = None
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
                        # a single element when we call this function from the admin reviewers page.
                        if photo_key_str == is_profile_key:
                            
                            # if it is already marked as "is_profile" then don't bother writing it again (to save a database write)
                            if not photo_object.is_profile:
                                photo_object.is_profile = True
                                photo_object.is_private = False
                                utils.put_object(photo_object)

                        else: # it is just a normal photo (not profile and not private)
                            
                            # if it is marked as private or as profile, then clear these flags and write the object... otherwise
                            # leave it as is without a write, since it is already correctly set.
                            if photo_object.is_private or photo_object.is_profile:
                                photo_object.is_private = False
                                photo_object.is_profile = False
                                utils.put_object(photo_object)
            
            if photo_object:
                if photo_object.is_private:
                    private_photos_keys_list.append(photo_key)
                else:
                    # photo is public
                    public_photos_keys_list.append(photo_key)
                if photo_object.is_profile:
                    assert(not photo_object.is_private)
                    profile_photo_key = photo_key
        
        
        # The following block takes care of setting up the user_photos_tracker, which will allow efficient access to the 
        # photos associated with each profile.
        user_photos_tracker_key = userobject.user_photos_tracker_key            
        if user_photos_tracker_key:     
            user_photos_tracker = user_photos_tracker_key.get()
            logging.warning("Remove check on user_photos_tracker once all userobjects have been updated to have one defined") 
            user_photos_tracker.profile_photo_key = profile_photo_key
            user_photos_tracker.public_photos_keys = list(public_photos_keys_list)
            user_photos_tracker.private_photos_keys = list(private_photos_keys_list)
            user_photos_tracker.put()          

           
        #utils.invalidate_user_summary_memcache(owner_uid) 
        return HttpResponse('Success')
    
    except:
        error_reporting.log_exception(logging.critical)       
        return HttpResponse('Error')            
    
#############################################
@requires_login
def store_about_user(request, owner_uid, section_name):
    # recieves to POST from the "edit_about_user" call, and stores to the appropriate data structure.
    # then re-direct back to the user profile.
    try:
        assert(owner_uid == request.session['userobject_str'])
        userobject = utils_top_level.get_userobject_from_request(request)

        text = request.POST.get(section_name, '')
        
        # make sure that the user isnt trying to do an html/javascript injection
        text = strip_tags(text)
        
       
        if text:
            userobject.about_user = text[:ABOUT_USER_MAX_DESCRIPTION_LEN]         
        else:
            userobject.about_user = "----"

        put_userobject(userobject)
            
        return HttpResponse('Success')
    
    except:
        error_reporting.log_exception(logging.critical, request = request)       
        return HttpResponse('Error')   


#############################################
#def verify_email_address_is_valid_and_send_confirmation(request, userobject, email_address):
    

    ## email_re is a built-in django regular expression that can be checked against for validity of email
    ## address. 
    #if email_re.match(email_address):
        #assert(userobject != None)
        #is_valid=True
        #countdown_time = 5 # give few seconds to make sure userobject has had time to propagate through servers (especially if this is a new registration) 
                           ## this is necessary because the task-queue could otherwise start in parallel with the writing of the userobject, which could 
                           ## cause a failure due to to email address not yet being stored properly.
        #taskqueue.add(queue_name = 'mail-queue',  countdown = countdown_time, url='/rs/admin/send_confirmation_email/',\
                      #params = {'uid': userobject.key.urlsafe(), 'email_address':email_address, 'remoteip': os.environ['REMOTE_ADDR'],
                                #'lang_code' : request.LANGUAGE_CODE})
    #else:
        #is_valid=False
    #return is_valid


#############################################
def update_when_to_send_next_notification_after_profile_modification(userobject):
    
    # update the when_to_send_next_notification to reflect the newly selected value in both the mail and contact
    # counter objects. Also, allows us to "disable" the message queuing for this user (meaning that the date for sending
    # a message notification is set to infinity) - Note: Other parts of the code could overwrite this value if they don't also
    # verify that the email address is valid.  (we don't check the userobject here, because it hasn't yet been updated with the 
    # new value)

    hours_between_message_notifications = utils.get_hours_between_notifications(userobject, constants.hours_between_message_notifications)
    hours_between_new_contacts_notifications = utils.get_hours_between_notifications(userobject, constants.hours_between_new_contacts_notifications)
    
    ndb.transaction (lambda: utils.when_to_send_next_notification_txn(userobject.unread_mail_count_ref, \
                           hours_between_message_notifications))
    
    ndb.transaction (lambda: utils.when_to_send_next_notification_txn (userobject.new_contact_counter_ref, \
                           hours_between_new_contacts_notifications))      
    
    
    
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
    
    # This function stores a new email address for a user profile. 

    try:
        assert(owner_uid == request.session['userobject_str'])
        userobject = utils_top_level.get_userobject_from_request(request)
        
        # Only VIP clients can modify their email address. 
        if userobject.client_paid_status or users.is_current_user_admin():
            
            
            # remove blank spaces from the email address -- to make it more likely to be acceptable
            posted_email = request.POST.get('email_address','')
            posted_email = posted_email.replace(' ', '')
            
            # make it lowercase so we can find it when we query 
            posted_email =posted_email.lower()
            email_is_valid = False
            

            if posted_email:
                email_is_valid = email_re.match(posted_email)
                
                if  email_is_valid:
                    userobject.email_address_is_valid = True                    
                    userobject.email_address = posted_email
                    logging.info("User %s has modified their email address %s to %s" % (
                        userobject.username, userobject.email_address, posted_email))
               
                    
            
            # if user clears the field, a blank value will not be written to 
            # the database, so, set it back to the default "----" so that it
            # will overwrite the previously stored address. If an invalid email address 
            # is entered, treat it the same as a clearing.
            if not posted_email: # if post == "" 
                userobject.email_address = "----" 
                logging.warning("User %s erased their email address %s" % (userobject.username, userobject.email_address))
                userobject.email_address_is_valid = False

            put_userobject(userobject)
                
            # in all cases if the email is cahnged we should updated the message queuing values - this is in case we go from
            # having a valid email to invalid or vice-versa -- we could explicity check for this is this becomes a bottleneck
            update_when_to_send_next_notification_after_profile_modification(userobject)
            return HttpResponse('Success')
    
        else:
            error_reporting.log_exception(logging.error, error_message= "Unauthorized user attempting to modify email address")
            return HttpResponse("Error - You must be a VIP member to update your email address")
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
        userobject.current_status_update_time = datetime.datetime.now()
        if current_status == "":
            current_status = "----" 
        
        userobject.current_status = current_status
        put_userobject(userobject)  
        return HttpResponse('Success')

    except:
        error_reporting.log_exception(logging.critical, request = request)       
        return HttpResponse('Error')      


@ajax_call_requires_login
def store_generic_checkbox_option_list(request, option_name, owner_uid):
    
    prepend_dont_care_to_list = False

    try:
        if settings.BUILD_NAME == "language_build":
            # This is necessary for ensuring that the languages and languages_to_learn contain "----" which is necessary for
            # ensuring that all profiles show up in "dont_care" searches.
            prepend_dont_care_to_list = True
            

        fields_to_store = [option_name,]
        http_return = store_data(request, fields_to_store, owner_uid, is_a_list = True,
                                 prepend_dont_care_to_list = prepend_dont_care_to_list)
        
    except:
        error_reporting.log_exception(logging.critical, request = request)      
        http_return = HttpResponse('Error')
        
    return http_return
    
@ajax_call_requires_login
def store_data(request, fields_to_store, owner_uid, is_a_list = False, update_title = False, is_signup_fields = False, 
               prepend_dont_care_to_list = False):
    # recieves to POST from the "edit_xxxx" call, and stores to the appropriate data structure.
    # then re-direct back to the user profile.
    # - uid - id of current user
    # - fields_to_store - data fields that are passed in in the current post
    # - is_a_list - if the post contains data from a checkbox, it should be processed as
    #               a list. 
    # - prepend_dont_care_to_list: we add a value of "----" to the list, which will be used in search queries where the condition is "don't care"

    try:
        assert(owner_uid == request.session['userobject_str'])
        userobject = utils_top_level.get_userobject_from_request(request)
        
        if request.method != 'POST':
            return HttpResponseBadRequest()
        
        for field in fields_to_store:
                       
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
                    if  (settings.BUILD_NAME == "language_build" and (field == 'languages' or field=='languages_to_learn')):
                        # if build is language_build and the field is languages or languages_to_learn, then don't set the value here
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
                    
            if field == 'country' or field == 'native_language':
                # do not allow them to set their country or native_language, to undefined value
                # These are the fields that have a ---- seperating the "important" values from the rest. 
                if post_val == '----':
                    # by setting to '', it will not be written to the userobject.
                    post_val = ''
                
            if settings.BUILD_NAME == "language_build":
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

                
        if is_signup_fields:
            # copy the current field into the search index list for the current field
            login_utils.copy_principal_user_data_fields_into_ix_lists(userobject)

        put_userobject(userobject)
        return HttpResponse('Success')

    except:
        error_message="Unable to store data for user - check POST"
        error_reporting.log_exception(logging.critical, error_message=error_message, request = request)       
        return HttpResponse('Error')


#############################################
@ajax_call_requires_login
def store_change_password_fields(request, owner_uid):

    try:
        assert(owner_uid == request.session['userobject_str'])
        userobject = utils_top_level.get_userobject_from_request(request)
        
        password_change_is_valid = False
        
        if request.method != 'POST':
            return HttpResponseBadRequest()
        
        current_password = request.POST.get('current_password','')
        new_password = request.POST.get('new_password', '')
        verify_new_password = request.POST.get('verify_new_password','')
        
        # Authenticate the original password      
        if new_password == verify_new_password and new_password != "":
                            
            if utils.old_passhash(current_password) == userobject.password:
                password_change_is_valid = True      
            elif utils.new_passhash(current_password, userobject.password_salt) == userobject.password:
                password_change_is_valid = True
    
               
        userobject.change_password_is_valid = password_change_is_valid
        userobject.password_attempted_change_date = datetime.datetime.now()             
    
                
        #only overwrite the password if the post was a valid password change
        if password_change_is_valid:
            userobject.password_salt = uuid.uuid4().hex
            userobject.password = utils.new_passhash(new_password, userobject.password_salt)
        else:
            logging.info("unable to set password to %s. Current password %s appears not to match" % (new_password, current_password))
            
            
        # write the object in all cases, because state information about the attempted password
        # change is written into the userobject. We use the attempted_password_change time in the
        # ajax function "load_change_password_fields" -- we should fix this in the future, and 
        # NOT write the userobject, unless a successful password change has occured -- we can eaily
        # pass the status back to the client and process with javascript as opposed to server side
        # tracking of this status (this is written like this because when I first started coding I didn't know
        # any javascript). 
        put_userobject(userobject)  
        
        return HttpResponse('Success')
    
    except:
        error_reporting.log_exception(logging.critical)       
        return HttpResponse('Error')

###########################################################################
def  reset_new_contact_or_mail_counter_notification_settings(object_ref_key):
    # resets the date_of_last_notification on the object to the current time. This can be used for both "new_contact_counter" and "unread_mail_count"
    try:      
        
        def txn(new_contact_counter_ref_key):
    
            counter_obj = object_ref_key.get()
            counter_obj.date_of_last_notification = datetime.datetime.now()
            counter_obj.num_new_since_last_notification = 0
            counter_obj.when_to_send_next_notification = datetime.datetime.max
            counter_obj.when_to_send_next_notification_string = str(counter_obj.when_to_send_next_notification)
            counter_obj.put()
        
        ndb.transaction(lambda: txn(object_ref_key))
    
    except:
        error_reporting.log_exception(logging.critical)            
    
    
###########################################################################

def  modify_new_contact_counter(new_contact_counter_ref_key, action_type, action_prefix,
                                action_postfix, value,
                                hours_between_notifications, update_notification_times, 
                                ):
    # updates the new_contact_counter_obj value based on the value passed in. Must
    # be run in a transaction to ensure that only a single update can take place at a time.
    # This value is used for tracking number of kisses, winks, keys, received by a user since 
    # the last time they viewed their contacts.
    
    try:
                
        def txn(new_contact_counter_ref_key, action_type, action_prefix, action_postfix, value):
    
            action_field_for_contact_count = action_prefix + action_type + action_postfix
            
            new_contact_counter_obj = new_contact_counter_ref_key.get()
            current_count = getattr(new_contact_counter_obj, action_field_for_contact_count)
                        
            current_count += value
            setattr(new_contact_counter_obj, action_field_for_contact_count, current_count)
        
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

                    # This number may go negative if someone gives a kiss, and then takes it away. 
                    # Or if a notification is sent out about a new contact, and then that contact is removed
                    # before the user has checked their contacts. 
                    # Not an exception,
                    # but it is good to keep it non-negative so that if new contacts are received after old contacts
                    # are taken away, this number will still be positive.
                    new_contact_counter_obj.num_new_since_last_notification = 0
                    
                    # don't send a notification if there are no new contacts
                    new_contact_counter_obj.when_to_send_next_notification = datetime.datetime.max
                
                new_contact_counter_obj.when_to_send_next_notification_string = str(new_contact_counter_obj.when_to_send_next_notification)  
                
            new_contact_counter_obj.put()
            return new_contact_counter_obj
        
        new_contact_counter_obj = ndb.transaction(lambda: txn(new_contact_counter_ref_key, action_type, action_prefix, action_postfix, value))
        return new_contact_counter_obj

    except:
        error_reporting.log_exception(logging.critical)          

###########################################################################
        
        
# New HR Datastore
def update_users_have_sent_messages_object_favorite_val(userobject, other_userobject, bool_val):

    try:
        users_have_sent_messages_object = utils.get_have_sent_messages_object(userobject.key, other_userobject.key)
    
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
            chat_request_action_on_receiver = "connected"
            counter_modify = 1
            
        elif initiate_contact_object.chat_friend_stored == "connected":
            # the user has decided to disconnect from the other user -- however the other users request still remains
            initiate_contact_object.chat_friend_stored = "request_received"
            chat_request_action_on_receiver = "connected"
            counter_modify = -1
        else:
            assert(False)
                    
        return (counter_modify, chat_request_action_on_receiver)
    
    except:
        error_reporting.log_exception(logging.critical)
        return (0, None)

###########################################################################
def modify_passive_initiate_contact_object(chat_request_action_on_receiver, add_or_remove, userobject_key, other_userobject_key):
    # chat-request_action_on_receiver is either "friend_request" or "connected", 
    # and add_or_remove is either +1 or -1 respectively
    #
    # "passive" initiate contact object means the initiate contact object referring to "other_userobject" kisses,keys,etc.
    # sent to "userobject". (this is the "opposite" of the "active" userobject).
    
    def txn(initiate_contact_object_key):
        # use a transaction to ensure that only a single update to this object will happen at a time.
        initiate_contact_object = initiate_contact_object_key.get()
        if chat_request_action_on_receiver == "friend_request":
            if add_or_remove == +1:
                initiate_contact_object.chat_friend_stored = "request_received"
            if add_or_remove == -1:
                initiate_contact_object.chat_friend_stored = None
                
        if chat_request_action_on_receiver == "connected":
            if add_or_remove == +1:
                initiate_contact_object.chat_friend_stored = "connected"
            if add_or_remove == -1:
                initiate_contact_object.chat_friend_stored = "request_sent"
            
        initiate_contact_object.chat_friend_stored_date = datetime.datetime.now()
        # NOTE: reversed userobjects in the following call to get the "passive" object (the user receiving 
        # the chat request)        
        utils.put_initiate_contact_object(initiate_contact_object, other_userobject_key, userobject_key)  
    
    # currently this function should only be called for chat_friend requests.
    assert(chat_request_action_on_receiver == "friend_request" or chat_request_action_on_receiver == "connected")   
    assert(add_or_remove == +1 or add_or_remove == -1)
    # NOTE: reversed userobjects in the following call to get the "passive" object (the user receiving 
    # the chat request)
    initiate_contact_object = utils.get_initiate_contact_object(other_userobject_key, userobject_key, create_if_does_not_exist=True)
    initiate_contact_object_key = initiate_contact_object.key 

    try: 
        ndb.transaction(lambda: txn(initiate_contact_object_key))
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
            initiate_contact_object = initiate_contact_object_key.get()
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
                invalidate_memcache_for_friends_lists(userobject_key.urlsafe())
                invalidate_memcache_for_friends_lists(other_userobject_key.urlsafe())
                
            # Update the set time for bot setting and removing the action
            setattr(initiate_contact_object, action_stored_date_str, datetime.datetime.now())
            utils.put_initiate_contact_object(initiate_contact_object, userobject_key, other_userobject_key)  
            return (counter_modify, chat_request_action_on_receiver, initiate_contact_object)
        
        
        initiate_contact_object_modified = False
        action_stored_date_str = action + "_stored_date"
        previous_chat_friend_stored_value = initiate_contact_object.chat_friend_stored
        initiate_contact_object_key = initiate_contact_object.key
    
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
                 ndb.transaction(lambda: txn(initiate_contact_object_key, action))
                initiate_contact_object_modified = True
            except:
                # transaction failed -- object not modified
                logging.warning("Trasaction failed in modify_active_initiate_contact_object")
                initiate_contact_object_modified = False
        else:
            # we do not write the initiate_contact_object since not enough time has passed since the last click
            pass
            
        return (initiate_contact_object, initiate_contact_object_modified, counter_modify, 
                chat_request_action_on_receiver, previous_chat_friend_stored_value)
    except:
        error_reporting.log_exception(logging.critical)
            
        
@ajax_call_requires_login
def store_initiate_contact(request, to_uid):
    # stores updates to winks, favorites, etc. This is called when users click on the associated icon. 
    

    userobject = utils_top_level.get_userobject_from_request(request)
    userobject_key = userobject.key
    userobject_nid = userobject_key.id()
    
    try:
        
        possible_actions = ('wink', 'favorite', 'kiss', 'key', 'chat_friend', 'blocked')
        other_userobject_key = ndb.Key(urlsafe = to_uid)
        other_userobject = utils_top_level.get_object_from_string(to_uid)
        
        if request.method != 'POST':
            return HttpResponseBadRequest()
        else:          
            action = request.POST.get('section_name', '')
            if action in possible_actions:
                
                initiate_contact_object = utils.get_initiate_contact_object(userobject_key, other_userobject_key, create_if_does_not_exist=True)
                (initiate_contact_object, initiate_contact_object_modified, counter_modify, chat_request_action_on_receiver, active_previous_chat_friend_stored_value) =\
                 modify_active_initiate_contact_object(action, initiate_contact_object, userobject_key, other_userobject_key, )
                
                if initiate_contact_object_modified:  
                    
                    owner_new_contact_counter_obj = userobject.new_contact_counter_ref.get()
                    
                    # first check that the user has not exceeded their quota for the given action
                    request_denied = False
                    if counter_modify > 0:
                        if action == "key":
                            if owner_new_contact_counter_obj.num_sent_key >= constants.MAX_KEYS_SENT_ALLOWED:
                                response_text = "<p>%s" % ugettext("""You have exceeded the limit of %(max_keys)s on the number of keys that you can send. 
                                Before sending additional keys, you must take back keys that you have given to other users.""") \
                                              % {'max_keys' : constants.MAX_KEYS_SENT_ALLOWED}
                                request_denied = True
                                
                        def max_chat_friends_response_text(chat_friend_requests_allowed):
                            return ugettext("""
                            You have reached the limit of %(max_requests)s on the number of chat friends
                            that you are allowed to request. Before requesting additional chat 
                            friends, you must remove some of your current chat friends.""") \
                                   % {'max_requests' : chat_friend_requests_allowed}
                                
                        if action == "chat_friend":
                            if userobject.client_paid_status or initiate_contact_object.chat_friend_stored != "request_sent":
                                # VIP clients are allowed to have the max number of chat friends OR
                                # we allow people to accept friend requests even after their free limit on friends has been exceeded. 
                                # ... But not to initiate new friend requests, However, we *never* allow them to exceed
                                # MAX_CHAT_FRIEND_REQUESTS_ALLOWED number of chat friends. This limit is in place because 
                                # it could use excessive CPU resources if the list gets too big.
                                if owner_new_contact_counter_obj.num_sent_chat_friend >= MAX_CHAT_FRIEND_REQUESTS_ALLOWED:
                                    response_text = "<p>%s" % max_chat_friends_response_text(MAX_CHAT_FRIEND_REQUESTS_ALLOWED)
                                    request_denied = True                                
                            
                            else:
                                # This user is neither VIP nor responding to a friend request, therefore they 
                                # only have the free limit of friends
                                if owner_new_contact_counter_obj.num_sent_chat_friend >= GUEST_NUM_CHAT_FRIEND_REQUESTS_ALLOWED:
                                    
                                    request_denied = True  
                                    
                                    response_text = "<p>%s" % max_chat_friends_response_text(GUEST_NUM_CHAT_FRIEND_REQUESTS_ALLOWED)
                                    
                                    if constants.SHOW_VIP_UPGRADE_OPTION:
                                        
                                        response_text += "<p>%s" % ugettext("""
                                        If you wish to increase this limit to %(max_requests)s, 
                                        you could consider becoming a VIP member.""")   % \
                                            {'max_requests' : MAX_CHAT_FRIEND_REQUESTS_ALLOWED}
                                     

                                        response_text += vip_render_payment_options.render_payment_options(request, userobject.username, userobject_nid)
                                        
                                        see_vip_benefits_txt = ugettext("See VIP benefits")
                                        response_text += '<strong><a class="cl-dialog_anchor cl-see_all_vip_benefits" href="#">%s</a></strong>' % see_vip_benefits_txt

                        if request_denied:
                            # un-do the request (toggle it) by calling the same function again, Note that we override the 
                            # minimum delay between clicks. 
                            (initiate_contact_object, initiate_contact_object_modified, counter_modify, chat_request_action_on_receiver, active_previous_chat_friend_stored_value) =\
                             modify_active_initiate_contact_object(action, initiate_contact_object, userobject_key, other_userobject_key, 
                                                                   override_minimum_delay = True)
                            return HttpResponse(response_text)
                                    
                    
               
                    # update the counter for the receiver, except for favorites and blocked since these fields 
                    # will never be displayed or available to the "viewed" user.
                    action_postfix = "_since_last_reset"
                    if action != "favorite" and action != 'blocked':
                        if counter_modify != 0:
                            if action != "chat_friend":
                                action_prefix = "num_received_" 
                            else: 
                                #action == "chat_friend"
                                #
                                # Note chat_request_action_on_receiver should be either friend_request or connected
                                
                                if chat_request_action_on_receiver == 'connected':
                                    action_prefix = "num_connected_"
                                else:
                                    action_prefix = "num_received_"
                                    
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
                            
                            # update the *receiver's* counters for kisses, winks, chat_friends, etc.
                            # Note: the behaviour of these counters for chat_friends is not 100% ideal, but it would require large 
                            # changes to correct. Eg. if a user recieves a friend request that they accept , the received request still 
                            # is counted as "1 new". However we can't reduce that counter by one, because we don't know if the user
                            # has already viewed the "friend requests" page, which would have already reset it to zero (and so subtracting
                            # one would make it go negative ..) .. 
                            receiver_new_contact_counter_obj = modify_new_contact_counter(other_userobject.new_contact_counter_ref, \
                                                         action, action_prefix, action_postfix, counter_modify, hours_between_notifications, 
                                                         update_notification_times = True,)                                                                                     

                            info_message = "Modifying %s on %s by %s" %(action, other_userobject.username, counter_modify)
                            logging.info(info_message)
                                                       
                            # if notification for sending the user notification is past due, send it now.
                            if receiver_new_contact_counter_obj.when_to_send_next_notification <= datetime.datetime.now():
                                
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
                                                      'uid': other_userobject.key.urlsafe()})
                                except:
                                    error_reporting.log_exception(logging.critical)
                                    
                            if action == "chat_friend" or action == "key":
                                # Update the counters on *owners* "new_contact_counter_ref" object to reflect how many
                                # friend requests or how many keys they have sent. 
                                # For now we only track keys and friend requests
                                action_prefix = "num_sent_"
                                action_postfix = ''
                                modify_new_contact_counter(userobject.new_contact_counter_ref, \
                                                       action, action_prefix, action_postfix, counter_modify, 
                                                       hours_between_notifications = None, update_notification_times = False,)                                             

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
        
    

def increase_reporting_or_reporter_unacceptable_count(model_class, userobject_key, increase_or_decrease_count):
    # Function for keeping track of how many times a profile has been marked as unacceptalbe (or how many
    # times a particular user has marked other profiles as unacceptable - depending on the model_class value)
    # We expect model_class to contain either CountReportingProfile or CountUnacceptableProfile
    # and it will update the appropriate counter. 
    
    def txn(profile_reporting_tracker):
        
        try:
            if not profile_reporting_tracker:
                profile_reporting_tracker = model_class()
                profile_reporting_tracker.profile_ref = userobject_key   
                if model_class == models.CountUnacceptableProfile:
                    # it is a new object, so this is the first time that it has been reported.
                    profile_reporting_tracker.datetime_first_reported_in_small_time_window = datetime.datetime.now()
                    
            profile_reporting_tracker.count += increase_or_decrease_count
            
            if model_class == models.CountUnacceptableProfile:
                if profile_reporting_tracker.datetime_first_reported_in_small_time_window + datetime.timedelta(hours = constants.SMALL_TIME_WINDOW_HOURS_FOR_COUNT_UNACCEPTABLE_PROFILE_REPORTS) <  datetime.datetime.now():
                    # window has closed, start a new one.
                    profile_reporting_tracker.datetime_first_reported_in_small_time_window  = datetime.datetime.now()
                    profile_reporting_tracker.num_times_reported_in_small_time_window = 1
                else:
                    # within the window - so increase the count
                    profile_reporting_tracker.num_times_reported_in_small_time_window += 1
        except:
            error_reporting.log_exception(logging.error, "profile_reporting_tracker = %s" % repr(profile_reporting_tracker))                

        profile_reporting_tracker.put()
        return profile_reporting_tracker 
        
    q = model_class.query().filter(model_class.profile_ref == userobject_key)
     
    profile_reporting_tracker = q.get()
    profile_reporting_tracker = ndb.transaction(lambda: txn(profile_reporting_tracker))

    return profile_reporting_tracker
    
    
@ajax_call_requires_login
def store_report_unacceptable_profile(request, display_uid):
    # This function is used for allowing users to notify us if a particular profile should be considered unacceptable. 
    # Once a profile receives a certain number of reports, we will generate a warning, and we will investigate.
    
    try:
        sender_userobject =  utils_top_level.get_userobject_from_request(request)
        owner_uid =  request.session['userobject_str']
        displayed_uid_key = ndb.Key(urlsafe = display_uid)
        owner_uid_key = ndb.Key(urlsafe = owner_uid)    
        
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
            mark_unacceptable_profile.key.delete()
            increase_or_decrease_count = -1 # we are removing a report of an unacceptable profile
            response = text_fields.profile_unreported
         
        count_reporting_profile = increase_reporting_or_reporter_unacceptable_count(models.CountReportingProfile, owner_uid_key, increase_or_decrease_count)
        
        count_unacceptable_profile = increase_reporting_or_reporter_unacceptable_count(models.CountUnacceptableProfile, displayed_uid_key, increase_or_decrease_count)

        lang_code = 'en'
        displayed_profile = utils_top_level.get_object_from_string(display_uid)
        displayed_href = "http://www.%(domain_name)s%(profile_href)s" % {
            'domain_name': settings.DOMAIN_NAME,
            'profile_href' :  profile_utils.get_userprofile_href(lang_code, displayed_profile),
        }
        displayed_profile_href = '<a href="%(href)s">%(username)s</a>' % {'href': displayed_href, 'username' : displayed_profile.username}

        sender_href = "http://www.%(domain_name)s%(profile_href)s" % {
            'domain_name': settings.DOMAIN_NAME,
            'profile_href' :  profile_utils.get_userprofile_href(lang_code, sender_userobject)
        }
        sender_profile_href = '<a href="%(href)s">%(username)s</a>' % {'href': sender_href, 'username' : sender_userobject.username}


        if count_unacceptable_profile.count >= NUM_REPORTS_FOR_UNACCEPTABLE_PROFILE:
            error_message = """Profile %s has been reported as unacceptable %s times<br>
            Most recent report by: %s who has reported %s profiles as unacceptable.<br>
            <br>Admin view %s: %s<br>
            <br>Admin view %s: %s<br>""" \
                          % (displayed_profile_href, count_unacceptable_profile.count, sender_profile_href,
                             count_reporting_profile.count,
                             displayed_profile_href,
                             utils.generate_profile_information_for_administrator(displayed_profile, True),
                             sender_profile_href,
                             utils.generate_profile_information_for_administrator(sender_userobject, True))

            email_utils.send_admin_alert_email(error_message, subject = "%s %s Unacceptable profile" % (settings.APP_NAME, displayed_profile.username))
            logging.error(error_message)
            
            
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
                error_message = "Profile %s has been deleted due to reports from other users in the time window" % displayed_profile_href
                email_utils.send_admin_alert_email(error_message, subject = "%s Deleted Profile" % settings.APP_NAME)
                logging.critical(error_message)
                login_utils.take_action_on_account_and_generate_response(request, displayed_profile, action_to_take = "delete", reason_for_profile_removal = "terms")
                
                # have not yet implemented the code to actually check blocked IPs and block them - this will be done in the future.
                blocked_ip_object = models.TemporarilyBlockedIPAddresses(blocked_ip = blocked_ip)
                blocked_ip_object.put()
        
        return HttpResponse(response)
    except:
        error_reporting.log_exception(logging.critical, request=request, error_message="Unable to report profile as unacceptable")        
        return HttpResponse("Error")
    

        

    


def check_and_fix_userobject(userobject, lang_code):
    # module that verifies that userobject contains the important variables and sub-objects that are expected
    # by other parts of the code. This detects profiles that have been corrupted and (not stored correctly
    # to the database), and will allow at least partial recovery.
    #
    # Possible enhancement: check not only if the value is not set, but that it is valid -- think carefully before doing this,
    # because a code error with incorrect allowable values could then cause a wipe out valid user data .. 
    
    try:
        is_modified = False
        
        owner_uid = userobject.key.urlsafe()
                      
        # define the fields that we want to verify are set, and define the value to assign to them if they are not set.
        # The following values are manditory for all builds. 
        execution_dict = {
            # each dictionary entry indexes a tuple which contains a function pointer, followed by the function parameters that
            # will be passed in to the function. This is necessary to delay execution of the function until it is verified that
            # it needs to be called.
            'new_contact_counter_ref': (utils.create_contact_counter_object, ()),
            'viewed_profile_counter_ref' : (login_utils.create_viewed_profile_counter_object, (userobject.key,)),
            'accept_terms_and_rules_key' : (login_utils.create_terms_and_rules_object, ()), 
            'unread_mail_count_ref': (utils.create_unread_mail_object, ()),
            'spam_tracker': (messages.initialize_and_store_spam_tracker, (None,)),
            'search_preferences2' : (login_utils.create_search_preferences2_object, (userobject, lang_code)),
            'last_login': (datetime.datetime.now,()),
            'previous_last_login': (datetime.datetime.now, ()),
            'user_tracker': (utils.create_and_return_usertracker, ()),
            'hash_of_creation_date': (utils.old_passhash, (str(userobject.creation_date),)),
            'email_options' : (lambda x: x, (['daily_notification_of_new_messages',],)),
            'user_photos_tracker_key' : (utils.create_and_return_user_photos_tracker, ()),

        }
        

        # Some checkbox fields may or may not appear in individual builds, and therefore we have to check the
        # UserProfileDetails.enabled_checkbox_fields_list[] to see if it is necessary to check the field 
        # for correctness.
        for field in UserProfileDetails.enabled_checkbox_fields_list:
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
            error_reporting.log_exception(logging.error, error_message=error_message)
            utils.put_userobject(userobject)


        return is_modified
            
    except:
        error_message = "Critical error in check_and_fix_userobject %s" % repr(userobject)
        error_reporting.log_exception(logging.critical, error_message=error_message)
        return False
        
        
        
        