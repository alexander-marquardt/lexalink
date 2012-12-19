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


from django.shortcuts import render_to_response
from django.utils.translation import ugettext
from django.template import loader
from django.template.context import Context
from django import http
from django.utils import simplejson

import random
import settings
import forms, admin, utils, error_reporting, logging
from models import UserModel
from forms import FormUtils
import constants, text_fields, time, chat_support, localizations, http_utils, common_data_structs
import online_presence_support
from rs.import_search_engine_overrides import *


if settings.BUILD_NAME == "Friend":
    import friend_bazaar_specific_code

def get_my_internal_advertisements():
    
    ad_list = []
    
    if constants.COMPANY_NAME == "Lexabit Inc.":
        
        # code to randomly select from a list of advertisements that are appropriate for the current website.
        pages_to_advertise = list(constants.pages_to_advertise) # make a copy of the original list
        num_pages_to_advertise = min(constants.MAX_NUM_PAGES_TO_ADVERTISE, len(pages_to_advertise))
        
        # Randomly select pages from the list
        
        while num_pages_to_advertise:
            idx = random.randint(0, len(pages_to_advertise) -1 )
            ad_list.append(pages_to_advertise.pop(idx))  
            num_pages_to_advertise -= 1
    
    return (ad_list)
        
def get_additional_ads_to_append(request, userobject = None):

    additional_ads_to_append = []
    
    try:
        if settings.BUILD_NAME == "Language" or settings.BUILD_NAME == "Friend":
            # we don't currently append any additional advertisements. 
            return additional_ads_to_append
        
        # the following two values should only be available if the user has submitted a search request - otherwise
        # they should not be defined (hopefully)
        search_preference = request.GET.get('preference', '')
        search_sex = request.GET.get('sex', '')
        search_relationship_status = request.GET.get('relationship_status', '')
        
        if userobject:
            search_preferences = userobject.search_preferences2
            if not search_preference:
                search_preference = search_preferences.preference
            if not search_sex:
                search_sex = search_preferences.sex
            if not search_relationship_status:
                search_relationship_status = search_preferences.relationship_status
                
            userobject_sex = userobject.sex
            userobject_preference = userobject.preference
            userobject_relationship_status = userobject.relationship_status
        else:
            userobject_sex = None
            userobject_preference = None
            userobject_relationship_status = None
    
        if settings.BUILD_NAME == "Single" or settings.BUILD_NAME == "Discrete":
            # let the lesbians and gays know about our other websites
            if (userobject_sex == 'male' and userobject_preference == 'male') or \
               ( search_sex == 'male' and search_preference == 'male'):
                additional_ads_to_append.append("Gay")
            if (userobject_sex == 'female' and userobject_preference == 'female') or \
               (search_sex == 'female' and search_preference == 'female'):
                additional_ads_to_append.append("Lesbian")
                
        if settings.BUILD_NAME == "Discrete":
            # Let the swingers know about Swinger
            if (userobject_sex == 'couple' or userobject_preference == 'couple') or \
               (search_sex == 'couple' or search_preference == 'couple'):
                additional_ads_to_append.append("Swinger")
                
            if (userobject_relationship_status == 'single' or search_relationship_status == 'single'):
                additional_ads_to_append.append("Single")
                

    except:
        error_reporting.log_exception(logging.critical)  
        
    return additional_ads_to_append
    
try:
    from rs.proprietary import advertisements
    logging.debug("imported proprietary advertisements")
    proprietary_ads_found = True
except:
    proprietary_ads_found = False
    logging.debug("unable to import proprietary advertisements")
    

def get_ashley_madison_sidebar_ad(request):
    
    banner_html = ''
    # Temporarily disable Ashley Madison advertisments.
    return banner_html
    
    if proprietary_ads_found:
        if len(advertisements.ashley_madison_sidebar_ads[request.LANGUAGE_CODE]) >= 1:
            idx = random.randint(0, len(advertisements.ashley_madison_sidebar_ads[request.LANGUAGE_CODE]) - 1)
            banner_html = advertisements.ashley_madison_sidebar_ads[request.LANGUAGE_CODE][idx]
    
        
    return banner_html

def get_ashley_madison_bottom_banner_ad(request):
    
    banner_html = ''
    
    # temporarily disable the bottom banner
    return banner_html
    
    if proprietary_ads_found:
        if len(advertisements.ashley_madison_horiz_banner_ads[request.LANGUAGE_CODE]) >= 1:
            idx = random.randint(0, len(advertisements.ashley_madison_horiz_banner_ads[request.LANGUAGE_CODE]) - 1)
            banner_html = advertisements.ashley_madison_horiz_banner_ads[request.LANGUAGE_CODE][idx]
    
    return banner_html

def render_main_html(request, generated_html, userobject = None, link_to_hide = '', 
                     page_title = '', refined_links_html = '', show_social_buttons = False, page_meta_description = '',
                     show_search_box = True, text_override_for_navigation_bar = '', hide_page_from_webcrawler = False,
                     enable_ads = True, show_login_link_override = False, hide_why_to_register = False,
                     do_not_try_to_dynamically_load_search_values = False, render_wrapper_only = False, 
                     hide_logo_banner_links = False):
    
    # function that takes care of defining a lot of the common code that needs to be defined before rendering one of the 
    # "main" views. 

    
    try:
        lang_idx = localizations.input_field_lang_idx[request.LANGUAGE_CODE]
        
        if show_search_box:
            search_bar = forms.MyHTMLSearchBarGenerator(lang_idx)
        else:
            search_bar = ''
        
        if userobject:
            username = userobject.username
            email_address = userobject.email_address
        else:
            username = ''
            email_address = ''
        
    
        additional_ads_to_append = []
        # render the HTML for the majority of pages that will be seen by users... However, individual profiles are rendered by views.user_main
        if userobject:
            owner_uid = str(userobject.key())
            owner_nid = userobject.key().id()
            owner_message_count = userobject.unread_mail_count_ref.unread_contact_count
            new_contact_count = utils.get_new_contact_count_sum(userobject.new_contact_counter_ref)
            registered_user_bool = True
            why_to_register = ''
            online_status_on_page_reload = online_presence_support.get_online_status(chat_support.ChatPresence, owner_uid)
            
            additional_ads_to_append = get_additional_ads_to_append(request, userobject)
    
        else:
            registered_user_bool = False
            username = ''
            display_uid = ''
            owner_uid = ''
            owner_nid = ''
            owner_message_count = new_contact_count = 0
            if not hide_why_to_register:
                why_to_register = ugettext("Remember the following benefits of registering with %(app_name)s.") % {'app_name': settings.APP_NAME}
                why_to_register += u"<br><br><ul>"
                why_to_register += ugettext("List of benefits for registering with %(app_name)s.") % {'app_name': settings.APP_NAME}
                why_to_register += u"</ul><br>"
            else:
                why_to_register = ''
                
            online_status_on_page_reload = "This should never be shown"
            
            additional_ads_to_append = get_additional_ads_to_append(request)
    
        # This code is used for generating maintenance warning messages. 
        (maintenance_soon_warning, maintenance_shutdown_warning) = admin.generate_code_for_maintenance_warning()
        
        
        unregistered_user_welcome_text = ugettext("""You must register with %(app_name)s to contact other users""") % {
            'app_name' : settings.APP_NAME}    
        
        # add in the generated region and sub-region menus
        country_code = request.GET.get('country', '----')
        region_code = request.GET.get('region', '----')
        location_response_dict = utils.get_location_dropdown_options_and_details(country_code, region_code)
        region_options_html = location_response_dict['region_options_html']
        sub_region_options_html = location_response_dict['sub_region_options_html']
        
        if settings.BUILD_NAME == "Friend":
            for_sale = request.GET.get('for_sale', '----')
            to_buy = request.GET.get('to_buy', '----')
            for_sale_sub_menu_options_html = utils.get_child_dropdown_options_and_details(for_sale, localizations.input_field_lang_idx[request.LANGUAGE_CODE])
            to_buy_sub_menu_options_html = utils.get_child_dropdown_options_and_details(to_buy, localizations.input_field_lang_idx[request.LANGUAGE_CODE])
        else:
            for_sale_sub_menu_options_html = "Not used - only for Friend"
            to_buy_sub_menu_options_html = "Not used - only for Friend"
                        
        
        primary_user_presentation_data_fields = constants.PassDataToTemplate()
        primary_user_presentation_data_fields.username = username
        primary_user_presentation_data_fields.email_address = email_address
        primary_user_presentation_data_fields.username_obfuscated = utils.AES16_Functionality.EncodeAES(username)
        primary_user_presentation_data_fields.owner_uid = owner_uid
        primary_user_presentation_data_fields.owner_nid = owner_nid
        primary_user_presentation_data_fields.owner_message_count = owner_message_count
        primary_user_presentation_data_fields.new_contact_count = new_contact_count
        primary_user_presentation_data_fields.max_active_polling_delay = constants.CHAT_MAX_ACTIVE_POLLING_DELAY_IN_CLIENT
        primary_user_presentation_data_fields.idle_polling_delay = constants.CHAT_IDLE_POLLING_DELAY_IN_CLIENT
        primary_user_presentation_data_fields.away_polling_delay = constants.CHAT_AWAY_POLLING_DELAY_IN_CLIENT
        primary_user_presentation_data_fields.inactivity_time_before_idle = constants.INACTIVITY_TIME_BEFORE_IDLE
        primary_user_presentation_data_fields.inactivity_time_before_away = constants.INACTIVITY_TIME_BEFORE_AWAY
        primary_user_presentation_data_fields.online_status_on_page_reload = online_status_on_page_reload
        primary_user_presentation_data_fields.do_not_try_to_dynamically_load_search_values = do_not_try_to_dynamically_load_search_values
        
        primary_user_presentation_data_fields.paypal_en_button_id = settings.PAYPAL_EN_BUTTON_ID
        primary_user_presentation_data_fields.paypal_es_button_id = settings.PAYPAL_ES_BUTTON_ID
        primary_user_presentation_data_fields.paypal_sandbox_button_id = settings.PAYPAL_SANDBOX_BUTTON_ID
        
            
        guest_user_data_fields = constants.PassDataToTemplate()
        guest_user_data_fields.registered_user_bool = registered_user_bool
        guest_user_data_fields.unregistered_user_welcome_text = unregistered_user_welcome_text
        guest_user_data_fields.why_to_register =  why_to_register
        guest_user_data_fields.show_social_buttons = show_social_buttons
        guest_user_data_fields.minimum_registration_age = constants.minimum_registration_age
        guest_user_data_fields.language = request.LANGUAGE_CODE
        guest_user_data_fields.testing_paypal_sandbox = settings.TESTING_PAYPAL_SANDBOX

    
        general_information_data_fields = constants.PassDataToTemplate()
        general_information_data_fields.settings_debug_flag = settings.DEBUG
        general_information_data_fields.is_cygwin = settings.IS_CYGWIN
        general_information_data_fields.maintenance_soon_warning = maintenance_soon_warning
        general_information_data_fields.maintenance_shutdown_warning = maintenance_shutdown_warning 
        general_information_data_fields.region_options_html = region_options_html
        general_information_data_fields.sub_region_options_html = sub_region_options_html
        general_information_data_fields.for_sale_sub_menu_options_html = for_sale_sub_menu_options_html
        general_information_data_fields.to_buy_sub_menu_options_html = to_buy_sub_menu_options_html
        general_information_data_fields.link_to_hide = link_to_hide
        general_information_data_fields.show_login_link_override = show_login_link_override
        general_information_data_fields.path_info = request.path_info



        
        meta_info = {}
        if page_title:
            meta_info['page_title'] = page_title
        else:
            if settings.SEO_OVERRIDES_ENABLED:
                meta_info['page_title'] = search_engine_overrides.get_main_page_title()
            else:
                meta_info['page_title'] = ''
                
        meta_info['content_description'] = page_meta_description
        if hide_page_from_webcrawler:
            meta_info['web_crawler_access'] = "noindex, nofollow"
        else:
            meta_info['web_crawler_access'] = ''
            
        meta_info['keywords_description'] =  meta_info['page_title']

        advertising_info = constants.PassDataToTemplate()            
        if  constants.enable_internal_ads :
            ad_list = get_my_internal_advertisements()
            ad_template_list = []
            for val in ad_list:
                ad_template_list.append('proprietary_ads/%s.html/' % val)
            advertising_info.ad_template_list = ad_template_list    
            
            additional_ads_template_list = []
            for val in additional_ads_to_append:
                additional_ads_template_list.append('proprietary_ads/%s.html/' % val)
            advertising_info.additional_ads_template_list = additional_ads_template_list
        else:
            advertising_info.ad_template_list = []          
            
        
        if enable_ads:
            if constants.enable_ashley_madison_ads:
                advertising_info.ashley_madison_bottom_banner_ad = get_ashley_madison_bottom_banner_ad(request)
                advertising_info.ashley_madison_sidebar_ad1 = get_ashley_madison_sidebar_ad(request)
                advertising_info.ashley_madison_sidebar_ad2 = get_ashley_madison_sidebar_ad(request)
           
        advertising_info.enable_ads = enable_ads
        advertising_info.enable_google_ads = constants.enable_google_ads
        advertising_info.enable_ashley_madison_ads = constants.enable_ashley_madison_ads
                
        if request.POST:
            # if anything is posted, then hide the language change links. This is necessary because
            # changing language calls and HttpResponseRedirect back to the calling page, but the 
            # POST information is lost, and therefore an error would be generated if the user tries
            # to change the language on such a page.
            languages = None
        else:
            languages = settings.LANGUAGES
            
        if render_wrapper_only:
            
            # we are only rendering the wrapper - the inner html will be loaded by a subsequent
            # ajax call
            http_response = render_to_response("common_wrapper.html", dict({  
                'meta_info': meta_info,                  
                'body_main_html' : '',
                'wrapper_data_fields' : common_data_structs.wrapper_data_fields,
            }, **constants.template_common_fields))     
            
        else:
            
            template = loader.get_template('main_container.html')        
            context = Context (dict({
                'LANGUAGES' : languages,                                    
                'primary_user_presentation_data_fields': primary_user_presentation_data_fields,
                'guest_user_data_fields': guest_user_data_fields,
                'general_information_data_fields': general_information_data_fields,
                'search_bar': search_bar,
                'generated_html': generated_html,
                'text_override_for_navigation_bar': text_override_for_navigation_bar,
                'advertising_info': advertising_info,
                'refined_links_html' : refined_links_html,
                'updated_meta_info': meta_info,  
                'hide_logo_banner_links' : hide_logo_banner_links,
                'request' : request,
                'javascript_version_id': settings.JAVASCRIPT_VERSION_ID,
                }, **constants.template_common_fields))
        
            body_main_html = template.render(context)
        
            if request.REQUEST.get("is_ajax_call", 'no') == 'yes':
                # We just check if it is an ajax request to see the entire page should be loaded, or just the body.
                http_response = http_utils.ajax_compatible_http_response(request, body_main_html)
                
            else:               
                # This is a traditional HTML request - entire page will be loaded
                http_response = render_to_response("common_wrapper.html", dict({      
                    'meta_info' : meta_info,
                    'body_main_html' : body_main_html,
                    'wrapper_data_fields' : common_data_structs.wrapper_data_fields,
                }, **constants.template_common_fields))
            
        return http_response
    
    except:
        from django.http import HttpResponseServerError
        error_reporting.log_exception(logging.critical)
        txt = ugettext('Internal error - this error has been logged, and will be investigated immediately')
        return http_utils.ajax_compatible_http_response(request, txt, HttpResponseServerError)


