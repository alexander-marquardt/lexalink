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

"use strict";

/* imported from channel-utils.js */
/* global chanUtils */

/* imported from chatbox.js */
/* global setupContactsAndGroupsBoxes */

/* imported from presence_and_chat.html */
/* global templatePresenceVars */

/* imported from rometo-utils.js */
/* global reportTryCatchError */
/* global mouseoverButtonHandler */
/* global reportAjaxError */

/* common_wrapper.html */
/* global removeChatboxes */

/* Declare exported functions */
/* exported launchChatboxes */

/* the following code is the dialog and javascript for creating new chat groups */
function submitCreateNewGroupPost(sectionName) {

    try {
        $.ajax({
            type: 'post',
            url:  "/rs/store_" + sectionName + "/",
            data: $("form#id-" + sectionName + "-form").serialize(),
            success: function() {
                //chanUtils.call_process_json_most_recent_chat_messages(json_response);
                $("#id-create-new-group-input").val('');

                chanUtils.callPollServerForStatusAndNewMessages();
                // make sure that the list of groups is shown after they create a new group
                $("#groups").chatbox("option", "boxManager").maximizeBox();
            },
            error: function(jqXHR, textStatus, errorThrown) {
                $("#id-error-dialog-box").dialog();
                $("#id-error-dialog-box").text(jqXHR.responseText);
                reportAjaxError(textStatus, errorThrown, "submitCreateNewGroupPost");
            },
            complete: function() {
                $("#id-create-group-dialog").dialog('close');
            }
        });
    } catch(err) {
        reportTryCatchError( err, "submitCreateNewGroupPost");
    }
}

function handleSubmitCreateNewGroup(sectionName) {
    // setup submit button and associate the action when clicked

    try {
        var submitButtonId = "#id-submit-" + sectionName;
        var editSectionId = "#id-edit-" + sectionName + "-section";

        $(submitButtonId).click(function() {
            submitCreateNewGroupPost(sectionName);
        });

        // Check to see if the enter key has been pressed inside the section -- treat this this same
        // as if the user had pressed the submit button
        $(editSectionId).keydown(function(e) {
            if (e.keyCode === 13) {
                submitCreateNewGroupPost(sectionName);
                e.stopImmediatePropagation();
                e.stopPropagation();
                return false;
            }
        });

        mouseoverButtonHandler($(submitButtonId));
    } catch(err) {
        reportTryCatchError( err, "handleSubmitCreateNewGroup");
    }
}




function launchChatboxes(){

    try {

        // we need to make sure that we only launch the chatboxes once, even though this code might be called
        // multiple times.
        if (typeof launchChatboxes.chatboxesLaunched === 'undefined') {
            launchChatboxes.chatboxesLaunched = false;
        }

        if (!launchChatboxes.chatboxesLaunched) {

            handleSubmitCreateNewGroup("create_new_group");

            if (removeChatboxes) {
                templatePresenceVars.chatIsDisabled = "yes";
            }
            
            setupContactsAndGroupsBoxes(templatePresenceVars.chatIsDisabled);

            // Open the socket that will be used for communicating from the browser to the server.
            // Note: since all chat goes through the server, the same socket will be used for channeling
            // all chats that a given user is currently participating in.
            chanUtils.setupAndChannelForCurrentClient(
                    templatePresenceVars.ownerUid,
                    templatePresenceVars.username,
                    templatePresenceVars.maxActivePollingDelay,
                    templatePresenceVars.idlePollingDelay,
                    templatePresenceVars.awayPollingDelay,
                    templatePresenceVars.inactivityTimeBeforeIdle,
                    templatePresenceVars.inactivityTimeBeforeAway,
                    templatePresenceVars.chatIsDisabled);

            launchChatboxes.chatboxesLaunched = true;
        }
    } catch(err) {
        reportTryCatchError( err, "launchChatboxes");
    }
}

