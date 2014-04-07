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

from django.utils.translation import ugettext

import logging
import site_configuration
from rs import utils_top_level, error_reporting, localizations, profile_utils, utils, forms, constants
from rs import user_profile_details, user_profile_main_data

if site_configuration.BUILD_NAME == "friend_build":
    import friend_bazaar_specific_code

MAX_NUM_CHARS_TO_DISPLAY_IN_LIST = 160

def display_userobject_first_half_summary(request, display_userobject, display_online_status, extra_info_html = None):
    # returns a summary of a single users userobject. 
    #
    
    try:
        
        lang_code = request.LANGUAGE_CODE
        lang_idx = localizations.input_field_lang_idx[request.LANGUAGE_CODE]
        lang_idx_offset = lang_idx + 1        
        
        # This is just a security checking funcion, since we previously set last_login to None for userobjects that had been 
        # eliminated -- we should never show a userobject if it's last_login is None -- and this code just notifies us if this happens.
        if display_userobject.last_login_string == None or display_userobject.unique_last_login == None:
            logging.warning("last_login values set to none for userobject %s" % display_userobject.username)  
            
        
        generated_html = ''
        
        generated_html += u'<div class="grid_9 alpha omega cl-search_results">\n'
        generated_html += u'<!-- following line defines the horizontal bar -->'
        generated_html += u'<div class = "grid_9 alpha omega cl-divider-line" ></div>'
        generated_html += u'<div class="grid_9 alpha omega cl-search_seperator" ></div>'
    
        generated_html += u'<div class="grid_9 alpha omega"> &nbsp;</div>\n'
    
        userobject_href = profile_utils.get_userprofile_href(request.LANGUAGE_CODE, display_userobject)

            
        heading_text = ugettext("See profile of:")
        generated_html += u'<div class="grid_9 alpha omega cl-text-14pt-format">\
        <a href="%s" rel="address:%s"><strong>%s</strong> %s </a>' % (
            userobject_href, userobject_href, heading_text, display_userobject.username)

        
        if display_online_status:
            userobject_key = display_userobject.key.urlsafe()
            status_string = utils.get_vip_online_status_string(userobject_key)
            generated_html += u' <br>%s' % status_string
        
        generated_html += "<br><br></div>\n"
        
        
        if extra_info_html:
            generated_html += "<br>%s<br><br>" % extra_info_html        
        
        
        status_string = ''

        if not display_userobject.user_is_marked_for_elimination:
            # Note, the "and userobject.current_status" should be eventually removed for efficiency .. but
            # is needed temporarily because some of the users might have this value set to "" from a previous 
            # code revision.            
            if display_userobject.current_status != "----" and display_userobject.current_status:
                status_string = u"<em>%s</em>" % (display_userobject.current_status)
                generated_html += u'<div class="grid_9 alpha omega ">%s<br><br></div>\n' % (status_string)
        
        photo_message = utils.get_photo_message(display_userobject)
            
        # get userobject photo
        generated_html += '<div class="grid_2 alpha">\n'
        
        generated_html += forms.FormUtils.generate_profile_photo_html(lang_code, display_userobject, photo_message, userobject_href, photo_size="medium")
    
    
        generated_html += '</div> <!-- end grid2 -->\n'
    
    
        # container for all the userobject information
        generated_html += '<div class="grid_7 omega">\n'
    
    
    
        generated_html += utils.generate_profile_summary_table(request.LANGUAGE_CODE, display_userobject)


        if not display_userobject.user_is_marked_for_elimination:
            # section for getting the text description of the user
            about_user = display_userobject.about_user
            if about_user != "----":
                generated_html += u'<Strong>%s:&nbsp;</Strong>\n' % ugettext("About me")
        
                if len(about_user) > constants.ABOUT_USER_SEARCH_DISPLAY_DESCRIPTION_LEN: 
                    about_user = display_userobject.about_user[:constants.ABOUT_USER_SEARCH_DISPLAY_DESCRIPTION_LEN] + "  ..."

                generated_html += u'<span class="cl-compressed-display-user-text">%s</span>\n' % about_user
                generated_html += u'<br><br>'
            
        if site_configuration.BUILD_NAME != "language_build" and site_configuration.BUILD_NAME != "friend_build":
            # section for getting physical description of the user
            description_printed = False
            for detail_field in user_profile_details.UserProfileDetails.details_fields_to_display_in_order:
                label = user_profile_details.UserProfileDetails.details_fields[detail_field]['label'][lang_idx]                         
                value = user_profile_details.UserProfileDetails.details_fields_options_dict[detail_field][lang_idx][getattr(display_userobject, detail_field)]
                
                if (value != u'----'):
        
                    description_printed = True   
                    generated_html += u'<strong>%s</strong>: \n' % label
                    if detail_field != user_profile_details.UserProfileDetails.details_fields_to_display_in_order[-1]:
                        generated_html += u'%s. ' % value
                    else:
                        generated_html += u'%s' % value   
                    
            if description_printed:
                generated_html += u'<br>\n'
            
        # section for getting all other information about the user
        if site_configuration.BUILD_NAME != "language_build" and site_configuration.BUILD_NAME != "friend_build":
            if display_userobject.languages[0] != "prefer_no_say":
                mylist = u'<strong>%s:</strong> ' % ugettext("Languages I speak")
                mylist += utils.generic_html_generator_for_list(lang_idx, 'languages' , display_userobject.languages )
                if len(mylist) > MAX_NUM_CHARS_TO_DISPLAY_IN_LIST:
                    generated_html += u'%s<br>' % (mylist[:MAX_NUM_CHARS_TO_DISPLAY_IN_LIST] + "...")
                else: generated_html += u'%s<br>' % mylist

        if site_configuration.BUILD_NAME == "language_build" :
            # Show native language of the user
            generated_html += u'<strong>%s:</strong> %s<br>' % (ugettext("Native language"),
                user_profile_main_data.UserSpec.signup_fields_options_dict['native_language'][lang_idx][display_userobject.native_language])
  
        if site_configuration.BUILD_NAME != "friend_build":
            if display_userobject.entertainment[0] != "prefer_no_say":
                mylist = u'<strong>%s:</strong> ' % user_profile_details.UserProfileDetails.checkbox_fields['entertainment']['label'][lang_idx]
                mylist += utils.generic_html_generator_for_list(lang_idx, 'entertainment', display_userobject.entertainment)
                if len(mylist) > MAX_NUM_CHARS_TO_DISPLAY_IN_LIST:
                    generated_html += u'%s<br>' % (mylist[:MAX_NUM_CHARS_TO_DISPLAY_IN_LIST] + "...")
                else: generated_html += u'%s<br>' % mylist
                
            if display_userobject.athletics[0] != "prefer_no_say":
                mylist = u'<strong>%s:</strong> ' % user_profile_details.UserProfileDetails.checkbox_fields['athletics']['label'][lang_idx]
                mylist += utils.generic_html_generator_for_list(lang_idx, 'athletics', display_userobject.athletics)
                if len(mylist) > MAX_NUM_CHARS_TO_DISPLAY_IN_LIST:
                    generated_html += u'%s<br>' % (mylist[:MAX_NUM_CHARS_TO_DISPLAY_IN_LIST] + "...")
                else: generated_html += u'%s<br>' % mylist
                
        else: # friend_build
            #sale_or_buy in ['for_sale', 'to_buy']:
            if len(display_userobject.for_sale_ix_list) > 1:
                sale_or_buy = 'for_sale'
                master_label = friend_bazaar_specific_code.label_tuples[sale_or_buy][lang_idx]
                generated_html += u"<strong>%s:</strong><br>" % master_label
                
                for category in friend_bazaar_specific_code.category_definitions_dict.keys():
                    field_name = '%s_%s' % (sale_or_buy, category)                
                    
                    field_list = getattr(display_userobject, field_name)
                    if field_list[0] != "prefer_no_say":
                        mylist = u'<em>%s:</em> ' % user_profile_details.UserProfileDetails.checkbox_fields[field_name]['label'][lang_idx]
                        mylist += utils.generic_html_generator_for_list(lang_idx, field_name, field_list)
                        if len(mylist) > MAX_NUM_CHARS_TO_DISPLAY_IN_LIST:
                            generated_html += u'%s<br>' % (mylist[:MAX_NUM_CHARS_TO_DISPLAY_IN_LIST] + "...")
                        else: generated_html += u'%s<br>' % mylist
                generated_html += u'<br>'
        
        if site_configuration.BUILD_NAME == "discrete_build" or site_configuration.BUILD_NAME == "gay_build" or site_configuration.BUILD_NAME == "swinger_build": # do not show turn-ons for other builds
            if display_userobject.turn_ons[0] != "prefer_no_say":
                mylist = u'<strong>%s:</strong> ' % user_profile_details.UserProfileDetails.checkbox_fields['turn_ons']['label'][lang_idx]
                mylist += utils.generic_html_generator_for_list(lang_idx, 'turn_ons', display_userobject.turn_ons)
                if len(mylist) > MAX_NUM_CHARS_TO_DISPLAY_IN_LIST:
                    generated_html += u'%s<br>' % (mylist[:MAX_NUM_CHARS_TO_DISPLAY_IN_LIST] + "...")
                else: generated_html += u'%s<br>' % mylist      
            
            if display_userobject.erotic_encounters[0] != "prefer_no_say":
                mylist = u'<strong>%s:</strong> ' % user_profile_details.UserProfileDetails.checkbox_fields['erotic_encounters']['label'][lang_idx]
                mylist += utils.generic_html_generator_for_list(lang_idx, 'erotic_encounters', display_userobject.erotic_encounters)
                if len(mylist) > MAX_NUM_CHARS_TO_DISPLAY_IN_LIST:
                    generated_html += u'%s<br>' % (mylist[:MAX_NUM_CHARS_TO_DISPLAY_IN_LIST] + "...")
                else: generated_html += u'%s<br>' % mylist                      
    
        return generated_html
    except:
        error_reporting.log_exception(logging.critical, error_message = 'display_userobject_first_half_summary %s exception.' % display_userobject.username)
        return ""


def display_userobject_second_half_summary(viewer_userobject, display_userobject):
    
    """ 
    Generates the part of the user summary that cannot be cached such as the last entrance time, which can change (and which
    must be displayed relative to the current time) """
    
    try: 
        generated_html = ''
        last_time_in_system = utils.return_time_difference_in_friendly_format(display_userobject.last_login)
        
        generated_html += u'<br><strong>%s: </strong>%s' % (ugettext("Last entrance"), last_time_in_system )
        generated_html += u'<br><br>\n'
        
        generated_html += u'</div> <!-- end grid8 -->'
        generated_html += u'</div> <!-- end grid10 -->\n'
        
        generated_html += utils.generate_profile_information_for_administrator(display_userobject, utils.user_is_admin(viewer_userobject))
        
        
        return generated_html
    except:
        error_reporting.log_exception(logging.critical, error_message = 'display_userobject_second_half_summary %s exception.' % display_userobject.username)
        return ""        
        
        
def get_userobject_summary(request, viewer_userobject, display_userobject_key, display_online_status, extra_info_html = None):
    
    """
    This is a wrapper function for display_userobject_summary that computes the summary only if it is not in
    memcache. We removed the memcaching of the summaries.
    """
    
    if not display_userobject_key:
        return None
    
    lang_code = request.LANGUAGE_CODE    
    display_uid = display_userobject_key.urlsafe()
    display_userobject = utils_top_level.get_object_from_string(display_uid)  

    summary_first_half_html = display_userobject_first_half_summary(request, display_userobject, display_online_status, 
                                                                    extra_info_html)              
    summary_second_half_html = display_userobject_second_half_summary(viewer_userobject, display_userobject)
        
    return summary_first_half_html + summary_second_half_html
    


def generate_html_for_list_of_profiles(request, viewer_userobject, query_results_keys, display_online_status,
                                     extra_info_html_dict = None):
    # Accepts results from a query, which is an array of user profiles that matched the previous query.
    # Goes through each profile, and generates a snippett of text + profile photo, which give a 
    # basic introduction to the user.


    generated_html = """<script type="text/javascript">
        $(document).ready(function() {
        fancyboxSetup($("a.cl-fancybox-profile-gallery"));
        });
        </script>"""

    
    for display_userobject_key in query_results_keys:
        extra_info_html = extra_info_html_dict[display_userobject_key] if extra_info_html_dict else None
        generated_html += get_userobject_summary(request, viewer_userobject, display_userobject_key, 
                                                 display_online_status, extra_info_html)
        
    return generated_html

def generate_summary_html_top(header_html, image_html = ''):

    # used for generatingthe HTML that defines the "top" part of the search results (ie. the opening of the form
    # element, as well as the header.
    
    generated_html_top = ''
    
    generated_html_top += u'<div class="cl-clear"></div>\n'
    generated_html_top += u'<div class="grid_9 alpha omega"><br><br>\n</div>'
    generated_html_top += u'<div class="grid_9 alpha omega ">\n'
    generated_html_top += u'%s <h1 style = "padding: 7px">%s</h1>\n' % (image_html, header_html)
    generated_html_top += u'</div> <!-- end grid9 -->\n'    
    return generated_html_top
    
def generate_summary_html_open_form(post_action):
    return u'<form method=GET action="%s">\n' % (post_action)
    

def generate_summary_html_close_form():
    generated_html_bottom = u'</form>\n'
    return generated_html_bottom


def generate_next_button_html():
    
    generated_html_top_next_button = ''
    generated_html_top_next_button += u"""<script type="text/javascript" language="javascript">
    $(document).ready(function(){
        mouseoverButtonHandler($(".cl-submit"));
        mouseoverButtonHandler($(".cl-cancel")); // this only affects buttons that are shown in rare instances (ie. eliminating profile)
    });
    </script>\n """ 
    
    generated_html_top_next_button += u'<div class="cl-clear"></div>\n'
    generated_html_top_next_button += u'<div class="grid_9 alpha omega">\n'
    generated_html_top_next_button += u'<input type="submit" class="cl-submit" value="%s >>">\n' % ugettext("Next")
    generated_html_top_next_button += u'</div> <!-- grid_9 -->\n'
    generated_html_top_next_button += u'<div class="cl-clear"></div>\n'

    generated_html_bottom_next_button = ''
    generated_html_bottom_next_button += u'<!-- following line defines the horizontal bar -->'
    generated_html_bottom_next_button += u'<div class="grid_9 alpha omega cl-divider-line " ></div>'
    generated_html_bottom_next_button += u'<div class="grid_9 alpha omega cl-search_seperator" ></div>'
        
    generated_html_bottom_next_button += u'<div class="grid_9 alpha omega">&nbsp;</div>\n'
    generated_html_bottom_next_button += u'<div class="cl-clear"></div>\n'
    generated_html_bottom_next_button += u'<div class="grid_9 alpha omega">\n'
    generated_html_bottom_next_button += u'<input type="submit" class="cl-submit" value="%s >>">\n' % ugettext("Next")
    generated_html_bottom_next_button += u'</div> <!-- grid_9 -->\n'
    generated_html_bottom_next_button += u'<div class="grid_9 alpha omega"><br><br><br><br></div>\n'    
    
    return (generated_html_top_next_button, generated_html_bottom_next_button)