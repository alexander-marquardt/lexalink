
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

""" This module is responsible for displaying the contact information for the current user. This will show the page
that includes who he/she has sent winks to, kisses, keys, favorites, blocked...
"""
from google.appengine.datastore.datastore_query import Cursor

from django.core.urlresolvers import reverse
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext

import datetime

import settings
from forms import MyHTMLSearchBarGenerator
import constants
from utils import requires_login
from utils import return_time_difference_in_friendly_format, get_new_contact_count_sum
from rs import profile_utils
import queries, rendering, localizations, error_reporting, logging
import utils, utils_top_level, display_profiles_summary
import http_utils


@requires_login
def show_contacts(request, contact_type, sent_or_received):
    
    
    try:
        userobject =  utils_top_level.get_userobject_from_request(request)
        
        if not userobject:
            generated_html = ''
            generated_title = ''
            
        else:
            owner_key = userobject.key
            owner_uid = owner_key.urlsafe()
            display_online_status = utils.do_display_online_status(owner_uid)
            show_online_status = utils.show_online_status(owner_uid)
            
            generated_title = header_html = u"%s %s" % (constants.ContactIconText.plural_icon_name[contact_type], 
                                                        constants.ContactIconText.contacts_actions_text[sent_or_received])
            generated_html_before_form = ''
            display_online_status = utils.do_display_online_status(owner_uid)           
            
            if contact_type != "chat_friend":
                query_value_to_match = True
                if sent_or_received == 'sent':
                    # if we are displaying kisses that were sent by the current user, then we are intersted
                    # in the profile that they sent the kiss to. This is the "displayed_profile" that they were
                    # looking at when they sent the kiss.
                    profile_to_show = 'displayed_profile'
                elif sent_or_received == 'received':
                    # otherwise, they have received a kiss from someone else (the viewer), and we should show the 
                    # viewers profile. 
                    profile_to_show = 'viewer_profile'

            elif contact_type == "chat_friend":
                # "chat_friend" requests need special treatment because they are not just a boolean like
                # other initiate_contact actions, these actions have a string that encodes the current
                # status of the request. 
                # Note: due to the fact that information about the chat status between two users is always
                #       encoded on the viewer object, we just query the viewer_object, and therefore 
                #       the profile_to_show is always "displayed_profile"
                profile_to_show = 'displayed_profile'
                if sent_or_received == 'sent':
                    query_value_to_match = 'request_sent'
                elif sent_or_received == 'received':
                    query_value_to_match = 'request_received'
                elif sent_or_received == 'connected':
                    query_value_to_match = 'connected'
                else:
                    assert(False)
                                
            generated_html_before_form += u'<div class="cl-clear"></div>\n'
            generated_html_before_form += '<ul>\n'                                
            generated_html_before_form += "</ul>\n"

            generated_html_hidden_variables = ''
            generated_html_top_next_button = ''
            generated_html_bottom_next_button = ''  
            
            post_action = "/%s/show_contacts/%s/%s/" % (request.LANGUAGE_CODE, contact_type, sent_or_received)
            generated_html_top = display_profiles_summary.generate_summary_html_top(header_html)
            
            generated_html_open_form = display_profiles_summary.generate_summary_html_open_form(post_action)        
            generated_html_close_form = display_profiles_summary.generate_summary_html_close_form()
            
            cursor_str = request.GET.get('show_contacts_cursor',None)
            paging_cursor = Cursor(urlsafe = cursor_str)

            (contact_query_results, new_cursor, more_results) = queries.query_with_cursor_initiate_contact_by_type_of_contact(
                owner_key, contact_type, 
                sent_or_received,
                query_value_to_match,
                paging_cursor)
            
            # convert the contact_query_results into a list of profile keys so that we can use the common code for
            # displaying a series of profile summaries. 
            profile_keys_list = (x.viewer_profile for x in contact_query_results)

            generated_html_body = display_profiles_summary.generate_html_for_list_of_profiles(request, userobject, profile_keys_list, 
                                                                                              display_online_status)            
                                                                 
            if more_results:
                generated_html_hidden_variables = \
                                    u'<input type=hidden id="id-show_contacts_cursor" name="show_contacts_cursor" \
                                    value="%(show_contacts_cursor)s">\n' % {'show_contacts_cursor': new_cursor.urlsafe()}           
                (generated_html_top_next_button, generated_html_bottom_next_button) = display_profiles_summary.generate_next_button_html()
                
            
            
            generated_html =   generated_html_top + generated_html_before_form + generated_html_open_form + generated_html_hidden_variables + generated_html_top_next_button + \
                                   generated_html_body + generated_html_bottom_next_button + generated_html_close_form
                            
            # reset the counter that tells the user how many new contacts (of the current type) they have received.
            current_property_counter_name = 'num_' + sent_or_received + '_' + contact_type + '_since_last_reset' 
            current_property_date_reset_name = "date_" + contact_type + "_count_reset"
            
            new_contact_counter_obj = userobject.new_contact_counter_ref.get()
            setattr(new_contact_counter_obj, current_property_counter_name, 0)
            setattr(new_contact_counter_obj, current_property_date_reset_name, datetime.datetime.now())
            utils.put_object(new_contact_counter_obj)
            
        
        return rendering.render_main_html(request, generated_html, userobject, page_title = generated_title, 
                                          refined_links_html = '', show_social_buttons = True,
                                          page_meta_description = '')
        
    except:
        error_reporting.log_exception(logging.critical)
        return rendering.render_main_html(request, 'Error')    
    
    
