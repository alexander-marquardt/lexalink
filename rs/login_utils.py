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

import datetime, logging, pickle, StringIO, os, re

from google.appengine.ext import db 
from google.appengine.api import taskqueue

# local settings
import settings

from django.template import Context, loader
from django.conf import settings
from django.core.validators import email_re
from django.utils.translation import ugettext

from models import UserSearchPreferences2, UniqueLastLoginOffsets
from user_profile_details import UserProfileDetails
from user_profile_main_data import UserSpec


import utils, email_utils
import sharding
import constants
import utils, utils_top_level, channel_support, chat_support, backup_data
import forms
import error_reporting
import models
import localizations, user_profile_main_data, online_presence_support
import rendering
import http_utils

#############################################

def store_session(request, userobject):
    
    # terminate any existing session/remove cookies - however, do not clear the databse as this will slow down the login 
    # let the cron jobs clear out the sessions from the database. 
    request.session.terminate(clear_data=False)
    
    userobject_str = str(userobject.key())
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

    # create "in-the-cloud" backups of the userobject
    backup_data.update_or_create_userobject_backups(request, userobject)    
    
    chat_support.update_or_create_open_conversation_tracker(owner_uid, "main", chatbox_minimized_maximized="maximized", type_of_conversation="NA")
    chat_support.update_or_create_open_conversation_tracker(owner_uid, "groups", chatbox_minimized_maximized="maximized", type_of_conversation="NA")
    
def html_for_posted_values(login_dict):
    # the following code returns posted values inside the generated HTML, so that we can use Jquery to 
    # search for these values, and replace them in the appropriate fields that were previously entered.
    # Note: the "hidden_" prefix -- this is necessary to avoid confusion with the real fields that have the
    # same name.
    
    html_for_previously_posted_values = ''
    if login_dict:
        for field in login_dict:
            hidden_field_name = "hidden_%s" % field
            hidden_field_id = "id-hidden_%s" % field
            value = login_dict[field]
            if value and value != '----':
                html_for_previously_posted_values += '<input type="hidden" id= "%s" name="%s" value="%s">\n' % (
                    hidden_field_id, hidden_field_name, value)
        
        return html_for_previously_posted_values

 
def generate_get_string_for_passing_login_fields(post_dict):
    # generates a get-style string which is used for passing login data within the URL (as opposed to in a POST)
    # This is necessary for certian steps during the login process.
    
    fields_to_pass_in_url = []
    fields_names = UserSpec.signup_fields_to_display_in_order + ['sub_region', 'region', 'country', 'password_hashed', 'login_type']
    for field in fields_names: 
        to_append = "%s=%s" % (field, post_dict[field])
        fields_to_pass_in_url.append(to_append)
        
    # seperate passed-in values with "&" as per html spec for a "get" request
    url_get_string = "&".join(fields_to_pass_in_url)    
    
    return url_get_string


def create_and_put_unique_last_login_offset_ref():
    
    unique_last_login_offset_ref = UniqueLastLoginOffsets()
    unique_last_login_offset_ref.put()
    return unique_last_login_offset_ref
    
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
    
    offset = 0 # the offset is in Days.
    # make sure it has the attribute, and that the attribute is set
    if hasattr(userobject, 'unique_last_login_offset_ref') and userobject.unique_last_login_offset_ref:
        unique_last_login_offset_ref = userobject.unique_last_login_offset_ref
        
        # loop over all offset values, and assign the value if the boolean in offset_ref indicates
        # that it should be assigned.
        for (offset_name, value) in constants.offset_values.iteritems():
            has_offset = getattr(unique_last_login_offset_ref, offset_name)
            if has_offset:
                
                if offset_name == "has_private_photo_offset":
                    # only count private photos if they don't have any public/profile photos
                    if not unique_last_login_offset_ref.has_profile_photo_offset and not unique_last_login_offset_ref.has_public_photo_offset:
                        # if it has a profile photo offset, don't count private_photo or public_photo offsets - 
                        # we want to avoid double counting.
                        offset += value
                elif offset_name == "has_public_photo_offset":
                    # only count public photos if they don't have a profile photo
                    if not unique_last_login_offset_ref.has_profile_photo_offset:
                        offset += value
                else:
                    offset += value
    else:
        # create the attribute
        unique_last_login_offset_ref = create_and_put_unique_last_login_offset_ref()
        
                
    unique_last_login_with_offset = userobject.last_login + datetime.timedelta(hours=offset)
    unique_last_login = "%s_%s" % (unique_last_login_with_offset, username)
    
    return (unique_last_login, unique_last_login_offset_ref)



#############################################

def error_check_signup_parameters(login_dict, lang_idx):
    
    error_list = [] # used for containing error messages to be presented to user in a friendly format   
    try:        
        if (not email_re.match(login_dict['email_address'])) or (len(login_dict['email_address'])>constants.MAX_TEXT_INPUT_LEN):
            error_list.append(u"%s" % constants.ErrorMessages.email_address_invalid)  
                
        if not login_dict['password']:
            error_list.append(u"%s" % constants.ErrorMessages.password_required)
                
        if login_dict['password'] != login_dict["password_verify"]:
            error_list.append(u"%s" % constants.ErrorMessages.passwords_not_match)
            
        if len(login_dict["password_verify"]) > constants.MAX_TEXT_INPUT_LEN:
            # this should never trigger, and is therefore just a message for admin (ie. in english only)
            error_list.append(u"%s" % "Password must be less than %s chars" % constants.MAX_TEXT_INPUT_LEN)
            
        # Verify that the password only contains acceptable characters  - this is necessary for 
        # the password hashing algorithm which only works with ascii chars.
        if (constants.rematch_non_alpha.search(login_dict['password']) != None):
            error_list.append(u"%s" %constants.ErrorMessages.password_alphabetic)
            
        # Verify that the username only contains acceptable characters 
        # This is not really necessary, but prevents people from entering strange names.
        if (constants.rematch_non_alpha.search(login_dict['username']) != None or len(login_dict['username']) < 3):
            error_list.append(u"%s" %constants.ErrorMessages.username_alphabetic)    
            
        if len(login_dict['username']) > constants.MAX_USERNAME_LEN:
            # this should never trigger, and is therefore just a message for admin (ie. in english only)
            error_list.append("Username must be less than %s chars" % constants.MAX_USERNAME_LEN)   
                        
        def try_remaining_signup_fields(field_name):
            try:
                # just make sure that a lookup on the given field-name doesn't trigger an exception -- which means
                # that it is valid, and can be used for lookups in our data structures.
                user_profile_main_data.UserSpec.signup_fields_options_dict[field_name][lang_idx][login_dict[field_name]]
            except:
                field_label = UserSpec.signup_fields[field_name]['label'][lang_idx]
                error_list.append(""""%s" %s""" % (field_label, ugettext("is not valid")))
            
        try_remaining_signup_fields("country")       
        try_remaining_signup_fields("sex")       
        try_remaining_signup_fields("age")
        
        if settings.BUILD_NAME != "Language" and settings.BUILD_NAME != "Friend":   
            try_remaining_signup_fields("preference")
            try_remaining_signup_fields("relationship_status")
        
        else:
            if settings.BUILD_NAME == "Language":
                try_remaining_signup_fields("native_language")
                try_remaining_signup_fields("language_to_learn")
            if settings.BUILD_NAME == "Friend":
                try_remaining_signup_fields("friend_price")
                try_remaining_signup_fields("friend_currency")                
                pass
            
        return(error_list)
    
    except: 
        error_reporting.log_exception(logging.critical)  
        error_list.append(ugettext('Internal error - this error has been logged, and will be investigated immediately'))
        return error_list

#############################################
def get_login_dict_from_post(request, login_type):
    # parses the POST data, and checks to see that something has been entered.
    
    login_dict = {}
    
    try:
        try:
            lang_idx = localizations.input_field_lang_idx[request.LANGUAGE_CODE]     
        except:
            error_reporting.log_exception(logging.critical)
            lang_idx = localizations.input_field_lang_idx['es']
        
        if login_type:
            login_dict['login_type'] = login_type
        if login_type == 'signup_fields' or login_type == "left_side_fields":
            
            if login_type == 'signup_fields':
                additional_fields =  ['password_hashed', 'country', 'region', 'sub_region']
            else:
                additional_fields = []
            fields_to_display_in_order = login_type + "_to_display_in_order"
            
            for field in getattr(UserSpec, fields_to_display_in_order) + additional_fields: 
                # Accept POST and GET -- use REQUEST to do this
                post_val = request.REQUEST.get(field, '----')
                if not post_val:
                    post_val = '----'
                    
                # probably a bit paranoid, but we cut the input to "MAX_TEXT_INPUT_LEN" - in case someone tries to overload our DB.
                login_dict[field] = post_val[:constants.MAX_TEXT_INPUT_LEN]
                
                        
    except:
        error_reporting.log_exception(logging.critical)
        error_list = ''
        
    return (login_dict) 




#############################################
def create_search_preferences2_object(userobject, lang_code):
    # set sensible initial search defaults based on the user profile
    # i.e., someone who prefers women should have the "sex" set to women.
    # For relationship_status, it is less obvious what the "optimal" setting would be
    # so, we just set the search setting to the same value as what the user has selected
    # Search location and age are set to the same as the client.
    
    if settings.BUILD_NAME != "Language" and settings.BUILD_NAME != "Friend":
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
        if settings.BUILD_NAME == "Language":
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
        if settings.BUILD_NAME == "Friend":
            search_preferences2 = UserSearchPreferences2(sex='----',
                                                         country='----',
                                                         region = '----',
                                                         sub_region = '----', # intentionally leave this loose.
                                                         age='----', 
                                                         for_sale = "----", 
                                                         to_buy = "----",
                                                         for_sale_sub_menu = "----",
                                                         to_buy_sub_menu = "----",
                                                         user_has_done_a_search = False,
                                                         query_order="unique_last_login",
                                                         lang_code = lang_code,
                                                         )
    
    search_preferences2.put()
    
    return search_preferences2
    
#############################################

def set_new_contact_counter_on_login(new_contact_counter_ref):
    # responsible for resetting the tracking of kisses, winks, keys, etc.. that have been received since
    # the last time the user logged in. Notice however, that we still keep the old value so that we can 
    # display it to the user (ie. we will show them the number of contact items received since the previous
    # time that they logged into the system)
    #
    # Could consider running this in a transaction -- but is not really necessary, since it gets reset periodically...

    
    new_contact_counter_ref.previous_num_received_kiss = new_contact_counter_ref.num_received_kiss_since_last_login
    new_contact_counter_ref.num_received_kiss_since_last_login = 0

    
    new_contact_counter_ref.previous_num_received_wink = new_contact_counter_ref.num_received_wink_since_last_login
    new_contact_counter_ref.num_received_wink_since_last_login = 0

    new_contact_counter_ref.previous_num_received_key = new_contact_counter_ref.num_received_key_since_last_login
    new_contact_counter_ref.num_received_key_since_last_login = 0
    
    new_contact_counter_ref.previous_num_received_friend_request_since_last_login = new_contact_counter_ref.num_received_friend_request_since_last_login
    new_contact_counter_ref.num_received_friend_request_since_last_login = 0
    
    new_contact_counter_ref.previous_num_received_friend_confirmation_since_last_login = new_contact_counter_ref.num_received_friend_confirmation_since_last_login
    new_contact_counter_ref.num_received_friend_confirmation_since_last_login = 0
   
    new_contact_counter_ref.put()
    

    

    
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
    return http_utils.redirect_to_url(request, "/%s/" % request.LANGUAGE_CODE)

    
def check_test_cookie(request):
    # checks that a cookie was successfully written and read from the client machine.
    if request.session.test_cookie_worked():
        return True
    else:
        return False

    
def delete_or_enable_account_and_generate_response(request, userobject, delete_or_enable, reason_for_profile_removal = None):
    # this function marks the user object as deleted, and assumes that verifications have already been done
    # This function should *NEVER* be exposed as a URL.
    
    try:
        remoteip  = os.environ['REMOTE_ADDR']
        
        
        def txn(user_key):
            # run in transaction to prevent conflicts with other writes to the userobject.
            userobject =  db.get(user_key) 
            
        
            if delete_or_enable == "delete":
                userobject.user_is_marked_for_elimination = True
        
                html_for_delete_account = u"<p>%s %s.</p>" % (ugettext("We have eliminated the profile of"), 
                                                                                userobject.username)
                userobject.reason_for_profile_removal = reason_for_profile_removal
                
            if delete_or_enable == "enable": 
                userobject.user_is_marked_for_elimination = False
                #userobject.last_login_string = str(datetime.datetime.now())
                #userobject.unique_last_login = str(datetime.datetime.now())
                html_for_delete_account = u"<p>%s %s.</p>" % (ugettext("We have enabled the profile of"),
                    userobject.username)
                userobject.reason_for_profile_removal = None
            
            utils.put_userobject(userobject)
            
            return html_for_delete_account
    
            
        # mark the userobject for elimination -- do in a transaction to ensure that there are no conflicts!
        
        html_for_delete_account = txn(userobject.key())
        
        info_message = "IP %s %s\n" % (remoteip, html_for_delete_account)
        logging.info(info_message)
    
        # Kill *ALL* sessions (remove from DB) that this user currently has open (on multiple machines)
        if delete_or_enable == "delete":
            utils.kill_user_sessions(userobject.user_tracker)
        
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
            http_response = delete_or_enable_account_and_generate_response(request, userobject, delete_or_enable = "delete")
        else: 
            generated_html =  u'<div class="cl-text-large-format"><br><br>'
    
            if not userobject:
                generated_html += u"%s: %s" % (ugettext("Profile does not exist"), username)
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
        return http_utils.redirect_to_url(request, "/%s/" % request.LANGUAGE_CODE)


def delete_or_enable_account(request, owner_uid, delete_or_enable):
    # marks the user account for deletion, which will be done by periodic batch/cleanup
    # scripts. 
    #
    # Later we will run a batch job that will clear out all emails, contacts, etc.

    try:
        owner_userobject = utils_top_level.get_userobject_from_request(request)
        
        if not owner_userobject:
            return http_utils.redirect_to_url(request, "/%s/" % request.LANGUAGE_CODE)
        
        assert(owner_uid == str(owner_userobject.key()))
        
        return delete_or_enable_account_and_generate_response(request, owner_userobject, delete_or_enable)
    except:
        error_reporting.log_exception(logging.critical)   
        return http_utils.redirect_to_url(request, "/%s/" % request.LANGUAGE_CODE)
    

def extract_data_from_get(request):
    
    # gets user login info from the GET string that is passed in -- also, writes the login data into the "additional_form_data"
    # string, which is useful for writing the data into a POST which will be posted to a storage function, if the validation
    # is passed correctly.
    
    additional_form_data = ''
    username = ''
    email_address = ''
    for field in UserSpec.signup_fields_to_display_in_order + ['sub_region', 'region', 'country', 'password_hashed', 'login_type']: 
        # Copy the GET into the hidden fields so they can be saved after the 
        # the user has solved a captcha.
        value = request.GET.get(field,'')

        additional_form_data += '<input type="hidden" name="%s" value="%s" />\n' % (
            field, value)
        if field == 'username':
            username = value
        if field == 'email_address':
            email_address = value
            email_address = email_address.lower()
            
    return(additional_form_data, username, email_address)


def extract_data_from_login_dict(login_dict):
    
    # gets user login info from the GET string that is passed in -- also, writes the login data into the "additional_form_data"
    # string, which is useful for writing the data into a POST which will be posted to a storage function, if the validation
    # is passed correctly.
    
    additional_form_data = ''
    username = ''
    email_address = ''
    for field in UserSpec.signup_fields_to_display_in_order + ['sub_region', 'region', 'country', 'password_hashed', 'login_type']: 
        # Copy the POST into the hidden fields so they can be saved after the 
        # the user has solved a captcha.
        value = login_dict[field]

        additional_form_data += '<input type="hidden" name="%s" value="%s" />\n' % (
            field, value)
        if field == 'username':
            username = value
        if field == 'email_address':
            email_address = value
            email_address = email_address.lower()
            
    return(additional_form_data, username, email_address)



def query_for_authorization_info(username, secret_verification_code):
    # given a username and secret_verification_code, query to see if it has already been registered, which
    # can happen if the user refreshes multiple times. 
    # Note, in the event that two users register
    # with the same username but different email addresses, the "secret_verification_code" should be almost
    # guaranteed to be unique. In any case, there is only an insignificant possibility of a clash if two
    # usernames (that are not already registered) are registered within the same time period and before one of them is activated. 
    
    assert(username)
    assert(secret_verification_code)
    
    query_filter_dict = {}   
    
    query_filter_dict['username'] = username
    query_filter_dict['secret_verification_code'] = secret_verification_code
    
    query = models.EmailAutorizationModel.all()
    for (query_filter_key, query_filter_value) in query_filter_dict.iteritems():
        query = query.filter(query_filter_key, query_filter_value)
        
    authorization_info = query.get()
    return authorization_info


def check_authorization_info_for_email_registrations_today(creation_day, email_address):
    
    query_filter_dict = {}   
    
    query_filter_dict['email_address'] = email_address
    query_filter_dict['creation_day'] = creation_day

    query = models.EmailAutorizationModel.all()
    for (query_filter_key, query_filter_value) in query_filter_dict.iteritems():
        query = query.filter(query_filter_key, query_filter_value)
        
    return query.count(constants.MAX_REGISTRATIONS_SINGLE_EMAIL_IN_TIME_WINDOW)
    
def check_authorization_info_for_ip_address_registrations_today(creation_day, ip_address):
    
    query_filter_dict = {}   
    
    query_filter_dict['ip_address'] = ip_address
    query_filter_dict['creation_day'] = creation_day
    
    query = models.EmailAutorizationModel.all()
    for (query_filter_key, query_filter_value) in query_filter_dict.iteritems():
        query = query.filter(query_filter_key, query_filter_value)
        
    return query.count(constants.MAX_REGISTRATIONS_SINGLE_IP)  

def email_address_already_has_account_registered(email_address):
    
    try:
        email_address = email_address.lower()
        query = models.UserModel.gql("WHERE email_address = :email_address and \
        is_real_user = True and\
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
    
    if not email_address_already_has_account_registered(email_address):

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
        return_val = "Code not sent"
        
    message_html += email_utils.text_for_footer_on_registration_email(os.environ['REMOTE_ADDR'])
        
    
    taskqueue.add(queue_name = 'fast-queue', url='/rs/admin/send_generic_email_message/', \
                  params = {'username' : username, 
                            'email_address': email_address,
                            'subject' : subject,
                            'lang_code' : lang_code,
                            'message_html' : message_html
                            })
    return return_val

    
def store_authorization_info_and_send_email(username, email_address, pickled_login_get_dict, lang_code):
    # Writes a (hopefully temporary) object to the database, which will be accessed when the user verifies their account 
    # by clicking on a URL directly from their email -- note, this function saves us from sending
    # out super long URLs that get broken up by email systems and that would therefore cause problems -- instead, we store
    # the user data in the database, and access it using a short email.

    try:
        
        # Will run periodic clean-up routines to remove registrations that were not completed
        secret_verification_code = utils.compute_secret_verification_code(username, email_address)
        creation_day = datetime.datetime.now().strftime("%d-%m-%Y")
        ip_address = os.environ['REMOTE_ADDR']
        
        
        # Now, check the database to ensure that we are not receiving thousands of requests from the same email address
        # We will put a hard limit on the number of registraton requests from a single email address in a single day.
        email_address_authorization_info_count = check_authorization_info_for_email_registrations_today(creation_day, email_address)
        if email_address_authorization_info_count >= constants.MAX_REGISTRATIONS_SINGLE_EMAIL_IN_TIME_WINDOW:
            # This user has already exceeded the number of allowed attempted registrations for this email address in the past day
            # do not allow additional registration. 
            # This prevents someone from spamming an email address with multiple registration requests. 
            error_message="Exceeded registrations allowed (%s) on email_address: %s" % (constants.MAX_REGISTRATIONS_SINGLE_EMAIL_IN_TIME_WINDOW, email_address)
            error_reporting.log_exception(logging.error, error_message=error_message)  
            
            return ugettext("We already sent an email to %(email_address)s and cannot send another email to the same account until tomorrow - please register with a different email address") % {
                'email_address' : email_address}
        
        #ip_address_registration_count = check_authorization_info_for_ip_address_registrations_today(creation_day, ip_address)
        #if ip_address_registration_count >= constants.MAX_REGISTRATIONS_SINGLE_IP:
            #error_message="Exceeded registrations allowed (%s) on IP: %s" % (constants.MAX_REGISTRATIONS_SINGLE_IP, ip_address)
            #error_reporting.log_exception(logging.critical, error_message=error_message)  
            #return u"El IP: %s ya ha registrado demasiadas cuentas hoy." % (ip_address)
        
        ## the following is just a warning (even though I report it as an error so that I don't miss it)
        ## We allow the registration to proceede
        #if ip_address_registration_count >= constants.MAX_REGISTRATIONS_SINGLE_IP/2:
            #logging.error("Getting close to limit for registrations permitted (%s) from IP: %s" % (constants.MAX_REGISTRATIONS_SINGLE_IP, ip_address))    
 
 
 
        authorization_info = query_for_authorization_info(username, secret_verification_code)
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
            return ugettext("""We have previously sent an email to %(email_address)s to activate the account for %(username)s. 
                               We cannot send another activation message for this account.""") % {
                            'email_address' : email_address, 'username' : username}            
        
        authorization_info.secret_verification_code = secret_verification_code    
        authorization_info.username = username  
        authorization_info.pickled_login_get_dict = pickled_login_get_dict
        authorization_info.has_been_authorized = False
        
        authorization_info.ip_address  = ip_address 
        authorization_info.email_address = email_address
        authorization_info.creation_day = creation_day
        
        code_sent_val = send_verification_email(username, email_address, secret_verification_code, lang_code)
        
        if code_sent_val == "Code sent":
            # Only write the authorization_info structure if we send the user an email that *contains* registration information,
            authorization_info.put()
                        
        return "OK" # just means that no internal errors occured.
    
    except:
        error_reporting.log_exception(logging.critical)   
        return 'Error'
        

def verify_user_login(request, login_dict):

    # Receives the user_login values and forces user to verify captcha or click on registration link (in an email) before
    # registration data is stored. Note, after this function is called, the store_data.store_new_user_after_verify() function
    # finishes the process/storage (called from the captcha, or from an email link sent to the user).

    try:
        generated_html = ''
        
        (additional_form_data, username, email_address) = extract_data_from_login_dict(login_dict)        
                   
        email_is_entered = False        
        if email_address and email_address != "----": 
    
            # if someone calls the associated URL without using our website (i.e hacking us), it is possible that they could pass in
            # bad values, and register invalid emails and usernames -- catch this.
            if (not email_re.match(email_address) or constants.rematch_non_alpha.search(username) != None or len(username) < 3):
                error_message="Invalid data passed in: username: %s email_address: %s" % (username, email_address)
                error_reporting.log_exception(logging.error, error_message=error_message)
                raise Exception(error_message)
                
            
            email_is_entered = True
            
            # pickle the GET string for re-insertion into the request object when the user clicks on the email link to
            # validate their account. 
            # We create a StringIO object because the pickle module expectes files to pickle the objects into. This is like a 
            # fake file. 
            pickled_login_get_dict_fake_file = StringIO.StringIO()
            
            pickle.dump(login_dict, pickled_login_get_dict_fake_file)        
            pickled_login_get_dict = pickled_login_get_dict_fake_file.getvalue()
            authorization_result = store_authorization_info_and_send_email(username, email_address, pickled_login_get_dict, request.LANGUAGE_CODE)   
            pickled_login_get_dict_fake_file.close()

                    
        # the following string is just an enconding of relevant post data for inclusion in the URL as a GET.
        string_for_get_login_data = generate_get_string_for_passing_login_fields(login_dict)
        
        assert(email_is_entered) 
             
        if authorization_result != "OK":     
            generated_html += u"""
                   <div class="cl-text-large-format">
                   <p></p><p>%s</p>
                   </div>
                   """ % (authorization_result)                

        href = "/%(locale)s/rs/resubmit_email/?%(string_for_get_login_data)s" % {
            'locale' : request.LANGUAGE_CODE,
            'string_for_get_login_data': string_for_get_login_data,
            }
        
        generated_html += u"""
        <div class="cl-text-large-format"><p><p>
        %(activate_code_to)s <strong> %(email_address)s </strong> %(from)s 
        <em>%(sender_email)s</em>. 
        </div>
        """ % {'activate_code_to' : ugettext("We have sent registration instructions to"), 
               'email_address': email_address, 'from' : ugettext("from"), 
               'sender_email': constants.sender_address_html,}
            
        generated_html += """<div class="cl-text-large-format"><p><p>** %(if_not_received)s</div>
        <div class="cl-text-large-format"></div>""" % {
        'if_not_received' : ugettext("""If you do not receive an email within a few minutes please check your Spam folder. 
        If the message from %(app_name)s has been marked as Spam, please mark it as not Spam so that you can recieve 
        future emails from us without any problems.""") % {'app_name' : settings.APP_NAME},
                                                    }

            
        generated_html += """<div>
        <p><p>%(problem_or_suggestion)s: \
        <strong>support@%(app_name)s.com</strong>.<p><p><p><p><p><p><p><p></div>
        """ % {'problem_or_suggestion' : ugettext("If you have any problems or suggestions, send us a message at"),
                'app_name': settings.APP_NAME}
    

    
        nav_bar = ugettext("Registering")
        return rendering.render_main_html(request, generated_html, text_override_for_navigation_bar = nav_bar, 
                                          link_to_hide = "login", hide_page_from_webcrawler=True, enable_ads = False,
                                          show_search_box = False, hide_why_to_register = True, hide_logo_banner_links = True)

    except:
        error_reporting.log_exception(logging.critical)   
        return "Error"
    
        

def resubmit_email(request):
    # if the user made a mistake when entering their email, this provides a simple for for resubmitting their email 
    # (without sending them back to the login page, which is another option)
    
    generated_html = ''
    (additional_form_data, username, email_address) = extract_data_from_get(request)  
       
    
    generated_html += u"""        
    <script type="text/javascript" language="javascript">
        $(document).ready(function(){
        
        mouseover_button_handler($("#id-submit-resubmit_email"))
        
     });
     </script>                

    
    <p><p><p>%(if_email)s<strong> %(email_address)s </strong>
    %(not_correct)s: </p>
    <form id="id-%(section_name)s-form" method="POST" action="/%(lang_code)s/" rel="form-address:/%(lang_code)s/">
    %(additional_form_data)s
    <strong>%(email)s: </strong><input type="text" class="cl-standard-textinput-width-px" id="id-signup_fields-email_address" name="email_address" maxlength=100>
    <input type=submit class = "cl-submit" id="id-submit-%(section_name)s" value="%(button_val)s">
    </form>
        
    <br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br>
    """ %   {'if_email' : ugettext("If the email address "), 'not_correct' : ugettext('is not correct, re-enter it here'), 
             'lang_code': request.LANGUAGE_CODE, 
             "email_address": email_address, 'section_name': 'resubmit_email', 'additional_form_data' : additional_form_data,
             'email': ugettext("Email"), 'button_val' : ugettext("Change email address"),
             }    
    
    nav_bar = ugettext("Registering")
    return rendering.render_main_html(request, generated_html, text_override_for_navigation_bar = nav_bar, 
                                               link_to_hide = "login", enable_ads = False, hide_page_from_webcrawler = True,
                                               show_search_box = False, hide_why_to_register = True)




