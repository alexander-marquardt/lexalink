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

# This module supports the reporting of the online presence. There are two types of 
# presence, "chat presence" (user is logged into the chat), and "user presence" (user
# is logged into the website). This module supports reporting of both types of presence.


from google.appengine.api import memcache

import logging, datetime

from rs import error_reporting, utils_top_level, models, constants

                
def get_polling_response_time_from_current_status(user_presence_status):
    # we verify the expected polling response time depending on the status of the user. This is highly coordinated
    # with the client side javascript. Ie. if the client is rapidly polling, then we can diagnose a logout/dropped
    # connection much faster than if the browser is in "Away" state, and only polls every 10 minutes. 
    
    constants.OnlinePresence = constants.OnlinePresence
    
    if user_presence_status == constants.OnlinePresence.ACTIVE:
        return constants.OnlinePresence.MAX_ACTIVE_POLLING_RESPONSE_TIME_FROM_CLIENT
    elif user_presence_status == constants.OnlinePresence.IDLE:
        return constants.OnlinePresence.MAX_IDLE_POLLING_RESPONSE_TIME_FROM_CLIENT
    elif user_presence_status == constants.OnlinePresence.AWAY:
        return constants.OnlinePresence.MAX_AWAY_POLLING_RESPONSE_TIME_FROM_CLIENT
    else:
        # for example, if user status is "enabled" this will trigger an error, since "enabled" status should
        # never be stored in the database (see description of ChatFriendTracker in models.py for more information)
        error_reporting.log_exception(logging.critical, error_message = "Error: user_presence_status = %s" % user_presence_status)
        return 0
    

def get_online_status(owner_uid):
    # Check if a user is online - this can be verified by checking the time of the last polling/checkin
    # and comparing this to the maximum expected polling delay
    
    try:
        presence_tracker_memcache_key = constants.OnlinePresence.STATUS_MEMCACHE_TRACKER_PREFIX + owner_uid
        presence_tracker = utils_top_level.deserialize_entities(memcache.get(presence_tracker_memcache_key))
        user_presence_status = constants.OnlinePresence.OFFLINE
        if presence_tracker is not None:

            if (presence_tracker.user_presence_status != constants.OnlinePresence.OFFLINE):
                
                polling_response_time = get_polling_response_time_from_current_status(presence_tracker.user_presence_status)
                if presence_tracker.connection_verified_time +\
                   datetime.timedelta(seconds = polling_response_time) >= datetime.datetime.now() :
                    user_presence_status = presence_tracker.user_presence_status
                else:
                    # The user has timed-out, they are now considered offline
                    user_presence_status = constants.OnlinePresence.OFFLINE
                    update_online_status(owner_uid, user_presence_status)
                    
        else:
            user_presence_status = constants.OnlinePresence.OFFLINE
                    
        return user_presence_status
        
    except:
        error_reporting.log_exception(logging.critical)
        return constants.OnlinePresence.OFFLINE
    
    
def update_online_status(owner_uid, user_presence_status):

    # presence_tracker is indexed by the uid of the owner - this structure is used for keeping track of
    # the last time that the user has "checked-in" -- this is necessary for understanding if the user is 
    # enabled/idle/away/logged off. 
    #
    # user_status: ACTIVE, IDLE, AWAY
    #
    # presence_tracker should be pulled out memcache. 
    
    try:

        assert(user_presence_status)
        
        presence_tracker_memcache_key = constants.OnlinePresence.STATUS_MEMCACHE_TRACKER_PREFIX + owner_uid
        presence_tracker = utils_top_level.deserialize_entities(memcache.get(presence_tracker_memcache_key))
        
        if presence_tracker is None:
            presence_tracker = models.OnlineStatusTracker()
            
        presence_tracker.user_presence_status = user_presence_status

        presence_tracker.connection_verified_time = datetime.datetime.now()
        memcache.set(presence_tracker_memcache_key, utils_top_level.serialize_entities(presence_tracker))  
            
    except:
        error_reporting.log_exception(logging.critical)
                
                
def get_chat_boxes_status(owner_uid):
    # Check if the chatboxes for the user indicated by owner_uid are currenly eneabled (open) or disabled (closed).  
    
    chat_boxes_status_memcache_key = constants.ChatBoxStatus.CHAT_BOX_STATUS_MEMCACHE_TRACKER_PREFIX  + owner_uid
    chat_boxes_status = memcache.get(chat_boxes_status_memcache_key)    
    
    if chat_boxes_status is None:
        chat_boxes_status = constants.ChatBoxStatus.IS_ENABLED
        
    return chat_boxes_status
    
    