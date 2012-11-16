
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
/* Contains functions for setting up a real-time channel for communicating with the server
   Copyright Alexander Marquardt / Lexabit Inc. March 19 2012*/






var chan_utils = new function () {
    // Notice the "new" in the function declaration - this creates an object as opposed to a class.

    try {

        //***********************************************************
        /* Variables that are visible to all methods in this object */
        var chan_utils_self = this;

        //********************************
        /* Private function declarations */

        var initialization = function(owner_uid, owner_username, max_polling_delay, idle_polling_delay, away_polling_delay, idle_timeout, away_timeout) {
            // initialize the dialog box that will be used for alerting the user to unknown conditions

            try {

                chan_utils_self.owner_uid = owner_uid; // set the object variable to the passed in value (chan_utils_self refers to the chan_utils object)
                chan_utils_self.owner_username = owner_username;

                chan_utils_self.initial_in_focus_polling_delay = 750; // when the chatbox input has focus, we poll at a fast speed (up until they go "idle" or leave focus)
                chan_utils_self.initial_message_polling_delay = 2500; //how often to poll for new messages when focus is not in the chatbox input
                chan_utils_self.message_polling_delay_ceiling = max_polling_delay * 1000; // convert seconds to ms

                // Note, the decay multipliers are only used if the user is "active" (not "idle" or "away"). If they are "idle" or "away", a constant (slow) polling
                // rate is currently used.
                chan_utils_self.focusout_and_active_decay_multiplier = 1.5; // each re-schedule is X% slower than the last (when the focus is not in the chatbox)
                chan_utils_self.decay_multiplier = chan_utils_self.focusout_and_active_decay_multiplier;
                chan_utils_self.focusin_and_active_decay_multiplier = 1.1; // if the user has focus in the chatbox, we decay the polling frequency much less.

                chan_utils_self.idle_polling_delay = idle_polling_delay * 1000;
                chan_utils_self.away_polling_delay = away_polling_delay * 1000;
                chan_utils_self.current_message_polling_delay = chan_utils_self.initial_message_polling_delay;

                chan_utils_self.idle_timeout = idle_timeout * 1000;
                chan_utils_self.away_timeout = away_timeout * 1000;

                chan_utils_self.chat_message_timeoutID = null; // used for cancelling a re-scheduled poll for new messages
                chan_utils_self.last_update_time_string_dict = {}; // shortcut for new Object() - uid is the key, and value is last update time
                //chan_utils_self.last_update_chat_message_id_dict = {}; // shortcut for new Object() - uid is the key, and value is DB/memcache ID of the last update

                chan_utils_self.user_online_status = "active";

                chan_utils_self.polling_is_locked_mutex = false; // use to ensure that we only have one polling request at a time - true when polling, false when free
                chan_utils_self.sending_message_is_locked_mutex = false; // when we are sending a message, we prevent processing of polling responses
                                                               // since the response to the send_message will be a duplicate/redundant
                chan_utils_self.string_of_messages_in_queue = '';

                chan_utils_self.list_of_open_chat_groups_members_boxes = [];
                chan_utils_self.time_to_pass_before_updating_list_of_open_chat_groups_members_boxes = 3 * 1000; // every 3 seconds
                chan_utils_self.last_time_we_updated_chat_groups_members_boxes = ( new Date()).getTime();
                chan_utils_self.list_of_usernames_in_each_group = {}; // dictionary indexed by group_id, which contains lists of the usernames -- this is used for checking if list has changed so we can highlight it
            }
            catch(err) {
                report_try_catch_error( err, "initialization");
            }
        };


        var internet_connection_is_down = function () {
            // this function is called if an ajax call fails (which indicates that the internet connection is down)
            try {
                var warning_message = $("#id-internet-down-dialog").text();
                $("#main").chatbox("option", "boxManager").refreshBox(warning_message);
            } catch(err) {
                report_try_catch_error( err, "internet_connection_is_down");
            }
        };

        var internet_connection_is_up = function () {
            // Remove dialog box warning that internet is down.
        };


        var session_is_open = function () {
            // able to connect to server and session is open. Remove dialog box.
        };



        var process_json_most_recent_chat_messages = function(json_response) {

            try{

                var new_one_on_one_message_received = false;

                if (json_response.hasOwnProperty('user_online_status')) {
                    if (json_response.user_online_status == "offline" || json_response.user_online_status == "expired_session") {
                        // the user has indicated that he wishes to go offline (or has expired session). If we have received this message,
                        // we are running in a javascript session that is still actively polling, and is therefore
                        // not offline on the client side. We must stop the client from polling in the current window.
                        chan_utils_self.execute_go_offline_on_client();
                    }
                }


                if (json_response.hasOwnProperty('conversation_tracker')) {


                    var conversation_tracker_dict = json_response.conversation_tracker;
                    for (var other_uid in conversation_tracker_dict) {
                        var array_of_chat_msg_time_strings = conversation_tracker_dict[other_uid].chat_msg_time_string_arr;
                        var chatbox_title = conversation_tracker_dict[other_uid].chatbox_title;
                        var box_is_minimized = conversation_tracker_dict[other_uid].box_is_minimized;
                        var type_of_conversation = conversation_tracker_dict[other_uid].type_of_conversation;
                        var highlight_box_enabled = true;





                        if (other_uid != "main" && other_uid != "groups") {

                            if (chan_utils_self.last_update_time_string_dict.hasOwnProperty(other_uid)) {
                                // the last_update_time_string_array has been previously loaded, and therefore
                                // we want to highlight/bounce the box when a new message is received
                                highlight_box_enabled = true;
                            } else {
                                // This is a totally new chatbox (new page load, or user opened new box), and we don't need/want to highlight it.
                                highlight_box_enabled = false;
                            }

                            chan_utils_self.last_update_time_string_dict[other_uid] = conversation_tracker_dict[other_uid].last_update_time_string;

                            // calling addBox just makes sure that it exists
                            chatboxManager.addBox(other_uid, chatbox_title, true, true, false, type_of_conversation,
                                    conversation_tracker_dict[other_uid]['nid'], conversation_tracker_dict[other_uid]['url_description']);

                            // load the message history into the chatbox
                            for (var msg_time_idx in array_of_chat_msg_time_strings) {
                                var msg_time_str = array_of_chat_msg_time_strings[msg_time_idx];
                                var sender_username = conversation_tracker_dict[other_uid].sender_username_dict[msg_time_str];
                                var chat_msg_text = conversation_tracker_dict[other_uid].chat_msg_text_dict[msg_time_str];
                                $("#" + other_uid).chatbox("option", "boxManager").addMsg(sender_username, chat_msg_text, highlight_box_enabled);

                                if (type_of_conversation == "one_on_one") {
                                    // we only start faster polling if a one_on_one message is received - since this is a direct communication
                                    // to the user, while group messages should not trigger faster polling.
                                    new_one_on_one_message_received = true;
                                }
                            }
                        }

                        if (box_is_minimized) {
                            $("#"+ other_uid).chatbox("option", "boxManager").minimizeBox();
                        } else {
                            $("#"+ other_uid).chatbox("option", "boxManager").maximizeBox();
                        }

                    }
                }

                var message;
                if (json_response.hasOwnProperty('contacts_info_dict')) {
                    if (!$.isEmptyObject(json_response.contacts_info_dict)) {

                        updateChatControlBox("main", json_response.contacts_info_dict);
                        updateUserChatBoxTitles(json_response.contacts_info_dict);
                    }
                    else {
                        message = $("#id-no-contacts-text").text();
                        $("#main").chatbox("option", "boxManager").refreshBox(message);
                    }
                }

                if (json_response.hasOwnProperty('chat_groups_dict')) {
                    if (!$.isEmptyObject(json_response.chat_groups_dict)) {

                        var chat_groups_dict = json_response.chat_groups_dict;
                        updateChatControlBox("groups", chat_groups_dict);
                        updateGroupChatBoxTitles(chat_groups_dict);
                    }
                    else {
                        message = $("#id-no-groups-text").text();
                        $("#groups").chatbox("option", "boxManager").refreshBox(message);
                    }
                }


                if (json_response.hasOwnProperty('chat_group_members')) {

                    for (var group_id in json_response.chat_group_members) {
                        var group_members_dict = json_response.chat_group_members[group_id];
                        var sorted_list_of_names_with_user_info = chan_utils_self.sort_user_or_groups_by_name(group_members_dict, false);

                        if (!chan_utils_self.list_of_usernames_in_each_group.hasOwnProperty(group_id)) {
                            chan_utils_self.list_of_usernames_in_each_group[group_id] = sorted_list_of_names_with_user_info;
                        }

                        if ( ! chan_utils_self.check_if_group_members_are_the_same(sorted_list_of_names_with_user_info, chan_utils_self.list_of_usernames_in_each_group[group_id])) {
                            chan_utils_self.list_of_usernames_in_each_group[group_id] = sorted_list_of_names_with_user_info;
                            $("#id-group_members-dialog-box-" + group_id).effect("highlight", {color:'#FFEEFF'}, 3000);
                        }

                        var display_list = chan_utils_self.displayAsListWithHrefs(group_id, sorted_list_of_names_with_user_info, true);
                        $("#id-group_members-dialog-box-" + group_id).html(display_list);
                    }
                }


                if (new_one_on_one_message_received) {
                    // reset the message polling delay to the initial value, since this user appears to now
                    // be involved in a conversation.
                    set_message_polling_timeout_and_schedule_poll(chan_utils_self.initial_message_polling_delay);
                }
            }
            catch(err) {
                report_try_catch_error( err, "process_json_most_recent_chat_messages");
            }
        };


        var set_message_polling_timeout_and_schedule_poll = function(current_message_polling_delay) {

            try {

                // we use a pseudo-exponentially increasing delay for controlling how often to poll the serever
                // because if a user is active, we want to poll more often, and if they have not done any action
                // we dramatically slow down the server polling - we can experimentally determine a good value
                clearTimeout(chan_utils_self.chat_message_timeoutID);

                if (chan_utils_self.user_online_status == "active") {
                    // for active user sessions, make sure that the delay has not exceeded the maximum, since
                    // we are growing the delay. For idle/away, this number is constant, and therefore
                    // we don't need to look at the ceiling or increase the value.
                    if (current_message_polling_delay > chan_utils_self.message_polling_delay_ceiling) {
                        current_message_polling_delay = chan_utils_self.message_polling_delay_ceiling;
                    } else {
                        chan_utils_self.current_message_polling_delay = current_message_polling_delay * chan_utils_self.decay_multiplier;
                    }
                }
                chan_utils_self.chat_message_timeoutID = setTimeout(poll_server_for_status_and_new_messages,current_message_polling_delay);

            } catch(err) {
                report_try_catch_error( err, "set_message_polling_timeout_and_schedule_poll");
            }
        };



        var poll_server_for_status_and_new_messages = function () {

            // polls the server for most recent chat messages - should re-schedule itself
            // on an exponentially declining schedule (exponentially increasing delay).

            try {

                var list_of_open_chat_groups_members_boxes_to_pass = [];
                var current_time = (new Date().getTime());
                var request_update = false;
                if (current_time - chan_utils_self.time_to_pass_before_updating_list_of_open_chat_groups_members_boxes >
                        chan_utils_self.last_time_we_updated_chat_groups_members_boxes ) {
                    chan_utils_self.last_time_we_updated_chat_groups_members_boxes = (new Date()).getTime();
                    // since we want to request new lists of group members, we must pass in the group_ids of the
                    // groups that we want updated.
                    list_of_open_chat_groups_members_boxes_to_pass = chan_utils_self.list_of_open_chat_groups_members_boxes;
                }

                var json_post_dict = {'last_update_time_string_dict' : chan_utils_self.last_update_time_string_dict,
                    //'last_update_chat_message_id_dict' : chan_utils_self.last_update_chat_message_id_dict,
                    'user_online_status': chan_utils_self.user_online_status,
                    'list_of_open_chat_groups_members_boxes' :  list_of_open_chat_groups_members_boxes_to_pass};
                var json_stringified_post = $.toJSON(json_post_dict);


                // prevent multiple polls from happening at the same time

                if (!chan_utils_self.polling_is_locked_mutex && !chan_utils_self.sending_message_is_locked_mutex) {
                    chan_utils_self.polling_is_locked_mutex = true;

                    $.ajax({
                        type: 'post',
                        url:  '/rs/channel_support/poll_server_for_status_and_new_messages/' + rnd() + "/",
                        contentType: 'json', // post data type
                        data: json_stringified_post,
                        dataType: 'json', // response type
                        success: function(json_response) {
                            if (!chan_utils_self.sending_message_is_locked_mutex) {
                                // only process this json response if we are not currently processing a send_message call.
                                process_json_most_recent_chat_messages(json_response);
                            }
                        },
                        error: function () {
                            internet_connection_is_down();
                        },
                        complete: function() {
                            if (chan_utils_self.user_online_status != "offline") {
                                // only poll if the user has not "logged off"  in this window or another window
                                set_message_polling_timeout_and_schedule_poll(chan_utils_self.current_message_polling_delay);
                                chan_utils_self.polling_is_locked_mutex = false;
                            }
                        }
                    });
                }
            } catch(err) {
                report_try_catch_error( err, "poll_server_for_status_and_new_messages");
            }
        };

        var track_user_activity_for_online_status = function () {

            try {
                // setup the timers for detecting user online/idle status
                bind_online_status_event_handlers();

                setIdleTimeout(chan_utils_self.idle_timeout);
                setAwayTimeout(chan_utils_self.away_timeout);

                document.onIdle = function() {
                    var new_main_title = $('#id-chat-contact-title-idle-text').text();
                    chatboxManager.changeOpacityOfAllBoxes(0.75);
                    if (chan_utils_self.user_online_status != "offline") { // only allow changes of activity status if user is "online"
                        chatboxManager.changeBoxtitle("main", new_main_title);
                        chan_utils_self.user_online_status = "idle";
                        chan_utils_self.current_message_polling_delay = chan_utils_self.idle_polling_delay;
                        chan_utils_self.update_user_online_status_on_server(chan_utils_self.user_online_status);

                    }
                };
                document.onAway = function() {
                    var new_main_title = $('#id-chat-contact-title-away-text').text();
                    chatboxManager.changeOpacityOfAllBoxes(0.25);
                    if (chan_utils_self.user_online_status != "offline") { // only allow changes of activity status if user is "online"
                        chatboxManager.changeBoxtitle("main", new_main_title);
                        chan_utils_self.user_online_status = "away";
                        chan_utils_self.current_message_polling_delay = chan_utils_self.away_polling_delay;
                        chan_utils_self.update_user_online_status_on_server(chan_utils_self.user_online_status);
                    }
                };
                document.onBack = function(isIdle, isAway) {
                    var new_main_title = $('#id-chat-contact-title-text').text();
                    chatboxManager.changeOpacityOfAllBoxes(1);
                    if (chan_utils_self.user_online_status != "offline") { // only allow changes of activity status if user is "online"
                        chatboxManager.changeBoxtitle("main", new_main_title);
                        chan_utils_self.user_online_status = "active";
                        chan_utils_self.update_user_online_status_on_server(chan_utils_self.user_online_status);
                        set_message_polling_timeout_and_schedule_poll(chan_utils_self.initial_message_polling_delay);
                    }
                };
            } catch(err) {
                report_try_catch_error( err, "track_user_activity_for_online_status");
            }
        };


        //*******************************
        /* Public function declarations */

        this.set_focusin_polling_delay = function () {
            try {
                // user has clicked the mouse (given focus) in the input for a chatbox
                chan_utils_self.current_message_polling_delay = chan_utils_self.initial_in_focus_polling_delay;
                chan_utils_self.decay_multiplier = chan_utils_self.focusin_and_active_decay_multiplier;
            } catch(err) {
                report_try_catch_error( err, "set_focusin_polling_delay");
            }
        };
        this.set_focusout_polling_delay = function () {
            try {
                // user has removed the focus from the chatbox input
                chan_utils_self.current_message_polling_delay = chan_utils_self.initial_message_polling_delay ;
                chan_utils_self.decay_multiplier = chan_utils_self.focusout_and_active_decay_multiplier ;
            } catch(err) {
                report_try_catch_error( err, "set_focusout_polling_delay");
            }
        };


        this.execute_go_offline_on_client = function () {
            try {
                // note: some of the server interaction is handled in the chatbox functions, since
                // we only want a *single* interaction with the server when the user clicks the
                // offline button. This function takes care of the rest of the functionality after
                // server has been informed of the new status.
                var offline_message = $('#id-chat-contact-main-box-offline-text').text();
                var new_main_title = $('#id-chat-contact-title-offline-text').text();
                $('#id-go-offline-button').hide();
                $('#id-go-online-button').show();
                chan_utils_self.user_online_status = "offline";

                chan_utils_self.stop_polling_server();
                chatboxManager.closeAllChatBoxes();
                $("#main").chatbox("option", "boxManager").hideChatboxContent();
                chatboxManager.changeBoxtitle("main", new_main_title);
                $("#main").chatbox("option", "boxManager").refreshBox(offline_message);
            } catch(err) {
                report_try_catch_error( err, "execute_go_offline_on_client");
            }
        };

        this.execute_go_online = function () {
            try {
                var new_main_title = $('#id-chat-contact-title-text').text();
                var loading_contacts_message = $('#id-chat-contact-main-box-loading-text').text();
                $('#id-go-online-button').hide();
                $('#id-go-offline-button').show();
                chan_utils_self.user_online_status = "active"; // must use "active" instead of "online" since online is reserved for reversing "offline"
                chan_utils_self.update_user_online_status_on_server("online"); // intentionally pass in "online" to force over-ride of the "offline"
                chan_utils_self.start_polling();
                $("#main").chatbox("option", "boxManager").showChatboxContent();
                chatboxManager.changeBoxtitle("main", new_main_title);
                $("#main").chatbox("option", "boxManager").refreshBox(loading_contacts_message);


                var groups_box_id = "groups";
                var type_of_conversation = "Not used/Not available";
                var groups_box_title = $("id-chat-group-title-text").text();
                chatboxManager.addBox(groups_box_id, groups_box_title, false, false, false, type_of_conversation, '', '');
                var message = $("#id-chat-groups-box-loading-text").text();
                $("#groups").chatbox("option", "boxManager").refreshBox(message);
            } catch(err) {
                report_try_catch_error( err, "execute_go_online");
            }
        };


        this.stop_polling_server = function() {
            try {
                clearTimeout(chan_utils_self.chat_message_timeoutID);
            } catch(err) {
                report_try_catch_error( err, "stop_polling_server");
            }
        };


        this.start_polling = function() {
            try {
                set_message_polling_timeout_and_schedule_poll(chan_utils_self.initial_message_polling_delay);
                track_user_activity_for_online_status();
            } catch(err) {
                report_try_catch_error( err, "start_polling");
            }
        };


        this.create_new_box_entry_on_server = function(other_uid, type_of_conversation) {
            // this is necessary for the case that a user opens a new conversation chatbox - we want to show
            // the conversation history.

            try {

                $.ajax({
                    type: 'post',
                    url:  '/rs/channel_support/open_new_chatbox/' + rnd() + "/",
                    data: {'other_uid': other_uid, 'type_of_conversation' : type_of_conversation},
                    success: function() {},
                    error: function(jqXHR, textStatus, errorThrown) {
                        report_ajax_error(textStatus, errorThrown, "create_new_box_entry_on_server");  
                    },
                    complete: function () {
                        poll_server_for_status_and_new_messages();
                    }
                });
            } catch(err) {
                report_try_catch_error( err, "create_new_box_entry_on_server");
            }
        };

        this.minimize_chatbox_on_server = function(other_uid) {
            $.ajax({
                type: 'post',
                url:  '/rs/channel_support/set_minimize_chat_box_status/' + rnd() + "/",
                data: {'other_uid': other_uid, 'chatbox_status' : 'minimized'},
                error: function(jqXHR, textStatus, errorThrown) {
                    report_ajax_error(textStatus, errorThrown, "minimize_chatbox_on_server");
                }
            });
        };

        this.initialize_main_and_group_boxes_on_server = function() {
            $.ajax({
                type: 'post',
                url:  '/rs/channel_support/initialize_main_and_group_boxes_on_server/' + rnd() + "/",
                data: {},
                error: function(jqXHR, textStatus, errorThrown) {
                    report_ajax_error(textStatus, errorThrown, "initialize_main_and_group_boxes_on_server");
                }
            });
        };


        this.maximize_chatbox_on_server = function(other_uid) {
            $.ajax({
                type: 'post',
                url:  '/rs/channel_support/set_minimize_chat_box_status/' + rnd() + "/",
                data: {'other_uid': other_uid, 'chatbox_status' : 'maximized'},
                error: function(jqXHR, textStatus, errorThrown) {
                    report_ajax_error(textStatus, errorThrown, "maximize_chatbox_on_server");
                }
            });
        };

        this.close_chatbox_on_server = function(other_uid, type_of_conversation) {
            $.ajax({
                type: 'post',
                url:  '/rs/channel_support/close_chat_box/' + rnd() + "/",
                data: {'other_uid': other_uid, 'type_of_conversation' : type_of_conversation},
                error: function(jqXHR, textStatus, errorThrown) {
                    report_ajax_error(textStatus, errorThrown, "close_chatbox_on_server");
                }
            });
        };

        this.close_all_chatboxes_on_server = function() {
            $.ajax({
                type: 'post',
                url:  '/rs/channel_support/close_all_chatboxes_on_server/' + rnd() + "/",
                data: {},
                error: function(jqXHR, textStatus, errorThrown) {
                    report_ajax_error(textStatus, errorThrown, "close_all_chatboxes_on_server");
                }
            });
        };

        this.update_user_online_status_on_server = function(new_status) {
            $.ajax({
                type: 'post',
                url:  '/rs/channel_support/update_user_online_status_on_server/' + rnd() + "/",
                data: {'user_online_status': new_status},
                success: function (response) {
                    if (response == "expired_session") {
                        // if session is expired, send to login screen if they try to change their chat online status
                        self.location = "/";
                    }
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    report_ajax_error(textStatus, errorThrown, "update_user_online_status_on_server");
                }
            });
        };

        this.call_process_json_most_recent_chat_messages = function(json_response) {
            try {
                process_json_most_recent_chat_messages(json_response);
            } catch(err) {
                report_try_catch_error( err, "call_process_json_most_recent_chat_messages");
            }
        };

        this.call_poll_server_for_status_and_new_messages = function () {
            try {
                poll_server_for_status_and_new_messages();
            } catch(err) {
                report_try_catch_error( err, "call_poll_server_for_status_and_new_messages");
            }
        };

        this.sort_user_or_groups_by_name = function(users_or_groups_dict, add_num_group_members_to_name) {

            // returns a 2D array containing [name, user_info_dict] pairs, and sorted by name
            // where user_info_dict is a dictionary with keys for 'username' and 'nid'
            //
            // if add_num_group_members_to_name is true, then we will prepend the number of members currently
            // in a chatgroup to the chatgroup name, before sorting -- this guarantees that more popular groups
            // are shown at the top of the list.

            try {

                var sorted_list_of_names_with_uids = []; // 2D array that will contain [name, user_info_dict]

                for (var uid in users_or_groups_dict) {
                    var user_or_group_info_dict = {};
                    user_or_group_info_dict['uid'] = uid;
                    user_or_group_info_dict['nid'] = users_or_groups_dict[uid]['nid'];
                    user_or_group_info_dict['url_description'] = users_or_groups_dict[uid]['url_description'];
                    if (add_num_group_members_to_name) {
                        var num_group_members = users_or_groups_dict[uid]['num_group_members'];
                        user_or_group_name = "[" + num_group_members + "] " + users_or_groups_dict[uid]['user_or_group_name'];
                    } else {
                        user_or_group_name = users_or_groups_dict[uid]['user_or_group_name'];
                    }
                    sorted_list_of_names_with_uids.push([user_or_group_name, user_or_group_info_dict]);
                }

                sorted_list_of_names_with_uids.sort(function(a,b) { return a[0] < b[0] ? -1 : 1;});
                return sorted_list_of_names_with_uids;
            } catch(err) {
                report_try_catch_error( err, "sort_group_members_by_name");
            }
            return false; // prevent lint warnings
        };

        this.check_if_group_members_are_the_same = function(array_one, array_two) {
            // accepts two sorted arrays, that contain [name, uid] pairs that are sorted by name. Steps through, and
            // checks if they are identical.

            try {

                var len_array_one = array_one.length;
                var len_array_two = array_two.length;

                if (len_array_one != len_array_two) {
                    // length of the arrays is different, so cannot be identical
                    return false;
                }
                else {
                    // loop over the arrays
                    for (var idx=0; idx < len_array_one; idx ++) {
                        if (array_one[idx][0] != array_two[idx][0]) {
                            // arrays have different names - not the same
                            return false;
                        }
                    }

                }
                return true;
            } catch(err) {
                report_try_catch_error( err, "check_if_group_members_are_the_same");
            }
            return false;  // prevent lint warnings
        };


        this.displayAsListWithHrefs = function (box_name, sorted_list_of_names_with_user_info, include_href) {

            /* This code displays the list of users that are currently members of a group discussion. Each username
             * includes a hyberlink to the profile of the given user. 
             */

            try {

                var display_list = '<ul id="id-chatbox-' + box_name + '-list' + '" class = "ui-chatbox-ul">';
                var array_length = sorted_list_of_names_with_user_info.length;

                for (var idx=0; idx < array_length; idx ++) {

                    var display_name = sorted_list_of_names_with_user_info[idx][0];
                    var uid = sorted_list_of_names_with_user_info[idx][1]['uid'];
                    var nid = sorted_list_of_names_with_user_info[idx][1]['nid'];
                    var url_description = sorted_list_of_names_with_user_info[idx][1]['url_description'];
                    if (include_href) {
                        var href = "/" + template_chatbox_vars.language + "/profile/" + nid + "/" + url_description + "/";
                        display_list += '<li><a data-uid="' + uid + '" href = "' + href + '" rel="address:' + href + '">' + display_name + '</a>';
                    } else {
                        display_list += '<li><a data-uid="' + uid + '" data-nid="' + nid + '" data-url_description="' + url_description + '" href = "#">' + display_name + '</a>';
                    }
                }
                display_list += '</ul>';

                return display_list;
            } catch(err) {
                report_try_catch_error( err, "displayAsListWithHrefs");
            }
            return false;  // prevent lint warnings
        };

        
        this.close_group_members_dialog = function(group_id) {

            try{
                idx_of_group_id = $.inArray(group_id, chan_utils_self.list_of_open_chat_groups_members_boxes);
                if (idx_of_group_id != -1) {
                    chan_utils_self.list_of_open_chat_groups_members_boxes.splice(idx_of_group_id, 1); // remove the element from the array
                    $('#id-group_members-dialog-box-' + group_id).remove(); // remove the div that we dynamically added just for this dialog
                }
            } catch(err) {
                report_try_catch_error( err, "close_group_members_dialog");
            }
        };

        this.open_group_members_dialog = function(group_id, box_title) {

            try {

                // adds this group_id to the datastructure that indicates which groups the user is currently looking at the "users" of

                // we dynamically create a new div, and we arbitrarily append it to the id-group_members-dialog-box div that is in the
                // document already (since it doesn't really matter where the div is - it just has to exist).
                if ($('#id-group_members-dialog-box-' + group_id).length === 0) {
                    // don't create the new div if it already existed
                    $("#id-group_members-dialog-box").append('<div id="id-group_members-dialog-box-' + group_id + '"></div>');
                }

                chan_utils_self.list_of_open_chat_groups_members_boxes.push(group_id);
                $("#id-group_members-dialog-box-" + group_id ).dialog({
                    width: 100,
                    title: box_title,
                    position: ['right', 'top'],
                    close: function(){
                        chan_utils_self.close_group_members_dialog(group_id);
                    }
                });
                $("#id-group_members-dialog-box-" + group_id ).parent().css({position : "fixed"});


                poll_server_for_status_and_new_messages(); // poll the server so that the list will be updated right away.
            } catch (err) {
                report_try_catch_error( err, "open_group_members_dialog");
            }
        };


        // the following is a globally visible function declaration
        this.send_message = function(to_uid, msg, type_of_conversation) {
            // user has sent a message from a chatbox in the current window - POST this message to the
            // server.

            try {

                // if there is an error in sending a message, then don't clear out the ChatboxInputBox - instead, allow
                // the user to just hit enter to re-send the message, as opposed to having to re-type it. This variable
                // tracks if there was a problem sending the message.
                var error_sending_message = false;

                // prevent polling while we are sending the message - we start polling again as soon as the ajax call is
                // complete. This is necessary to (help to) prevent double-submission/reception at the same moment.
                clearTimeout(chan_utils_self.chat_message_timeoutID);

                if (!chan_utils_self.sending_message_is_locked_mutex) {
                    chan_utils_self.sending_message_is_locked_mutex = true;

                    // clear the string of the queued messages, since we are now processing the most
                    // up-to-date submission, which should contain all values from this string

                    var json_post_dict = {'to_uid' : to_uid, 'message': msg,
                    'sender_username': chan_utils_self.owner_username,
                    'type_of_conversation' : type_of_conversation,
                    'last_update_time_string_dict' : chan_utils_self.last_update_time_string_dict,
                    //'last_update_chat_message_id_dict' : chan_utils_self.last_update_chat_message_id_dict,
                    'user_online_status': chan_utils_self.user_online_status};


                    $.ajax({
                        type: 'post',
                        url:  '/rs/channel_support/post_message/' + rnd() + "/",
                        contentType: 'json', // send type
                        data: $.toJSON(json_post_dict),
                        dataType: 'json', // response type
                        success: function(json_response) {
                            process_json_most_recent_chat_messages(json_response);
                        },
                        error: function () {
                            // report error message with original text (so that the user can copy/paste it to re-try
                            $("#" + to_uid).chatbox("option", "boxManager").addMsg("Error sending", msg, true);
                            internet_connection_is_down();
                            error_sending_message = true;
                            // because we may have asynchronously cleared the message out of the input box (if the code
                            // following this ajax call is executed before this error function is called), we re-write it
                            // here.
                            $("#" + to_uid).chatbox("option", "boxManager").setChatboxInputBox(msg);
                        },
                        complete: function () {
                            // reset the message polling delay - we use the "in_focus" delay, since we know that the user is in the chatbox
                            set_message_polling_timeout_and_schedule_poll(chan_utils_self.initial_in_focus_polling_delay);
                            chan_utils_self.sending_message_is_locked_mutex = false;

                            // finally, send messages that have been queued while waiting for the server to respond
                            if ( chan_utils_self.string_of_messages_in_queue !== '') {
                                chan_utils_self.send_message(to_uid, chan_utils_self.string_of_messages_in_queue, type_of_conversation);
                                chan_utils_self.string_of_messages_in_queue = '';
                            }
                        }
                    });
                } else {
                    // if the user is attempting to send too many messages at once (which would overload the server) -
                    // we queue these messages and will send them (as a single string) when the current ajax call enters into the "complete" branch.
                    chan_utils_self.string_of_messages_in_queue += msg + "<br>";

                }
                if (! error_sending_message) {
                    // If an error in sending the message has been detected, then do not clear the InputBox -- however,
                    // due to the asynchronous nature of the ajax call, this code might be executed before an error is detected
                    // (meaning that error_sending_message might still be false, due to still waiting for error handler to run) --
                    // which means that we could possibly clear the InputBox even if a sending error has/will occured - however, if this
                    // happens, this is handled by the write of msg (therefore undoing the clear) to the InputBox done in the ajax error handler above.
                    $("#" + to_uid).chatbox("option", "boxManager").setChatboxInputBox('');
                }
            }
            catch(err) {
                report_try_catch_error( err, "send_message");
            }
        };

        // the following is a globally visible function declaration
        this.setup_and_channel_for_current_client = function(owner_uid, owner_username,
                max_polling_delay, idle_polling_delay, away_polling_delay,
                idle_timeout, away_timeout, online_status_on_page_reload) {
            // Sets up a "channel" (which is technically not a channel, but longer-term, we will use channels instead of polling)

            try {
                initialization(owner_uid, owner_username, max_polling_delay, idle_polling_delay, away_polling_delay, idle_timeout, away_timeout);

                if (online_status_on_page_reload != "offline") {
                    var loading_contacts_message = $('#id-chat-contact-main-box-loading-text').text();
                    chan_utils_self.start_polling();
                    $("#main").chatbox("option", "boxManager").refreshBox(loading_contacts_message);

                    var loading_groups_message = $("#id-chat-groups-box-loading-text").text();
                    $("#groups").chatbox("option", "boxManager").refreshBox(loading_groups_message);

                    // if the user is online, then we will check for resize events on the window, which can
                    // change the width of the chatboxes (this is not necessary if they are offline since they should
                    // not have chatboxes open)
                    catch_window_resize_events();
                } else {
                    // user is offline
                    var offline_message = $('#id-chat-contact-main-box-offline-text').text();
                    $("#main").chatbox("option", "boxManager").refreshBox(offline_message);
                }
            } catch (err) {
                report_try_catch_error( err, "setup_and_channel_for_current_client");
            }
        };
    }
    catch(err) {
        report_try_catch_error( err, "chan_utils - outer class/object");
    }
};