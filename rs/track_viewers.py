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

from django.utils.translation import ugettext

import models
from google.appengine.ext import ndb
from google.appengine.datastore.datastore_query import Cursor
from rs import utils, models, error_reporting, display_profiles_summary, utils_top_level
import rendering
import datetime, logging

PAGESIZE = 6

def store_viewer_in_displayed_profile_viewer_tracker(viewer_uid, displayed_uid):
    """ Keep track of which profiles "viewers" have viewed other "displayed" profiles  """

    logging.info("*************** store_viewer_in_displayed_profile_viewer_tracker")
    try:
        viewer_key = ndb.Key(urlsafe = viewer_uid)
        displayed_key = ndb.Key(urlsafe = displayed_uid)
        
        # Get the counter ojbect for the profile that is being viewed ie. the "displayed" profile's counter
        # We get this asynchronously so that it happens in parallel with the query for the viewer_object. 
        vc_q = models.ViewedCounter.query()
        vc_q = vc_q.filter(models.ViewedCounter.displayed_profile == displayed_key)
        viewed_counter_object_future = vc_q.get_async() # note async - this is a "future", not an object
        
        # Check if the database already has stored an entry for the viewer looking at the displayed profile
        vt_q = models.ViewerTracker.query()
        vt_q = vt_q.filter(models.ViewerTracker.displayed_profile == displayed_key)
        vt_q = vt_q.filter(models.ViewerTracker.viewer_profile == viewer_key)
        viewer_tracker_object = vt_q.get()
        
        if viewer_tracker_object:
            viewer_tracker_object.view_time = datetime.datetime.now()
            is_a_new_viewer = False
        else:
            # create a new object
            viewer_tracker_object = models.ViewerTracker()
            viewer_tracker_object.displayed_profile = displayed_key
            viewer_tracker_object.viewer_profile = viewer_key
            is_a_new_viewer = True
            
        viewer_tracker_object.put()
        
        viewed_counter_object = viewed_counter_object_future.get_result()
        if not viewed_counter_object:
            viewed_counter_object = models.ViewedCounter()
        
        if is_a_new_viewer:
            viewed_counter_object.num_views += 1
            viewed_counter_object.put()
        
        
    except:
        error_reporting.log_exception(logging.critical)
        

def get_number_of_views_of_profile(profile_key):
    
    vc_q = models.ViewedCounter.query()
    vc_q = vc_q.filter(models.ViewedCounter.displayed_profile == profile_key)    
    viewed_counter = c_q.get()
    num_views = viewer_counter.num_views
    return num_views


def get_profile_keys_list_from_viewer_tracker_object_list(viewer_tracker_object_list):
    
    viewer_profile_keys_list = []
    for viewer_tracker_object in viewer_tracker_object_list:
        viewer_profile_keys_list.append(viewer_tracker_object.viewer_profile)
        
    return viewer_profile_keys_list
        
def get_list_of_profile_views(profile_key, paging_cursor):
    
    # get the list of proviles that have looked at the "profile_key" profile. (ie. displayed_profile == profile_key)
    
    # Check if the database already has stored an entry for the viewer looking at the displayed profile
    vt_q = models.ViewerTracker.query()
    vt_q = vt_q.order(-models.ViewerTracker.view_time)
    vt_q = vt_q.filter(models.ViewerTracker.displayed_profile == profile_key)

    if paging_cursor:
        (viewer_tracker_object_list, new_cursor, more_results) = vt_q.fetch_page(PAGESIZE, start_cursor = paging_cursor)
    else:
        (viewer_tracker_object_list, new_cursor, more_results) = vt_q.fetch_page(PAGESIZE)        
        
    
    viewer_profile_keys_list = get_profile_keys_list_from_viewer_tracker_object_list(viewer_tracker_object_list)
    
    return (viewer_profile_keys_list, new_cursor, more_results)


def generate_html_for_profile_views(request):
    
    try:
        userobject =  utils_top_level.get_userobject_from_request(request)
        
        if not userobject:
            return ''
        
        owner_uid = userobject.key.urlsafe()
        
        generated_title = generated_header = ugettext("Profile views")
        generated_html_hidden_variables = ''
        generated_html_top_next_button = ''
        generated_html_bottom_next_button = ''    
        post_action = "/%s/profile_views/" % (request.LANGUAGE_CODE)
        generated_html_top = display_profiles_summary.generate_summary_html_top(post_action, generated_header)
        generated_html_bottom = display_profiles_summary.generate_summary_html_bottom()
        display_online_status = utils.do_display_online_status(owner_uid)
        
        cursor_str = request.GET.get('profile_views_cursor',None)
        paging_cursor = Cursor(urlsafe = cursor_str)
        
        (viewer_profile_keys_list, new_cursor, more_results) = get_list_of_profile_views(userobject.key, paging_cursor)
        generated_html_body = display_profiles_summary.generate_html_for_list_of_profiles(request, userobject, viewer_profile_keys_list, 
                                                                                          display_online_status)
        
        if more_results:
            generated_html_hidden_variables = \
                                u'<input type=hidden id="id-profile_views_cursor" name="profile_views_cursor" \
                                value="%(profile_views_cursor)s">\n' % {'profile_views_cursor': new_cursor.urlsafe()}           
            (generated_html_top_next_button, generated_html_bottom_next_button) = display_profiles_summary.generate_next_button_html()
            
        
        generated_html =  generated_html_top + generated_html_hidden_variables + generated_html_top_next_button + \
                       generated_html_body + generated_html_bottom_next_button + generated_html_bottom
        
        return rendering.render_main_html(request, generated_html, userobject, page_title = generated_title, 
                                          refined_links_html = '', show_social_buttons = True,
                                          page_meta_description = '')
        
    except:
        error_reporting.log_exception(logging.critical)
        return rendering.render_main_html(request, 'Error')