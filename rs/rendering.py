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
import settings, site_configuration
import forms, admin, utils, error_reporting, logging
from models import UserModel
from forms import FormUtils
import constants, text_fields, time, chat_support, localizations, http_utils, common_data_structs, channel_support, online_presence_support
import online_presence_support, menubar
from rs.import_search_engine_overrides import *


if settings.BUILD_NAME == "friend_build":
    import friend_bazaar_specific_code

def get_my_internal_advertisements(additional_ads_to_include = []):
    
    try:
        ad_list = []
        
        if constants.COMPANY_NAME == "Lexabit Inc.":
            
            # code to randomly select from a list of advertisements that are appropriate for the current website.
            ads_to_show = constants.lexabit_self_publicity_ads + additional_ads_to_include
            num_ads_to_show = min(constants.MAX_NUM_LEXABIT_ADS_TO_SHOW, len(ads_to_show))
            
            # Randomly select pages from the list
            
            while num_ads_to_show:
                idx = random.randint(0, len(ads_to_show) -1 )
                ad_list.append(ads_to_show.pop(idx))  
                num_ads_to_show -= 1
        
        if constants.append_more_advertising_info_dialog:
            ad_list.append("more_advertising_info_dialog")
            
        return (ad_list)
    
    except:
        error_reporting.log_exception(logging.critical)
        return ad_list
        
def get_additional_ads_to_append(request, userobject = None):

    additional_ads_to_append = []
    
    try:
        if settings.BUILD_NAME == "language_build" or settings.BUILD_NAME == "friend_build":
            # we don't currently append any additional advertisements. 
            return additional_ads_to_append
        
        # the following two values should only be available if the user has submitted a search request - otherwise
        # they should not be defined (hopefully)
        search_preference = request.GET.get('preference', '')
        search_sex = request.GET.get('sex', '')
        search_relationship_status = request.GET.get('relationship_status', '')
        
        if userobject:
            search_preferences = userobject.search_preferences2.get()
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
    
        if settings.BUILD_NAME == "single_build" or settings.BUILD_NAME == "discrete_build":
            # let the lesbians and gays know about our other websites
            if (userobject_sex == 'male' and userobject_preference == 'male') or \
               ( search_sex == 'male' and search_preference == 'male'):
                additional_ads_to_append.append("gay_build")
            if (userobject_sex == 'female' and userobject_preference == 'female') or \
               (search_sex == 'female' and search_preference == 'female'):
                additional_ads_to_append.append("lesbian_build")
                
        if settings.BUILD_NAME == "discrete_build":
            # Let the swingers know about swinger_build
            if (userobject_sex == 'couple' or userobject_preference == 'couple') or \
               (search_sex == 'couple' or search_preference == 'couple'):
                additional_ads_to_append.append("swinger_build")
                
            if (userobject_relationship_status == 'single' or search_relationship_status == 'single'):
                additional_ads_to_append.append("single_build")
                

    except:
        error_reporting.log_exception(logging.critical)  
        
    return additional_ads_to_append
    
try:
    from rs.proprietary import advertisements
    proprietary_ads_found = True
except:
    proprietary_ads_found = False
    


def get_ad(request, ads_to_select_from):
    
    try:
        banner_html = ''
        
        #if ads_to_select_from == "ashley_madison_sidebar_ads" or ads_to_select_from == "ashley_madison_bottom_banner_ads":
            ## Temporarily disable Ashley Madison advertisments.
            #return banner_html
        
        if proprietary_ads_found:
            if len(getattr(advertisements, ads_to_select_from)[request.LANGUAGE_CODE]) >= 1:
                idx = random.randint(0, len(getattr(advertisements, ads_to_select_from)[request.LANGUAGE_CODE]) - 1)
                banner_html = getattr(advertisements, ads_to_select_from)[request.LANGUAGE_CODE][idx]
            
        return banner_html
    
    except:
        error_reporting.log_exception(logging.critical)




def render_main_html(request, generated_html, userobject = None, link_to_hide = '', 
                     page_title = '', refined_links_html = '', show_social_buttons = False, page_meta_description = '',
                     show_search_box = True, text_override_for_navigation_bar = '', hide_page_from_webcrawler = False,
                     enable_ads = True, show_login_link_override = False, hide_why_to_register = False,
                     do_not_try_to_dynamically_load_search_values = False, render_wrapper_only = False, 
                     hide_logo_banner_links = False, remove_chatboxes = False):
    
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
            client_paid_status = userobject.client_paid_status
        else:
            username = ''
            email_address = ''
            client_paid_status = None
    
        additional_ads_to_append = []
        # render the HTML for the majority of pages that will be seen by users... However, individual profiles are rendered by views.user_main
        if userobject:
            owner_uid = userobject.key.urlsafe()
            owner_nid = userobject.key.integer_id()
            owner_message_count = userobject.unread_mail_count_ref.get().unread_contact_count
            new_contact_counter_obj = userobject.new_contact_counter_ref.get()            
            contacts_dropdown_html = menubar.generate_contacts_dropdown_html(new_contact_counter_obj)
            registered_user_bool = True
            why_to_register = ''
            # Check if the user has disabled their chat - this will propagate through to all of the users open windows
            # and will close the chat windows, and will stop polling from the chat boxes. 
            chat_boxes_status = online_presence_support.get_chat_boxes_status(owner_uid)
            chat_is_disabled = "yes" if chat_boxes_status == constants.ChatBoxStatus.IS_DISABLED else "no"
            
            # Update user online presence - since we know that the user is logged in and has just requested a page to 
            # be rendered, we are sure that they are active. The computational cost of this is very low.
            online_presence_support.update_online_status(owner_uid, constants.OnlinePresence.ACTIVE)
            additional_ads_to_append = get_additional_ads_to_append(request, userobject)
            
            num_profile_views_since_last_check = userobject.viewed_profile_counter_ref.get().num_views_since_last_check

    
        else:
            registered_user_bool = False
            username = ''
            display_uid = ''
            owner_uid = ''
            owner_nid = ''
            owner_message_count = new_contact_count_sum = removed_contact_count_sum = 0
            num_profile_views_since_last_check = 0
            contacts_dropdown_html = ''
            if not hide_why_to_register:
                why_to_register = utils.get_why_to_register()
            else:
                why_to_register = ''
                
            chat_is_disabled = "yes"
            
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
        
        if settings.BUILD_NAME == "friend_build":
            for_sale = request.GET.get('for_sale', '----')
            to_buy = request.GET.get('to_buy', '----')
            for_sale_sub_menu_options_html = utils.get_child_dropdown_options_and_details(for_sale, localizations.input_field_lang_idx[request.LANGUAGE_CODE])
            to_buy_sub_menu_options_html = utils.get_child_dropdown_options_and_details(to_buy, localizations.input_field_lang_idx[request.LANGUAGE_CODE])
        else:
            for_sale_sub_menu_options_html = "Not used - only for friend_build"
            to_buy_sub_menu_options_html = "Not used - only for friend_build"
                        
        
        # Information for users that are signed in with an account
        primary_user_presentation_data_fields = {}
        primary_user_presentation_data_fields['username'] = username
        primary_user_presentation_data_fields['email_address'] = email_address
        primary_user_presentation_data_fields['owner_uid'] = owner_uid
        primary_user_presentation_data_fields['owner_nid'] = owner_nid
        primary_user_presentation_data_fields['owner_message_count'] = owner_message_count
        primary_user_presentation_data_fields['contacts_dropdown_html'] = contacts_dropdown_html
        primary_user_presentation_data_fields['user_presence_delay_constants'] = constants.OnlinePresenceConstants
        primary_user_presentation_data_fields['chat_is_disabled'] = chat_is_disabled
        primary_user_presentation_data_fields['do_not_try_to_dynamically_load_search_values'] = do_not_try_to_dynamically_load_search_values
        primary_user_presentation_data_fields['remove_chatboxes'] = "yes" if remove_chatboxes else "no"
        primary_user_presentation_data_fields['client_paid_status'] = client_paid_status
        primary_user_presentation_data_fields['num_profile_views_since_last_check'] = num_profile_views_since_last_check
            
        # Information for users that have not signed up for an account.
        guest_user_data_fields = {}
        guest_user_data_fields['registered_user_bool'] = registered_user_bool
        guest_user_data_fields['unregistered_user_welcome_text'] = unregistered_user_welcome_text
        guest_user_data_fields['why_to_register'] =  why_to_register
        guest_user_data_fields['show_social_buttons'] = show_social_buttons
        guest_user_data_fields['minimum_registration_age'] = constants.minimum_registration_age
        guest_user_data_fields['language'] = request.LANGUAGE_CODE

    
        general_information_data_fields = {}
        general_information_data_fields['settings_debug_flag'] = site_configuration.DEBUG
        general_information_data_fields['is_cygwin'] = site_configuration.IS_CYGWIN
        general_information_data_fields['maintenance_soon_warning'] = maintenance_soon_warning
        general_information_data_fields['maintenance_shutdown_warning'] = maintenance_shutdown_warning 
        general_information_data_fields['region_options_html'] = region_options_html
        general_information_data_fields['sub_region_options_html'] = sub_region_options_html
        general_information_data_fields['for_sale_sub_menu_options_html'] = for_sale_sub_menu_options_html
        general_information_data_fields['to_buy_sub_menu_options_html'] = to_buy_sub_menu_options_html
        general_information_data_fields['link_to_hide'] = link_to_hide
        general_information_data_fields['show_login_link_override'] = show_login_link_override
        general_information_data_fields['path_info'] = request.path_info


        paypal_button = utils.render_paypal_button(request, username, owner_nid)
        
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

        advertising_info = {}  
        side_ad_template_list = []
        bottom_ad_template = None
        
        if enable_ads:
            ad_list = get_my_internal_advertisements(additional_ads_to_append)
            
            for ad_name in ad_list:
                side_ad_template_list.append(utils.render_internal_ad(ad_name))
                
            advertising_info['ad_template_list'] = side_ad_template_list    
            
            if constants.enable_google_ads:
                side_ad_template_list.append(utils.render_google_ad('GOOGLE_AD_160x600'))
                side_ad_template_list.append(utils.render_google_ad('GOOGLE_AD_160x600'))
                bottom_ad_template = utils.render_google_ad('GOOGLE_AD_728x90')
                
            #elif constants.enable_ashley_madison_ads:
                #bottom_ad_template = get_ad(request, "ashley_madison_bottom_banner_ads")
                #side_ad_template_list.append(get_ad(request, "ashley_madison_sidebar_ads"))
                
            else:
                bottom_ad_template = utils.render_internal_ad("Client_Bottom_Ad1")
                
            

                
        random.shuffle(side_ad_template_list) # randomize the order of the advertisements.
        advertising_info['ad_template_list'] = side_ad_template_list    
        advertising_info['bottom_ad_template'] = bottom_ad_template
        advertising_info['enable_ads'] = enable_ads
        
                
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
                'paypal_button' : paypal_button,
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


