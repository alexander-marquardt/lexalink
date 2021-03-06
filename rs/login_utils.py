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


""" This module contains support functions for logging-in the user. """

import datetime, logging, os, re
from google.appengine.ext import ndb 

from google.appengine.api import taskqueue

# local settings
import settings

from django.template import Context, loader
from django.conf import settings
from django.core.validators import email_re
from django.utils.translation import ugettext
from django import http

from models import UserSearchPreferences2
from user_profile_main_data import UserSpec


import utils, email_utils, messages
import sharding
import constants
import utils, utils_top_level, channel_support, chat_support
import forms
import error_reporting
import models
import localizations, user_profile_main_data, user_profile_details, online_presence_support, search_results
import rendering
import gaesessions
from rs import profile_utils

#############################################

def store_session(request, userobject):
    
    try:
        # terminate any existing session/remove cookies - however, do not clear the databse as this will slow down the login 
        # let the cron jobs clear out the sessions from the database. 
        request.session.terminate(clear_data=False)
        
        userobject_str = userobject.key.urlsafe()
        owner_uid = userobject_str
        
        # set the object passsed in to have a reference to the current session. Note: the act of just writing a value into the session
        # will cause a new session to be formed if one does not exist already. 
        request.session.__setitem__('userobject_str', userobject_str)
        
        # the username is useful for chat conversations etc. without having to pull the entire userobject out of hte 
        # database
        request.session.__setitem__('username', userobject.username)
        
        # keep track of the current session id for the current user, so that if necessary we can remotely remove their sessions
        # from the database.
        utils.add_session_id_to_user_tracker(userobject.user_tracker, request.session.sid)
        
        # force user to appear online and active in the chat boxes (from module chat_support)
        online_presence_support.update_online_status(owner_uid, constants.OnlinePresence.ACTIVE)
        channel_support.update_chat_boxes_status(owner_uid, constants.ChatBoxStatus.IS_ENABLED)
        
        chat_support.update_or_create_open_conversation_tracker(owner_uid, "main", chatbox_minimized_maximized="maximized", type_of_conversation="NA")
        chat_support.update_or_create_open_conversation_tracker(owner_uid, "groups", chatbox_minimized_maximized="maximized", type_of_conversation="NA")
    
        expiry_datetime = request.session.get_expiration_datetime()
        logging.info("Stored session id %s for user %s (%s). Expires %s" % (request.session.sid, 
                                            userobject.username, userobject.key, expiry_datetime))
    except: 
        error_reporting.log_exception(logging.critical)      
    

###################################################
## START Profile Display Offset values

# This data structure is used for offsetting the unique_last_login value so that search order will be
# modified based on profile characteristics that are considered to be important.
# offsets are given in hours



## END Profile Display Offset values
###################################################

def compute_unique_last_login(userobject):
    """ adds appropriate offsets to the current "unique_last_login" value so that 
    the search results will be ordered based on the profile completeness of the current user.

    If this function is only called when the user logs in, then it may be the case that their profile
    ranking does not reflect any photos that they upload during their session. They would have to
    exit and login again to get credit for any photos added to their profile, and full credit is
    not given until after their photo has been approved by the administrator for public display.
    """
    
    try:
        offset = 0 # the offset is in Days.

        user_photo_tracker = userobject.user_photos_tracker_key.get()

        # The following logic is needed to ensure that a user only gets credit for a profile photo (or any public
        # photo that may become their profile photo) in the case that it is approved for public viewing.
        # If it is not approved, then we do not update their ranking to include the profile photo bonus.
        has_at_least_one_public_approved_photo = False
        for public_photo_key in user_photo_tracker.public_photos_keys:
            public_photo = public_photo_key.get()
            if public_photo.is_approved and not public_photo.is_private:
                has_at_least_one_public_approved_photo = True
                break

        if has_at_least_one_public_approved_photo:
            # if they have one public and approved photo, then give them the credit as if they had a profile
            # photo - this photo will be made public if necessary when admin reviews all of their photos.
            offset += constants.unique_last_login_offset_values_in_days['has_profile_photo_offset']

        # Otherwise, check if user has any photos (public that are not approved yet) , or private photos. Give
        # credit as if they have uploaded private photos, until the public photos receive approval.
        elif user_photo_tracker.public_photos_keys or user_photo_tracker.private_photos_keys:
            offset += constants.unique_last_login_offset_values_in_days['has_private_photo_offset']

        if userobject.about_user != '----':
            offset += constants.unique_last_login_offset_values_in_days['has_about_user_offset']

        unique_last_login_with_offset = userobject.last_login + datetime.timedelta(days=offset)
        unique_last_login = "%s_%s" % (unique_last_login_with_offset, userobject.username)
        logging.info('New unique_last_login: %s. last_login: %s' % (unique_last_login, userobject.last_login))
        return unique_last_login

    except: 
        error_reporting.log_exception(logging.critical)  

#############################################

def error_check_signup_parameters(login_dict, lang_idx):
    
    error_dict = {} # used for containing error messages to be presented to user in a friendly format   
    try:        
        if (not email_re.match(login_dict['email_address'])) or (len(login_dict['email_address'])>constants.MAX_TEXT_INPUT_LEN):
            error_dict['email_address'] = u"%s" % constants.ErrorMessages.email_address_invalid
                
        if login_dict['password'] == "----":
            error_dict['password'] = u"%s" % constants.ErrorMessages.password_required
            
        if len(login_dict["password"]) > constants.MAX_TEXT_INPUT_LEN:
            error_dict['password'] = u"%s" % ugettext("<strong>Password</strong> must not be more than %(max_len)s characters") % {
                'max_len' : constants.MAX_TEXT_INPUT_LEN}
            
        # Verify that the username only contains acceptable characters 
        # This is not really necessary, but prevents people from entering strange names.
        if (len(login_dict['username']) < 3 or login_dict['username'] == "----"): 
            error_dict['username'] = u"%s" % constants.ErrorMessages.username_too_short              
        elif (constants.rematch_non_alpha.search(login_dict['username']) != None):
            error_dict['username'] = u"%s" %constants.ErrorMessages.username_alphabetic   
            
        if len(login_dict['username']) > constants.MAX_USERNAME_LEN:
            error_dict['username'] = ugettext("<strong>Username</strong> must not be more than %(max_len)s characters") % {
                'max_len': constants.MAX_USERNAME_LEN}  
                        
        def try_remaining_signup_fields(field_name):
            try:
                # just make sure that a lookup on the given field-name doesn't trigger an exception -- which means
                # that it is valid, and can be used for lookups in our data structures.
                user_profile_main_data.UserSpec.signup_fields_options_dict[field_name][lang_idx][login_dict[field_name]]
            except:
                field_label = UserSpec.signup_fields[field_name]['label'][lang_idx]
                error_dict[field_name] = ugettext('<strong>%(field_label)s</strong> must be selected') % {'field_label': field_label}
            
        try_remaining_signup_fields("country")       
        try_remaining_signup_fields("sex")       
        try_remaining_signup_fields("age")
        
        if settings.BUILD_NAME != "language_build":
            try_remaining_signup_fields("preference")
            try_remaining_signup_fields("relationship_status")
        
        else: # settings.BUILD_NAME == "language_build":
            try_remaining_signup_fields("native_language")
            try_remaining_signup_fields("language_to_learn")
            
        return(error_dict)
    
    except: 
        error_reporting.log_exception(logging.critical)  
        error_dict['internal'] = 'Internal error - this error has been logged, and will be investigated immediately'
        return error_dict

#############################################
def get_registration_dict_from_post(request):
    # parses the POST data, and checks to see that something has been entered.
    
    login_dict = {}
    
    try:
        try:
            lang_idx = localizations.input_field_lang_idx[request.LANGUAGE_CODE]     
        except:
            error_reporting.log_exception(logging.critical)
            lang_idx = localizations.input_field_lang_idx['es']
        
        additional_fields =  ['country', 'region', 'sub_region']
        
        for field in UserSpec.signup_fields_to_display_in_order + additional_fields: 
            # Accept POST and GET -- use REQUEST to do this
            post_val = request.REQUEST.get(field, '----')
            if not post_val:
                post_val = '----'
                
            # probably a bit paranoid, but we cut the input to "MAX_TEXT_INPUT_LEN" - in case someone tries to overload our DB.
            login_dict[field] = post_val[:constants.MAX_TEXT_INPUT_LEN]
                
    except:
        error_reporting.log_exception(logging.critical)
        
    return (login_dict) 


def create_viewed_profile_counter_object(userobject_key):

    viewed_counter_object = models.ViewedProfileCounter()
    viewed_counter_object.owner_profile = userobject_key
    viewed_counter_object.put()
    return viewed_counter_object.key

def create_terms_and_rules_object():
    accept_terms_and_rules_object = models.AcceptTermsAndRules()
    accept_terms_and_rules_object.put()
    return accept_terms_and_rules_object.key

#############################################
def create_search_preferences2_object(userobject, lang_code):
    # set sensible initial search defaults based on the user profile
    # i.e., someone who prefers women should have the "sex" set to women.
    # For relationship_status, it is less obvious what the "optimal" setting would be
    # so, we just set the search setting to the same value as what the user has selected
    # Search location and age are set to the same as the client.
    
    try:
        if settings.BUILD_NAME != "language_build":
            search_preferences2 = UserSearchPreferences2(sex=userobject.preference,
                                                       relationship_status='----',
                                                       country= "----",
                                                       region = "----",
                                                       sub_region = '----', # intentionally leave this loose.
                                                       age='----', 
                                                       user_has_done_a_search = False,
                                                       preference=userobject.sex,
                                                       query_order="unique_last_login",
                                                       lang_code=lang_code,
                                                       )
        else: # if settings.BUILD_NAME == "language_build":
            search_preferences2 = UserSearchPreferences2(sex='----',
                                                         country='----',
                                                         region = '----',
                                                         sub_region = '----', # intentionally leave this loose.
                                                         age='----',
                                                         user_has_done_a_search = False,
                                                         query_order="unique_last_login",
                                                         language_to_teach = userobject.native_language,
                                                         language_to_learn = userobject.language_to_learn,
                                                         lang_code = lang_code,
                                                         )

        search_preferences2.put()
        
        return search_preferences2.key
    
    except: 
        error_reporting.log_exception(logging.critical)      
    
#############################################   
    
def store_crawler_session(request):
    # stores a session for google crawler and for superuser access. 
    # verify that IP address is either a google address, or my home IP address before enabling this.
    
    # Only call this function AFTER login credentials have been verified.

    try:
        remoteip  = os.environ['REMOTE_ADDR']
            
        # ensure that the IP address which has attempted to access all regions, is authorized.
        if constants.GOOGLE_CRAWLER_IP_PATTERN.match(remoteip) or \
           constants.MY_HOME_IP_PATTERN.match(remoteip) or \
           constants.LOCAL_IP_PATTERN.match(remoteip):
    
            # session will expire after 30 minute (note, value passed in is seconds, so multiply by 60)
            # If we ever user google AdSense again, we will have to expire the session after a reasonable amount of time .. 
            #request.session.set_expiry(30 * 60) 
            
            request.session.__setitem__(constants.CRAWLER_SESSION_NAME, "Dummy")
            error_reporting.log_exception(logging.info, error_message="Crawler session successfuly set")  
            status = "Success"
        else:
            error_reporting.log_exception(logging.info, error_message="Crawler session not set")  
            status = "Invalid IP %s" % remoteip
            
        return status
    except:
        error_reporting.log_exception(logging.critical)  
        
    return "Error"
        
def clear_old_session(request):  
    # Used for clearing old sessions
    
    try:
        request.session.terminate(clear_data = True)
    except:
        error_reporting.log_exception(logging.critical)  
        

def clear_session(request):  
    # Used for clearing old sessions -- returns HttpResponse so we can call direct from a URL
    clear_old_session(request)
    return http.HttpResponseRedirect("/%s/" % request.LANGUAGE_CODE)

    
def check_test_cookie(request):
    # checks that a cookie was successfully written and read from the client machine.
    if request.session.test_cookie_worked():
        return True
    else:
        return False

def remove_photos_from_profile(userobject):
    # queries for all photos associated with a userprofile, and deletes them.
    # Also updates the user_photos_tracker to not reference to any photos.


    all_user_photo_keys = models.PhotoModel.query().filter(models.PhotoModel.parent_object == userobject.key).fetch(keys_only = True)
    num_photos = len(all_user_photo_keys)
    for photo_key in all_user_photo_keys:
        photo_key.delete()

    logging.info("Removing %d photos from userobject %s" % (num_photos, userobject.username))

    if userobject.user_photos_tracker_key:
        user_photos_tracker = userobject.user_photos_tracker_key.get()
        user_photos_tracker.profile_photo_key = None
        user_photos_tracker.public_photos_keys = []
        user_photos_tracker.private_photos_keys = []
        user_photos_tracker.put()

    
def take_action_on_account_and_generate_response(request, userobject, action_to_take, reason_for_profile_removal = None, new_password = None, 
                                                 new_email_address = None, return_html_or_text = "html"):
    # this function marks the user object as deleted, enabled, etc (defined by action_to_take), and assumes that verifications have already been done
    # This function should *NEVER* be exposed as a URL.
    
    try:
        remoteip  = os.environ['REMOTE_ADDR']
        profile_href = profile_utils.get_userprofile_href(request.LANGUAGE_CODE, userobject, is_primary_user=False)
        linked_username = """<a href="%s">%s</a>""" % (profile_href, userobject.username,)

        if action_to_take == "delete":
            # doesn't need to be inside transaction since a conflict doesn't really matter, and because we are doing
            # a query which does not work inside a transaction.
            remove_photos_from_profile(userobject)

        def txn(user_key):
            # run in transaction to prevent conflicts with other writes to the userobject.
            userobject =  user_key.get()
        
            if action_to_take == "delete":
                userobject.user_is_marked_for_elimination = True
                # The following html is multi-lingual because this branch can be executed by a user call, and the return value
                # will be displayed as html to the user. 
                html_for_action_on_account = u"%s %s<br>" % (ugettext("We have deleted the profile of"), linked_username)
                userobject.reason_for_profile_removal = reason_for_profile_removal
                
            elif action_to_take == "undelete": 
                userobject.user_is_marked_for_elimination = False

                html_for_action_on_account = u"%s %s.<br>" % ("We have un-deleted the profile of",
                    linked_username)
                userobject.reason_for_profile_removal = None
                
                
            elif action_to_take == "reset":
                # Reset access to this profile. This requires setting a new password as well as a new email address 
                if not new_email_address:
                    html_for_action_on_account = u"You must pass in an email address to enable account. /rs/admin/action/reset/name/[name_val]/[email_val]/[password_val]/<br>"
                else:
                    html_for_action_on_account = u"We have reset access to %s. New email is %s and new password is %s<br>"  % (
                        linked_username, new_email_address, new_password)     
                    
                    # Note: eventually , we may consider storing the original email_address and hashed-password in a seperate data structure
                    # in case we wan the ability to roll-back  profiles that we have "reset" to their original owners. Not a priority right
                    # now, and so not done yet. 
                    userobject.email_address = new_email_address
                    userobject.password = utils.new_passhash(new_password, userobject.password_salt)
                    userobject.reason_for_profile_removal = None    
                    if new_email_address in constants.REGISTRATION_EXEMPT_EMAIL_ADDRESSES_SET:
                        userobject.email_options[0] = 'only_password_recovery'
                    else:
                        html_for_action_on_account += """<p>WARNING, the email address you have set is not in 
                        REGISTRATION_EXEMPT_EMAIL_ADDRESSES_SET: %s. This means that notification emails will be sent
                        to %s</p>""" % (constants.REGISTRATION_EXEMPT_EMAIL_ADDRESSES_SET, new_email_address)
                        userobject.email_options[0] = 'daily_notification_of_new_messages'
                        
            elif action_to_take == "set_password":
                if not new_password:
                    html_for_action_on_account = "You need to pass in a password. /rs/admin/action/set_password/name/[name_val]/[new_password]/<br>"
                else:
                    html_for_action_on_account = u"We set new password for %s to %s<br>" % (linked_username, new_password)                
                    userobject.password = utils.new_passhash(new_password, userobject.password_salt)
            elif action_to_take == "list":
                html_for_action_on_account = u"%s<br>" % linked_username
            else: 
                html_for_action_on_account = u'Error: unknown action_to_take %s on user %s<br>' % (action_to_take, linked_username)
            
            utils.put_userobject(userobject)
            
            return html_for_action_on_account
    
            
        # mark the userobject for elimination -- do in a transaction to ensure that there are no conflicts!
        
        html_for_delete_account = ndb.transaction(lambda: txn(userobject.key))
        
        info_message = "IP %s %s\n" % (remoteip, html_for_delete_account)
        logging.info(info_message)
    
        # Kill *ALL* sessions (remove from DB) that this user currently has open (on multiple machines)
        if action_to_take == "delete" or action_to_take == "reset":
            gaesessions.kill_user_sessions(userobject.user_tracker)
        
        if return_html_or_text == "html":
            template = loader.select_template(["proprietary_html_content/goodbye_message.html", "common_helpers/default_goodbye_message.html"])
            context = Context(dict({
                'html_for_delete_account': html_for_delete_account, 
                'build_name': settings.BUILD_NAME,}, **constants.template_common_fields))
            
            generated_html = template.render(context)
            nav_bar_text = ugettext("You have exited")
            
            response = search_results.generate_search_results(request, 
                                                              type_of_search="normal", 
                                                              register_enter_click_sends_to_landing=True, 
                                                              hide_page_from_webcrawler=True,
                                                              text_override_for_navigation_bar = nav_bar_text,  
                                                              extra_html_above_results = generated_html)

            return response
        else:
            return html_for_delete_account
        
    except:
        error_reporting.log_exception(logging.critical)   
        return ""
    
def delete_userobject_with_name_and_security_hash(request, username, hash_of_creation_date):
    # receives a username and a security hash, and deletes the userobject -- this is meant to be called directly
    # from email links, without forcing a login of the user. 
    
    try:
        userobject = utils.get_active_userobject_from_username(username)
        
        if userobject and \
           hash_of_creation_date == userobject.hash_of_creation_date[:constants.EMAIL_OPTIONS_CONFIRMATION_HASH_SIZE] and\
           userobject.user_is_marked_for_elimination == False:
            http_response = take_action_on_account_and_generate_response(request, userobject, action_to_take = "delete")
        else: 
            generated_html =  u'<div class="cl-text-large-format"><br><br>'
    
            if not userobject:
                generated_html += u"%s" % ugettext("Profile %(username)s has already been deleted, or never existed") % {'username': username}
            else:
                generated_html += ugettext("Error - Not authorized")
                
            generated_html += u'</div>'
            nav_bar_text = ugettext("You have exited")
            
            
            http_response = search_results.generate_search_results(request, 
                                                             type_of_search="normal", 
                                                             register_enter_click_sends_to_landing=True, 
                                                             hide_page_from_webcrawler=True,
                                                             text_override_for_navigation_bar = nav_bar_text,
                                                             extra_html_above_results = generated_html)            

            error_message = "Error: unable to delete username: %s hash_of_creation_date: %s" % (
                username, hash_of_creation_date)
            error_reporting.log_exception(logging.error, error_message=error_message)  
       
        return http_response
    except:
        error_reporting.log_exception(logging.critical)   
        return http.HttpResponseRedirect("/%s/" % request.LANGUAGE_CODE)


def delete_or_undelete_account(request, owner_uid, delete_or_undelete):
    # marks the user account for deletion, which will be done by periodic batch/cleanup
    # scripts. 
    #
    # Later we will run a batch job that will clear out all emails, contacts, etc.

    try:
        owner_userobject = utils_top_level.get_userobject_from_request(request)
        
        if not owner_userobject:
            return http.HttpResponseRedirect("/%s/" % request.LANGUAGE_CODE)
        
        assert(owner_uid == owner_userobject.key.urlsafe())
        
        return take_action_on_account_and_generate_response(request, owner_userobject, delete_or_undelete)
    except:
        error_reporting.log_exception(logging.critical)   
        return http.HttpResponseRedirect("/%s/" % request.LANGUAGE_CODE)
    




def extract_data_from_login_dict(login_dict):
    
    # gets user login info from the GET string that is passed in -- also, writes the login data into the "additional_form_data"
    # string, which is useful for writing the data into a POST which will be posted to a storage function, if the validation
    # is passed correctly.
    
    additional_form_data = ''
    username = ''
    email_address = ''
    for field in UserSpec.signup_fields_to_display_in_order + ['sub_region', 'region', 'country']: 
        # Copy the POST into the hidden fields so they can be saved after the 
        # the user has solved a captcha.
        value = login_dict[field]

        if field == 'username':
            username = value
        if field == 'email_address':
            email_address = value
            email_address = email_address.lower()
            
    return(username, email_address)


def check_if_username_and_email_are_in_authorization_info(username, email_address):
    
    assert(username)
    assert(email_address)
    q = models.EmailAutorizationModel.query()
    q = q.filter(models.EmailAutorizationModel.username == username)
    q = q.filter(models.EmailAutorizationModel.email_address == email_address)
    authorization_info = q.get()
    return authorization_info

def query_authorization_info_for_username(username,):

    assert(username)
    
    q = models.EmailAutorizationModel.query()
    q = q.filter(models.EmailAutorizationModel.username == username)
    
    authorization_info = q.get()
        
    return authorization_info


def check_authorization_info_for_email_registrations_today(creation_day, email_address):
    
    q = models.EmailAutorizationModel.query()
    q = q.filter(models.EmailAutorizationModel.email_address == email_address)
    q = q.filter(models.EmailAutorizationModel.creation_day == creation_day)
        
    return q.count(constants.MAX_REGISTRATIONS_SINGLE_EMAIL_IN_TIME_WINDOW)
    
    
def check_authorization_info_for_ip_address_registrations_today(creation_day, ip_address):
    
    q = models.EmailAutorizationModel.query()   
    q = q.filter(models.EmailAutorizationModel.ip_address == ip_address)
    q = q.filter(models.EmailAutorizationModel.creation_day == creation_day)

    return q.count(constants.MAX_REGISTRATIONS_SINGLE_IP)  

def email_address_already_has_account_registered(email_address):
    
    try:
        email_address = email_address.lower()
        query = models.UserModel.gql("WHERE email_address = :email_address and \
        user_is_marked_for_elimination = False \
        ORDER BY last_login_string DESC", 
        email_address = email_address)
        
        userobject = query.get()    
        
        if userobject:
            return True
        else:
            return False
    except:
        error_reporting.log_exception(logging.critical)   
        return False
    
def send_verification_email(currently_displayed_url, username, email_address, secret_verification_code, lang_code):
    
    try:
        if not email_address_already_has_account_registered(email_address) or email_address in constants.REGISTRATION_EXEMPT_EMAIL_ADDRESSES_SET:
    
            subject = ugettext("Verification of your email and registration")  
    
            message_html = u"<p>%s, " % ugettext("Hello %(username)s") % {'username': username}
            message_html += u"<p>%s:<p>" % \
                   ugettext("To activate your account in %(app_name)s click on the following link") % \
                   {'app_name' : settings.APP_NAME }
            href = """http://www.%(app_name)s.com%(currently_displayed_url)s?show_verification=true&amp;\
verification_username=%(username)s&amp;secret_verification_code=%(secret_verification_code)s""" % \
                {'currently_displayed_url' : currently_displayed_url, 
                 'app_name' : settings.APP_NAME, 
                 'username' : username, 
                 'secret_verification_code' : secret_verification_code,
                 }
            
            message_html += href
            message_html += "<p>%s: %s<p>" % (ugettext("Verification code"), secret_verification_code)            
            message_html += u"<p>%s. " % ugettext("If clicking on the link appears not to work, you can copy and paste it into your browser")
                            
            return_val = "Code sent"                
        else:
            # If the user is not allowed to register because they already have an account registered with the current email 
            # address, we *intentionally* don't write to the authorization info, because we want for them to be able to 
            # sign-up a new account after deleting their existing account - even if they are still within the "time_window" 
            # (currently a day) for receiving registration notifications on a single email address. 
            # This makes sense, because the current authorization_info is useless as long as they have an account already registered for
            # their current email address -- and if they do decide to register on a new email address, then a new authorization_info will
            # be written at that point in time. 
            subject = ugettext("Verification failed")  
            message_html = u"<p>%s, " % ugettext("Hello %(username)s") % {'username': username}
            message_html += u"<p>%s" % \
                               ugettext("""
                               Unfortunately we are unable to register your new account in %(app_name)s, since you already have an account registered.
                               If you wish to register a new account, please delete the old account first.""") % \
                               {'app_name' : settings.APP_NAME }    
            message_html += u"%s" % utils.html_to_request_new_password(email_address)
            
            return_val = "Code not sent"
            
        message_html += email_utils.text_for_footer_on_registration_email(os.environ['REMOTE_ADDR'])
            
        
        taskqueue.add(queue_name = 'fast-queue', url='/rs/admin/send_generic_email_message/', \
                      params = {'username' : username, 
                                'email_address': email_address,
                                'subject' : subject,
                                'lang_code' : lang_code,
                                'message_html' : message_html
                                })
    except:
        return_val = "Unknown internal error - check logs"
        error_reporting.log_exception(logging.critical)   
        
    return return_val

    
def store_authorization_info_and_send_email(currently_displayed_url, username, email_address, encrypted_password, password_salt, pickled_login_get_dict, lang_code):
    # Writes a (hopefully temporary) object to the database, which will be accessed when the user verifies their account 
    # by clicking on a URL directly from their email -- note, this function saves us from sending
    # out super long URLs that get broken up by email systems and that would therefore cause problems -- instead, we store
    # the user data in the database, and access it using a short email.
    # 
    # returns (authorizaion_info_status, secret_verification_code)
    secret_verification_code = ''
    try:
        
        # Will run periodic clean-up routines to remove registrations that were not completed
        secret_verification_code = utils.compute_secret_verification_code(username, email_address)
        creation_day = datetime.datetime.now().strftime("%Y-%m-%d")
        ip_address = os.environ['REMOTE_ADDR']
        
        
        # Now, check the database to ensure that we are not receiving thousands of requests from the same email address
        # We will put a hard limit on the number of registraton requests from a single email address in a single day.
        email_address_authorization_info_count = check_authorization_info_for_email_registrations_today(creation_day, email_address)
        if email_address_authorization_info_count >= constants.MAX_REGISTRATIONS_SINGLE_EMAIL_IN_TIME_WINDOW and \
           email_address not in constants.REGISTRATION_EXEMPT_EMAIL_ADDRESSES_SET:
            # This user has already exceeded the number of allowed attempted registrations for this email address in the past day
            # do not allow additional registration. 
            # This prevents someone from spamming an email address with multiple registration requests. 
            error_message = ugettext("We already sent an email to %(email_address)s and cannot send another email to the same account until tomorrow - please register with a different email address") % {
                'email_address' : email_address}
            error_reporting.log_exception(logging.error, error_message=error_message)  
            
            return error_message
        
        ip_address_registration_count = check_authorization_info_for_ip_address_registrations_today(creation_day, ip_address)
        if ip_address_registration_count >= constants.MAX_REGISTRATIONS_SINGLE_IP and \
            ip_address not in constants.REGISTRATION_EXEMPT_IP_ADDRESS_SET and \
            email_address not in constants.REGISTRATION_EXEMPT_EMAIL_ADDRESSES_SET:
            error_message="Exceeded registrations allowed on IP: %s. Username %s email_address %s not registered." % (ip_address, username, email_address)
            error_reporting.log_exception(logging.critical, error_message=error_message)  
            email_utils.send_admin_alert_email(error_message, subject="%s - IP %s registration exceeded" % (settings.APP_NAME, ip_address))
            return "OK" # Don't inform the user of this error - they are hacking our system and don't need any extra help
        
        # the following is just a warning (even though I report it as an error so that I don't miss it)
        # We allow the registration to proceede
        if ip_address_registration_count >= constants.MAX_REGISTRATIONS_SINGLE_IP/2:
            logging.error("Getting close to limit for registrations permitted (%s) from IP: %s" % (constants.MAX_REGISTRATIONS_SINGLE_IP, ip_address))    
         
 
        authorization_info = check_if_username_and_email_are_in_authorization_info(username, email_address)
        # make sure that the combination of email_address and username has not already been written to the database. 
        # if it has, just overwrite with the new GET string instead of creating a new object.
        if not authorization_info:
            # if the object doesn't exist, then create a new one and send an email notification
            # about the registration.
            send_notification_email = True
            authorization_info = models.EmailAutorizationModel()            
        else:
            # The email / username combination is already registered -- therefore we do NOT send an email
            send_notification_email = False
            error_message = ugettext("""We have previously sent an email to %(email_address)s to activate the account for %(username)s. 
            We cannot send another activation message for this account.""") % {'email_address' : email_address, 'username' : username}   
            return (error_message, secret_verification_code)
        
        authorization_info.secret_verification_code = secret_verification_code    
        authorization_info.username = username  
        authorization_info.pickled_login_get_dict = pickled_login_get_dict
        authorization_info.has_been_authorized = False
        authorization_info.encrypted_password = encrypted_password
        authorization_info.password_salt = password_salt
        authorization_info.ip_address  = ip_address 
        authorization_info.email_address = email_address
        authorization_info.creation_day = creation_day
        
        logging.info("** Secret code for %s (%s) set to %s\n\n" % (username, email_address, secret_verification_code))
        code_sent_val = send_verification_email(currently_displayed_url, username, email_address, secret_verification_code, lang_code)
        
        if code_sent_val == "Code sent":
            authorization_info.put()
                        
        return ("OK") # just means that no internal errors or violations occured.
    
    except:
        error_reporting.log_exception(logging.critical)   
        return ('Unknown Error')
        


def copy_principal_user_data_fields_into_ix_lists(userobject):

    try:
        for field in user_profile_main_data.UserSpec.principal_user_data + ['region', 'sub_region',]:
            
            val = getattr(userobject, field)
            ix_field_name = field + "_ix_list"
            ix_list = [u'----',]
            if val:
                ix_list.append(val)
            setattr(userobject, ix_field_name, ix_list)   
    except:
        error_message = "Unknown error userobject: %s" % (repr(userobject))
        error_reporting.log_exception(logging.critical, error_message = error_message)




#############################################
def setup_new_user_defaults_and_structures(userobject, username, lang_code):
    """ set sensible initial defaults for the profile details. 
        Also, sets other defaults that need to be configured upon login.
        lang_code: the langage that the user is viewing the website in.
        native_language: (if set -- currenly only in language_build) refers to the native language that the user speaks.
        Note, the user could be viewing the website in English, but be a native speaker of German .. 
        therefore we would mark him initally as speaking both English and German. 
    """
    
    try:
    
        copy_principal_user_data_fields_into_ix_lists(userobject)
        
        userobject.email_options = ['daily_notification_of_new_messages_or_contacts']
        
    
        for field_name in user_profile_details.UserProfileDetails.enabled_checkbox_fields_list:
            setattr(userobject, field_name, ['prefer_no_say' ])
                
        if settings.BUILD_NAME == "language_build":
            
            # set language fields to ['----', *language* ], since we know that the user has already specified 
            # a language (only for LikeLangage)
            userobject.languages = [u'----',]
            userobject.languages.append(userobject.native_language)
                
            userobject.languages_to_learn = [u'----',]
            userobject.languages_to_learn.append(userobject.language_to_learn)
        else:
            try:
                # set the languages field to include the language that the user is currently viewing this website in.
                # Note: we don't do this for language_build, because viewing/reading in a language is not enough information 
                # for us to determine if the user is tryingto learn the language, or if they speak well enough to teach
                # someone else. Additionally, in language_build, we have the user language. Here we are inferring it.
                userobject.languages = []
                userobject.languages.append(localizations.language_code_transaltion[lang_code])
            except:
                error_reporting.log_exception(logging.critical, error_message = "Error, unknown lang_code %s passed in" % lang_code)
                userobject.languages = ['english',]
                
    
        userobject.last_login =  datetime.datetime.now()
        userobject.last_login_string = str(userobject.last_login)
    
        userobject.previous_last_login = datetime.datetime.now()
        
        userobject.hash_of_creation_date = utils.old_passhash(str(userobject.creation_date))

        userobject.unique_last_login = str(datetime.datetime.now())

        userobject.unread_mail_count_ref = utils.create_unread_mail_object()
        userobject.new_contact_counter_ref = utils.create_contact_counter_object()
        
        userobject.spam_tracker = messages.initialize_and_store_spam_tracker(userobject.spam_tracker) 
        
        userobject.user_tracker = utils.create_and_return_usertracker()
        
        userobject.user_photos_tracker_key = utils.create_and_return_user_photos_tracker()
            
        sharding.increment("number_of_new_users_shard_counter")
    
        # setup structures for chat
        owner_uid = userobject.key.urlsafe
    
        # userobject will be put in the function that called this. 
        return userobject 
    
    except: 
        error_reporting.log_exception(logging.critical)     
        return None