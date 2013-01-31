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


from google.appengine.ext import blobstore

from django.core.urlresolvers import reverse
import re, datetime, localizations, os

from user_profile_details import UserProfileDetails
import logging

from google.appengine.ext.db import BadRequestError

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseNotAllowed, HttpResponseBadRequest
from django.core.validators import email_re
from django.utils.translation import ugettext

import settings

from forms import *
from constants import *
from user_profile_main_data import UserSpec
from models import UserSearchPreferences2, PhotoModel
from login_utils import *
from utils import passhash, get_new_contact_count_sum, return_time_difference_in_friendly_format, requires_login
import mailbox 
import debugging
import admin, mailbox, login_utils, channel_support
import email_utils, backup_data, utils_top_level, sitemaps
import error_reporting, store_data, text_fields, lang_settings
from rs import profile_utils, online_presence_support, online_presence_support, track_viewers
from django import http
import http_utils, common_data_structs

if settings.BUILD_NAME == "Friend":
    import friend_bazaar_specific_code
    
try:
    from rs.proprietary import search_engine_overrides
except:
    pass

import chat_support

# do not move this above other imports, or the ugettext could be replaced by an imported lambda function
from django.utils.translation import ugettext

from callbacks_from_html import MyHTMLCallbackGenerator


#############################################
def redirect_to_user_main(request, display_uid,  is_primary_user = False):
    # function that will redirect this out-of-date URL to the correct new URL format
    try:
        userobject = utils_top_level.get_object_from_string(display_uid)
        redirect_url = profile_utils.get_userprofile_href(request.LANGUAGE_CODE, userobject, is_primary_user)
        logging.info("Re-directing old url for uid: %s to new url %s" % (display_uid, redirect_url))
        return http.HttpResponsePermanentRedirect(redirect_url)  
    
    except BadRequestError:
        # The request to the datastore service has one or more invalid properties. This has occured after moving
        # data from one application to another, and people/google have stored URLs that contain stale display_uid strings.
        error_reporting.log_exception(logging.info, error_message = "Incorrect display_uid app identifier, re-directing")
        new_uid = utils.convert_string_key_from_old_app_to_current_app(display_uid)
        if new_uid and new_uid != display_uid:
            # to prevent infinite loop, only redirect if the "new_uid" is different from the "display_uid"
            # For example, we want to be sure that we don't re-direct a bad uid key that is already in the
            # application name of current application.
            logging.info("Stale uid (from old application identifier): %s converted to %s" % (display_uid, new_uid))            
            return redirect_to_user_main(request, new_uid, is_primary_user)
        else:
            raise Exception("Bad display_uid passed into views.user_main")
    except:
        error_reporting.log_exception(logging.critical)        
        return http_utils.redirect_to_url(request, "/%s/" % request.LANGUAGE_CODE)


def user_main(request, display_nid, is_primary_user = False, profile_url_description = None):
    # The users "main" page, after logging in. Will show their profile.
    # display_uid - is the object key of the profile currently displayed -- if the client is viewing other
    #       users, then the uid references the other users object. If the client is viewing their own
    #       profile , then uid is a referenct to their own user object.
    # is_primary_user - allows us to re-use large portions of this code to display user profiles
    #    that belong to other users in the system. This means that edit is enabled, and private
    #    is displayed.
    try:
        display_uid = utils.get_uid_from_nid(display_nid)
        
        lang_code = request.LANGUAGE_CODE
        lang_idx = localizations.input_field_lang_idx[lang_code]
        
        # Do not remove these initializations unless you are 100% sure that the variable has been set in ALL branches.
        new_user_welcome_text = ""
        no_about_user_section_warning = ''
        email_is_not_entered_text = ""
        previous_contact_query_key_str = ''
        user_has_no_photo_text = ''
        html_for_mail_history_summary = ''
        unregistered_user_welcome_text = ''
        registered_user_bool = False
        have_sent_messages_object = None
        account_has_been_removed_message = ''
        why_to_register = ''
        link_to_hide = ''
        page_title = ''
    
        # owner userobject refers to the client that is currently logged in
        owner_userobject = utils_top_level.get_userobject_from_request(request)
        show_vip_info = False
        
        if owner_userobject:
            owner_uid = request.session['userobject_str']
            owner_nid = utils.get_nid_from_uid(owner_uid)
            registered_user_bool = True # viewing user is logged in
            link_to_hide = 'login'
            show_vip_info = utils.do_display_online_status(owner_uid)
            
        else:
            owner_userobject = None
            owner_uid = ''
            owner_nid = ''
            registered_user_bool = False
            # take away all permissions if this is a non-logged-in user
            is_primary_user = False
            
            # This is probably a guest that is just looking
            # at the site (hasn't logged in) -- just tell them to login
            unregistered_user_welcome_text = ugettext("You must register with %(app_name)s to contact other users") % {
                'app_name' : settings.APP_NAME}
    
            unregistered_user_welcome_text = "%s <em>%s</em><br><br>" % (unregistered_user_welcome_text, text_fields.cookies_not_enabled_text)
            # following text is replaced even in english
            why_to_register = ugettext("Remember the following benefits of registering with %(app_name)s.") % {'app_name': settings.APP_NAME}
            why_to_register += u"<br><br><ul>"
            why_to_register += ugettext("List of benefits for registering with %(app_name)s.") % {'app_name': settings.APP_NAME}
            why_to_register += u"</ul><br>"
            
            
        # is_primary_user means that the logged in client is viewing their own profile.
        if is_primary_user:
            # means that we are displaying the profile of the current user -- they have
            # privledges to edit, etc.
            if display_uid != owner_uid:
                # Re-direct to the display_uid profile view (without any permissions)-- the logged in user has 
                # attempted to enter into another users private area (probably by manually
                # modifying the URL). 
                display_userobject = utils_top_level.get_object_from_string(display_uid)
                redirect_url = profile_utils.get_userprofile_href(lang_code, display_userobject)                
                return http_utils.redirect_to_url(request, redirect_url)
                      
            else:
                # Show the new user the welcome text, only for as long as the user has not yet 
                # done a search for other clients (we use this as an indicator that they understand
                # how the system works, and so do not need the welcome message any longer)
                
                display_userobject = owner_userobject
        
                search_preferences_object = owner_userobject.search_preferences2.get()
                if not search_preferences_object.user_has_done_a_search:
                    new_user_welcome_text = u"%s<br><br>" % text_fields.welcome_text
                if not owner_userobject.email_address_is_valid:
                    email_is_not_entered_text = u"%s<br><br>" % text_fields.email_is_not_entered_text
                                 
                # Note: we use the has_about_user boolean instead of just checking against the default value of "----"
                # because this allows us to continue to show the warning message until they have entered the minimum
                # number of characters in their description.
                if not owner_userobject.has_about_user:
                    # this value is over-written for all languages (including english) to give more descriptive text.
                    no_about_user_section_warning = ugettext("""It is recommendable that you write a description of at 
        least %(num_chars)s characters""") % {'num_chars' : (constants.ABOUT_USER_MIN_DESCRIPTION_LEN)}
                    no_about_user_section_warning += u"<br><br>"
                
                unique_last_login_offset_object = owner_userobject.unique_last_login_offset_ref.get()
                if not (unique_last_login_offset_object.has_public_photo_offset or \
                        unique_last_login_offset_object.has_private_photo_offset):
                    user_has_no_photo_text = u"%s<br><br>" % text_fields.user_has_no_photo_text
                else:
                    user_has_no_photo_text = ''
                    
        else:
            # get the "display" user object based on the uid key passed in -- the current client is viewing
            # someone else's profile
            try:
                display_userobject = utils_top_level.get_object_from_string(display_uid)
                assert(display_userobject)
                
                # if the description portion of the URL does not match what we expect for the current profile, then
                # re-direct to a URL with the correct description.
                # This is done for cases where the user has changed some aspect of their profile description 
                # (country, sex, etc.), so that the URL will be re-directed to reflect the new values.
                if profile_url_description:
                    quoted_profile_url_description = urllib.quote(profile_url_description.encode('utf8'))
                else:
                    quoted_profile_url_description = None
                    
                    
                expected_profile_url_description = profile_utils.get_profile_url_description(lang_code, display_uid)                    
                if quoted_profile_url_description != expected_profile_url_description:
                    redirect_url = profile_utils.get_userprofile_href(lang_code, display_userobject)
                    logging.info("redirecting from %s to %s\n" % (quoted_profile_url_description, expected_profile_url_description))
                    return http.HttpResponsePermanentRedirect(redirect_url)
                    

            except:
                error_message = "Unable to get userobject for display_uid %s" % display_uid
                error_reporting.log_exception(logging.error, error_message = error_message)
                # re raise the error since we cannot continue processing
                raise Exception(error_message)
          

            if owner_userobject:
                # Get the summary of the message history between these two users.
                (html_for_mail_history_summary, have_sent_messages_object) =\
                 mailbox.get_mail_history_summary(request, owner_userobject, display_userobject)
                
                # track the fact that the logged in user is vieweing another persons profile
                # track_viewers.store_viewer_in_displayed_profile_viewer_tracker(owner_uid, display_uid)
        
        (page_title, meta_description) = FormUtils.generate_title_and_meta_description_for_current_profile(lang_code, display_uid)
      
        html_for_main = MyHTMLCallbackGenerator(request, display_userobject, is_primary_user, owner_userobject, have_sent_messages_object)
               
        
        search_bar = MyHTMLSearchBarGenerator(lang_idx)
        
        if owner_userobject:
            # this is the logged-in client
            owner_username = owner_userobject.username
            unread_mail_count_object = owner_userobject.unread_mail_count_ref.get()
            owner_message_count = unread_mail_count_object.unread_contact_count
            new_contact_counter_object = owner_userobject.new_contact_counter_ref.get()
            new_contact_count = get_new_contact_count_sum(new_contact_counter_object)
        else:
            # this is a guest that is not logged-in
            owner_username = ''
            owner_message_count = new_contact_count = 0
            
        if display_userobject.user_is_marked_for_elimination:
            account_has_been_removed_message =  utils.get_removed_user_reason_html(display_userobject)
            
        display_username = display_userobject.username
                  
        last_entrance = return_time_difference_in_friendly_format(display_userobject.previous_last_login)
        current_entrance = return_time_difference_in_friendly_format(display_userobject.last_login)
        debugging_html = debugging.get_html_for_unique_last_login_calculations(display_userobject)
        
                
        # Display the welcome section
        if new_user_welcome_text or user_has_no_photo_text or no_about_user_section_warning or\
           email_is_not_entered_text:
            display_welcome_section = True
        else:
            display_welcome_section = False
            
        (vip_status) = utils.get_vip_status(display_userobject)
        
        # The following data fields are shown to the logged in user when they are viewing their own profile -- mostly
        # suggestions on what they need to do to make their profile complete.
        primary_user_profile_data_fields = constants.PassDataToTemplate()
        primary_user_profile_data_fields.is_primary_user = is_primary_user
        
        if is_primary_user:
            primary_user_profile_data_fields.display_welcome_section = display_welcome_section
            primary_user_profile_data_fields.email_is_not_entered_text = email_is_not_entered_text
            primary_user_profile_data_fields.new_user_welcome_text = new_user_welcome_text
            primary_user_profile_data_fields.user_has_no_photo_text = user_has_no_photo_text
            primary_user_profile_data_fields.no_about_user_section_warning = no_about_user_section_warning
            primary_user_profile_data_fields.max_checkbox_values_in_combined_ix_list = constants.MAX_CHECKBOX_VALUES_IN_COMBINED_IX_LIST
            primary_user_profile_data_fields.owner_uid = owner_uid
            primary_user_profile_data_fields.owner_nid = owner_nid
            primary_user_profile_data_fields.is_adult = constants.IS_ADULT
            
            
            
            if vip_status:
                # Let the user know when their VIP status will expire
                datetime_to_display = display_userobject.client_paid_status_expiry
                primary_user_profile_data_fields.vip_status_expiry_friendly_text = \
                    utils.return_time_difference_in_friendly_format(datetime_to_display, capitalize = False, data_precision = 3, time_is_in_past = False)
            else:
                primary_user_profile_data_fields.vip_status_expiry_friendly_text = None            

                                
        # The following data fields are shown in the profile being viewed (including if it is the profile of the logged in user)
        viewed_profile_data_fields = constants.PassDataToTemplate()
    
        viewed_profile_data_fields.last_entrance = last_entrance    
        viewed_profile_data_fields.display_username = display_username
        viewed_profile_data_fields.display_uid = display_uid
        viewed_profile_data_fields.display_nid = display_nid
        viewed_profile_data_fields.profile_url_description = profile_utils.get_profile_url_description(lang_code, display_uid)
        viewed_profile_data_fields.current_entrance = current_entrance
        viewed_profile_data_fields.html_for_mail_history_summary = html_for_mail_history_summary
        viewed_profile_data_fields.account_has_been_removed_message = account_has_been_removed_message
        viewed_profile_data_fields.debugging_html = debugging_html
        viewed_profile_data_fields.profile_information_for_admin = utils.generate_profile_information_for_administrator(owner_userobject, display_userobject)

        
        
        # Note, the following "or" ensures that if the user is viewing their own profile, they will always see the 
        # photo boxes -- allows us to hide the photo section if no photos are present
        unique_last_login_offset = display_userobject.unique_last_login_offset_ref.get()
        viewed_profile_data_fields.show_photos_section = is_primary_user or unique_last_login_offset.has_public_photo_offset \
                                  or unique_last_login_offset.has_private_photo_offset
        
        if show_vip_info:
            viewed_profile_data_fields.show_online_status = utils.get_vip_online_status_string(display_uid)
        
        
        template = loader.get_template("user_main_helpers/main_body.html")
        context = Context(dict({
            'primary_user_profile_data_fields': primary_user_profile_data_fields,
            'viewed_profile_data_fields': viewed_profile_data_fields,
            'search_bar': search_bar,
            'html_for_main': html_for_main,
            'unregistered_user_welcome_text': unregistered_user_welcome_text  ,
            'registered_user_bool': registered_user_bool,
            'build_name': settings.BUILD_NAME,
            }, **constants.template_common_fields))
    
        generated_html = template.render(context)
        
        return rendering.render_main_html(request, generated_html, owner_userobject, link_to_hide=link_to_hide, 
                                          page_title = page_title, show_social_buttons = not is_primary_user, 
                                          page_meta_description = meta_description)
    
    except:
        error_reporting.log_exception(logging.critical)        
        return http_utils.redirect_to_url(request, "/%s/" % request.LANGUAGE_CODE)

        

#############################################
# to prevent possible problems with multiple sessions being active at once, make sure that the 
# user is logged out before letting them log in. Also, this should make it more difficult for
# jealous spouse to accidently discover that their partner has been logged in, since previous session
# will be automatically logged out if the user goes to the home page.


def login(request, is_admin_login = False, referring_code = None):
    # displays the information for allowing the user to log in. Also, processes the post information
    # from login attempts.
    # 
    # if referring_code is passed in, this means that this user has been referred by a friend. We therefore write
    # a cookie to their computer (with the refferers ID) so that we can detect if they register at some point in the future. 
    # This is then used for crediting the referrings account. 
    
    try:
                
        error_list = [] # used for containing error messages to be presented to user in a friendly format
        login_type = '' # default value required for first pass, since no request has yet taken place
        login_dict = None
        html_for_posted_values = ''
        
        # hashed_password is used for storing a hashed version of the password that was previously entered,
        # so that if the login page is called back with previously entered data, we can check if the password
        # has already been encrypted, or if it is still cleartext.
        hashed_password = ''
        
        lang_idx = localizations.input_field_lang_idx[request.LANGUAGE_CODE]
                            
                
        # Note that this function can be called from a POST or a GET (URL-passing in login parameters), 
        # or on initial loading without POST information.
        # If it is called without POST information, then the default login page is simply displayed. Otherwise
        # the POST data is analyzed to see if the login/signup is successful.
        # GET is used for sending an incorrect login back to the original login page along with parameters
        # that have previously been entered (such as a username)
        # 
        if request.method == 'POST' or request.method == 'GET':
               
            login_type = request.REQUEST.get('login_type', '') # use REQUEST, because this applies to either GET or POST
            login_dict = get_login_dict_from_post(request, login_type)
            
            country_encoded = None
            region_encoded = None
            
            http_country_code = request.META.get('HTTP_X_APPENGINE_COUNTRY', None)
            if http_country_code:
                # check if country is valid and is allowed to register profiles on our website
                if http_country_code in localizations.forbidden_countries:
    
                    # user will not be allowed to register or login from un-supported countries.
                    forbidden_country_name = localizations.forbidden_countries[http_country_code] 
                    message_for_client = u"We do not currently allow users from %s" % forbidden_country_name
                    error_list.append(message_for_client)
                    logging.warning(message_for_client)
                else:
                    tmp_country_encoded = "%s,," % http_country_code
                    if tmp_country_encoded in localizations.location_dict[0]:
                        # make sure that it is a country that we support.
                        country_encoded = tmp_country_encoded
                    else:
                        logging.warning("Logging in user in unknown country: %s" % http_country_code)  
                        
                http_region_code = request.META.get('HTTP_X_APPENGINE_REGION', None)
                if country_encoded and http_region_code:
                    http_region_code = http_region_code.upper()
                    
                    # check if the region code matches a region key 
                    tmp_region_encoded = "%s,%s," % (http_country_code, http_region_code)
                    if tmp_region_encoded in localizations.location_dict[0]:
                        region_encoded = tmp_region_encoded
                    else:
                        logging.warning("Region code %s not found in location_dict" % http_region_code)
                
            
            # the following code returns posted values inside the generated HTML, so that we can use Jquery to 
            # search for these values, and replace them in the appropriate fields that were previously entered.
            # Note: the "id-hidden_" prefix -- this is necessary to avoid confusion with the real fields that have the
            # same name.
            if login_dict:
                html_for_posted_values = login_utils.html_for_posted_values(login_dict)  
            else:
                # we are displaying a "fresh" home-page, without any information submitted from the user.            
                # write country as a hidden input fields so that the Javascript can discover it, and set the dropdown appropriately
                if country_encoded:
                    
                    html_for_posted_values = '<input type="hidden" id= "%s" name="%s" value="%s" />\n' % (
                                "id-hidden_country", "hidden_country", country_encoded)   
                    
                    if region_encoded:
                        html_for_posted_values += '<input type="hidden" id= "%s" name="%s" value="%s" />\n' % (
                                    "id-hidden_region", "hidden_region", region_encoded)                           
            
                    if settings.BUILD_NAME == "Friend":
                        # we need to set the appropriate currency for the current country
                        friend_currency = friend_bazaar_specific_code.country_to_currency_map[country_encoded]
                        html_for_posted_values += '<input type="hidden" id= "%s" name="%s" value="%s" />\n' % (
                                "id-hidden_friend_currency", "friend_currency", friend_currency) 
                
            ##### existing user is logging in ##################################
            if (login_type == 'left_side_fields'):
                
                #clear_old_session(request)
                username = ''
                
                # remove spaces in the username/email field
                login_dict['username_email'] = login_dict['username_email'].replace(' ', '')
                
                # this is a callback from the routines that store the user profile when an email authorization link is clicked on.
                user_already_registered = request.REQUEST.get('already_registered', '') 
                if (user_already_registered):
                    username = login_dict['username_email'] 
                    message_for_client = u"""Ya la cuenta de %s esta registrada. 
                    Puedes entrar directamente con tu "Nick" y contraseña en las casillas arriba. """ % (
                        username)       
                    error_list.append(message_for_client)   
                    
                else:
                    
                    query_filter_dict = {}
                    
                    # if the password has been reset, then the 'password_reset' value will contain
                    # the new password (as opposed to directly overwriting the 'password' field). This is done  to prevent
                    # random people from resetting other peoples passwords. -- Once the user has 
                    # logged in using the new 'reset_password', then we copy this field over to the 'password'
                    # field. If the user never logs in with this 'reset_password', then the original password
                    # is not over-written -- and we instead erase the 'reset_password' value
                    query_filter_dict_for_new_password = {}
                    
                    # Verify that the password only contains acceptable characters  - 
                    # this is necessary for the password hashing algorithm which only works with ascii chars, 
                    # and make sure that it is not empty.
                    if not login_dict['password'] or rematch_non_alpha.search(login_dict['password']) != None :
                        error_list.append(ErrorMessages.password_alphabetic)
                    else:
                        if not is_admin_login:
                            
                            # make sure that the password is not empty -- should never even get into here
                            # if it is not set (earlier error checking should catch this). 
                            assert(login_dict['password'])
                                   
                            # we do not check the password if this is an admin login - since 
                            # admin logins are already verified using google account login.
                            # All "normal" logins MUST check the password!!
                            query_filter_dict['password'] = passhash(login_dict['password'])
                            
                            # make sure that profile has not been marked for elimination (if we are an administrator, we can
                            # still log into deleted accounts, so we don't add this value into the search query)
                            query_filter_dict['user_is_marked_for_elimination'] = False
        
                    if email_re.match(login_dict['username_email']):                       
                        query_filter_dict['email_address'] = login_dict['username_email'].lower()
                    else:
                        username = login_dict['username_email'].upper()
                        query_filter_dict['username'] = username
                        if (rematch_non_alpha.search(username) != None or len(username) < 3):
                            error_list.append(ErrorMessages.username_alphabetic)
                        
                    # make sure that we are accessing a "real" userobject (not a backup)    
                    query_filter_dict['is_real_user'] = True
                    
                    # the following order is not really necessary -- but just ensures that the most recently
                    # accessed object will be returned in case of a conflict (which might occur if a person uses the same email
                    # address for multiple accounts)
                    query_order_string = "-%s" % 'last_login_string'
    
                if not error_list:
                    
                    password_has_been_reset = False
                    query = UserModel.all().order(query_order_string)
                    for (query_filter_key, query_filter_value) in query_filter_dict.iteritems():
                        query = query.filter(query_filter_key, query_filter_value)
                    userobject = query.get()
    
                    if not userobject and not is_admin_login:
                        # if the original query failed, do a query using the 'password_reset' value --
                        # this will contain a new password, if the user has requested a new password be 
                        # sent to their email account.
                        # set up the query to check the 'password_reset' value
                        del(query_filter_dict['password'])
                        query_filter_dict['password_reset'] = passhash(login_dict['password'])                    
    
                        query = UserModel.all().order(query_order_string)
                        for (query_filter_key, query_filter_value) in query_filter_dict.iteritems():
                            query = query.filter(query_filter_key, query_filter_value)
                        userobject = query.get()    
                        if userobject:
                            password_has_been_reset = True
    
                        # Note, that the above code has deleted the password from the query, and instead used the password_reset value.
                        # restore the query values to contain the original password. 
                        del(query_filter_dict['password_reset'])
                        query_filter_dict['password'] = passhash(login_dict['password'])
                    
                    
                    if not userobject and not is_admin_login:
                        # The user was unable to login -- 
                        # check to see if the username/email+password was registered at some point, and has been eliminated
    
                        query_filter_dict['user_is_marked_for_elimination'] = True
                        
                        query = UserModel.all().order(query_order_string)
                        for (query_filter_key, query_filter_value) in query_filter_dict.iteritems():
                            query = query.filter(query_filter_key, query_filter_value)
                        eliminated_userobject = query.get()
                        
                        # if no eliminated object was found, try again, but this time only if the user has entered a username (not an email)
                        # and we will remove the password from the query. This will allow better reporting for people who may have forgotten
                        # their password. (we do not query without password for an email address login to prevent people from probing our system
                        # to see if an email address was registered)
                        if not eliminated_userobject:
                            
                            if 'username' in query_filter_dict and query_filter_dict['username']:
                                # we know that a username as opposed to an email address was entered
                                del(query_filter_dict['password'])
                                query = UserModel.all().order(query_order_string)
                                for (query_filter_key, query_filter_value) in query_filter_dict.iteritems():
                                    query = query.filter(query_filter_key, query_filter_value)
                                eliminated_userobject = query.get()                            
                                        
                                # re-insert the password into the query parameters for future queries.
                                query_filter_dict['password'] = passhash(login_dict['password'])
                        
                        if eliminated_userobject:
                            # Let user know that the profile was eliminated. 
                            message_for_client = u"""El perfil de %s ha sido eliminado. """ % (eliminated_userobject.username)       
                            error_list.append(message_for_client)
                            
                        else: # the profile (email + password OR username) did not appear in the list of eliminated userobjects
                            
                            # check to see if the username or email is registered but we can only find backup copies (as opposed to the real object)
                            # This would be a *very serious* error condition that should be addressed immediately - this error check is here
                            # because this condition has occured in the past for unknown reasons.
                             
                            # We are just making sure that if the username/email
                            # is registered (meaning that we can find a profile that matches the username/email), 
                            # and that at least one of the userobjects has "is_real_user" set to true.
                            #
                            # must include both eliminated and current profiles to prevent false error reporting, which could otherwise
                            # occur if a user eliminated a profile, but enters in the wrong password
                            
                            del(query_filter_dict['user_is_marked_for_elimination']) 
                            del(query_filter_dict['password'])
                            
                            # search for a backup userobject
                            query_filter_dict['is_real_user'] = False
                            query = UserModel.all().order(query_order_string)
                            for (query_filter_key, query_filter_value) in query_filter_dict.iteritems():
                                query = query.filter(query_filter_key, query_filter_value)
                            backup_userobject = query.get()
                            
                            # now search for a real userobject
                            query_filter_dict['is_real_user'] = True
                            query = UserModel.all().order(query_order_string)
                            for (query_filter_key, query_filter_value) in query_filter_dict.iteritems():
                                query = query.filter(query_filter_key, query_filter_value)
                            real_userobject = query.get()                        
                            
                            # if backup exists, and there is no "real" userobject, report an error.
                            if backup_userobject and not real_userobject:
                                error_message  = u"""The profile of %s (entered with username_email=%s) has appeared as backup objects, 
                                but primary object is not found (this condition can also occur if the user has erased their email address, but it remains
                                in the backup objects and then they try to enter using their email address). 
                                """ % (backup_userobject.username, login_dict['username_email']) 
                                email_utils.send_admin_alert_email(error_message, "%s Login Error" % settings.APP_NAME)
                                error_reporting.log_exception(logging.critical, error_message=error_message)                   
                        
                    if userobject:
                        # success, user is in database and has entered correct data
                        owner_uid = userobject.key.urlsafe()
                        owner_nid = utils.get_nid_from_uid(owner_uid)
                        
                        # make sure that the userobject has all the parts that the code expects it to have.
                        store_data.check_and_fix_userobject(userobject, request.LANGUAGE_CODE)
    
                        # if administrator is logging in, do not update anything. 
                        if not is_admin_login:
                            
                            if password_has_been_reset:
                                # The user has logged in using the new password - so eliminate the 
                                # original password.
                                userobject.password = userobject.password_reset
                                userobject.password_reset = None
                            else: # entering with the original password
                                
                                # if the user has entered with the original password, then remove the reset_password
                                # so that they don't have two valid passwords floating around
                                if userobject.password_reset != None:
                                    userobject.password_reset = None
                                
    
                            userobject.previous_last_login = userobject.last_login
                            userobject.last_login =  datetime.datetime.now()   
                            userobject.last_login_string = str(userobject.last_login)
                                                    
                            if not utils.get_vip_status(userobject):
                                # client has lost their VIP status - clear from both the userobject and and the 
                                # unique_last_login_offset structures.
                                userobject.client_paid_status = None
                                userobject.client_is_exempt_from_spam_captchas = False
                                
                                # this user up until now has not had to solve any captchas since he was a VIP member - therefore, it is possible
                                # that his spam_tracker has accumulated a number of times being reported as spammer. We don't want to punish people
                                # after they lose their vip status, and so we set the number of captchas solved to be equal to the number of times
                                # reported as a spammer (this means that any previous spam messages will not require that a new captcha be solved). 
                                userobject.spam_tracker.number_of_captchass_solved_total = userobject.spam_tracker.num_times_reported_as_spammer_total
                                userobject.spam_tracker.put()
                                
                                
                                
                            (userobject.unique_last_login, userobject.unique_last_login_offset_ref) = \
                             get_or_create_unique_last_login(userobject, userobject.username)
                            
                            # remove chat boxes from previous sessions.
                            channel_support.close_all_chatboxes_internal(owner_uid)
    
                            login_utils.set_new_contact_counter_on_login(userobject.new_contact_counter_ref)
                         
                            # reset the new_messages_since_last_notification data strutures since the user 
                            # is logging in, and is obviously aware of new messages etc. 
                            store_data.reset_new_contact_or_mail_counter_notification_settings(userobject.unread_mail_count_ref.key())
                            store_data.reset_new_contact_or_mail_counter_notification_settings(userobject.new_contact_counter_ref.key()) 
                            
                            # log information about this users login time, and IP address
                            utils.update_ip_address_on_user_tracker(userobject.user_tracker)
                            
                            utils.store_login_ip_information(request, userobject)
    
                            utils.put_userobject(userobject)
    
                        # update session to point to the current userobject
                        store_session(request, userobject)
                    
    
                        logging.info("Logging in User: %s IP: %s country code: %s -re-directing to edit_profile_url" % (userobject.username, os.environ['REMOTE_ADDR'], http_country_code))
    
                        # Set language to whatever the user used the last time they were logged in. 
                        lang_code = userobject.search_preferences2.lang_code
                        assert(lang_settings.set_language_in_session(request, lang_code))
                        # Note: we "manually" set the language in the URL on purpose, because we need to guarantee that the language
                        # stored in the profile, session and URL are consistent (so that the user can change it if it is not correct)
                        redirect_url = "/%(lang_code)s/edit_profile/%(owner_nid)s/" % {
                                'lang_code': lang_code, 'owner_nid':owner_nid}                        
                        return http_utils.redirect_to_url(request, redirect_url)                        

                    else:
                        error_list.append(ErrorMessages.incorrect_username_password)
                
            ##### new user is signing up ########################################
            elif (login_type == 'signup_fields'):
                            
                login_dict['country'] = request.REQUEST.get('country', '----')
                login_dict['sub_region'] = request.REQUEST.get('sub_region', '----')
                login_dict['region'] = request.REQUEST.get('region', '----')
                
                # re-write all user names to upper-case to prevent confusion
                # and amateur users from not being able to log in.
                login_dict['username'] = login_dict['username'].upper()
                            
                # if email address is given, make sure that it is valid
                if login_dict['email_address'] and login_dict['email_address'] != "----":
                    # remove blank spaces from the email address -- to make it more likely to be acceptable
                    login_dict['email_address'] = login_dict['email_address'].replace(' ', '')
                    login_dict['email_address'] = login_dict['email_address'].lower()
                
                error_list += login_utils.error_check_signup_parameters(login_dict, lang_idx)
                
                # Now check if username is already taken
                query = UserModel.query().filter(UserModel.username == login_dict['username'])
                query_result = query.fetch(limit=1)
                if len(query_result) > 0:
                    error_list.append(ErrorMessages.username_taken)
                else:
                    # now check if the username is in the process of being registered (in EmailAuthorization model)
                    query = models.EmailAutorizationModel.query().filter(models.EmailAutorizationModel.username == login_dict['username'])
                    query_result = query.fetch(limit=1)
                    if len(query_result) > 0:
                        error_list.append(ErrorMessages.username_taken)   
                        
                # if there are no errors, then store the signup information.
                if not error_list:
    
                    # we keep a copy of the hashed password so that if we are re-directed back to the login page
                    # with a hashed password (as opposed to cleartext), we can check to see if the password matches
                    # the previously hashed password. If there is a match, then DO NOT hash it again -- just leave it
                    # as it is, because we know that it is already hashed.  
                    login_dict['password_hashed'] = request.REQUEST.get('password_hashed', '')
                    
                    if login_dict['password'] != login_dict['password_hashed']:
                        # encrypt the password -- but only if it is a new password or if the password
                        # has been changed by the user if it does not match the password stored in password_hashed
                        password_hashed = passhash(login_dict['password'])
                        login_dict['password'] = password_hashed
                        login_dict['password_hashed'] = password_hashed
                    else:
                        # it is already hashed -- don't has it again.
                        login_dict['password_hashed'] = login_dict['password']
                    
                    # we should totally remove 'password_verify' from the UserModel eventually -- but for 
                    # now just set it to the password (since we have just replaced the password with the hash).
                    login_dict['password_verify'] = login_dict['password']
                                   
                    response =  login_utils.verify_user_login(request, login_dict)
                    return response
            
            else:
                assert(login_type == '') 
                
    
                
            # the following information is used for telling the user that the emailed link that they have clicked on was unable to be
            # authorized. 
            # unable_to_verify_user GET value contains the username that we were unable to find in the authorization info data struct.
            unable_to_verify_username = request.REQUEST.get('unable_to_verify_user', '') 
            if (unable_to_verify_username):
                message_for_client = u"""
                No podemos verifificar/autorizar la cuenta para %s. 
                Este puede pasar si ya has verificado esta cuenta una vez.
                Si la cuenta %s es tuya, puedes entrar directamente con tu "Nick" y contraseña en las casillas arriba. """ % (
                    unable_to_verify_username, unable_to_verify_username)               
                error_list.append(message_for_client)
                
        # The following two calls generate the table rows required for displaying the login
        # note that this is a reference to the class, *not* to an instance (object) of the class. This is because
        # we do not want to re-generate a new object for each unique login (this would make caching
        # difficult).
        html_for_signup = MyHTMLLoginGenerator.as_table_rows(localizations.input_field_lang_idx[request.LANGUAGE_CODE], 'signup_fields')
        
        # This code is used for generating maintenance warning messages. 
        (maintenance_soon_warning, maintenance_shutdown_warning) = admin.generate_code_for_maintenance_warning()
            
        # login_type is passed in to ensure that error-messages occur in the correct part of the
        # display.    
        if error_list:
            error_reporting.log_exception(logging.info, error_message=repr(error_list))
            
        meta_info = constants.PassDataToTemplate()
        if settings.SEO_OVERRIDES_ENABLED:
            meta_info.page_title = search_engine_overrides.get_main_page_title()
        else:
            meta_info.page_title = ''
            
        meta_info.content_description =  meta_info.page_title
        meta_info.keywords_description =  meta_info.page_title
        
        template = loader.get_template('login.html')
        context = Context (dict({   
            'LANGUAGES' : settings.LANGUAGES,                
            'html_for_signup': html_for_signup,
            'login_type' : login_type, 
            'html_for_previously_posted_values' : html_for_posted_values,
            'is_admin_login': is_admin_login,
            'maintenance_soon_warning': maintenance_soon_warning,
            'maintenance_shutdown_warning': maintenance_shutdown_warning,
            'link_to_hide': 'login',
            'errors': error_list,
            'minimum_registration_age' : constants.minimum_registration_age,
            'request' : request,
            'javascript_version_id': settings.JAVASCRIPT_VERSION_ID,
            'welcome_html': welcome_html(),
            }, **constants.template_common_fields))
        body_main_html = template.render(context)
        
        if request.REQUEST.get("is_ajax_call", ''):
            # We check if it is an ajax request to see the entire page should be loaded, or just the body.
            http_response = http_utils.ajax_compatible_http_response(request, body_main_html)
            
        else:               
            http_response = render_to_response("common_wrapper.html", dict({   
                'meta_info': meta_info,
                'wrapper_data_fields' : common_data_structs.wrapper_data_fields,
                'body_main_html' : body_main_html,
            }, **constants.template_common_fields))
        
        if referring_code:
            # write the code into a cookie on the users computer, so that if/when they register we can credit the referring profile
            logging.info("Writing referring_code %s to cookie" % referring_code)
            num_days = 30
            max_age = num_days*24*60*60  
            expires = datetime.datetime.strftime(datetime.datetime.utcnow() + datetime.timedelta(seconds=max_age), "%a, %d-%b-%Y %H:%M:%S GMT")
            http_response.set_cookie(constants.REFERRING_COOKIE_CODE , value=referring_code, max_age=max_age, expires=expires, path='/', domain=None, secure=None)
                
    
        return http_response
    
    except: 
        return utils.return_and_report_internal_error(request)


        
#############################################

def welcome_html():
    
    template = loader.select_template(["proprietary_html_content/welcome_message.html", "common_helpers/default_welcome_message.html"])
    context = Context(constants.template_common_fields)
    generated_html = template.render(context)    
    return generated_html

def welcome(request):
    # Displays the welcome information about the website (shoud probably change the name to 
    # "information" instead of  welcome ... 

    try:
        # owner userobject refers to the client that is currently logged in
        userobject = utils_top_level.get_userobject_from_request(request)  
        generated_html = welcome_html()
        return rendering.render_main_html(request, generated_html, userobject,
                                          show_social_buttons = True, hide_why_to_register = True)
    except:
        error_reporting.log_exception(logging.critical)


def terms(request):
    # Displays the legal stuff 
    # owner userobject refers to the client that is currently logged in
    
    try:
        userobject = utils_top_level.get_userobject_from_request(request)  
        
        # notice that we have placed the path to the terms file inside a ugettext call, which means that 
        # depending on the current language, different terms and conditions file will be called. 
        # Eg. in the case of the current language being spanish, 'terminos.html' would be called instead.
        # If you have not specified a terms and conditions file, then the "default_terms.html" file will be loaded,
        # which should be overwritten before you go live with your website.
        template = loader.select_template(['proprietary_html_content/' + ugettext("terms.html"), "common_helpers/default_terms.html"])
        context = Context(dict({ 'minimum_registration_age': constants.minimum_registration_age}, **constants.template_common_fields))
        generated_html = template.render(context)
        return rendering.render_main_html(request, generated_html, userobject, hide_why_to_register = True)

    except:
        error_reporting.log_exception(logging.critical)
      

def logout(request, html_for_delete_account = ''):
    # Closes the user session, and displays the logout page.
       
    try: 
        try:
            owner_uid =  request.session['userobject_str']
            userobject = utils_top_level.get_userobject_from_request(request)  
            # mark the user presence as OFFLINE (if another session is logged into a different browser, this will be
            # over-written to reflect the status in the other session as soon as that session pings the server with its status)
            online_presence_support.update_online_status(owner_uid, constants.OnlinePresence.OFFLINE)            

        except:
            userobject = None
        
        template = loader.select_template(["proprietary_html_content/goodbye_message.html", "common_helpers/default_goodbye_message.html"])
        context = Context(constants.template_common_fields)
        generated_html = template.render(context)
        nav_bar_text = ugettext("You have exited")
        response = rendering.render_main_html(request, generated_html, userobject,
                                              text_override_for_navigation_bar = nav_bar_text, 
                                              show_login_link_override = True,
                                              do_not_try_to_dynamically_load_search_values = True,
                                              remove_chatboxes = True)
        
        login_utils.clear_old_session(request)
        

        
        response.delete_cookie(settings.SESSION_COOKIE_NAME)
        return response
    except:
        error_reporting.log_exception(logging.critical)
        

def press(request):
    
    try:
        # owner userobject refers to the client that is currently logged in
        userobject = utils_top_level.get_userobject_from_request(request)  
        
        template = loader.select_template(["proprietary_html_content/%s_press.html" % settings.APP_NAME, "common_helpers/default_press.html"] )
        context = Context(constants.template_common_fields)
        generated_html = template.render(context)
        return rendering.render_main_html(request, generated_html, userobject,
                                          show_social_buttons = True)
    except:
        error_reporting.log_exception(logging.critical)
              
      
def crawler_login(request):
    
    try:
        error_reporting.log_exception(logging.info, "logging in crawler")
        return render_to_response("crawler_login.html")
    except:
        error_reporting.log_exception(logging.critical)
          

def crawler_auth(request):
    
    
    try:
        error_reporting.log_exception(logging.info, error_message = 'META Header = %s' % request.META) 
        
        username = request.POST.get('username', '') 
        password = request.POST.get('password', '') 
        
        if username == constants.CRAWLER_USERNAME and password == constants.CRAWLER_PASSWORD:
            status = login_utils.store_crawler_session(request)
        else:
            status = "Invalid username: '%s' password: '%s'" % (username, password)
    
        error_reporting.log_exception(logging.warning, error_message = "Crawler authorization status %s" % status)
        return HttpResponse(status)
    except:
        error_reporting.log_exception(logging.critical)
          


def robots_txt(request):
    
    # generates the robots.txt file, including links to the sitemap_index files.
    
    number_of_sitemaps = sitemaps.get_highest_sitemap_index_number()
    sitemaps_links = ''
    if number_of_sitemaps:
        for idx in range(0, number_of_sitemaps):
            sitemap_number = idx + 1
            sitemaps_links += 'sitemap: http://www.%(domain_name)s/sitemap_index-%(sitemap_number)s.xml\n' % {
                'domain_name' : settings.DOMAIN_NAME,
                'sitemap_number' : sitemap_number,}
    
    logging.info("sitemaps_links %s" % sitemaps_links)    
    http_response = render_to_response("robots.txt", {'sitemaps_links' : sitemaps_links})
    return http_response
