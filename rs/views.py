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


import urllib
from google.appengine.ext.db import BadRequestError

from django.shortcuts import render_to_response


from forms import *
from login_utils import *
from utils import return_time_difference_in_friendly_format
import search_results
import mailbox, login_utils
import utils_top_level, sitemaps
import error_reporting, text_fields
from rs import profile_utils, track_viewers
from rs import vip_render_payment_options
from rs import store_data
from django import http

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
            error_reporting.log_exception(logging.warning, error_message="Bad display_uid passed into views.user_main")
            return http.HttpResponsePermanentRedirect("/%s/" % request.LANGUAGE_CODE)

    except Exception as e:

        # due to a strange bug in NDB, we cannot directly catch the ProtocolBufferDecodeError exception, and
        # instead have to check the name of the exception. This exception is caused by a key that cannot
        # be correctly decoded.
        if e.__class__.__name__ == 'ProtocolBufferDecodeError':
            error_message = "display_uid is invalid, and cannot be used to get a userobject"
            error_reporting.log_exception(logging.warning, error_message = error_message)

            # do a permanent redirect back to the main search results to prevent this URL from being accessed again
            return http.HttpResponsePermanentRedirect("/%s/" % request.LANGUAGE_CODE)
        else:
            error_reporting.log_exception(logging.critical)
            return http.HttpResponseRedirect("/%s/" % request.LANGUAGE_CODE)


def user_main(request, display_nid, is_primary_user = False, profile_url_description = None):
    # The users "main" page, after logging in. Will show their profile.
    # display_uid - is the object key of the profile currently displayed -- if the client is viewing other
    #       users, then the uid references the other users object. If the client is viewing their own
    #       profile , then uid is a referenct to their own user object.
    # is_primary_user - allows us to re-use large portions of this code to display user profiles
    #    that belong to other users in the system. This means that edit is enabled, and private
    #    is displayed.

    display_userobject = None
    lang_code = request.LANGUAGE_CODE
    
    try:
        display_uid = utils.get_uid_from_nid(display_nid)
        
        lang_idx = localizations.input_field_lang_idx[lang_code]
        
        # Do not remove these initializations unless you are 100% sure that the variable has been set in ALL branches.
        new_user_welcome_text = ""
        email_is_not_entered_text = ""
        user_has_no_photo_text = ''
        html_for_mail_history_summary = ''
        unregistered_user_welcome_text = ''
        have_sent_messages_object = None
        account_has_been_removed_message = ''
        link_to_hide = ''

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
            unregistered_user_welcome_text = ugettext("You must register to contact other users") 
    
            unregistered_user_welcome_text = "%s <em>%s</em><br><br>" % (unregistered_user_welcome_text, text_fields.cookies_not_enabled_text)

            
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
                return http.HttpResponseRedirect(redirect_url)
                      
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
                                 

                user_photo_tracker = owner_userobject.user_photos_tracker_key.get()

                if not (user_photo_tracker.public_photos_keys or user_photo_tracker.private_photos_keys):
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
                
                # make sure that user that we are looking at has not been eliminated before trying to
                # track a viewer (this check can e eliminated in a few months)
                if not display_userobject.user_is_marked_for_elimination:
                    # track the fact that the logged in user is vieweing another persons profile
                    track_viewers.store_viewer_in_owner_profile_viewer_tracker(owner_uid, display_uid)
        
        (page_title, meta_description) = FormUtils.generate_title_and_meta_description_for_current_profile(lang_code, display_uid)
      
        html_for_main = MyHTMLCallbackGenerator(request, display_userobject, is_primary_user, owner_userobject, have_sent_messages_object)
        
   
               
        search_bar = MyHTMLSearchBarGenerator(lang_idx)
           
        if display_userobject.user_is_marked_for_elimination:
            account_has_been_removed_message =  utils.get_removed_user_reason_html(display_userobject)
            
        display_username = display_userobject.username
                  
        last_entrance = return_time_difference_in_friendly_format(display_userobject.previous_last_login)
        current_entrance = return_time_difference_in_friendly_format(display_userobject.last_login)
        debugging_html = ''
        
                
        # Display the welcome section
        if new_user_welcome_text or user_has_no_photo_text or\
           email_is_not_entered_text:
            display_welcome_section = True
        else:
            display_welcome_section = False
            
        vip_status = utils.get_client_vip_status(display_userobject)
        
        # The following data fields are shown to the logged in user when they are viewing their own profile -- mostly
        # suggestions on what they need to do to make their profile complete.
        primary_user_profile_data_fields = {}
        primary_user_profile_data_fields['is_primary_user'] = is_primary_user
        
        if is_primary_user:
            primary_user_profile_data_fields['display_welcome_section'] = display_welcome_section
            primary_user_profile_data_fields['email_is_not_entered_text'] = email_is_not_entered_text
            primary_user_profile_data_fields['new_user_welcome_text'] = new_user_welcome_text
            primary_user_profile_data_fields['user_has_no_photo_text'] = user_has_no_photo_text
            primary_user_profile_data_fields['owner_uid'] = owner_uid
            primary_user_profile_data_fields['owner_nid'] = owner_nid
            
            
            
            if vip_status:
                # Let the user know when their VIP status will expire
                datetime_to_display = display_userobject.client_paid_status_expiry
                primary_user_profile_data_fields['vip_status_expiry_friendly_text'] = \
                    utils.return_time_difference_in_friendly_format(datetime_to_display, capitalize = False, data_precision = 3, time_is_in_past = False)
            else:
                primary_user_profile_data_fields['vip_status_expiry_friendly_text'] = None            

                                
        # The following data fields are shown in the profile being viewed (including if it is the profile of the logged in user)
        viewed_profile_data_fields = {}
    
        viewed_profile_data_fields['last_entrance'] = last_entrance    
        viewed_profile_data_fields['display_username'] = display_username
        viewed_profile_data_fields['display_uid'] = display_uid
        viewed_profile_data_fields['display_nid'] = display_nid
        viewed_profile_data_fields['profile_url_description'] = profile_utils.get_profile_url_description(lang_code, display_uid)
        viewed_profile_data_fields['current_entrance'] = current_entrance
        viewed_profile_data_fields['html_for_mail_history_summary'] = html_for_mail_history_summary
        viewed_profile_data_fields['account_has_been_removed_message'] = account_has_been_removed_message
        viewed_profile_data_fields['debugging_html'] = debugging_html
        viewed_profile_data_fields['profile_information_for_admin'] = utils.generate_profile_information_for_administrator(display_userobject, utils.user_is_admin(owner_userobject))
        
        
        if not display_userobject.user_is_marked_for_elimination:
            # Note, the following "or" ensures that if the user is viewing their own profile, they will always see the
            # photo boxes -- allows us to hide the photo section if no photos are present
            user_photo_tracker = display_userobject.user_photos_tracker_key.get()
            viewed_profile_data_fields['show_photos_section'] = is_primary_user or user_photo_tracker.public_photos_keys or\
                user_photo_tracker.private_photos_keys
        
        if show_vip_info:
            viewed_profile_data_fields['show_online_status'] = utils.get_vip_online_status_string(display_uid)
        
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
        # something went wrong, perhaps there is a problem with the userobject. Check it and fix if necessary:
        if display_userobject:
            has_been_fixed = store_data.check_and_fix_userobject(display_userobject, lang_code)
            # if userobject has been fixed, we try rendering it again
            if has_been_fixed:
                return user_main(request, display_nid, is_primary_user, profile_url_description)

        error_reporting.log_exception(logging.critical)
        return http.HttpResponseRedirect("/%s/" % request.LANGUAGE_CODE)

        

#############################################

def welcome_html():
    why_to_register = utils.get_why_to_register()
    template = loader.select_template(["proprietary_html_content/welcome_message.html", "common_helpers/default_welcome_message.html"])
    context = Context(dict({'why_to_register' : why_to_register}, **constants.template_common_fields))
    generated_html = template.render(context)    
    return generated_html

def vip_purchase_main_html(request, owner_nid):

    userobject = utils_top_level.get_userobject_from_nid(owner_nid)
    vip_payment_options = vip_render_payment_options.render_payment_options(request, userobject)

    return render_to_response('user_main_helpers/vip_purchase_main.html',
                              dict({'vip_payment_options':vip_payment_options}, **constants.template_common_fields))

def welcome(request):
    # Displays the welcome information about the website (should probably change the name to
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
        context = Context(dict({}, **constants.template_common_fields))
        generated_html = template.render(context)
        return rendering.render_main_html(request, generated_html, userobject, hide_why_to_register = True)

    except:
        error_reporting.log_exception(logging.critical)
      

def logout(request):
    # Closes the user session, and displays the logout page.
       
    try: 

        response = search_results.generate_search_results(request, type_of_search = "normal", this_is_a_logout = True, 
                            text_override_for_navigation_bar = ugettext("You have exited"),
                            register_enter_click_sends_to_landing = True,)
        
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
        return http.HttpResponse(status)
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


#     if settings.BUILD_NAME == "discrete_build" or settings.BUILD_NAME ==  "single_build" or settings.BUILD_NAME ==  "lesbian_build":
#         site_specific_allow_disallow = ''
#     else :
#         site_specific_allow_disallow = """
# Allow: /*/search/?query_order=last_login_string
# Allow: /*/search/?query_order=unique_last_login
# Disallow: /*/search/?*
#"""

    # Disallow searching through some permutations that we previously had specifically included links to

    if settings.BUILD_NAME == "discrete_build" or settings.BUILD_NAME ==  "single_build" or settings.BUILD_NAME ==  "lesbian_build":
         site_specific_allow_disallow = ''

    elif settings.BUILD_NAME == "language_build":
                site_specific_allow_disallow = """
Disallow: /*/search/?*sex=*
Disallow: /*/search/?*age=*
Disallow: /*/search/?*region=*
Disallow: /*/search/?*sub_region=*
"""

    else:
        site_specific_allow_disallow = """
Disallow: /*/search/?*age=*
Disallow: /*/search/?*relationship_status=*
"""

    http_response = render_to_response("robots.txt", {'sitemaps_links' : sitemaps_links,
        'site_specific_allow_disallow': site_specific_allow_disallow})

    return http_response
