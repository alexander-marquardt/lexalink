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

from django.utils.translation import ugettext, ungettext

import models
from google.appengine.ext import ndb
from google.appengine.datastore.datastore_query import Cursor
from rs import utils, models, error_reporting, display_profiles_summary, utils_top_level
import rendering, site_configuration
import datetime, logging

PAGESIZE = 6
MAX_PROFILE_VIEWS_TO_SHOW_TO_NON_VIP = 1


def store_viewer_in_owner_profile_viewer_tracker(viewer_uid, displayed_uid):
    """ Keep track of which profiles "viewers" have viewed other "displayed" profiles  """

    try:
        viewer_key = ndb.Key(urlsafe = viewer_uid)
        displayed_key = ndb.Key(urlsafe = displayed_uid)
        
        # Get the counter ojbect for the profile that is being viewed ie. the "displayed" profile's counter
        # We get this asynchronously so that it happens in parallel with the query for the viewer_object. 
        vc_q = models.ViewedProfileCounter.query()
        vc_q = vc_q.filter(models.ViewedProfileCounter.owner_profile == displayed_key)
        viewed_profile_counter_object_future = vc_q.get_async() # note async - this is a "future", not an object
        
        # Check if the database already has stored an entry for the viewer looking at the displayed profile
        vt_q = models.ViewerTracker.query()
        vt_q = vt_q.filter(models.ViewerTracker.displayed_profile == displayed_key)
        vt_q = vt_q.filter(models.ViewerTracker.viewer_profile == viewer_key)
        viewer_tracker_object = vt_q.get()
        
        if viewer_tracker_object:
            last_view_time = viewer_tracker_object.view_time 
            viewer_tracker_object.view_time = datetime.datetime.now()
            is_a_new_viewer = False
        else:
            # create a new object
            last_view_time = datetime.datetime.min
            viewer_tracker_object = models.ViewerTracker()
            viewer_tracker_object.displayed_profile = displayed_key
            viewer_tracker_object.viewer_profile = viewer_key
            is_a_new_viewer = True
            
        viewer_tracker_object.put()
        
        # Now deal with the viewed_profile_counter_object, which tracks how many other people have viewed a particular profile.
        write_profile_counter_object = False
        viewed_profile_counter_object = viewed_profile_counter_object_future.get_result()
            
        if is_a_new_viewer:
            viewed_profile_counter_object.count_num_unique_views += 1
            write_profile_counter_object = True
        
        if last_view_time < viewed_profile_counter_object.last_check_time:
            # We only want to count each viewer a single time in the "num_views_since_last_check" field.
            # Therefore, if the viewer profile last looked at the displayed profile some time before 
            # the displayed profile looked at "profile views", then we increase the value.
            viewed_profile_counter_object.num_views_since_last_check  += 1
            write_profile_counter_object = True
         
        if write_profile_counter_object:
            viewed_profile_counter_object.put()
        
        
    except:
        error_reporting.log_exception(logging.critical)
        

def get_total_unique_number_of_views_of_profile(viewed_profile_counter_key):
    if not viewed_profile_counter_key:
        return 0
    
    viewed_profile_counter = viewed_profile_counter_key.get()
    return viewed_profile_counter.count_num_unique_views

def get_number_of_profile_views_since_last_check(viewed_profile_counter_key):
    if not viewed_profile_counter_key:
        return 0
    
    viewed_profile_counter = viewed_profile_counter_key.get()
    return viewed_profile_counter.num_views_since_last_check

def reset_number_of_profile_views_since_last_check(viewed_profile_counter_key):
    
    if not viewed_profile_counter_key:
        return 0
    viewed_profile_counter = viewed_profile_counter_key.get()
    viewed_profile_counter.last_check_time = datetime.datetime.now()
    viewed_profile_counter.num_views_since_last_check = 0
    viewed_profile_counter.put()
    

def get_profile_keys_list_from_viewer_tracker_object_list(viewer_tracker_object_list):
    
    # loop over the list of viewer_tracker_objects, and return a list of the corresponding 
    # UserModel objects keys. 
    
    viewer_profile_keys_list = []
    for viewer_tracker_object in viewer_tracker_object_list:
        viewer_profile_keys_list.append(viewer_tracker_object.viewer_profile)
        
    return viewer_profile_keys_list
        
def get_list_of_profile_views(profile_key, owner_is_vip, paging_cursor):
    
    # get the list of proviles that have looked at the "profile_key" profile. (ie. owner_profile == profile_key)
    
    if owner_is_vip: 
        # If they are VIP, then the will see all of the people that have viewed their profile in the past 3 months
        num_profiles_to_get = PAGESIZE
    else:
        num_profiles_to_get = MAX_PROFILE_VIEWS_TO_SHOW_TO_NON_VIP    
        paging_cursor = None

    # Check if the database already has stored an entry for the viewer looking at the displayed profile
    vt_q = models.ViewerTracker.query()
    vt_q = vt_q.order(-models.ViewerTracker.view_time)
    vt_q = vt_q.filter(models.ViewerTracker.displayed_profile == profile_key)

    if paging_cursor:
        (viewer_tracker_object_list, new_cursor, more_results) = vt_q.fetch_page(num_profiles_to_get, start_cursor = paging_cursor)
    else:
        (viewer_tracker_object_list, new_cursor, more_results) = vt_q.fetch_page(num_profiles_to_get)        
        
    if not owner_is_vip:
        new_cursor = None
        more_results = False
    
    viewer_profile_keys_list = get_profile_keys_list_from_viewer_tracker_object_list(viewer_tracker_object_list)
    
    return (viewer_profile_keys_list, new_cursor, more_results)


def generate_html_for_profile_views(request):
    
    # Generates the display html that shows which other members have viewed the current users profile. 
    
    try:
        userobject =  utils_top_level.get_userobject_from_request(request)
        
        if not userobject:
            generated_html = ''
            
        else:
            owner_key = userobject.key
            owner_uid = owner_key.urlsafe()
            display_online_status = utils.do_display_online_status(owner_uid)
            owner_is_vip = utils.owner_is_vip(owner_uid)
            
            generated_title = header_html = "%s." % ugettext("Members that have viewed your profile (most recent are shown first)") % {'username' : userobject.username}
            generated_html_before_form = ''
    
            viewed_profile_counter_object = userobject.viewed_profile_counter_ref.get()
    
            last_check_time_str = utils.get_date_or_time_in_current_language(viewed_profile_counter_object.last_check_time)
            num_views_since_last_check = viewed_profile_counter_object.num_views_since_last_check
            unique_views_since_date_str = utils.get_date_or_time_in_current_language(viewed_profile_counter_object.unique_views_since_date)
            count_num_unique_views = viewed_profile_counter_object.count_num_unique_views
            
            generated_html_before_form += u'<div class="cl-clear"></div>\n'
            generated_html_before_form += '<ul>\n'
            
            if (viewed_profile_counter_object.last_check_time != datetime.datetime.min):
                # if they have never checked who has viewed their profile, then this information is idential to the 
                # value presented in the unique_views_since_date_str, and could be confusing - just eliminate it.
                generated_html_before_form += "<li>%s</li>\n" % ugettext("""Your profile has been viewed by %(num_views_since_last_check)s members since you last checked %(last_check_time_str)s. 
                """) % {
                    'num_views_since_last_check' : num_views_since_last_check, 
                    'last_check_time_str' : last_check_time_str}
            
            generated_html_before_form += "<li>%s</li>\n" % ugettext("""
            %(count_num_unique_views)s members have viewed your profile since %(unique_views_since_date_str)s
            """) % {
                'count_num_unique_views' : count_num_unique_views,
                'unique_views_since_date_str' : unique_views_since_date_str,}
            
            
            if not owner_is_vip:
                assert(MAX_PROFILE_VIEWS_TO_SHOW_TO_NON_VIP == 1) # if this number is changed, we need to change the error message below
                generated_html_before_form += "<li>%s</li>" % ugettext("As a free (non-VIP) member of %(app_name)s you can only see the last person that viewed your profile") % {
                    'app_name' : site_configuration.APP_NAME}
                # make sure that we don't show negative number of people that have viewed the profile
                upgrade_to_vip_text = ugettext("Upgrade to VIP")
                vip_status_link = '<a class="cl-see_all_vip_benefits" href="#">%s</a>' % upgrade_to_vip_text
                generated_html_before_form += "<li>%s</li>\n" % (
                    ugettext("""%(vip_status_link)s to see all %(count_num_unique_views)s members that have viewed your 
                    profile since %(unique_views_since_date_str)s""") % {
                        'vip_status_link' : vip_status_link, 
                        'count_num_unique_views' : count_num_unique_views,
                        'unique_views_since_date_str' : unique_views_since_date_str,})
                
            generated_html_before_form += "</ul>\n"
                
            generated_html_hidden_variables = ''
            generated_html_top_next_button = ''
            generated_html_bottom_next_button = ''  
            
            post_action = "/%s/show_profile_views/" % (request.LANGUAGE_CODE)
            generated_html_top = display_profiles_summary.generate_summary_html_top(header_html)
            
            generated_html_open_form = display_profiles_summary.generate_summary_html_open_form(post_action)        
            generated_html_close_form = display_profiles_summary.generate_summary_html_close_form()
            
            cursor_str = request.GET.get('profile_views_cursor',None)
            paging_cursor = Cursor(urlsafe = cursor_str)
            
            (viewer_profile_keys_list, new_cursor, more_results) = get_list_of_profile_views(userobject.key, owner_is_vip, paging_cursor)            
            
            generated_html_body = display_profiles_summary.generate_html_for_list_of_profiles(request, userobject, viewer_profile_keys_list, 
                                                                                              display_online_status)
            
    
                                                                                            
            if more_results:
                generated_html_hidden_variables = \
                                    u'<input type=hidden id="id-profile_views_cursor" name="profile_views_cursor" \
                                    value="%(profile_views_cursor)s">\n' % {'profile_views_cursor': new_cursor.urlsafe()}           
                (generated_html_top_next_button, generated_html_bottom_next_button) = display_profiles_summary.generate_next_button_html()
                
            
            
            generated_html =   generated_html_top + generated_html_before_form + generated_html_open_form + generated_html_hidden_variables + generated_html_top_next_button + \
                                   generated_html_body + generated_html_bottom_next_button + generated_html_close_form
                            
            # reset the counter that tells the user how many "new" viewers of their profile there have been since the last check.
            reset_number_of_profile_views_since_last_check(userobject.viewed_profile_counter_ref)
            
        
        return rendering.render_main_html(request, generated_html, userobject, page_title = generated_title, 
                                          refined_links_html = '', show_social_buttons = True,
                                          page_meta_description = '')
        
    except:
        error_reporting.log_exception(logging.critical)
        return rendering.render_main_html(request, 'Error')