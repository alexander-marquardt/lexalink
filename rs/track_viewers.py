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


import models
from google.appengine.ext import db
from rs import utils, models, error_reporting
import datetime, logging

def store_viewer_in_displayed_profile_viewer_tracker(viewer_uid, displayed_uid):
    """ Keep track of which profiles "viewers" have viewed other "displayed" profiles  """

    try:
        viewer_key = db.Key(viewer_uid)
        displayed_key = db.Key(displayed_uid)
        
        # Get the counter ojbect for the profile that is being viewed ie. the "displayed" profile's counter
        # We get this asynchronously so that it happens in parallel with the query for the viewer_object. 
        vc_q = models.ViewedCounter.query()
        vc_q = vc_q.filter(models.ViewedCounter.displayed_profile == displayed_key)
        viewed_counter_object_future = vc_q.get_async() # note async - this is a "future", not an object
        
        # Check if the database already has stored an entry for the viewer looking at the displayed profile
        vo_q = models.ViewerTracker.query()
        vo_q = vo_q.filter(models.ViewerTracker.displayed_profile == viewer_key)
        vo_q = vo_q.filter(models.ViewerTracker.viewer_profile == displayed_key)
        viewer_tracker_object = vo_q.get()
        
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
            viewed_counter_object.viewed_counter += 1
            viewed_counter_object.put()
        
        
    except:
        error_reporting.log_exception(logging.critical, error_message = error_message)
        
