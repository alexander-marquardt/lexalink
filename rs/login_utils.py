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

from models import UserSearchPreferences2, UniqueLastLoginOffsets
from user_profile_details import UserProfileDetails
from user_profile_main_data import UserSpec


import utils, email_utils, messages
import sharding
import constants
import utils, utils_top_level, channel_support, chat_support
import forms
import error_reporting
import models
import localizations, user_profile_main_data, user_profile_details, online_presence_support
import rendering
import gaesessions

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
    



def create_and_put_unique_last_login_offset_ref():
    
    unique_last_login_offset_obj = UniqueLastLoginOffsets()
    unique_last_login_offset_obj.put()
    return unique_last_login_offset_obj.key
    
def get_or_create_unique_last_login(userobject, username):
    """ adds appropriate offsets to the current "unique_last_login" value so that 
    the search results will be ordered based on the settings of the current user.
    
    If the unique_last_login_ref object doesn't exist, this function will create it
    and it will be passed back to the calilng function for association with the userobject.
    
    This function returns the new value for "unique_last_login", but also returns the reference to
    the unique_last_login_offset_ref object -- which can be ignored if it is not neede (if, if you
    are 100% certian that this object already exists, and it is already stored in the userobject). We
    don't write this value directly to the userobject (we don't put() it to the database), because 
    generally this function is called right before a put of the userobject is going to happen, and it
    would be wasteful to write this value 2x when we can just do it 1x by passing the value to the 
    caller.
    """
    
    try:
    
        offset = 0 # the offset is in Days.
        # make sure it has the attribute, and that the attribute is set
        if hasattr(userobject, 'unique_last_login_offset_ref') and userobject.unique_last_login_offset_ref:
            unique_last_login_offset_key = userobject.unique_last_login_offset_ref
            unique_last_login_offset_obj = unique_last_login_offset_key.get()
            
            # loop over all offset values, and assign the value if the boolean in offset_ref indicates
            # that it should be assigned.
            for (offset_name, value) in constants.offset_values.iteritems():
                has_offset = getattr(unique_last_login_offset_obj, offset_name)
                if has_offset:
                    
                    if offset_name == "has_private_photo_offset":
                        # only count private photos if they don't have any public/profile photos
                        if not unique_last_login_offset_obj.has_profile_photo_offset and not unique_last_login_offset_obj.has_public_photo_offset:
                            # if it has a profile photo offset, don't count private_photo or public_photo offsets - 
                            # we want to avoid double counting.
                            offset += value
                    elif offset_name == "has_public_photo_offset":
                        # only count public photos if they don't have a profile photo
                        if not unique_last_login_offset_obj.has_profile_photo_offset:
                            offset += value
                    else:
                        offset += value
        else:
            # create the attribute
            unique_last_login_offset_key = create_and_put_unique_last_login_offset_ref()
            
                    
        unique_last_login_with_offset = userobject.last_login + datetime.timedelta(hours=offset)
        unique_last_login = "%s_%s" % (unique_last_login_with_offset, username)
        
        return (unique_last_login, unique_last_login_offset_key)

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
        elif login_dict['password'] != login_dict["password_verify"]:
            error_dict['password_verify'] = u"%s" % constants.ErrorMessages.passwords_not_match
            
        if len(login_dict["password_verify"]) > constants.MAX_TEXT_INPUT_LEN:
            error_dict['password_verify'] = u"%s" % ugettext("<strong>Password</strong> must not be more than %(max_len)s characters") % {
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
        
        if settings.BUILD_NAME != "language_build" and settings.BUILD_NAME != "friend_build":   
            try_remaining_signup_fields("preference")
            try_remaining_signup_fields("relationship_status")
        
        else:
            if settings.BUILD_NAME == "language_build":
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
        if settings.BUILD_NAME != "language_build" and settings.BUILD_NAME != "friend_build":
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
        else:
            if settings.BUILD_NAME == "language_build":
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
            if settings.BUILD_NAME == "friend_build":
                search_preferences2 = UserSearchPreferences2(sex='----',
                                                             country='----',
                                                             region = '----',
                                                             sub_region = '----', # intentionally leave this loose.
                                                             age='----', 
                                                             for_sale = "----", 
                                                             for_sale_sub_menu = "----",
                                                             user_has_done_a_search = False,
                                                             query_order="unique_last_login",
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

    
def take_action_on_account_and_generate_response(request, userobject, action_to_take, reason_for_profile_removal = None, new_password = None, 
                                                 new_email_address = None, return_html_or_text = "html"):
    # this function marks the user object as deleted, enabled, etc (defined by action_to_take), and assumes that verifications have already been done
    # This function should *NEVER* be exposed as a URL.
    
    try:
        remoteip  = os.environ['REMOTE_ADDR']
        
        
        def txn(user_key):
            # run in transaction to prevent conflicts with other writes to the userobject.
            userobject =  user_key.get()
        
            if action_to_take == "delete":
                userobject.user_is_marked_for_elimination = True
        
                # The following html is multi-lingual because this branch can be executed by a user call, and the return value
                # will be displayed as html to the user. 
                html_for_delete_account = u"<p>%s %s.</p>" % (ugettext("We have deleted the profile of"), userobject.username)
                userobject.reason_for_profile_removal = reason_for_profile_removal
                
            elif action_to_take == "undelete": 
                userobject.user_is_marked_for_elimination = False

                html_for_delete_account = u"<p>%s %s.</p>" % ("We have un-deleted the profile of",
                    userobject.username)
                userobject.reason_for_profile_removal = None
                
                
            elif action_to_take == "reset":
                # Reset access to this profile. This requires setting a new password as well as a new email address since
                # these values were previously removed.
                if not new_email_address:
                    html_for_delete_account = u"<p>You must pass in an email address to enable account. /rs/admin/action/reset/name/[name_val]/[email_val]/[password_val]/</p>"
                else:
                    html_for_delete_account = u"<p>We have reset access to %s. New email is %s and new password is %s</p>"  % (
                        userobject.username, new_email_address, new_password)     
                    
                    # Note: eventually , we may consider storing the original email_address and hashed-password in a seperate data structure
                    # in case we wan the ability to roll-back  profiles that we have "reset" to their original owners. Not a priority right
                    # now, and so not done yet. 
                    userobject.email_address = new_email_address
                    userobject.password = utils.new_passhash(new_password, userobject.password_salt)
                    userobject.reason_for_profile_removal = None    
                    if new_email_address in constants.REGISTRATION_EXEMPT_EMAIL_ADDRESSES_SET:
                        userobject.email_options[0] = 'only_password_recovery'
                    else:
                        userobject.email_options[0] = 'daily_notification_of_new_messages'
                        
            elif action_to_take == "set_password":
                if not new_password:
                    html_for_delete_account = "<p>You need to pass in a password. /rs/admin/action/set_password/name/[name_val]/[new_password]/</p>"
                else:
                    html_for_delete_account = u"<p>We set new password for %s to %s</p>" % (userobject.username, new_password)                
                    userobject.password = utils.new_passhash(new_password, userobject.password_salt)
            else: 
                html_for_delete_account = u'<p>Error: unknown action_to_take: %s</p>' % action_to_take
            
            utils.put_userobject(userobject)
            
            return html_for_delete_account
    
            
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
            response = rendering.render_main_html(request, generated_html, text_override_for_navigation_bar = nav_bar_text, 
                                                           hide_page_from_webcrawler = True,
                                                           show_search_box = False, hide_why_to_register = True)
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
            http_response = rendering.render_main_html(request, generated_html, text_override_for_navigation_bar = nav_bar_text, 
                                                       hide_page_from_webcrawler = True,
                                                       show_search_box = True, hide_why_to_register = True)
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
    
def send_verification_email(username, email_address, secret_verification_code, lang_code):
    
    try:
        if not email_address_already_has_account_registered(email_address) or email_address in constants.REGISTRATION_EXEMPT_EMAIL_ADDRESSES_SET:
    
            subject = ugettext("Verification of your email and registration")  
    
            message_html = u"<p>%s, " % ugettext("Hello %(username)s") % {'username': username}
            message_html += u"<p>%s:<p>" % \
                   ugettext("To activate your account in %(app_name)s, click on the following link to verify your request") % \
                   {'app_name' : settings.APP_NAME }
            message_html += """<a href=http://www.%(app_name)s.com/%(lang_code)s/rs/authenticate/%(username)s/%(secret_verification_code)s/>\
    http://www.%(app_name)s.com/%(lang_code)s/rs/authenticate/%(username)s/%(secret_verification_code)s/</a>""" % \
                {'lang_code': lang_code, 'app_name' : settings.APP_NAME, 
                 'username' : username, 
                 'secret_verification_code' : secret_verification_code,
                 }
            
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

    
def store_authorization_info_and_send_email(username, email_address, encrypted_password, password_salt, pickled_login_get_dict, lang_code):
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
            
            return (error_message, secret_verification_code)
        
        ip_address_registration_count = check_authorization_info_for_ip_address_registrations_today(creation_day, ip_address)
        if ip_address_registration_count >= constants.MAX_REGISTRATIONS_SINGLE_IP and \
           ip_address not in constants.REGISTRATION_EXEMPT_IP_ADDRESS_SET:
            error_message="Exceeded registrations allowed on IP: %s" % (ip_address)
            error_reporting.log_exception(logging.critical, error_message=error_message)  
            email_utils.send_admin_alert_email(error_message, subject="%s - IP %s registration exceeded" % (settings.APP_NAME, ip_address))
            return (error_message, secret_verification_code)
        
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
        
        code_sent_val = send_verification_email(username, email_address, secret_verification_code, lang_code)
        
        if code_sent_val == "Code sent":
            # Only write the authorization_info structure if we send the user an email that *contains* registration information,
            authorization_info.put()
                        
        return ("OK", secret_verification_code) # just means that no internal errors or violations occured.
    
    except:
        error_reporting.log_exception(logging.critical)   
        return ('Unknown Error', secret_verification_code)
        


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
            
        (userobject.unique_last_login, userobject.unique_last_login_offset_ref) = \
         get_or_create_unique_last_login(userobject, username)
        
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