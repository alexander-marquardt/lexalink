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

from rs import error_reporting, utils_top_level, models



                
def get_polling_response_time_from_current_status(PresenceClass, online_status):
    # we verify the expected polling response time depending on the status of the user. This is highly coordinated
    # with the client side javascript. Ie. if the client is rapidly polling, then we can diagnose a logout/dropped
    # connection much faster than if the browser is in "Away" state, and only polls every 10 minutes. 
    
    if online_status == PresenceClass.ACTIVE:
        return PresenceClass.MAX_ACTIVE_POLLING_RESPONSE_TIME_FROM_CLIENT
    elif online_status == PresenceClass.IDLE:
        return PresenceClass.MAX_IDLE_POLLING_RESPONSE_TIME_FROM_CLIENT
    elif online_status == PresenceClass.AWAY:
        return PresenceClass.MAX_AWAY_POLLING_RESPONSE_TIME_FROM_CLIENT
    else:
        # for example, if user status is "enabled" this will trigger an error, since "enabled" status should
        # never be stored in the database (see description of ChatFriendTracker in models.py for more information)
        error_reporting.log_exception(logging.critical, error_message = "online_status = %s" % online_status)
        return 0
    

def get_online_status(PresenceClass, owner_uid):
    # Check if a user is online - this can be verified by checking the time of the last polling/checkin
    # and by checking that they have not logged-out (either from chat or from the website completely)
    
    try:
        # check the memcache-only friend tracker login time, since this gives us an accurate reading of the
        # users activity
        presence_tracker_memcache_key = PresenceClass.STATUS_MEMCACHE_TRACKER_PREFIX + owner_uid
        presence_tracker = utils_top_level.deserialize_entities(memcache.get(presence_tracker_memcache_key))
        if presence_tracker is not None:

            if presence_tracker.online_status == PresenceClass.DISABLED:
                return PresenceClass.DISABLED # indicates that the user has intentionally logged-off
            else:
                polling_response_time = get_polling_response_time_from_current_status(PresenceClass, presence_tracker.online_status)
                if presence_tracker.connection_verified_time +\
                   datetime.timedelta(seconds = polling_response_time) >= datetime.datetime.now() :
                    return presence_tracker.online_status
                else:
                    return PresenceClass.TIMEOUT
        else:
            # we don't know their status, but return TIMEOUT which means they haven't checked in in a long time (and they will
            # therefore not show up in their friends lists until their status is changed to something other than TIMEOUT).
            return PresenceClass.TIMEOUT
        
    except:
        error_reporting.log_exception(logging.critical)
        return PresenceClass.DISABLED
    
