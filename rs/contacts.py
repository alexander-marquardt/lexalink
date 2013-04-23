
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

import settings
from forms import MyHTMLSearchBarGenerator
from constants import ContactIconText, MAX_NUM_INITIATE_CONTACT_OBJECTS_TO_DISPLAY
from utils import requires_login
from utils import return_time_difference_in_friendly_format, get_new_contact_count_sum
from rs import profile_utils
import queries, rendering, localizations, error_reporting, logging
import utils, utils_top_level, display_profiles_summary
import http_utils

sent_received_list = ['received', 'sent', ]
custom_config = []

if settings.BUILD_NAME != "Language" and settings.BUILD_NAME != "Friend":
    for idx, sent_received in enumerate(sent_received_list):
        custom_config.append([
            
            {
                'contact_type': None,
                'display_divider' : True, 
                'sent_or_received': sent_received},     
            {
                'contact_type': 'key',
                'sent_or_received':  sent_received,}, 
            {
                'contact_type': 'chat_friend',
                'sent_or_received':  sent_received,}, 
            {            
                'contact_type': 'wink',
                'sent_or_received':  sent_received,}, 
            {
                'contact_type': 'kiss',
                'sent_or_received':  sent_received,}, 
            ])
else: # set up Language with greeting instead of wink, and *no* kisses
    for idx, sent_received in enumerate(sent_received_list):
        custom_config.append([
            
            {
                'contact_type': None,
                'display_divider' : True, 
                'sent_or_received': sent_received,},    
            {
                'contact_type': 'key',
                'sent_or_received':  sent_received,}, 
            {
                'contact_type': 'chat_friend',
                'sent_or_received':  sent_received,}, 
            {
                'contact_type': 'wink',
                'sent_or_received':  sent_received,}, 
            ])    
    
favorite_config = [
    {
        'contact_type': None,
        'display_divider' : True,
        'sent_or_received':  'saved',},         
    {
        'contact_type': 'favorite',
        'sent_or_received':  'sent',}, 
    {
        'contact_type': 'chat_friend',
        'sent_or_received':  'connected',}, 
    {
        'contact_type': 'blocked',
        'sent_or_received':  'sent',}, # 'sent' because this user initiated it
    {
        'contact_type': None,
        'display_divider' : True,
        'sent_or_received':  '',}, 
]

# custom_config has two indexes, first for 'sent', second for 'received' - constructed in the for loop above
display_contact_config = custom_config[0] + custom_config[1] + favorite_config


def generate_new_contacts_html(userobject):
    # Generates the HTML that corresponds to the newest contact the user has received. 
    # Ie. "you have 3 new winks, 1 new kiss"...
    
    generated_html = ''
    
    
    new_contact_counter_obj = userobject.new_contact_counter_ref.get()
    
    new_kiss_count = new_contact_counter_obj.num_received_kiss_since_last_login + \
             new_contact_counter_obj.previous_num_received_kiss
    new_wink_count = new_contact_counter_obj.num_received_wink_since_last_login + \
             new_contact_counter_obj.previous_num_received_wink
    new_key_count = new_contact_counter_obj.num_received_key_since_last_login + \
               new_contact_counter_obj.previous_num_received_key
    new_friend_request_count = new_contact_counter_obj.num_received_friend_request_since_last_login + \
                              new_contact_counter_obj.previous_num_received_friend_request
    new_friend_confirmation_count = new_contact_counter_obj.num_received_friend_confirmation_since_last_login + \
                                   new_contact_counter_obj.previous_num_received_friend_confirmation
    
    if new_wink_count or new_kiss_count or new_key_count or new_friend_request_count or new_friend_confirmation_count:
        
        previous_last_login_in_friendly_format = return_time_difference_in_friendly_format(userobject.previous_last_login)
        text_since_last_login = \
            ugettext(u"Since the last time you entered in %(app_name)s.com, %(previous_login)s, you have received")\
            % {'app_name': settings.APP_NAME, 'previous_login' : previous_last_login_in_friendly_format}

        generated_html += u"""
        <div class="cl-clear"></div> 
        <div class="grid_9 alpha omega"> &nbsp;<br><br></div>
    
        <div class="grid_9 alpha omega cl-center-text"> 
        %(text_since_last_login)s:<br><strong>
        """ % {'text_since_last_login' : text_since_last_login}

        if new_kiss_count:
            generated_html += u" %d %s<br>" %  (new_kiss_count, ContactIconText.plural_icon_name['kiss'], )
        
        if new_wink_count:
            generated_html += u" %d %s<br>" %  (new_wink_count, ContactIconText.plural_icon_name['wink'], )
        
        if new_key_count:
            generated_html += u" %d %s<br>" %  (new_key_count, ContactIconText.plural_icon_name['key'], )
            
        if new_friend_request_count:
            generated_html += u" %d %s<br>" %  (new_friend_request_count, ContactIconText.chat_friend_plural_text['request_received'], )
        
        if new_friend_confirmation_count:
            generated_html += u" %d %s<br>" %  (new_friend_confirmation_count, ContactIconText.chat_friend_plural_text['connected'], )
            
        generated_html += u'</strong></div>\n     <div class="cl-clear"></div>'
        
        
    return generated_html

                    


def generate_contacts_html(userobject, lang_code):
    # generates the html that will show the contents of the users contact lists .

    generated_html = ''
    
    
    try:

        generated_html += u"""
        <div class="cl-clear"></div> 
    
        <div class="grid_9 alpha omega cl-header-format"> 
        %(my_contacts)s
        </div>
        
        <div class="cl-clear"></div> 
        """ % {'my_contacts': ugettext("My contacts") }
        
        generated_html += '<div class="grid_9 alpha omega cl-contacts_page"> '
        
        generated_html += generate_new_contacts_html(userobject)
        
        for contact_config in display_contact_config:
            
            try:
                sent_or_received = contact_config['sent_or_received']
                contact_type = contact_config['contact_type']
                
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
                        
                        
                # if the datastrcuture calls for a divider, display it ..and directly continue to next loop iteration 
                if contact_config.has_key('display_divider'):
                    if sent_or_received == 'sent':
                        sent_or_received_label = u"%s" % ContactIconText.sent
                    elif sent_or_received == 'received':
                        sent_or_received_label = u"%s" % ContactIconText.received
                    elif sent_or_received == 'saved':
                        sent_or_received_label =  u"%s" % ContactIconText.saved
                    else:
                        sent_or_received_label = ''
                        
                    generated_html += u'<div class="cl-clear"></div> '
                    generated_html += u'<div class="grid_9 alpha omega"><br><br></div>\n'
                    generated_html += u'<div class="grid_9 alpha omega cl-divider-line"" ></div>'
                    generated_html += u'<div class="grid_9 alpha omega"><br></div>\n'
                    if sent_or_received_label:            
                        generated_html += u'<div class="grid_9 alpha omega"><strong>%s</strong><br>(%s %d)</div>' % (
                            sent_or_received_label, 
                            ContactIconText.the_last, MAX_NUM_INITIATE_CONTACT_OBJECTS_TO_DISPLAY)
                        generated_html += u'<div class="grid_9 alpha omega"><br></div>\n'
                    continue
        
                if settings.BUILD_NAME == "Language" or settings.BUILD_NAME == "Friend":
                    generated_html += '<div class="grid_3 alpha omega">'
                else:
                    generated_html += '<div class="grid_2 alpha omega">'
                
                if contact_type != "chat_friend":
                    section_label =  u"%s" % ContactIconText.plural_icon_name[contact_type]
                else:
                    section_label =  u"%s" % ContactIconText.chat_friend_plural_text[query_value_to_match]
                                                                               
                        
                date_key = "%s_stored_date" % contact_type
        
                    
                image_name = ContactIconText.icon_images[contact_type]
                
                generated_html += """
                <div class="cl-clear"></div> 
        
                
                <strong>%s<br></strong><img src="/%s/img/%s/%s" align=left alt=""><br><br><br>
                
                <div class="cl-clear"></div> """ % (section_label, settings.LIVE_STATIC_DIR, settings.BUILD_NAME, image_name)
                

                    
                contact_query_results = queries.query_initiate_contact_by_type_of_contact(userobject.key, contact_type, 
                                                                                          sent_or_received,
                                                                                          MAX_NUM_INITIATE_CONTACT_OBJECTS_TO_DISPLAY,
                                                                                          query_value_to_match)
                if not contact_query_results:
                    there_are_none_text = ugettext("You don't have any yet")
                    generated_html += u'%s<br>' % there_are_none_text
        
                for contact in contact_query_results:
                    
                    profile_key = getattr(contact, profile_to_show)
                    
                    # THIS IS INEFFICIENT  - Need to figure out a better way to generate the userprofile_href without 
                    # getting the object.
                    profile = profile_key.get()
                    
                    date = getattr(contact, date_key)
                    
                    if date >= userobject.previous_last_login:
                        strong_open = "<strong>"
                        strong_close = "</strong>"
                    else:
                        strong_open = ""
                        strong_close = ""         
                    
                    date_stored =  return_time_difference_in_friendly_format(date, data_precision = 1)
                    profile_href = profile_utils.get_userprofile_href(lang_code, profile, is_primary_user=False)
                    
                    
                    generated_html += u'<a href="%s" rel="address:%s">%s %s</a>\n' % (profile_href, profile_href, strong_open, profile.username, )
                    generated_html += u'%s %s<br>' % (date_stored, strong_close)
                
                generated_html += '</div>'  # close grid_3
            except:
                error_reporting.log_exception(logging.critical)

        generated_html += '</div>' # class="grid_9 alpha omega cl-contacts_page"
    
        return generated_html
    except:
        error_reporting.log_exception(logging.critical)
        return ''

@requires_login
def generate_contacts_display(request , owner_uid):
    # code for displaying the contacts of the client.
    
    generated_html = ''
    try:
        lang_idx = localizations.input_field_lang_idx[request.LANGUAGE_CODE]
        
        if not utils.access_allowed_to_page(request, owner_uid):
            return http_utils.redirect_to_url(request, "/%s/" % request.LANGUAGE_CODE)
    
        userobject =  utils_top_level.get_object_from_string(owner_uid)
        username = userobject.username
        generated_html = generate_contacts_html(userobject, request.LANGUAGE_CODE)
        
        # note must declare lang_idx = lang_idx for this to work since other parameters appear before it.
        return rendering.render_main_html(request, generated_html, userobject)
    except:
        from django.http import HttpResponseServerError
        error_reporting.log_exception(logging.critical)
        return HttpResponseServerError(ugettext('Internal error - this error has been logged, and will be investigated immediately'))


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
            
            generated_title = header_html = "%s %s" % (contact_type, sent_or_received)
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
            
            post_action = "/%s/show_contacts/" % (request.LANGUAGE_CODE)
            generated_html_top = display_profiles_summary.generate_summary_html_top(header_html)
            
            generated_html_open_form = display_profiles_summary.generate_summary_html_open_form(post_action)        
            generated_html_close_form = display_profiles_summary.generate_summary_html_close_form()
            
            cursor_str = request.GET.get('show_contacts_cursor',None)
            paging_cursor = Cursor(urlsafe = cursor_str)

            (contact_query_results, new_cursor, more_results) = queries.query_with_cursor_initiate_contact_by_type_of_contact(owner_key, contact_type, 
                                                                                      sent_or_received,
                                                                                      query_value_to_match,
                                                                                      paging_cursor)
            # convert the contact_query_results into a list of profile keys so that we can use the common code for
            # displaying a series of profile summaries. 
            profile_keys_list = (x.displayed_profile for x in contact_query_results)

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
            # TODO - write this code
            
        
        return rendering.render_main_html(request, generated_html, userobject, page_title = generated_title, 
                                          refined_links_html = '', show_social_buttons = True,
                                          page_meta_description = '')
        
    except:
        error_reporting.log_exception(logging.critical)
        return rendering.render_main_html(request, 'Error')    