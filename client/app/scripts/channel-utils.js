
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

'use strict';


var chanUtils = new function () {
    // Notice the "new" in the function declaration - this creates an object as opposed to a function or class.

    try {

        //***********************************************************
        /* Variables that are visible to all methods in this object */
        var chanUtilsSelf = this;

        //********************************
        /* Private function declarations */

        var initialization = function(ownerUid, ownerUsername, presenceMaxActivePollingDelay, presenceIdlePollingDelay, presenceAwayPollingDelay,
                                      presenceIdleTimeout, presenceAwayTimeout) {
            // initialize the dialog box that will be used for alerting the user to unknown conditions

            try {

                chanUtilsSelf.ownerUid = ownerUid; // set the object variable to the passed in value (chanUtilsSelf refers to the chanUtils object)
                chanUtilsSelf.ownerUsername = ownerUsername;

                chanUtilsSelf.initialInFocusPollingDelay = 750; // when the chatbox input has focus, we poll at a fast speed (up until they go "idle" or leave focus)
                chanUtilsSelf.initialMessagePollingDelay = 2500; //how often to poll for new messages when focus is not in the chatbox input
                chanUtilsSelf.activePollingDelayCeiling = presenceMaxActivePollingDelay * 1000; // convert seconds to ms

                // Note, the decay multipliers are only used if the user is "active" (not "idle" or "away"). If they are "idle" or "away", a constant (slow) polling
                // rate is currently used.
                chanUtilsSelf.focusoutAndActiveDecayMultiplier = 1.5; // each re-schedule is X% slower than the last (when the focus is not in the chatbox)
                chanUtilsSelf.decayMultiplier = chanUtilsSelf.focusoutAndActiveDecayMultiplier;
                chanUtilsSelf.focusinAndActiveDecayMultiplier = 1.1; // if the user has focus in the chatbox, we decay the polling frequency much less.

                chanUtilsSelf.presenceIdlePollingDelay = presenceIdlePollingDelay * 1000;
                chanUtilsSelf.presenceAwayPollingDelay = presenceAwayPollingDelay * 1000;
                chanUtilsSelf.currentMessagePollingDelay = chanUtilsSelf.initialMessagePollingDelay;

                chanUtilsSelf.presenceIdleTimeout = presenceIdleTimeout * 1000;
                chanUtilsSelf.presenceAwayTimeout = presenceAwayTimeout * 1000;

                chanUtilsSelf.chatMessageTimeoutID = null; // used for cancelling a re-scheduled poll for new messages
                chanUtilsSelf.lastUpdateTimeStringDict = {}; // shortcut for new Object() - uid is the key, and value is last update time
                //chanUtilsSelf.last_update_chat_message_id_dict = {}; // shortcut for new Object() - uid is the key, and value is DB/memcache ID of the last update

                chanUtilsSelf.chatBoxesStatus = "unknown"; // "chat_enabled" or "chat_disabled"
                chanUtilsSelf.userPresenceStatus = "user_presence_active"; // should be "user_presence_active", "user_presence_idle", or "user_presence_away"
                chanUtilsSelf.blockFurtherPolling = false;

                chanUtilsSelf.pollingIsLockedMutex = false; // use to ensure that we only have one polling request at a time - true when polling, false when free
                chanUtilsSelf.sendingMessageIsLockedMutex = false; // when we are sending a message, we prevent processing of polling responses
                                                               // since the response to the send_message will be a duplicate/redundant
                chanUtilsSelf.stringOfMessagesInQueue = '';

                chanUtilsSelf.listOfOpenChatGroupsMembersBoxes = [];
                chanUtilsSelf.timeToPassBeforeUpdatingListOfOpenChatGroupsMembersBoxes = 20 * 1000; // every 20 seconds
                chanUtilsSelf.lastTimeWeUpdatedChatGroupsMembersBoxes = 0;
                chanUtilsSelf.listOfUsernamesInEachGroup = {}; // dictionary indexed by group_id, which contains lists of the usernames -- this is used for checking if list has changed so we can highlight it

                chanUtilsSelf.timeToPassBeforeUpdatingFriendsOnlineDict = 10 * 1000; // every 10 seconds
                chanUtilsSelf.lastTimeWeUpdatedFriendsOnlineDict = 0;
                
                chanUtilsSelf.timeaToPassBeforeUpdatingChatGroupsDict = 10 * 1000; // every 10 seconds
                chanUtilsSelf.lastTimeWeUpdatedChatGroupsDict = 0;

                chanUtilsSelf.chatboxIdleObject = chatboxManager.trackUserActivityForOnlineStatus();
            }
            catch(err) {
                reportTryCatchError( err, "initialization");
            }
        };


        var internetConnectionIsDown = function () {
            // this function is called if an ajax call fails (which indicates that the internet connection is down)
            try {
                var warningMessage = $("#id-internet-down-dialog").text();
                $("#main").chatbox("option", "boxManager").refreshBox(warningMessage);
            } catch(err) {
                reportTryCatchError( err, "internet_connection_is_down");
            }
        };

        var internetConnectionIsUp = function () {
            // Remove dialog box warning that internet is down.
        };


        var sessionIsOpen = function () {
            // able to connect to server and session is open. Remove dialog box.
        };



        var processJsonMostRecentChatMessages = function(jsonResponse) {

            try{

                var newOneOnOneMessageReceived = false;

                if ("session_status" in jsonResponse && jsonResponse["session_status"] === "session_expired_session") {
                    chanUtilsSelf.executeGoOfflineOnClient();
                    chanUtilsSelf.blockFurtherPolling = true;
                }
                else if ("session_status" in jsonResponse && jsonResponse["session_status"] === "session_server_error") {
                    chanUtilsSelf.executeGoOfflineOnClient();
                    chanUtilsSelf.blockFurtherPolling = true;
                }
                else if ("chat_boxes_status" in jsonResponse && jsonResponse["chat_boxes_status"] === "chat_disabled") {
                    if (chanUtilsSelf.chatBoxesStatus != "chat_disabled") {
                        chanUtilsSelf.executeGoOfflineOnClient();
                    }
                }
                else if ("chat_boxes_status" in jsonResponse && jsonResponse["chat_boxes_status"] === "chat_enabled") {
                    if (chanUtilsSelf.chatBoxesStatus != "chat_enabled") {
                        /* chat is not currently enabled, but it should enabled based on the status received in the
                           jsonResponse. Go online. */
                        chanUtilsSelf.executeGoOnlineOnClient();
                    }
                }

                if (jsonResponse.hasOwnProperty('conversation_tracker')) {


                    var keep_open_boxes_list = [];

                    var conversation_tracker_dict = jsonResponse.conversation_tracker;
                    for (var other_uid in conversation_tracker_dict) {
                        var array_of_chat_msg_time_strings = conversation_tracker_dict[other_uid].chat_msg_time_string_arr;
                        var chatbox_title = conversation_tracker_dict[other_uid].chatbox_title;
                        var chatbox_minimized_maximized = conversation_tracker_dict[other_uid].chatbox_minimized_maximized;
                        var type_of_conversation = conversation_tracker_dict[other_uid].type_of_conversation;
                        var highlight_box_enabled = true;




                        if (conversation_tracker_dict[other_uid].hasOwnProperty('keep_open')) {

                            keep_open_boxes_list.push(other_uid);

                            if (other_uid != "main" && other_uid != "groups") {

                                if (conversation_tracker_dict[other_uid].hasOwnProperty('update_conversation')) {

                                    if (chanUtilsSelf.lastUpdateTimeStringDict.hasOwnProperty(other_uid)) {
                                        // the last_update_time_string_array has been previously loaded, and therefore
                                        // we want to highlight/bounce the box when a new message is received
                                        highlight_box_enabled = true;
                                    } else {
                                        // This is a totally new chatbox (new page load, or user opened new box), and we don't need/want to highlight it.
                                        highlight_box_enabled = false;
                                    }

                                    chanUtilsSelf.lastUpdateTimeStringDict[other_uid] = conversation_tracker_dict[other_uid]["last_update_time_string"];

                                    // calling addBox just makes sure that it exists. Since we just received notification of the existance of this
                                    // box from the server, it has *not* been "just_opened". 
                                    var just_opened = false;
                                    chatboxManager.addBox(other_uid, chatbox_title, true, true, false, type_of_conversation,
                                            conversation_tracker_dict[other_uid]['nid'], conversation_tracker_dict[other_uid]['url_description'],
                                            just_opened);

                                    // load the message history into the chatbox
                                    for (var msg_time_idx in array_of_chat_msg_time_strings) {
                                        var msg_time_str = array_of_chat_msg_time_strings[msg_time_idx];
                                        var sender_username = conversation_tracker_dict[other_uid].sender_username_dict[msg_time_str];
                                        var chat_msg_text = conversation_tracker_dict[other_uid].chat_msg_text_dict[msg_time_str];
                                        $("#" + other_uid).chatbox("option", "boxManager").addMsg(sender_username, chat_msg_text, highlight_box_enabled);

                                        if (type_of_conversation == "one_on_one") {
                                            // we only start faster polling if a one_on_one message is received - since this is a direct communication
                                            // to the user, while group messages should not trigger faster polling.
                                            newOneOnOneMessageReceived = true;
                                        }
                                    }
                                }
                            }
                        }


                        if (chatbox_minimized_maximized) {
                            if (chatbox_minimized_maximized == "minimized") {
                                $("#"+ other_uid).chatbox("option", "boxManager").minimizeBox();
                            } else if (chatbox_minimized_maximized == "maximized") {
                                $("#"+ other_uid).chatbox("option", "boxManager").maximizeBox();
                            } else {
                                throw "chatbox_minimized_maximized value: " + chatbox_minimized_maximized;
                            }
                        }

                    }

                    // close chat boxes that did not have the "keep_open" property set
                    var currently_open_chatboxes = chatboxManager.showList;
                    for (var idx = 0; idx < currently_open_chatboxes.length; idx ++) {
                        var box_id = currently_open_chatboxes[idx];

                        if ($.inArray(box_id, keep_open_boxes_list) == -1) {

                            if ($("#" + box_id).chatbox("option", 'just_opened') !== true) {
                                // we only check the "keep_open" value for boxes that were not just created,
                                // since the keep_open property needs a few milliseconds to propagate through the server and
                                // back to the client.
                                chatboxManager.closeChatboxOnClient(box_id)
                            }
                            else {
                                // we just received a "keep_open" confirmation for the newly created box, and therefore it is
                                // no longer a "just_opened" box (the new chatbox has propagated through the server and
                                // back to the client). change just_opened to false.
                                $("#" + box_id).chatbox("option", 'just_opened', false)
                            }
                        }
                    }
                }

                var message;
                if (jsonResponse.hasOwnProperty('contacts_info_dict')) {
                    if (!$.isEmptyObject(jsonResponse.contacts_info_dict)) {

                        updateChatControlBox("main", jsonResponse.contacts_info_dict);
                        updateUserChatBoxTitles(jsonResponse.contacts_info_dict);
                    }
                    else {
                        message = $("#id-no-contacts-text").text();
                        $("#main").chatbox("option", "boxManager").refreshBox(message);
                    }
                }

                if (jsonResponse.hasOwnProperty('chat_groups_dict')) {
                    if (!$.isEmptyObject(jsonResponse.chat_groups_dict)) {

                        var chat_groups_dict = jsonResponse.chat_groups_dict;
                        updateChatControlBox("groups", chat_groups_dict);
                        updateGroupChatBoxTitles(chat_groups_dict);
                    }
                    else {
                        message = $("#id-no-groups-text").text();
                        $("#groups").chatbox("option", "boxManager").refreshBox(message);
                    }
                }


                if (jsonResponse.hasOwnProperty('chat_group_members')) {

                    for (var group_id in jsonResponse.chat_group_members) {
                        var group_members_dict = jsonResponse.chat_group_members[group_id];
                        var sorted_list_of_names_with_user_info = chanUtilsSelf.sort_user_or_groups_by_name("members", group_members_dict, true);

                        if (!chanUtilsSelf.listOfUsernamesInEachGroup.hasOwnProperty(group_id)) {
                            chanUtilsSelf.listOfUsernamesInEachGroup[group_id] = sorted_list_of_names_with_user_info;
                        }

                        if ( ! chanUtilsSelf.check_if_group_members_are_the_same(sorted_list_of_names_with_user_info, chanUtilsSelf.listOfUsernamesInEachGroup[group_id])) {
                            chanUtilsSelf.listOfUsernamesInEachGroup[group_id] = sorted_list_of_names_with_user_info;
                            $("#id-group_members-dialog-box-" + group_id).effect("highlight", {color:'#FFEEFF'}, 3000);
                        }

                        var display_list = chanUtilsSelf.displayAsListWithHrefs(group_id, sorted_list_of_names_with_user_info, true);
                        $("#id-group_members-dialog-box-contents-" + group_id).html(display_list);
                        chanUtilsSelf.showListHoverDescriptions(group_id, group_members_dict);
                    }
                }


                if (newOneOnOneMessageReceived) {
                    // reset the message polling delay to the initial value, since this user appears to now
                    // be involved in a conversation.
                    chanUtilsSelf.set_message_polling_timeout_and_schedule_poll(chanUtilsSelf.initialMessagePollingDelay);
                }
            }
            catch(err) {
                reportTryCatchError( err, "processJsonMostRecentChatMessages");
            }
        };




        var generate_json_post_dict = function() {
            
            var current_time = (new Date().getTime());
            var listOfOpenChatGroupsMembersBoxesToPass = [];
            var getFriendsOnlineDict = "no";
            var getChatGroupsDict = "no";

            if (current_time - chanUtilsSelf.timeToPassBeforeUpdatingListOfOpenChatGroupsMembersBoxes >
                chanUtilsSelf.lastTimeWeUpdatedChatGroupsMembersBoxes ) {
                chanUtilsSelf.lastTimeWeUpdatedChatGroupsMembersBoxes = current_time;
                // since we want to request new lists of group members, we must pass in the group_ids of the
                // groups that we want updated.
                listOfOpenChatGroupsMembersBoxesToPass = chanUtilsSelf.listOfOpenChatGroupsMembersBoxes;
            }

            if (current_time - chanUtilsSelf.timeToPassBeforeUpdatingFriendsOnlineDict >
                chanUtilsSelf.lastTimeWeUpdatedFriendsOnlineDict ) {
                chanUtilsSelf.lastTimeWeUpdatedFriendsOnlineDict = current_time;
                // since we want to request new lists of group members, we must pass in the group_ids of the
                // groups that we want updated.
                getFriendsOnlineDict = "yes";
            }


            if (current_time - chanUtilsSelf.timeaToPassBeforeUpdatingChatGroupsDict >
                chanUtilsSelf.lastTimeWeUpdatedChatGroupsDict ) {
                chanUtilsSelf.lastTimeWeUpdatedChatGroupsDict = current_time;
                // since we want to request new lists of group members, we must pass in the group_ids of the
                // groups that we want updated.
                getChatGroupsDict = "yes";
            }
            

            var jsonPostDict = {"lastUpdateTimeStringDict" : chanUtilsSelf.lastUpdateTimeStringDict,
            //'last_update_chat_message_id_dict' : chanUtilsSelf.last_update_chat_message_id_dict,
            "userPresenceStatus": chanUtilsSelf.userPresenceStatus,
            "listOfOpenChatGroupsMembersBoxes" :  listOfOpenChatGroupsMembersBoxesToPass,
            'getFriendsOnlineDict' : getFriendsOnlineDict,
            'getChatGroupsDict' : getChatGroupsDict};

             return jsonPostDict;
        }

        var poll_server_for_status_and_new_messages = function () {

            // polls the server for most recent chat messages - should re-schedule itself
            // on an exponentially declining schedule (exponentially increasing delay).

            try {
                // prevent multiple polls from happening at the same time

                if (!chanUtilsSelf.pollingIsLockedMutex && !chanUtilsSelf.sendingMessageIsLockedMutex) {
                    chanUtilsSelf.pollingIsLockedMutex = true;


                    var list_of_open_chat_groups_members_boxes_to_pass = [];

                    var json_post_dict = generate_json_post_dict();
                    var json_stringified_post = $.toJSON(json_post_dict);
                    

                    $.ajax({
                        type: 'post',
                        url:  '/rs/channel_support/poll_server_for_status_and_new_messages/' + rnd() + "/",
                        contentType: 'json', // post data type
                        data: json_stringified_post,
                        dataType: 'json', // response type
                        success: function(json_response) {
                            if (!chanUtilsSelf.sendingMessageIsLockedMutex) {
                                // only process this json response if we are not currently processing a send_message call.
                                processJsonMostRecentChatMessages(json_response);
                            }
                        },
                        error: function () {
                            internetConnectionIsDown();
                        },
                        complete: function() {
                            if (!chanUtilsSelf.blockFurtherPolling) {
                                chanUtilsSelf.set_message_polling_timeout_and_schedule_poll(chanUtilsSelf.currentMessagePollingDelay);
                            }
                            chanUtilsSelf.pollingIsLockedMutex = false;
                        }
                    });
                }
            } catch(err) {
                reportTryCatchError( err, "poll_server_for_status_and_new_messages", "warning");
            }
        };




        //*******************************
        /* Public function declarations */

        this.set_message_polling_timeout_and_schedule_poll = function(current_message_polling_delay) {

            try {

                // we use a pseudo-exponentially increasing delay for controlling how often to poll the serever
                // because if a user is active, we want to poll more often, and if they have not done any action
                // we dramatically slow down the server polling - we can experimentally determine a good value


                clearTimeout(chanUtilsSelf.chatMessageTimeoutID);

                if (chanUtilsSelf.userPresenceStatus == "user_presence_active") {
                    // for active user sessions, make sure that the delay has not exceeded the maximum, since
                    // we are growing the delay. For idle/away, this number is constant, and therefore
                    // we don't need to look at the ceiling or increase the value.
                    if (current_message_polling_delay > chanUtilsSelf.activePollingDelayCeiling ||
                            chanUtilsSelf.chatBoxesStatus == "chat_disabled") {
                        current_message_polling_delay = chanUtilsSelf.activePollingDelayCeiling;
                    } else {
                        current_message_polling_delay = current_message_polling_delay * chanUtilsSelf.decayMultiplier;
                    }
                    chanUtilsSelf.currentMessagePollingDelay = current_message_polling_delay;
                }
                
                chanUtilsSelf.chatMessageTimeoutID = setTimeout(poll_server_for_status_and_new_messages, current_message_polling_delay);

            } catch(err) {
                reportTryCatchError( err, "set_message_polling_timeout_and_schedule_poll");
            }
        };


        this.set_focusin_polling_delay = function () {
            try {
                // user has clicked the mouse (given focus) in the input for a chatbox
                chanUtilsSelf.currentMessagePollingDelay = chanUtilsSelf.initialInFocusPollingDelay;
                chanUtilsSelf.decayMultiplier = chanUtilsSelf.focusinAndActiveDecayMultiplier;
            } catch(err) {
                reportTryCatchError( err, "set_focusin_polling_delay");
            }
        };
        this.set_focusout_polling_delay = function () {
            try {
                // user has removed the focus from the chatbox input
                chanUtilsSelf.currentMessagePollingDelay = chanUtilsSelf.initialMessagePollingDelay ;
                chanUtilsSelf.decayMultiplier = chanUtilsSelf.focusoutAndActiveDecayMultiplier ;
            } catch(err) {
                reportTryCatchError( err, "set_focusout_polling_delay");
            }
        };


        this.executeGoOfflineOnClient = function () {
            try {
                // note: some of the server interaction is handled in the chatbox functions, since
                // we only want a *single* interaction with the server when the user clicks the
                // offline button. This function takes care of the rest of the functionality after
                // server has been informed of the new status.
                var offline_message = $('#id-chat-contact-main-box-disactivated-text').text();
                var new_main_title = $('#id-chat-contact-title-disactivated-text').text();
                $('#id-go-offline-button').hide();
                $('#id-go-online-button').show();
                chanUtilsSelf.chatBoxesStatus = "chat_disabled";

                chatboxManager.closeAllChatBoxes();
                chatboxManager.changeBoxtitle("main", new_main_title);
                $("#main").chatbox("option", "boxManager").refreshBox(offline_message);
            } catch(err) {
                reportTryCatchError( err, "execute_go_offline_on_client", "warning");
            }
        };

        this.executeGoOnlineOnClient = function () {

            try {
                var new_main_title = $('#id-chat-contact-title-text').text();
                var loading_contacts_message = $('#id-chat-contact-main-box-loading-text').text();
                $('#id-go-online-button').hide();
                $('#id-go-offline-button').show();
                chanUtilsSelf.userPresenceStatus = "user_presence_active";
                chanUtilsSelf.chatBoxesStatus = "chat_enabled";

                chanUtilsSelf.start_polling();
                //$("#main").chatbox("option", "boxManager").showChatboxContent();
                chatboxManager.changeBoxtitle("main", new_main_title);
                $("#main").chatbox("option", "boxManager").refreshBox(loading_contacts_message);


                var groups_box_id = "groups";
                var type_of_conversation = "Not used/Not available";
                var groups_box_title = $("id-chat-group-title-text").text();
                var just_opened = true;
                chatboxManager.addBox(groups_box_id, groups_box_title, false, false, false, type_of_conversation, '', '', just_opened);
                var message = $("#id-chat-groups-box-loading-text").text();
                $("#groups").chatbox("option", "boxManager").refreshBox(message);

                // if the user is online, then we will check for resize events on the window, which can
                // change the width of the chatboxes (this is not necessary if they are offline since they should
                // not have chatboxes open)
                catch_window_resize_events();
                
            } catch(err) {
                reportTryCatchError( err, "execute_go_online_on_client", "warning");
            }
        };


        /*this.stop_polling_server = function() {
            try {
                clearTimeout(chanUtilsSelf.chatMessageTimeoutID);
            } catch(err) {
                reportTryCatchError( err, "stop_polling_server");
            }
        };*/


        this.start_polling = function() {
            // just a simple wrapper function for calling set_message_polling_timeout_and_schedule_poll
            try {
                if (chanUtilsSelf.chatBoxesStatus == "chat_enabled") {
                    chanUtilsSelf.currentMessagePollingDelay = chanUtilsSelf.initialMessagePollingDelay;
                    poll_server_for_status_and_new_messages();
                } else {
                    // if chatboxes are not enabled, we want to still poll in order to keep the userPresenceStatus up-to-date
                    // but we want to do it at a slower rate in order to waste less CPU resources.
                    chanUtilsSelf.set_message_polling_timeout_and_schedule_poll(chanUtilsSelf.activePollingDelayCeiling);
                }
            
            } catch(err) {
                reportTryCatchError( err, "start_polling");
            }
        };


        this.create_new_box_entry_on_server = function(box_id) {
            // this is necessary for the case that a user opens a new conversation chatbox - we want to show
            // the conversation history.

            try {

                var json_post_dict = generate_json_post_dict();
                json_post_dict = $.extend({'other_uid': box_id, 'type_of_conversation' : $("#" + box_id).chatbox("option", 'type_of_conversation')}, json_post_dict);
                var json_stringified_post = $.toJSON(json_post_dict);

                $.ajax({
                    type: 'post',
                    url:  '/rs/channel_support/open_new_chatbox/' + rnd() + "/",
                    data:json_stringified_post,
                    dataType: 'json', // response type                    
                    success: function(json_response) {
                        processJsonMostRecentChatMessages(json_response);
                    },
                    error: function(jqXHR, textStatus, errorThrown) {
                        report_ajax_error(textStatus, errorThrown, "create_new_box_entry_on_server");  
                    },
                    complete: function () {
                        chanUtilsSelf.set_message_polling_timeout_and_schedule_poll(chanUtilsSelf.initialInFocusPollingDelay);
                    }
                });
            } catch(err) {
                reportTryCatchError( err, "create_new_box_entry_on_server", "warning");
            }
        };

        this.minimize_chatbox_on_server = function(other_uid) {
            $.ajax({
                type: 'post',
                url:  '/rs/channel_support/set_minimize_chat_box_status/' + rnd() + "/",
                data: {'other_uid': other_uid, 'chatbox_minimized_maximized' : 'minimized'},
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
                data: {'other_uid': other_uid, 'chatbox_minimized_maximized' : 'maximized'},
                error: function(jqXHR, textStatus, errorThrown) {
                    report_ajax_error(textStatus, errorThrown, "maximize_chatbox_on_server");
                }
            });
        };

        this.close_chatbox_on_server = function(box_id) {
            $.ajax({
                type: 'post',
                url:  '/rs/channel_support/close_chat_box/' + rnd() + "/",
                data: {'other_uid': box_id, 'type_of_conversation' : $("#" + box_id).chatbox("option", 'type_of_conversation')},
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


        this.update_chat_boxes_status_on_server = function(new_chat_boxes_status) {
            $.ajax({
                type: 'post',
                url:  '/rs/channel_support/update_chatbox_status_on_server/' + rnd() + "/",
                data: {"chatBoxesStatus" : new_chat_boxes_status},
                success: function (response) {
                    if (response == "session_expired_session") {
                        // if session is expired, reload the current page (which will kill the chatboxes and will
                        // show them that they are entered as a guest.
                        location.reload();
                    }
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    report_ajax_error(textStatus, errorThrown, "update_chatbox_status_on_server");
                }
            });
        };


        this.update_user_presence_status_on_server = function(new_user_presence_status) {
            $.ajax({
                type: 'post',
                url:  '/rs/channel_support/update_user_presence_on_server/' + rnd() + "/",
                data: {"userPresenceStatus": new_user_presence_status},
                success: function (response) {
                    if (response == "session_expired_session") {
                        location.reload();
                    }
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    report_ajax_error(textStatus, errorThrown, "update_user_presence_on_server");
                }
            });
        };

        this.call_process_json_most_recent_chat_messages = function(json_response) {
            try {
                processJsonMostRecentChatMessages(json_response);
            } catch(err) {
                reportTryCatchError( err, "call_process_json_most_recent_chat_messages");
            }
        };

        this.call_poll_server_for_status_and_new_messages = function () {
            try {
                poll_server_for_status_and_new_messages();
            } catch(err) {
                reportTryCatchError( err, "call_poll_server_for_status_and_new_messages", "warning");
            }
        };

        this.sort_user_or_groups_by_name = function(box_name, users_or_groups_dict, sort_ascending) {

            // returns a 2D array containing [name, user_info_dict] pairs, and sorted by name
            // where user_info_dict is a dictionary with keys for 'username' and 'nid'
            //
            // if add_num_group_members_to_name is true, then we will prepend the number of members currently
            // in a chatgroup to the chatgroup name, before sorting -- this guarantees that more popular groups
            // are shown at the top of the list.

            var userOrGroupName = undefined;

            try {

                var sorted_list_of_names_with_uids = []; // 2D array that will contain [name, user_info_dict]

                for (var uid in users_or_groups_dict) {
                    var user_or_group_info_dict = {};
                    var online_status = undefined;
                    user_or_group_info_dict['uid'] = uid;
                    user_or_group_info_dict['nid'] = users_or_groups_dict[uid]['nid'];
                    user_or_group_info_dict['url_description'] = users_or_groups_dict[uid]['url_description'];
                    if (box_name === "groups") {
                        var num_group_members = users_or_groups_dict[uid]['num_group_members'];
                        var num_members_str = FormatNumberLength(num_group_members, 2);
                        userOrGroupName = "[" + num_members_str + "] " + users_or_groups_dict[uid]['user_or_group_name'];
                    } else {
                        if (box_name != "main" &&  box_name != "members") {
                            throw "Error in sort_user_or_groups_by_name";
                        }
                        // this is the "main" box which contains list of contacts online
                        if (users_or_groups_dict[uid]['user_presence_status'] != "hidden_online_status") {
                            online_status = $('#id-chat-contact-title-' + users_or_groups_dict[uid]['user_presence_status'] + '-image').html();
                        } else {
                            online_status = '';
                        }
                        userOrGroupName = online_status + users_or_groups_dict[uid]['user_or_group_name'] ;
                    }
                    sorted_list_of_names_with_uids.push([userOrGroupName, user_or_group_info_dict]);
                }

                if (sort_ascending) {
                    sorted_list_of_names_with_uids.sort(function(a,b) { return a[0] < b[0] ? -1 : 1;});
                } else {
                    sorted_list_of_names_with_uids.sort(function(a,b) { return a[0] > b[0] ? -1 : 1;});                    
                }
                return sorted_list_of_names_with_uids;
            } catch(err) {
                reportTryCatchError( err, "sort_group_members_by_name");
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
                reportTryCatchError( err, "check_if_group_members_are_the_same");
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
                        var href = "/" + template_presence_vars.language + "/profile/" + nid + "/" + url_description + "/";
                        display_list += '<li><a id="dlist-' + box_name + '-' + nid + '" data-uid="' + uid + '" href = "' + href + '" rel="address:' + href + '">' + display_name + '</a>';
                    } else {
                        display_list += '<li><a data-uid="' + uid + '" data-nid="' + nid + '" data-url_description="' + url_description + '" href = "#">' + display_name + '</a>';
                    }
                }
                display_list += '</ul>';

                return display_list;
            } catch(err) {
                reportTryCatchError( err, "displayAsListWithHrefs");
            }
            return false;  // prevent lint warnings
        };

        this.showListHoverDescriptions = function(box_name, group_members_dict) {
            try {
                for (var uid in group_members_dict) {
                    var nid = group_members_dict[uid]['nid'];
                    var profile_title = group_members_dict[uid]['profile_title'];
                    // since the actual link is surrounded by a <li> declaration, and we want to show the title
                    // when any part of the <li> is hovered over, we select the parent of the anchor.
                    $("#dlist-" +box_name + "-" + nid).parent().attr('title', profile_title);
                }
            } catch(err) {
                reportTryCatchError( err, "showListHoverDescriptions");
            }
        };

        
        this.closeGroupMembersDialog = function(group_id) {

            try{
                var idxOfGroupId = $.inArray(group_id, chanUtilsSelf.listOfOpenChatGroupsMembersBoxes);
                if (idxOfGroupId != -1) {
                    chanUtilsSelf.listOfOpenChatGroupsMembersBoxes.splice(idxOfGroupId, 1); // remove the element from the array
                    $('#id-group_members-dialog-box-' + group_id).remove(); // remove the div that we dynamically added just for this dialog
                }
            } catch(err) {
                reportTryCatchError( err, "closeGroupMembersDialog");
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

                    if (!js_client_is_vip) {
                        // if this client is not a VIP, then show them the option of viewing other members online status.
                        var show_online_status_text = $('#id-show_online_status_menu_element').text();
                        // ideally we would use a button instead of an anchor, however this will require a lot of work due to the fact that we have used a standard
                        // dialog box (not a chatbox), which means that the format, padding, borders, etc. is different than the chatboxes.
                        $("#id-group_members-dialog-box-" + group_id).append('<div class="cl-left-text"><a class="cl-dialog_anchor" id="id-show_online_status_anchor" href="#">' + show_online_status_text + '</a></div><br>');
                        $('#id-show_online_status_anchor').click(function(){
                            return show_online_status_main_dialog();
                        });
                    }

                    $("#id-group_members-dialog-box-" + group_id).append('<div id="id-group_members-dialog-box-contents-' + group_id + '"></div>');
                }

                chanUtilsSelf.listOfOpenChatGroupsMembersBoxes.push(group_id);
                
                $("#id-group_members-dialog-box-" + group_id ).dialog({
                    width: 200,
                    title: box_title,
                    position: ['right', 'top'],
                    close: function(){
                        chanUtilsSelf.closeGroupMembersDialog(group_id);
                    }
                });

                chanUtilsSelf.lastTimeWeUpdatedChatGroupsMembersBoxes = 0; // this will force list to be displayed immediately
                poll_server_for_status_and_new_messages(); // poll the server so that the list will be updated right away.
            } catch (err) {
                reportTryCatchError( err, "open_group_members_dialog");
            }
        };


        // the following is a globally visible function declaration
        this.send_message = function(box_id, msg) {
            // user has sent a message from a chatbox in the current window - POST this message to the
            // server.

            chanUtilsSelf.userPresenceStatus = "user_presence_active";

            try {

                // if there is an error in sending a message, then don't clear out the ChatboxInputBox - instead, allow
                // the user to just hit enter to re-send the message, as opposed to having to re-type it. This variable
                // tracks if there was a problem sending the message.
                var error_sending_message = false;

                // prevent polling while we are sending the message - we start polling again as soon as the ajax call is
                // complete. This is necessary to (help to) prevent double-submission/reception at the same moment.
                clearTimeout(chanUtilsSelf.chatMessageTimeoutID);

                if (!chanUtilsSelf.sendingMessageIsLockedMutex) {
                    chanUtilsSelf.sendingMessageIsLockedMutex = true;
                    var type_of_conversation = $("#" + box_id).chatbox("option", 'type_of_conversation');

                    // clear the string of the queued messages, since we are now processing the most
                    // up-to-date submission, which should contain all values from this string
                    chanUtilsSelf.stringOfMessagesInQueue = '';


                    var json_post_dict = {'to_uid' : box_id, 'message': msg,
                    'sender_username': chanUtilsSelf.ownerUsername,
                    'type_of_conversation' : type_of_conversation,
                    "lastUpdateTimeStringDict" : chanUtilsSelf.lastUpdateTimeStringDict,
                    "userPresenceStatus": chanUtilsSelf.userPresenceStatus};


                    $.ajax({
                        type: 'post',
                        url:  '/rs/channel_support/post_message/' + rnd() + "/",
                        contentType: 'json', // send type
                        data: $.toJSON(json_post_dict),
                        dataType: 'json', // response type
                        success: function(json_response) {
                            processJsonMostRecentChatMessages(json_response);
                        },
                        error: function () {
                            // report error message with original text (so that the user can copy/paste it to re-try
                            $("#" + box_id).chatbox("option", "boxManager").addMsg("Error sending", msg, true);
                            internetConnectionIsDown();
                            error_sending_message = true;
                            // because we may have asynchronously cleared the message out of the input box (if the code
                            // following this ajax call is executed before this error function is called), we re-write it
                            // here.
                            $("#" + box_id).chatbox("option", "boxManager").setChatboxInputBox(msg);
                        },
                        complete: function () {
                            
                            chanUtilsSelf.sendingMessageIsLockedMutex = false;

                            // finally, send messages that have been queued while waiting for the server to respond
                            if ( chanUtilsSelf.stringOfMessagesInQueue !== '') {
                                chanUtilsSelf.send_message(box_id, chanUtilsSelf.stringOfMessagesInQueue);

                            }

                            // reset the message polling delay - we use the "in_focus" delay, since we know that the user is in the chatbox
                            chanUtilsSelf.set_message_polling_timeout_and_schedule_poll(chanUtilsSelf.initialInFocusPollingDelay);
                        }
                    });
                } else {
                    // if the user is attempting to send too many messages at once (which would overload the server) -
                    // we queue these messages and will send them (as a single string) when the current ajax call enters into the "complete" branch.
                    chanUtilsSelf.stringOfMessagesInQueue += msg + "\n";

                }
                if (! error_sending_message) {
                    // If an error in sending the message has been detected, then do not clear the InputBox -- however,
                    // due to the asynchronous nature of the ajax call, this code might be executed before an error is detected
                    // (meaning that error_sending_message might still be false, due to still waiting for error handler to run) --
                    // which means that we could possibly clear the InputBox even if a sending error has/will occured - however, if this
                    // happens, this is handled by the write of msg (therefore undoing the clear) to the InputBox done in the ajax error handler above.
                    $("#" + box_id).chatbox("option", "boxManager").setChatboxInputBox('');
                }
            }
            catch(err) {
                reportTryCatchError( err, "send_message");
            }
        };

        // the following is a globally visible function declaration
        this.setup_and_channel_for_current_client = function(owner_uid, owner_username,
                presence_max_active_polling_delay, presence_idle_polling_delay, presence_away_polling_delay,
                presence_idle_timeout, presence_away_timeout, chat_is_disabled) {
            // Sets up a "channel" (which is technically not a channel, but longer-term, we will use channels instead of polling)

            try {
                initialization(owner_uid, owner_username, presence_max_active_polling_delay, presence_idle_polling_delay, presence_away_polling_delay, presence_idle_timeout, presence_away_timeout);

                if (chat_is_disabled != "yes") {
                    chanUtilsSelf.executeGoOnlineOnClient();
                } else {
                    // user is offline
                    var offline_message = $('#id-chat-contact-main-box-disactivated-text').text();
                    $("#main").chatbox("option", "boxManager").refreshBox(offline_message);
                    // even though the chat is disabled, we continue polling the server in order to keep the
                    // userPresenceStatus up-to-date.
                    chanUtilsSelf.start_polling();
                }
            } catch (err) {
                reportTryCatchError( err, "setup_and_channel_for_current_client");
            }
        };
    }
    catch(err) {
        reportTryCatchError( err, "chanUtils - outer class/object");
    }
};