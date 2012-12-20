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


<!-- the following code is the dialog and javascript for creating new chat groups -->
function submit_create_new_group_post(section_name) {

    try {
        $.ajax({
            type: 'post',
            url:  "/rs/store_" + section_name + "/",
            data: $("form#id-" + section_name + "-form").serialize(),
            success: function(response) {
                //chan_utils.call_process_json_most_recent_chat_messages(json_response);
                $("#id-create-new-group-input").val('');

                chan_utils.call_poll_server_for_status_and_new_messages();
                // make sure that the list of groups is shown after they create a new group
                $("#groups").chatbox("option", "boxManager").maximizeBox();
            },
            error: function(jqXHR, textStatus, errorThrown) {
                $("#id-error-dialog-box").dialog();
                $("#id-error-dialog-box").text(jqXHR.responseText);
                report_ajax_error(textStatus, errorThrown, "submit_create_new_group_post");
            },
            complete: function(response) {
                $("#id-create-group-dialog").dialog('close');
            }
        });
    } catch(err) {
        report_try_catch_error( err, "submit_create_new_group_post");
    }
}

function handle_submit_create_new_group(section_name) {
    // setup submit button and associate the action when clicked

    try {
        var submit_button_id = "#id-submit-" + section_name;
        var edit_section_id = "#id-edit-" + section_name + "-section";

        $(submit_button_id).click(function() {
            submit_create_new_group_post(section_name);
        });

        // Check to see if the enter key has been pressed inside the section -- treat this this same
        // as if the user had pressed the submit button
        $(edit_section_id).keydown(function(e) {
            if (e.keyCode == 13) {
                submit_create_new_group_post(section_name);
                e.stopImmediatePropagation();
                e.stopPropagation();
                return false;
            }
        });

        mouseover_button_handler($(submit_button_id));
    } catch(err) {
        report_try_catch_error( err, "handle_submit_create_new_group");
    }
}



function launch_chatboxes(){

    try {

        // we need to make sure that we only launch the chatboxes once, even though this code might be called
        // multiple times.
        if (typeof launch_chatboxes.chatboxes_launched == 'undefined')
            launch_chatboxes.chatboxes_launched = false;

        if (!launch_chatboxes.chatboxes_launched) {

            handle_submit_create_new_group("create_new_group");

            if (remove_chatboxes)
                template_chatbox_vars.chat_is_disabled = "yes";
            
            setupContactsAndGroupsBoxes(template_chatbox_vars.chat_is_disabled);

            // Open the socket that will be used for communicating from the browser to the server.
            // Note: since all chat goes through the server, the same socket will be used for channeling
            // all chats that a given user is currently participating in.
            chan_utils.setup_and_channel_for_current_client(
                    template_chatbox_vars.owner_uid,
                    template_chatbox_vars.username,
                    template_chatbox_vars.chat_max_active_polling_delay,
                    template_chatbox_vars.chat_idle_polling_delay,
                    template_chatbox_vars.chat_away_polling_delay,
                    template_chatbox_vars.chat_inactivity_time_before_idle,
                    template_chatbox_vars.chat_inactivity_time_before_away,
                    template_chatbox_vars.chat_is_disabled);

            launch_chatboxes.chatboxes_launched = true;
        }
    } catch(err) {
        report_try_catch_error( err, "launch_chatboxes");
    }
};
