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

# This module is used for tracking the online status of each user so that we can display to other users if they are currently
# active, idle, away, disconnected .. etc. 
# The "user presence" is different than "chat presence" in that "chat presence" is only used for tracking the status
# of the users chat connection, while "user presence" is more general, and applies to weather the user is actively using
# the website.

import logging
from django.utils import simplejson
from django import http

from rs import constants, channel_support, online_presence_support, error_reporting

class UserPresence(object): 
    # Define the values that will be used to define the chat online presence for each user that has 
    # their chatboxes open.
    
    
    DISABLED = "Disabled is not currently used for user precence tracking" 
    ENABLED = "Enabled is not currently used for user precence tracking" 

    # When chat is enabled, user status can be one of the following values.
    ACTIVE = "user_presence_active" # user is actively using the website (not only chat, but also navigating or moving the mouse)
    IDLE = "user_presence_idle"     # user has not moved the cursor across the page in INACTIVITY_TIME_BEFORE_IDLE seconds
    AWAY = "user_presence_away"    # user has not moved the cursor across the page in INACTIVITY_TIME_BEFORE_AWAY seconds
    # timeout is when the user has been inactive for so long that they are effectively offline so they will
    # not appear as online in contact lists  -- but they will go "active" if they do anything    
    TIMEOUT = "user_presence_timeout" 
    
    STATUS_MEMCACHE_TRACKER_PREFIX = "_user_presence_memcache_tracker_" + constants.FORCE_UPDATE_USER_PRESENCE_MEMCACHE_STRING

    # taking into account javascript single-threadedness and client loading, polling does not always happen as fast as we scheduled.
    MAX_ACTIVE_POLLING_RESPONSE_TIME_FROM_CLIENT = 1.5 * constants.UserPresenceConstants.ACTIVE_POLLING_DELAY_IN_CLIENT  
    MAX_IDLE_POLLING_RESPONSE_TIME_FROM_CLIENT = 1.5 * constants.UserPresenceConstants.IDLE_POLLING_DELAY_IN_CLIENT # amount of time server waits for a response before marking user as offline
    MAX_AWAY_POLLING_RESPONSE_TIME_FROM_CLIENT = 1.5 * constants.UserPresenceConstants.AWAY_POLLING_DELAY_IN_CLIENT # amount of time server waits for a response before marking user as offline

        
def update_user_presence(request):
    
    # Store the user presence information in the appropriate data structures (currently in memcache)
   
    try:
    
        if 'userobject_str' in request.session:
            owner_uid = request.session['userobject_str']            
        
            if request.method == 'POST':
                user_online_presence = request.POST.get('user_online_presence', '')
                assert(user_online_presence)

            channel_support.update_online_status(UserPresence, owner_uid, user_online_presence)
            response = "OK"
            
        else:
            # Users session has expired - just ignore the updates. (Note: we do not upate their online 
            # status to TIMEOUT here, since they may have other sessions open in another browser, and we
            # don't want to interfear with those other updates)
            response = "expired_session"
            
        return http.HttpResponse(response)
            
    except:
        error_reporting.log_exception(logging.critical)           
        return http.HttpResponseBadRequest("Error");
        

def get_user_presence_status(owner_uid):
    # Get the current status of the user
    return online_presence_support.get_online_status(UserPresence, owner_uid)