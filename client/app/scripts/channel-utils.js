'use strict';

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

/* Declare functions that are defined in other files, so that jshint doesn't complain  */
/* global chatboxManager */
/* global updateChatControlBox */
/* global updateUserChatBoxTitles */
/* global updateGroupChatBoxTitles */
/* global catchWindowResizeEvents */
/* global formatNumberLength */
/* global jsClientIsVip */
/* global showOnlineStatusMainDialog */

/* imported from presence_and_chat.html */
/* global templatePresenceVars */

/* imported from rometo-utils.js */
/* global reportTryCatchError */
/* global rnd */
/* global reportAjaxError */


/* Declare exported functions */
/* exported chanUtils */

function ChanUtils() {
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
                    if (chanUtilsSelf.chatBoxesStatus !== "chat_disabled") {
                        chanUtilsSelf.executeGoOfflineOnClient();
                    }
                }
                else if ("chat_boxes_status" in jsonResponse && jsonResponse["chat_boxes_status"] === "chat_enabled") {
                    if (chanUtilsSelf.chatBoxesStatus !== "chat_enabled") {
                        /* chat is not currently enabled, but it should enabled based on the status received in the
                           jsonResponse. Go online. */
                        chanUtilsSelf.executeGoOnlineOnClient();
                    }
                }

                if (jsonResponse.hasOwnProperty('conversation_tracker')) {


                    var keepOpenBoxesList = [];

                    var conversationTrackerDict = jsonResponse["conversation_tracker"];
                    for (var otherUid in conversationTrackerDict) {
                        var arrayOfChatMsgTimeStrings = conversationTrackerDict[otherUid]["chat_msg_time_string_arr"];
                        var chatboxTitle = conversationTrackerDict[otherUid]["chatbox_title"];
                        var chatboxMinimizedMaximized = conversationTrackerDict[otherUid]["chatbox_minimized_maximized"];
                        var typeOfConversation = conversationTrackerDict[otherUid]["typeOfConversation"];
                        var highlightBoxEnabled = true;




                        if (conversationTrackerDict[otherUid].hasOwnProperty('keep_open')) {

                            keepOpenBoxesList.push(otherUid);

                            if (otherUid !== "main" && otherUid !== "groups") {

                                if (conversationTrackerDict[otherUid].hasOwnProperty('update_conversation')) {

                                    if (chanUtilsSelf.lastUpdateTimeStringDict.hasOwnProperty(otherUid)) {
                                        // the last_update_time_string_array has been previously loaded, and therefore
                                        // we want to highlight/bounce the box when a new message is received
                                        highlightBoxEnabled = true;
                                    } else {
                                        // This is a totally new chatbox (new page load, or user opened new box), and we don't need/want to highlight it.
                                        highlightBoxEnabled = false;
                                    }

                                    chanUtilsSelf.lastUpdateTimeStringDict[otherUid] = conversationTrackerDict[otherUid]["last_update_time_string"];

                                    // calling addBox just makes sure that it exists. Since we just received notification of the existance of this
                                    // box from the server, it has *not* been "justOpened".
                                    var justOpened = false;
                                    chatboxManager.addBox(otherUid, chatboxTitle, true, true, false, typeOfConversation,
                                            conversationTrackerDict[otherUid]['nid'], conversationTrackerDict[otherUid]['url_description'],
                                            justOpened);

                                    // load the message history into the chatbox
                                    for (var msgTimeIdx in arrayOfChatMsgTimeStrings) {
                                        var msgTimeStr = arrayOfChatMsgTimeStrings[msgTimeIdx];
                                        var senderUsername = conversationTrackerDict[otherUid]["sender_username_dict"][msgTimeStr];
                                        var chatMsgText = conversationTrackerDict[otherUid]["chat_msg_text_dict"][msgTimeStr];
                                        $("#" + otherUid).chatbox("option", "boxManager").addMsg(senderUsername, chatMsgText, highlightBoxEnabled);

                                        if (typeOfConversation === "one_on_one") {
                                            // we only start faster polling if a one_on_one message is received - since this is a direct communication
                                            // to the user, while group messages should not trigger faster polling.
                                            newOneOnOneMessageReceived = true;
                                        }
                                    }
                                }
                            }
                        }


                        if (chatboxMinimizedMaximized) {
                            if (chatboxMinimizedMaximized === "minimized") {
                                $("#"+ otherUid).chatbox("option", "boxManager").minimizeBox();
                            } else if (chatboxMinimizedMaximized === "maximized") {
                                $("#"+ otherUid).chatbox("option", "boxManager").maximizeBox();
                            } else {
                                throw "chatbox_minimized_maximized value: " + chatboxMinimizedMaximized;
                            }
                        }

                    }

                    // close chat boxes that did not have the "keep_open" property set
                    var currentlyOpenChatboxes = chatboxManager.showList;
                    for (var idx = 0; idx < currentlyOpenChatboxes.length; idx ++) {
                        var boxId = currentlyOpenChatboxes[idx];

                        if ($.inArray(boxId, keepOpenBoxesList) === -1) {

                            if ($("#" + boxId).chatbox("option", 'justOpened') !== true) {
                                // we only check the "keep_open" value for boxes that were not just created,
                                // since the keep_open property needs a few milliseconds to propagate through the server and
                                // back to the client.
                                chatboxManager.closeChatboxOnClient(boxId);
                            }
                            else {
                                // we just received a "keep_open" confirmation for the newly created box, and therefore it is
                                // no longer a "justOpened" box (the new chatbox has propagated through the server and
                                // back to the client). change justOpened to false.
                                $("#" + boxId).chatbox("option", 'justOpened', false);
                            }
                        }
                    }
                }

                var message;
                if (jsonResponse.hasOwnProperty('contacts_info_dict')) {
                    if (!$.isEmptyObject(jsonResponse["contacts_info_dict"])) {

                        updateChatControlBox("main", jsonResponse["contacts_info_dict"]);
                        updateUserChatBoxTitles(jsonResponse["contacts_info_dict"]);
                    }
                    else {
                        message = $("#id-no-contacts-text").text();
                        $("#main").chatbox("option", "boxManager").refreshBox(message);
                    }
                }

                if (jsonResponse.hasOwnProperty('chat_groups_dict')) {
                    if (!$.isEmptyObject(jsonResponse["chat_groups_dict"])) {

                        var chatGroupsDict = jsonResponse["chat_groups_dict"];
                        updateChatControlBox("groups", chatGroupsDict);
                        updateGroupChatBoxTitles(chatGroupsDict);
                    }
                    else {
                        message = $("#id-no-groups-text").text();
                        $("#groups").chatbox("option", "boxManager").refreshBox(message);
                    }
                }


                if (jsonResponse.hasOwnProperty('chat_group_members')) {

                    for (var groupId in jsonResponse["chat_group_members"]) {
                        var groupMembersDict = jsonResponse["chat_group_members"][groupId];
                        var sortedListOfNamesWithUserInfo = chanUtilsSelf.sortUserOrGroupsByName("members", groupMembersDict, true);

                        if (!chanUtilsSelf.listOfUsernamesInEachGroup.hasOwnProperty(groupId)) {
                            chanUtilsSelf.listOfUsernamesInEachGroup[groupId] = sortedListOfNamesWithUserInfo;
                        }

                        if ( ! chanUtilsSelf.checkIfGroupMembersAreTheSame(sortedListOfNamesWithUserInfo, chanUtilsSelf.listOfUsernamesInEachGroup[groupId])) {
                            chanUtilsSelf.listOfUsernamesInEachGroup[groupId] = sortedListOfNamesWithUserInfo;
                            $("#id-group_members-dialog-box-" + groupId).effect("highlight", {color:'#FFEEFF'}, 3000);
                        }

                        var displayList = chanUtilsSelf.displayAsListWithHrefs(groupId, sortedListOfNamesWithUserInfo, true);
                        $("#id-group_members-dialog-box-contents-" + groupId).html(displayList);
                        chanUtilsSelf.showListHoverDescriptions(groupId, groupMembersDict);
                    }
                }


                if (newOneOnOneMessageReceived) {
                    // reset the message polling delay to the initial value, since this user appears to now
                    // be involved in a conversation.
                    chanUtilsSelf.setMessagePollingTimeoutAndSchedulePoll(chanUtilsSelf.initialMessagePollingDelay);
                }
            }
            catch(err) {
                reportTryCatchError( err, "processJsonMostRecentChatMessages");
            }
        };




        var generateJsonPostDict = function() {
            
            var currentTime = (new Date().getTime());
            var listOfOpenChatGroupsMembersBoxesToPass = [];
            var getFriendsOnlineDict = "no";
            var getChatGroupsDict = "no";

            if (currentTime - chanUtilsSelf.timeToPassBeforeUpdatingListOfOpenChatGroupsMembersBoxes >
                chanUtilsSelf.lastTimeWeUpdatedChatGroupsMembersBoxes ) {
                chanUtilsSelf.lastTimeWeUpdatedChatGroupsMembersBoxes = currentTime;
                // since we want to request new lists of group members, we must pass in the group_ids of the
                // groups that we want updated.
                listOfOpenChatGroupsMembersBoxesToPass = chanUtilsSelf.listOfOpenChatGroupsMembersBoxes;
            }

            if (currentTime - chanUtilsSelf.timeToPassBeforeUpdatingFriendsOnlineDict >
                chanUtilsSelf.lastTimeWeUpdatedFriendsOnlineDict ) {
                chanUtilsSelf.lastTimeWeUpdatedFriendsOnlineDict = currentTime;
                // since we want to request new lists of group members, we must pass in the group_ids of the
                // groups that we want updated.
                getFriendsOnlineDict = "yes";
            }


            if (currentTime - chanUtilsSelf.timeaToPassBeforeUpdatingChatGroupsDict >
                chanUtilsSelf.lastTimeWeUpdatedChatGroupsDict ) {
                chanUtilsSelf.lastTimeWeUpdatedChatGroupsDict = currentTime;
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
        };

        var pollServerForStatusAndNewMessages = function () {

            // polls the server for most recent chat messages - should re-schedule itself
            // on an exponentially declining schedule (exponentially increasing delay).

            try {
                // prevent multiple polls from happening at the same time

                if (!chanUtilsSelf.pollingIsLockedMutex && !chanUtilsSelf.sendingMessageIsLockedMutex) {
                    chanUtilsSelf.pollingIsLockedMutex = true;

                    var jsonPostDict = generateJsonPostDict();
                    var jsonStringifiedPost = $.toJSON(jsonPostDict);
                    

                    $.ajax({
                        type: 'post',
                        url:  '/rs/channel_support/poll_server_for_status_and_new_messages/' + rnd() + "/",
                        contentType: 'json', // post data type
                        data: jsonStringifiedPost,
                        dataType: 'json', // response type
                        success: function(jsonResponse) {
                            if (!chanUtilsSelf.sendingMessageIsLockedMutex) {
                                // only process this json response if we are not currently processing a send_message call.
                                processJsonMostRecentChatMessages(jsonResponse);
                            }
                        },
                        error: function () {
                            internetConnectionIsDown();
                        },
                        complete: function() {
                            if (!chanUtilsSelf.blockFurtherPolling) {
                                chanUtilsSelf.setMessagePollingTimeoutAndSchedulePoll(chanUtilsSelf.currentMessagePollingDelay);
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

        this.setMessagePollingTimeoutAndSchedulePoll = function(currentMessagePollingDelay) {

            try {

                // we use a pseudo-exponentially increasing delay for controlling how often to poll the serever
                // because if a user is active, we want to poll more often, and if they have not done any action
                // we dramatically slow down the server polling - we can experimentally determine a good value


                clearTimeout(chanUtilsSelf.chatMessageTimeoutID);

                if (chanUtilsSelf.userPresenceStatus === "user_presence_active") {
                    // for active user sessions, make sure that the delay has not exceeded the maximum, since
                    // we are growing the delay. For idle/away, this number is constant, and therefore
                    // we don't need to look at the ceiling or increase the value.
                    if (currentMessagePollingDelay > chanUtilsSelf.activePollingDelayCeiling ||
                            chanUtilsSelf.chatBoxesStatus === "chat_disabled") {
                        currentMessagePollingDelay = chanUtilsSelf.activePollingDelayCeiling;
                    } else {
                        currentMessagePollingDelay = currentMessagePollingDelay * chanUtilsSelf.decayMultiplier;
                    }
                    chanUtilsSelf.currentMessagePollingDelay = currentMessagePollingDelay;
                }
                
                chanUtilsSelf.chatMessageTimeoutID = setTimeout(pollServerForStatusAndNewMessages, currentMessagePollingDelay);

            } catch(err) {
                reportTryCatchError( err, "setMessagePollingTimeoutAndSchedulePoll");
            }
        };


        this.setFocusinPollingDelay = function () {
            try {
                // user has clicked the mouse (given focus) in the input for a chatbox
                chanUtilsSelf.currentMessagePollingDelay = chanUtilsSelf.initialInFocusPollingDelay;
                chanUtilsSelf.decayMultiplier = chanUtilsSelf.focusinAndActiveDecayMultiplier;
            } catch(err) {
                reportTryCatchError( err, "setFocusinPollingDelay");
            }
        };
        this.setFocusoutPollingDelay = function () {
            try {
                // user has removed the focus from the chatbox input
                chanUtilsSelf.currentMessagePollingDelay = chanUtilsSelf.initialMessagePollingDelay ;
                chanUtilsSelf.decayMultiplier = chanUtilsSelf.focusoutAndActiveDecayMultiplier ;
            } catch(err) {
                reportTryCatchError( err, "setFocusoutPollingDelay");
            }
        };


        this.executeGoOfflineOnClient = function () {
            try {
                // note: some of the server interaction is handled in the chatbox functions, since
                // we only want a *single* interaction with the server when the user clicks the
                // offline button. This function takes care of the rest of the functionality after
                // server has been informed of the new status.
                var offlineMessage = $('#id-chat-contact-main-box-disactivated-text').text();
                var newMainTitle = $('#id-chat-contact-title-disactivated-text').text();
                $('#id-go-offline-button').hide();
                $('#id-go-online-button').show();
                chanUtilsSelf.chatBoxesStatus = "chat_disabled";

                chatboxManager.closeAllChatBoxes();
                chatboxManager.changeBoxtitle("main", newMainTitle);
                $("#main").chatbox("option", "boxManager").refreshBox(offlineMessage);
            } catch(err) {
                reportTryCatchError( err, "execute_go_offline_on_client", "warning");
            }
        };

        this.executeGoOnlineOnClient = function () {

            try {
                var newMainTitle = $('#id-chat-contact-title-text').text();
                var loadingContactsMessage = $('#id-chat-contact-main-box-loading-text').text();
                $('#id-go-online-button').hide();
                $('#id-go-offline-button').show();
                chanUtilsSelf.userPresenceStatus = "user_presence_active";
                chanUtilsSelf.chatBoxesStatus = "chat_enabled";

                chanUtilsSelf.startPolling();
                //$("#main").chatbox("option", "boxManager").showChatboxContent();
                chatboxManager.changeBoxtitle("main", newMainTitle);
                $("#main").chatbox("option", "boxManager").refreshBox(loadingContactsMessage);


                var groupsBoxId = "groups";
                var typeOfConversation = "Not used/Not available";
                var groupsBoxTitle = $("id-chat-group-title-text").text();
                var justOpened = true;
                chatboxManager.addBox(groupsBoxId, groupsBoxTitle, false, false, false, typeOfConversation, '', '', justOpened);
                var message = $("#id-chat-groups-box-loading-text").text();
                $("#groups").chatbox("option", "boxManager").refreshBox(message);

                // if the user is online, then we will check for resize events on the window, which can
                // change the width of the chatboxes (this is not necessary if they are offline since they should
                // not have chatboxes open)
                catchWindowResizeEvents();
                
            } catch(err) {
                reportTryCatchError( err, "executeGoOnlineOnClient", "warning");
            }
        };


        /*this.stop_polling_server = function() {
            try {
                clearTimeout(chanUtilsSelf.chatMessageTimeoutID);
            } catch(err) {
                reportTryCatchError( err, "stop_polling_server");
            }
        };*/


        this.startPolling = function() {
            // just a simple wrapper function for calling setMessagePollingTimeoutAndSchedulePoll
            try {
                if (chanUtilsSelf.chatBoxesStatus === "chat_enabled") {
                    chanUtilsSelf.currentMessagePollingDelay = chanUtilsSelf.initialMessagePollingDelay;
                    pollServerForStatusAndNewMessages();
                } else {
                    // if chatboxes are not enabled, we want to still poll in order to keep the userPresenceStatus up-to-date
                    // but we want to do it at a slower rate in order to waste less CPU resources.
                    chanUtilsSelf.setMessagePollingTimeoutAndSchedulePoll(chanUtilsSelf.activePollingDelayCeiling);
                }
            
            } catch(err) {
                reportTryCatchError( err, "start_polling");
            }
        };


        this.createNewBoxEntryOnServer = function(boxId) {
            // this is necessary for the case that a user opens a new conversation chatbox - we want to show
            // the conversation history.

            try {

                var jsonPostDict = generateJsonPostDict();
                jsonPostDict = $.extend({'other_uid': boxId, 'typeOfConversation' : $("#" + boxId).chatbox("option", 'typeOfConversation')}, jsonPostDict);
                var jsonStringifiedPost = $.toJSON(jsonPostDict);

                $.ajax({
                    type: 'post',
                    url:  '/rs/channel_support/open_new_chatbox/' + rnd() + "/",
                    data:jsonStringifiedPost,
                    dataType: 'json', // response type                    
                    success: function(jsonResponse) {
                        processJsonMostRecentChatMessages(jsonResponse);
                    },
                    error: function(jqXHR, textStatus, errorThrown) {
                        reportAjaxError(textStatus, errorThrown, "createNewBoxEntryOnServer");
                    },
                    complete: function () {
                        chanUtilsSelf.setMessagePollingTimeoutAndSchedulePoll(chanUtilsSelf.initialInFocusPollingDelay);
                    }
                });
            } catch(err) {
                reportTryCatchError( err, "createNewBoxEntryOnServer", "warning");
            }
        };

        this.minimizeChatboxOnServer = function(otherUid) {
            $.ajax({
                type: 'post',
                url:  '/rs/channel_support/set_minimize_chat_box_status/' + rnd() + "/",
                data: {'other_uid': otherUid, 'chatbox_minimized_maximized' : 'minimized'},
                error: function(jqXHR, textStatus, errorThrown) {
                    reportAjaxError(textStatus, errorThrown, "minimizeChatboxOnServer");
                }
            });
        };

        this.initializeMainAndGroupBoxesOnServer = function() {
            $.ajax({
                type: 'post',
                url:  '/rs/channel_support/initialize_main_and_group_boxes_on_server/' + rnd() + "/",
                data: {},
                error: function(jqXHR, textStatus, errorThrown) {
                    reportAjaxError(textStatus, errorThrown, "initialize_main_and_group_boxes_on_server");
                }
            });
        };


        this.maximizeChatboxOnServer = function(otherUid) {
            $.ajax({
                type: 'post',
                url:  '/rs/channel_support/set_minimize_chat_box_status/' + rnd() + "/",
                data: {'other_uid': otherUid, 'chatbox_minimized_maximized' : 'maximized'},
                error: function(jqXHR, textStatus, errorThrown) {
                    reportAjaxError(textStatus, errorThrown, "maximizeChatboxOnServer");
                }
            });
        };

        this.closeChatboxOnServer = function(boxId) {
            $.ajax({
                type: 'post',
                url:  '/rs/channel_support/close_chat_box/' + rnd() + "/",
                data: {'other_uid': boxId, 'typeOfConversation' : $("#" + boxId).chatbox("option", 'typeOfConversation')},
                error: function(jqXHR, textStatus, errorThrown) {
                    reportAjaxError(textStatus, errorThrown, "closeChatboxOnServer");
                }
            });
        };

        this.closeAllChatboxesOnServer = function() {
            $.ajax({
                type: 'post',
                url:  '/rs/channel_support/close_all_chatboxes_on_server/' + rnd() + "/",
                data: {},
                error: function(jqXHR, textStatus, errorThrown) {
                    reportAjaxError(textStatus, errorThrown, "close_all_chatboxes_on_server");
                }
            });
        };


        this.updateChatBoxesStatusOnServer = function(newChatBoxesStatus) {
            $.ajax({
                type: 'post',
                url:  '/rs/channel_support/update_chatbox_status_on_server/' + rnd() + "/",
                data: {"chatBoxesStatus" : newChatBoxesStatus},
                success: function (response) {
                    if (response === "session_expired_session") {
                        // if session is expired, reload the current page (which will kill the chatboxes and will
                        // show them that they are entered as a guest.
                        location.reload();
                    }
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    reportAjaxError(textStatus, errorThrown, "update_chatbox_status_on_server");
                }
            });
        };


        this.updateUserPresenceStatusOnServer = function(newUserPresenceStatus) {
            $.ajax({
                type: 'post',
                url:  '/rs/channel_support/update_user_presence_on_server/' + rnd() + "/",
                data: {"userPresenceStatus": newUserPresenceStatus},
                success: function (response) {
                    if (response === "session_expired_session") {
                        location.reload();
                    }
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    reportAjaxError(textStatus, errorThrown, "update_user_presence_on_server");
                }
            });
        };

        this.callProcessJsonMostRecentChatMessages = function(jsonResponse) {
            try {
                processJsonMostRecentChatMessages(jsonResponse);
            } catch(err) {
                reportTryCatchError( err, "call_process_json_most_recent_chat_messages");
            }
        };

        this.callPollServerForStatusAndNewMessages = function () {
            try {
                pollServerForStatusAndNewMessages();
            } catch(err) {
                reportTryCatchError( err, "call_poll_server_for_status_and_new_messages", "warning");
            }
        };

        this.sortUserOrGroupsByName = function(boxName, usersOrGroupsDict, sortAscending) {

            // returns a 2D array containing [name, user_info_dict] pairs, and sorted by name
            // where user_info_dict is a dictionary with keys for 'username' and 'nid'
            //
            // if add_num_group_members_to_name is true, then we will prepend the number of members currently
            // in a chatgroup to the chatgroup name, before sorting -- this guarantees that more popular groups
            // are shown at the top of the list.

            var userOrGroupName;

            try {

                var sortedListOfNamesWithUids = []; // 2D array that will contain [name, user_info_dict]

                for (var uid in usersOrGroupsDict) {
                    var userOrGroupInfoDict = {};
                    var onlineStatus;
                    userOrGroupInfoDict['uid'] = uid;
                    userOrGroupInfoDict['nid'] = usersOrGroupsDict[uid]['nid'];
                    userOrGroupInfoDict['urlDescription'] = usersOrGroupsDict[uid]['urlDescription'];
                    if (boxName === "groups") {
                        var numGroupMembers = usersOrGroupsDict[uid]['num_group_members'];
                        var numMembersStr = formatNumberLength(numGroupMembers, 2);
                        userOrGroupName = "[" + numMembersStr + "] " + usersOrGroupsDict[uid]['user_or_group_name'];
                    } else {
                        if (boxName !== "main" &&  boxName !== "members") {
                            throw "Error in sortUserOrGroupsByName";
                        }
                        // this is the "main" box which contains list of contacts online
                        if (usersOrGroupsDict[uid]['user_presence_status'] !== "hidden_online_status") {
                            onlineStatus = $('#id-chat-contact-title-' + usersOrGroupsDict[uid]['user_presence_status'] + '-image').html();
                        } else {
                            onlineStatus = '';
                        }
                        userOrGroupName = onlineStatus + usersOrGroupsDict[uid]['user_or_group_name'] ;
                    }
                    sortedListOfNamesWithUids.push([userOrGroupName, userOrGroupInfoDict]);
                }

                if (sortAscending) {
                    sortedListOfNamesWithUids.sort(function(a,b) { return a[0] < b[0] ? -1 : 1;});
                } else {
                    sortedListOfNamesWithUids.sort(function(a,b) { return a[0] > b[0] ? -1 : 1;});
                }
                return sortedListOfNamesWithUids;
            } catch(err) {
                reportTryCatchError( err, "sort_group_members_by_name");
            }
            return false; // prevent lint warnings
        };

        this.checkIfGroupMembersAreTheSame = function(arrayOne, arrayTwo) {
            // accepts two sorted arrays, that contain [name, uid] pairs that are sorted by name. Steps through, and
            // checks if they are identical.

            try {

                var lenArrayOne = arrayOne.length;
                var lenArrayTwo = arrayTwo.length;

                if (lenArrayOne !== lenArrayTwo) {
                    // length of the arrays is different, so cannot be identical
                    return false;
                }
                else {
                    // loop over the arrays
                    for (var idx=0; idx < lenArrayOne; idx ++) {
                        if (arrayOne[idx][0] !== arrayTwo[idx][0]) {
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


        this.displayAsListWithHrefs = function (boxName, sortedListOfNamesWithUserInfo, includeHref) {

            /* This code displays the list of users that are currently members of a group discussion. Each username
             * includes a hyberlink to the profile of the given user. 
             */

            try {

                var displayList = '<ul id="id-chatbox-' + boxName + '-list' + '" class = "ui-chatbox-ul">';
                var arrayLength = sortedListOfNamesWithUserInfo.length;

                for (var idx=0; idx < arrayLength; idx ++) {

                    var displayName = sortedListOfNamesWithUserInfo[idx][0];
                    var uid = sortedListOfNamesWithUserInfo[idx][1]['uid'];
                    var nid = sortedListOfNamesWithUserInfo[idx][1]['nid'];
                    var urlDescription = sortedListOfNamesWithUserInfo[idx][1]['urlDescription'];
                    if (includeHref) {
                        var href = "/" + templatePresenceVars.language + "/profile/" + nid + "/" + urlDescription + "/";
                        displayList += '<li><a id="dlist-' + boxName + '-' + nid + '" data-uid="' + uid + '" href = "' + href + '" rel="address:' + href + '">' + displayName + '</a>';
                    } else {
                        displayList += '<li><a data-uid="' + uid + '" data-nid="' + nid + '" data-urlDescription="' + urlDescription + '" href = "#">' + displayName + '</a>';
                    }
                }
                displayList += '</ul>';

                return displayList;
            } catch(err) {
                reportTryCatchError( err, "displayAsListWithHrefs");
            }
            return false;  // prevent lint warnings
        };

        this.showListHoverDescriptions = function(boxName, groupMembersDict) {
            try {
                for (var uid in groupMembersDict) {
                    var nid = groupMembersDict[uid]['nid'];
                    var profileTitle = groupMembersDict[uid]['profile_title'];
                    // since the actual link is surrounded by a <li> declaration, and we want to show the title
                    // when any part of the <li> is hovered over, we select the parent of the anchor.
                    $("#dlist-" +boxName + "-" + nid).parent().attr('title', profileTitle);
                }
            } catch(err) {
                reportTryCatchError( err, "showListHoverDescriptions");
            }
        };

        
        this.closeGroupMembersDialog = function(groupId) {

            try{
                var idxOfGroupId = $.inArray(groupId, chanUtilsSelf.listOfOpenChatGroupsMembersBoxes);
                if (idxOfGroupId !== -1) {
                    chanUtilsSelf.listOfOpenChatGroupsMembersBoxes.splice(idxOfGroupId, 1); // remove the element from the array
                    $('#id-group_members-dialog-box-' + groupId).remove(); // remove the div that we dynamically added just for this dialog
                }
            } catch(err) {
                reportTryCatchError( err, "closeGroupMembersDialog");
            }
        };


        this.openGroupMembersDialog = function(groupId, boxTitle) {

            try {

                // adds this group_id to the datastructure that indicates which groups the user is currently looking at the "users" of

                // we dynamically create a new div, and we arbitrarily append it to the id-group_members-dialog-box div that is in the
                // document already (since it doesn't really matter where the div is - it just has to exist).
                if ($('#id-group_members-dialog-box-' + groupId).length === 0) {
                    // don't create the new div if it already existed
                    $("#id-group_members-dialog-box").append('<div id="id-group_members-dialog-box-' + groupId + '"></div>');

                    if (!jsClientIsVip) {
                        // if this client is not a VIP, then show them the option of viewing other members online status.
                        var showOnlineStatusText = $('#id-show_online_status_menu_element').text();
                        // ideally we would use a button instead of an anchor, however this will require a lot of work due to the fact that we have used a standard
                        // dialog box (not a chatbox), which means that the format, padding, borders, etc. is different than the chatboxes.
                        $("#id-group_members-dialog-box-" + groupId).append('<div class="cl-left-text"><a class="cl-dialog_anchor" id="id-show_online_status_anchor" href="#">' + showOnlineStatusText + '</a></div><br>');
                        $('#id-show_online_status_anchor').click(function(){
                            return showOnlineStatusMainDialog();
                        });
                    }

                    $("#id-group_members-dialog-box-" + groupId).append('<div id="id-group_members-dialog-box-contents-' + groupId + '"></div>');
                }

                chanUtilsSelf.listOfOpenChatGroupsMembersBoxes.push(groupId);
                
                $("#id-group_members-dialog-box-" + groupId ).dialog({
                    width: 200,
                    title: boxTitle,
                    position: ['right', 'top'],
                    close: function(){
                        chanUtilsSelf.closeGroupMembersDialog(groupId);
                    }
                });

                chanUtilsSelf.lastTimeWeUpdatedChatGroupsMembersBoxes = 0; // this will force list to be displayed immediately
                pollServerForStatusAndNewMessages(); // poll the server so that the list will be updated right away.
            } catch (err) {
                reportTryCatchError( err, "open_group_members_dialog");
            }
        };


        // the following is a globally visible function declaration
        this.sendMessage = function(boxId, msg) {
            // user has sent a message from a chatbox in the current window - POST this message to the
            // server.

            chanUtilsSelf.userPresenceStatus = "user_presence_active";

            try {

                // if there is an error in sending a message, then don't clear out the ChatboxInputBox - instead, allow
                // the user to just hit enter to re-send the message, as opposed to having to re-type it. This variable
                // tracks if there was a problem sending the message.
                var errorSendingMessage = false;

                // prevent polling while we are sending the message - we start polling again as soon as the ajax call is
                // complete. This is necessary to (help to) prevent double-submission/reception at the same moment.
                clearTimeout(chanUtilsSelf.chatMessageTimeoutID);

                if (!chanUtilsSelf.sendingMessageIsLockedMutex) {
                    chanUtilsSelf.sendingMessageIsLockedMutex = true;
                    var typeOfConversation = $("#" + boxId).chatbox("option", 'typeOfConversation');

                    // clear the string of the queued messages, since we are now processing the most
                    // up-to-date submission, which should contain all values from this string
                    chanUtilsSelf.stringOfMessagesInQueue = '';


                    var jsonPostDict = {'toUid' : boxId, 'message': msg,
                    'senderUsername': chanUtilsSelf.ownerUsername,
                    'typeOfConversation' : typeOfConversation,
                    "lastUpdateTimeStringDict" : chanUtilsSelf.lastUpdateTimeStringDict,
                    "userPresenceStatus": chanUtilsSelf.userPresenceStatus};


                    $.ajax({
                        type: 'post',
                        url:  '/rs/channel_support/post_message/' + rnd() + "/",
                        contentType: 'json', // send type
                        data: $.toJSON(jsonPostDict),
                        dataType: 'json', // response type
                        success: function(jsonResponse) {
                            processJsonMostRecentChatMessages(jsonResponse);
                        },
                        error: function () {
                            // report error message with original text (so that the user can copy/paste it to re-try
                            $("#" + boxId).chatbox("option", "boxManager").addMsg("Error sending", msg, true);
                            internetConnectionIsDown();
                            errorSendingMessage = true;
                            // because we may have asynchronously cleared the message out of the input box (if the code
                            // following this ajax call is executed before this error function is called), we re-write it
                            // here.
                            $("#" + boxId).chatbox("option", "boxManager").setChatboxInputBox(msg);
                        },
                        complete: function () {
                            
                            chanUtilsSelf.sendingMessageIsLockedMutex = false;

                            // finally, send messages that have been queued while waiting for the server to respond
                            if ( chanUtilsSelf.stringOfMessagesInQueue !== '') {
                                chanUtilsSelf.sendMessage(boxId, chanUtilsSelf.stringOfMessagesInQueue);

                            }

                            // reset the message polling delay - we use the "in_focus" delay, since we know that the user is in the chatbox
                            chanUtilsSelf.setMessagePollingTimeoutAndSchedulePoll(chanUtilsSelf.initialInFocusPollingDelay);
                        }
                    });
                } else {
                    // if the user is attempting to send too many messages at once (which would overload the server) -
                    // we queue these messages and will send them (as a single string) when the current ajax call enters into the "complete" branch.
                    chanUtilsSelf.stringOfMessagesInQueue += msg + "\n";

                }
                if (! errorSendingMessage) {
                    // If an error in sending the message has been detected, then do not clear the InputBox -- however,
                    // due to the asynchronous nature of the ajax call, this code might be executed before an error is detected
                    // (meaning that error_sending_message might still be false, due to still waiting for error handler to run) --
                    // which means that we could possibly clear the InputBox even if a sending error has/will occured - however, if this
                    // happens, this is handled by the write of msg (therefore undoing the clear) to the InputBox done in the ajax error handler above.
                    $("#" + boxId).chatbox("option", "boxManager").setChatboxInputBox('');
                }
            }
            catch(err) {
                reportTryCatchError( err, "send_message");
            }
        };

        // the following is a globally visible function declaration
        this.setupAndChannelForCurrentClient = function(ownerUid, ownerUsername,
                presenceMaxActivePollingDelay, presenceIdlePollingDelay, presenceAwayPollingDelay,
                presenceIdleTimeout, presenceAwayTimeout, chatIsDisabled) {
            // Sets up a "channel" (which is technically not a channel, but longer-term, we will use channels instead of polling)

            try {
                initialization(ownerUid, ownerUsername, presenceMaxActivePollingDelay, presenceIdlePollingDelay, presenceAwayPollingDelay, presenceIdleTimeout, presenceAwayTimeout);

                if (chatIsDisabled !== "yes") {
                    chanUtilsSelf.executeGoOnlineOnClient();
                } else {
                    // user is offline
                    var offlineMessage = $('#id-chat-contact-main-box-disactivated-text').text();
                    $("#main").chatbox("option", "boxManager").refreshBox(offlineMessage);
                    // even though the chat is disabled, we continue polling the server in order to keep the
                    // userPresenceStatus up-to-date.
                    chanUtilsSelf.startPolling();
                }
            } catch (err) {
                reportTryCatchError( err, "setup_and_channel_for_current_client");
            }
        };
    }
    catch(err) {
        reportTryCatchError( err, "chanUtils - outer class/object");
    }
}

var chanUtils = new ChanUtils();