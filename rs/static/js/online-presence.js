/*
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
*/

var online_presence_object = new function() {

    var online_presence_self = this;


    update_user_presence_status_on_server = function(new_status) {
        $.ajax({
            type: 'post',
            url:  '/rs/user_presence/update_user_presence_on_server/' + rnd() + "/",
            data: {'user_online_presence': new_status},
            success: function (response) {
                if (response == "expired_session") {
                    // if session is expired, send to login screen if they try to change their chat online status
                    self.location = "/";
                }
            },
            error: function(jqXHR, textStatus, errorThrown) {
                report_ajax_error(textStatus, errorThrown, "update_user_presence_status_on_server");
            }
        });
    }



    var track_user_activity_for_online_status = function () {

        try {
            // setup the timers for detecting user online/idle status
            idle_params = {};
            idle_params.idle_timeout = online_presence_self.inactivity_time_before_idle;
            idle_params.away_timeout = online_presence_self.inactivity_time_before_away;

            idle_params.onIdle = function() {
                update_user_presence_status_on_server("user_presence_idle");
                online_presence_self.user_presence_status = "user_presence_idle";
            };
            idle_params.onAway = function() {
                update_user_presence_status_on_server("user_presence_away");
                online_presence_self.user_presence_status = "user_presence_away";

            };
            idle_params.onBack = function(isIdle, isAway) {
                update_user_presence_status_on_server("user_presence_active");
                online_presence_self.user_presence_status = "user_presence_active";                
            };

            chatbox_idle_object = IdleClass(idle_params);
            return chatbox_idle_object;

        } catch(err) {
            report_try_catch_error( err, "track_user_activity_for_online_status");
        }
    }


    this.initialize = function (
        max_active_polling_delay,
        idle_polling_delay,
        away_polling_delay,
        inactivity_time_before_idle,
        inactivity_time_before_away)
    {
        online_presence_self.user_presence_status = "user_presence_active"

        online_presence_self.max_active_polling_delay = max_active_polling_delay * 1000;
        online_presence_self.idle_polling_delay = idle_polling_delay * 1000;
        online_presence_self.away_polling_delay = away_polling_delay * 1000;
        online_presence_self.inactivity_time_before_idle = inactivity_time_before_idle * 1000;
        online_presence_self.inactivity_time_before_away = inactivity_time_before_away * 1000;

        // keep a pointer to the chatbox_idle object so that it doesn't get cleaned up
        online_presence_self.chatbox_idle_object = track_user_activity_for_online_status();

    }
}


function launch_user_presence() {
    
    try {
        online_presence_object.initialize(
            template_user_presence_vars.max_active_polling_delay,
            template_user_presence_vars.idle_polling_delay,
            template_user_presence_vars.away_polling_delay,
            template_user_presence_vars.inactivity_time_before_idle,
            template_user_presence_vars.inactivity_time_before_away)

    } catch(err) {
        report_try_catch_error( err, "launch_chatboxes");
    }
}