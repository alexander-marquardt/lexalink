# -*- coding: utf-8 -*- 

################################################################################
# LexaLink Copyright information - do not remove this copyright notice
# Copyright (C) 2012 
#
# Lexalink - a free social network and dating website platform for the Google App Engine. 
#
# Original author: Alexander Marquardt
# Documentation and additional information: http://www.LexaLink.com
# Git source code repository: https://github.com/alexander-marquardt/lexalink 
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


from django.core.urlresolvers import reverse

from django.utils import simplejson
from django import http
from google.appengine.api import memcache
from django.utils.translation import ugettext


import time, logging, datetime

from rs import models, utils, utils_top_level, constants, error_reporting, chat_support, profile_utils, online_presence_support

def initialize_main_and_group_boxes_on_server(request):
    # ensures that the main and group boxes have an open_conversation object assigned - this is 
    # needed for tracking the chatbox_minimized_maximized status. 
    #
    # Note: we do not want to modify chatbox_minimized_maximized if it has already been assigned a value. Therefore, we pass in
    # a 'leaveUnchanged' value to the update_or_create_open_conversation_tracker function
    
    try:
        if 'userobject_str' in request.session:
            owner_uid = request.session['userobject_str']
            chat_support.update_or_create_open_conversation_tracker(owner_uid, "main", chatbox_minimized_maximized='leaveUnchanged', type_of_conversation="NA")
            chat_support.update_or_create_open_conversation_tracker(owner_uid, "groups", chatbox_minimized_maximized='leaveUnchanged', type_of_conversation="NA")
            
            # expire the timer on the memcache for group updates, so that we immediately send the new list
            chat_group_timer_memcache_key = "chat_group_timer_memcache_key_" + owner_uid
            memcache.delete(chat_group_timer_memcache_key)
            
            # same for friends list
            check_friends_online_last_update_memcache_key = constants.CHECK_CHAT_FRIENDS_ONLINE_LAST_UPDATE_MEMCACHE_PREFIX + owner_uid
            memcache.delete(check_friends_online_last_update_memcache_key)
        else:
            # user is not logged in (probably session timed out)-- do nothing
            pass
                    
        return http.HttpResponse()
    except:
        error_reporting.log_exception(logging.critical)
        return http.HttpResponseBadRequest("Error");     

def set_minimize_chat_box_status(request):
    # User has clicked on the "_" to minimize a conversation. We want to remember this for future/other
    # windows, and re-loads.
    try:
        owner_uid = request.session['userobject_str']
        other_uid = request.POST.get('otherUid', None)
        chatbox_minimized_maximized = request.POST.get('chatboxMinimizedMaximized', None)
        
        assert(owner_uid and other_uid and chatbox_minimized_maximized)
        type_of_conversation = 'leaveUnchanged' # we will not change this value, so don't need to pass it in
        chat_support.update_or_create_open_conversation_tracker(owner_uid, other_uid, chatbox_minimized_maximized, type_of_conversation)
            
        return http.HttpResponse()
    except:
        error_reporting.log_exception(logging.critical)
        return http.HttpResponseBadRequest("Error");     
    

            

    
def close_chat_box(request):
    # user has clicked on the X to delete a chatbox. Remove it from the database/memcache of open conversations.
    
    
    try:
        if not request.session.__contains__('userobject_str'):
            error_reporting.log_exception(logging.warning, error_message = "No session")
            # This is not an error in the program, it is just that their session has expired, so return a normal HttpResponse
            return http.HttpResponse("Error - no session");
            
        owner_uid = request.session['userobject_str']
        other_uid = request.POST.get('otherUid', '')
        type_of_conversation = request.POST.get('typeOfConversation', '')
        assert (other_uid and type_of_conversation)
        
        if type_of_conversation == "group":
            assert('username' in request.session)
            username = request.session['username']
            
            chat_support.delete_uid_from_group(owner_uid, other_uid)
            
        chat_support.delete_open_conversation_tracker_object(owner_uid, other_uid)

        return http.HttpResponse()
    except:
        error_reporting.log_exception(logging.critical)
        return http.HttpResponseBadRequest("Error");
    
    
def close_all_chatboxes_internal(owner_uid):
    # user has logged-in/started new session - close all previously open chat boxes
    
    try:
        open_conversation_objects = chat_support.query_currently_open_conversations(owner_uid)
        for open_conversation_object in open_conversation_objects:
            other_uid = open_conversation_object.other_uid
            if open_conversation_object.type_of_conversation == "group" : 
                chat_support.delete_uid_from_group(owner_uid, other_uid)
                
            chat_support.delete_open_conversation_tracker_object(owner_uid, other_uid)
    except:
        error_reporting.log_exception(logging.critical)            
            
        
def close_all_chatboxes_on_server(request):
    
    try:
        if 'userobject_str' in request.session:
            owner_uid = request.session['userobject_str']
            close_all_chatboxes_internal(owner_uid)
        else:
            # Chatboxes should have automatically been closed after session expires - due to the fact that CHAT_DISABLED status
            # is returned when polling status when a session is not passed in.
            error_reporting.log_exception(logging.warning, error_message = "User tried to close all chatboxes after session expired")
            
        return http.HttpResponse()
    except:
        error_reporting.log_exception(logging.critical)
        return http.HttpResponseBadRequest("Error");

def update_chatbox_status_on_server(request):
    
    try:
        if 'userobject_str' in request.session:
            owner_uid = request.session['userobject_str']
            chat_boxes_status = request.POST.get('chatBoxesStatus', '')
            assert(chat_boxes_status)
            update_chat_boxes_status(owner_uid, chat_boxes_status)
            response = "OK"
        else:
            response = constants.SessionStatus.EXPIRED_SESSION 

        return http.HttpResponse(response)
    except:
        error_reporting.log_exception(logging.critical)
        return http.HttpResponseBadRequest("Error");
    

def update_user_presence_on_server(request):
    
    try:
        if 'userobject_str' in request.session:
            owner_uid = request.session['userobject_str']
            user_presence_status = request.POST.get('userPresenceStatus', '')
            assert(user_presence_status)
            online_presence_support.update_online_status(owner_uid, user_presence_status)
            response = "OK"
        else:
            response = constants.SessionStatus.EXPIRED_SESSION 

        return http.HttpResponse(response)
    except:
        error_reporting.log_exception(logging.critical)
        return http.HttpResponseBadRequest("Error");
    

            
def update_chat_boxes_status(owner_uid, chat_boxes_status):
    
    try:
        chat_boxes_status_memcache_key = constants.ChatBoxStatus.CHAT_BOX_STATUS_MEMCACHE_TRACKER_PREFIX + owner_uid
        memcache.set(chat_boxes_status_memcache_key, chat_boxes_status)
        
        if chat_boxes_status == 'chatEnabled':
            chatbox_minimized_maximized = "maximized"
        elif chat_boxes_status == 'chatDisabled':
            chatbox_minimized_maximized = "minimized"
        else:
            raise Exception("Unknown chat_boxes_status: %s" % chat_boxes_status)
           
        chat_support.update_or_create_open_conversation_tracker(owner_uid, "main", chatbox_minimized_maximized=chatbox_minimized_maximized, type_of_conversation="NA")
        chat_support.update_or_create_open_conversation_tracker(owner_uid, "groups", chatbox_minimized_maximized=chatbox_minimized_maximized, type_of_conversation="NA")
         
    except:
        error_reporting.log_exception(logging.critical)    
    
def poll_server_for_status_and_new_messages(request):
    
   
    try:
        lang_code = request.LANGUAGE_CODE
        
        new_update_time_string = str(datetime.datetime.now())
        response_dict = {}
    
        if 'userobject_str' in request.session:
            owner_uid = request.session['userobject_str']            
        
            if request.method == 'POST':
                json_post_data = simplejson.loads(request.raw_post_data)
                
                last_update_time_string_dict = json_post_data['lastUpdateTimeStringDict']
                user_presence_status = json_post_data['userPresenceStatus']
                
                if 'getFriendsOnlineDict' in json_post_data and json_post_data['getFriendsOnlineDict'] == 'yes':
                    get_friends_online_dict = True 
                else: 
                    get_friends_online_dict = False
                
                if 'getChatGroupsDict' in json_post_data and json_post_data['getChatGroupsDict'] == 'yes':
                    get_chat_groups_dict = True 
                else: 
                    get_chat_groups_dict = False                
                
                if 'listOfOpenChatGroupsMembersBoxes' in json_post_data:
                    list_of_open_chat_groups_members_boxes_on_client = json_post_data['listOfOpenChatGroupsMembersBoxes']
                else:
                    list_of_open_chat_groups_members_boxes_on_client = []
            else:
                assert(False)
            
            online_presence_support.update_online_status(owner_uid, user_presence_status)
            
            assert(owner_uid == request.session['userobject_str'])
                                    
            chat_boxes_status = online_presence_support.get_chat_boxes_status(owner_uid)
            response_dict['chatBoxesStatus'] = chat_boxes_status
            
            if chat_boxes_status != constants.ChatBoxStatus.IS_DISABLED:
            
                if get_friends_online_dict:
                    # we use memcache to prevent the friends online from being updated every time data is polled- 
                    # we set the memcache to expire after a certian amount of time, and only if it is expired
                    # will we generate a new friends list - this is done like this to reduce server loading. 
                    check_friends_online_last_update_memcache_key = constants.CHECK_CHAT_FRIENDS_ONLINE_LAST_UPDATE_MEMCACHE_PREFIX + owner_uid
                    contacts_info_dict = memcache.get(check_friends_online_last_update_memcache_key)
                    if contacts_info_dict is None:
                        # get the data structure that represents the "friends online" for the current user.
                        contacts_info_dict = chat_support.get_friends_online_dict(lang_code, owner_uid);
                        memcache.set(check_friends_online_last_update_memcache_key, contacts_info_dict, constants.SECONDS_BETWEEN_GET_FRIENDS_ONLINE)
                   
                    # Send the contacts list since the client requested it
                    response_dict['contactsInfoDict'] = contacts_info_dict
                
                
                # get the data structure that represents the currently available chat groups - this is common for
                # all users - this is memcached and pulled from database if not available.
                chat_groups_dict = chat_support.get_chat_groups_dict();
                if get_chat_groups_dict:
                    response_dict['chatGroupsDict'] = chat_groups_dict
                    
                    
                if list_of_open_chat_groups_members_boxes_on_client:
                    # the client has open chat groups, send updated list of which members are in each group
                        
                    # loop over list_of_open_chat_groups_members_boxes_on_client and get the members in each group
                    # notice that this is not a list of the members for all groups that the user currently has open,
                    # it is a list of the members for the groups that the user currently has a window open that has
                    # the list of members (group chat and the display of who is in the group are two different windows)
                    response_dict['chatGroupMembers'] = {}
                    for group_uid in list_of_open_chat_groups_members_boxes_on_client:
                        response_dict['chatGroupMembers'][group_uid] = chat_support.get_group_members_dict(lang_code, owner_uid, group_uid)
                
                response_dict['conversationTracker'] = {} 
                open_conversation_objects = chat_support.query_currently_open_conversations(owner_uid)
                for open_conversation_object in open_conversation_objects:
                    
                    other_uid = open_conversation_object.other_uid
                    
                    # Construct the JSON response
                    response_dict['conversationTracker'][other_uid] = {}                    
                    
                    # Send in a 'keepOpen' value so that the client knows that this convesation is still active
                    # and should not be closed. (if it does not receive a 'keepOpen' value in the response, then
                    # the client will close the associated chatbox
                    response_dict['conversationTracker'][other_uid]['keepOpen'] = "yes"
        
                    if other_uid in last_update_time_string_dict:
                        last_update_time_string = last_update_time_string_dict[other_uid]
                    else:
                        last_update_time_string = ''
                        
                    # if the time of the last message received by the browser is less than the last update
                    # then we need to send the client an update
                    if  last_update_time_string < open_conversation_object.current_chat_message_time_string:
                        
                        chatbox_title = open_conversation_object.chatbox_title
    
                        response_dict['conversationTracker'][other_uid]['updateConversation'] = "yes"
                        response_dict['conversationTracker'][other_uid]['chatboxMinimizedMaximized'] = open_conversation_object.chatbox_minimized_maximized
                        
                        # make sure this is not the main, or groups chatbox (ie, it must be a conversation box)
                        if other_uid != "main" and other_uid != "groups":
                            
                            type_of_conversation = open_conversation_object.type_of_conversation # 'oneOnOne' or "group"
                            response_dict['conversationTracker'][other_uid]['typeOfConversation'] = type_of_conversation
                            
                            recent_chat_messages = chat_support.query_recent_chat_messages(owner_uid, other_uid, last_update_time_string, type_of_conversation)
                            recent_chat_messages.reverse()
        
                            response_dict['conversationTracker'][other_uid]['chatboxTitle'] = chatbox_title
                            response_dict['conversationTracker'][other_uid]['chatMsgTimeStringArr'] = []
                            response_dict['conversationTracker'][other_uid]['senderUsernameDict'] = {}
                            response_dict['conversationTracker'][other_uid]['chatMsgTextDict'] = {}
                            
                            if type_of_conversation == 'oneOnOne':
                                response_dict['conversationTracker'][other_uid]["nid"] = utils.get_nid_from_uid(other_uid)                       
                                response_dict['conversationTracker'][other_uid]['urlDescription'] = profile_utils.get_profile_url_description(lang_code, other_uid)
    
                            for msg_object in recent_chat_messages:
                                response_dict['conversationTracker'][other_uid]['chatMsgTimeStringArr'].append(msg_object.chat_msg_time_string)
                                response_dict['conversationTracker'][other_uid]['chatMsgTextDict'][msg_object.chat_msg_time_string] = msg_object.chat_msg_text
                                response_dict['conversationTracker'][other_uid]['senderUsernameDict'][msg_object.chat_msg_time_string] = msg_object.sender_username
                                
                            response_dict['conversationTracker'][other_uid]['lastUpdateTimeString'] = open_conversation_object.current_chat_message_time_string
                                     
        else: # *not* 'userobject_str' in request.session
            (response_dict['sessionStatus'], response_dict['chatBoxesStatus']) = \
                (constants.SessionStatus.EXPIRED_SESSION , constants.ChatBoxStatus.IS_DISABLED)

    except:
        # if there is an error - return INTERNAL_ERROR so that the script will stop polling
        (response_dict['sessionStatus'], response_dict['chatBoxesStatus']) = \
            (constants.SessionStatus.SERVER_ERROR , constants.ChatBoxStatus.IS_DISABLED)
        error_reporting.log_exception(logging.error)

        
    json_response = simplejson.dumps(response_dict)
    return http.HttpResponse(json_response, mimetype='text/javascript')


def process_message_to_chat_group(from_uid, group_uid, chatbox_minimized_maximized):
    # create or update a conversation object on all group members. We also need to periodically check the online
    # status of all group members to ensure that they are not offline, and if they are offline they should be removed
    # from the group updates.

    try:
        type_of_conversation = "group"
                       
        verify_from_uid_is_in_group = False
        group_tracker_object = utils_top_level.get_object_from_string(group_uid)
        group_members_list = group_tracker_object.group_members_list[:]
        for owner_uid in group_members_list:
            
            if from_uid == owner_uid:
                verify_from_uid_is_in_group = True
                
            chat_support.update_or_create_open_conversation_tracker(owner_uid, group_uid, chatbox_minimized_maximized, type_of_conversation)
            
        if not verify_from_uid_is_in_group:
            # the user that has sent a message to this group is not currently in the list of members
            # in the group. This could happen if they have "timed out" (for example a dropped connection
            # that came back), but they are now trying to send a message to a group that they still have
            # displayed on their screen. 
            open_new_chatbox_internal(from_uid, group_uid, type_of_conversation)
            
    except:
        error_reporting.log_exception(logging.critical)
        

def post_message(request):
    # 
    # when a user sends a message, it is processed as a post. Therefore, this function stores the message
    # in the appropriate data structures for future lookup/sending on the next poll of the receiver (client
    # code is designed so that the sender does a poll immediately and receiver will get the message whenever
    # their next poll occurs).
    # 
    # For efficiency, when we do a post, we also return all the most recent chat messages that 
    # the client browser has not yet updated (since we have to send a response anyway, we just make it
    # a more complete response)
    from django.utils.html import strip_tags
    
    try: 
        new_update_time_string = str(datetime.datetime.now())
        
        if 'userobject_str' in request.session:
            from_uid = request.session['userobject_str']
            
            assert('username' in request.session)
            sender_username = request.session['username']

        else: 
            error_message = "Error - session not found"
            error_reporting.log_exception(logging.error, error_message = error_message)
            return http.HttpResponse(error_message)
        
        # They just posted a message, and therefore are active.
        online_presence_support.update_online_status(from_uid, constants.OnlinePresence.ACTIVE)
        
        if request.method == 'POST':
            json_post_data = simplejson.loads(request.raw_post_data)
            to_uid = json_post_data['toUid']
            # for efficiency we pull username from post instead of reading from database, however this is a
            # potential security hole that could allow someone to (sort of) pretend to be another user.            
            # Remove this code immediately - just  waiting for current sessions to expire.
            sender_username = json_post_data['senderUsername']
            
            type_of_conversation = json_post_data['typeOfConversation']
            
        else:
            assert(False)       
        
        if to_uid and from_uid and sender_username and type_of_conversation:
            message_text = json_post_data['message']
            message_text = message_text[:constants.CHAT_MESSAGE_CUTOFF_CHARS]
            message_text = strip_tags(message_text)
            success = chat_support.store_chat_message(sender_username, from_uid, to_uid, message_text, type_of_conversation)   
            chatbox_minimized_maximized = "maximized"
            
            if type_of_conversation == 'oneOnOne':
                # create or update a conversation object on both the sender and receiver
                switch_uids_struct = [(from_uid, to_uid), (to_uid, from_uid)]    
                for (owner_uid, other_uid) in switch_uids_struct:
                    chat_support.update_or_create_open_conversation_tracker(owner_uid, other_uid, chatbox_minimized_maximized, type_of_conversation)
            elif type_of_conversation == "group":
                process_message_to_chat_group(from_uid, to_uid, chatbox_minimized_maximized)
                
            
        else: 
            error_reporting.log_exception(logging.critical, "post_message has been called without enough info in post")
            return http.HttpResponseBadRequest("Error");
        
        if success:   
            return poll_server_for_status_and_new_messages(request)
        else:
            raise Exception("Chat message was not delivered");
    except:
        error_reporting.log_exception(logging.critical)
        return http.HttpResponseServerError("Error")
    
    

        

def open_new_chatbox_internal(owner_uid, other_uid, type_of_conversation):
    

    try:
        if type_of_conversation == "group":
            # need to make sure that the current users uid is in the list of group members
            group_tracker_object = utils_top_level.get_object_from_string(other_uid)
            group_members_list = group_tracker_object.group_members_list[:]
            if owner_uid not in group_members_list:
                # For group conversations, the group_id is passed in the other_uid parameter
                group_id = other_uid
                
                group_members_list.append(owner_uid)
                group_tracker_object.group_members_list = group_members_list
                group_tracker_object.number_of_group_members += 1
                utils.put_object(group_tracker_object)  
                
                # expire the memcache for the list of users that are currently in the group - since 
                # we have just added a new user the memcached list is out of date
                chat_support.expire_group_members_dict_memcache(group_id)
                             
                
        # Note: do not move the following call to update_or_create_open_conversation_tracker to above the 
        # store_chat_message call, or it will cause the message to appear twice.
        chatbox_minimized_maximized = 'leaveUnchanged'
        chat_support.update_or_create_open_conversation_tracker(owner_uid, other_uid, chatbox_minimized_maximized, type_of_conversation)
    except:
        error_reporting.log_exception(logging.critical)        
        
    
def open_new_chatbox(request):
    # Function to call to guarantee that a chatbox has been allocated. We use this when we create a new 
    # chatbox but the user has not sent or received any messages yet, and when the user sends a message
    # in a chatbox that was previously "dead" (closed in another window and therefore no longer active)

    try:
        if 'userobject_str' in request.session:
            owner_uid = request.session['userobject_str']
            
            if request.method == 'POST':
                json_post_data = simplejson.loads(request.raw_post_data)  
                other_uid = json_post_data['otherUid']
                type_of_conversation = json_post_data['typeOfConversation']            
                    
                if other_uid != "main" and other_uid != "groups":
                    open_new_chatbox_internal(owner_uid, other_uid, type_of_conversation)   
    
                response =  poll_server_for_status_and_new_messages(request)
        else:
            error_reporting.log_exception(logging.warning, error_message ="Error in user trying to open new chatbox.")
            response =  http.HttpResponseBadRequest("Error")
    except:
        error_reporting.log_exception(logging.critical, error_message = "Exception trying to open new chatbox")
        response = http.HttpResponseBadRequest("Error" )
    
    
    return response
    
def store_create_new_group(request):
    # this function is called when a user wishes to create a new chat group. 
    
    try:
        if 'userobject_str' in request.session:

            response_dict = {}
            owner_uid = request.session['userobject_str']
            
            assert('username' in request.session)
            sender_username = request.session['username']
                
            new_group_name = request.POST.get('createNewGroupName', None)
            # make sure that the group name is not too long (to prevent buffer overflow attacks, etc)
            new_group_name = new_group_name[:constants.MAX_CHARS_IN_GROUP_NAME]
            
            # monitor the number of groups that this user is trying to create, and if a limit is exceeded do not
            # allow any more creations
            memcache_key = "max_chat_groups_per_user_" + owner_uid
            current_groups_count = memcache.get(memcache_key)
            
            if current_groups_count is None:
                current_groups_count = 0
            
            if current_groups_count > constants.MAX_CHAT_GROUPS_PER_USER:
                # check if the named group already exists, and if it does return it
                chat_group = chat_support.query_chat_group_by_name(new_group_name)
                if chat_group is not None:
                    group_gid = chat_group.key.urlsafe()
                else:
                    # otherwise, the group does not already exist and this user cannot create any more groups. Return an error.
                    return http.HttpResponseBadRequest(ugettext("Error - group creation limit exceeded"))
            else:
                current_groups_count += 1
                memcache.set(memcache_key, current_groups_count, constants.SECONDS_BETWEEN_EXPIRE_MAX_CHAT_GROUPS_PER_USER)

                userobject = utils_top_level.get_object_from_string(owner_uid)
                group_gid = chat_support.create_chat_group(new_group_name, userobject.username, owner_uid)
                
            open_new_chatbox_internal(owner_uid, group_gid, type_of_conversation = "group")
            
            # reset the memcache for the chat_groups
            chat_support.get_chat_groups_dict(overwrite_memcache = True)
            
            # expire the timer on the memcache for group updates, so that we immediately send the new list
            chat_group_timer_memcache_key = "chat_group_timer_memcache_key_" + owner_uid
            user_group_list_is_up_to_date = memcache.delete(chat_group_timer_memcache_key)
            
            response = http.HttpResponse("OK")
            
        else:
            error_reporting.log_exception(logging.warning, "Session error in user trying to create new chat group.")
            response = http.HttpResponseBadRequest(ugettext("Error - you appear to have been logged out"));
    except:
        error_reporting.log_exception(logging.critical)
        response = http.HttpResponseBadRequest("Error");
        
        
    
    return response
        
        