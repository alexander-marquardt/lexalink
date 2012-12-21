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

from google.appengine.api import memcache
from google.appengine.ext import db 

from django.utils import simplejson
import datetime, copy, re
import logging

import utils, error_reporting, queries, logging
import models, constants, settings
from rs import forms, profile_utils, online_presence_support

import utils_top_level

# Chat enabled/disabled strings
# In order to over-ride a CHAT_DISABLED status, the client javascript will pass in a ENABLED value 
# If a ENABLED value is passed in, it will be stored as ACTIVE    




# memcache key prefixes
OPEN_CONVERSATIONS_MEMCACHE_DICTIONARY_PREFIX = "_open_conversations_memcache_dictionary_" + constants.FORCE_UPDATE_CHAT_MEMCACHE_STRING
CURRENTLY_OPEN_CONVERSATIONS_PREFIX = "_currently_open_conversations_" + constants.FORCE_UPDATE_CHAT_MEMCACHE_STRING
CHAT_GROUPS_MEMBERS_DICT_MEMCACHE_PREFIX = "_chat_group_members_dict_memecache_prefix_" + constants.FORCE_UPDATE_CHAT_MEMCACHE_STRING
CHAT_GROUP_MEMBERS_NAMES_MEMCACHE_PREFIX = "_chat_group_members_names_memcache_prefix_" + constants.FORCE_UPDATE_CHAT_MEMCACHE_STRING
CHAT_MESSAGE_NUMBER_MEMCACHE_PREFIX = "_memcache_message_number_memcache_prefix_" + constants.FORCE_UPDATE_CHAT_MEMCACHE_STRING
CHAT_MESSAGE_OBJECT_MEMCACHE_PREFIX = "_memcache_message_object_memcache_prefix_" + constants.FORCE_UPDATE_CHAT_MEMCACHE_STRING
CHAT_GROUPS_LIST_MEMCACHE_KEY = "_chat_groups_list_memcache_key_" + constants.FORCE_UPDATE_CHAT_MEMCACHE_STRING


def get_open_conversation_tracker_object(owner_uid, other_uid):
    

    # use memcache to simulate the DB functionality (if we ever enable the DB writes we should
    # incorporate this datastructure and memcache enhancement into the main code.)
    open_conversations_memcache_dictionary_key = OPEN_CONVERSATIONS_MEMCACHE_DICTIONARY_PREFIX + owner_uid
    open_conversations_dictionary = memcache.get(open_conversations_memcache_dictionary_key)
    open_conversation_tracker_object = None
    if open_conversations_dictionary is not None:
        if other_uid in open_conversations_dictionary:
            open_conversation_tracker_object = utils_top_level.deserialize_entities(open_conversations_dictionary[other_uid])
                
            
    return open_conversation_tracker_object


def put_open_conversation_tracker_object(owner_uid, other_uid, open_conversation_tracker_object):
    
    open_conversations_memcache_dictionary_key = OPEN_CONVERSATIONS_MEMCACHE_DICTIONARY_PREFIX + owner_uid
    open_conversations_dictionary = memcache.get(open_conversations_memcache_dictionary_key)
    if open_conversations_dictionary is None:
        open_conversations_dictionary = {}
    open_conversations_dictionary[other_uid] = utils_top_level.serialize_entities(open_conversation_tracker_object)
    memcache.set(open_conversations_memcache_dictionary_key, open_conversations_dictionary)


def delete_open_conversation_tracker_object(owner_uid, other_uid):

    # use memcache to simulate DB
    open_conversations_memcache_dictionary_key = OPEN_CONVERSATIONS_MEMCACHE_DICTIONARY_PREFIX + owner_uid
    open_conversations_dictionary = memcache.get(open_conversations_memcache_dictionary_key)
    if other_uid in open_conversations_dictionary:
        del open_conversations_dictionary[other_uid]
        memcache.set(open_conversations_memcache_dictionary_key, open_conversations_dictionary)

                
        
def update_or_create_open_conversation_tracker(owner_uid, other_uid, chatbox_minimized_maximized, type_of_conversation):
    # update the conversation_tracker on the owner object. This function
    # is only called when a new chatbox is opened, or when a new message is sent/received to a chatbox, or when
    # a chatbox is minimized/maximized. 
    # For efficiency, we only use memcache. This means that if memcache is flushed, the user might have to
    # manually re-open a chatbox.
    # 
    open_conversation_tracker_object = get_open_conversation_tracker_object(owner_uid, other_uid)
    if not open_conversation_tracker_object:
        # This is a new conversation, so we set up all the required non-changing fields 
        open_conversation_tracker_object = models.OpenConversationsTracker()
        open_conversation_tracker_object.owner_uid = owner_uid
        open_conversation_tracker_object.other_uid = other_uid
        
        if other_uid != "main" and other_uid != "groups":
            if not open_conversation_tracker_object.chatbox_title:
                if type_of_conversation == "one_on_one":
                    other_userobject = utils_top_level.get_object_from_string(other_uid)
                    open_conversation_tracker_object.chatbox_title = other_userobject.username
                elif type_of_conversation == "group":
                    group_tracker_object = utils_top_level.get_object_from_string(other_uid)
                    open_conversation_tracker_object.chatbox_title = group_tracker_object.group_name
                else:
                    assert(type_of_conversation == "leave_unchanged")
                    
            if type_of_conversation != "leave_unchanged":
                open_conversation_tracker_object.type_of_conversation = type_of_conversation # group or one_on_one
   
        else:
            open_conversation_tracker_object.chatbox_title = "NA"
        
    if chatbox_minimized_maximized != "leave_unchanged":
        open_conversation_tracker_object.chatbox_minimized_maximized = chatbox_minimized_maximized    
        
    open_conversation_tracker_object.current_chat_message_time_string = str(datetime.datetime.now())
    
    # write the owners conversations dictionary memcache
    put_open_conversation_tracker_object(owner_uid, other_uid, open_conversation_tracker_object)

def query_currently_open_conversations(owner_uid):
    
    # Get the list of conversations (chat boxes) that the user currently has open. We pull this out of memcache -
    # if memcache is flused, then the next time a user refreshes their page, they will have to manually re-open
    # the chat. 

    open_conversations_memcache_dictionary_key = OPEN_CONVERSATIONS_MEMCACHE_DICTIONARY_PREFIX + owner_uid
    open_conversations_dictionary = memcache.get(open_conversations_memcache_dictionary_key)
    currently_open_conversations_list = []
    if open_conversations_dictionary is not None:
        for other_uid in open_conversations_dictionary:
            currently_open_conversations_list.append(utils_top_level.deserialize_entities(open_conversations_dictionary[other_uid]))

    return currently_open_conversations_list

        
def get_dict_of_friends_uids_and_userinfo(lang_code, userobject_key):
    
    # returns an array of all of the users that are "chat_friends" of the current user. The returned list
    # contains all chat_friends of the current user, irrespective of if they are currently online/connected
    # to the chat.
    
    userdict = {}
    
    # Note: the "connected" in the following function does not refer to online status - it refers to the fact
    # that two users are "connected" in the sense that they have agreed to be "chat friends"
    contact_query_results = queries.query_initiate_contact_by_type_of_contact(userobject_key, "chat_friend", None , 
                                                                              constants.MAX_CHAT_FRIEND_REQUESTS_ALLOWED,
                                                                              "connected")
    for contact in contact_query_results:
        profile = getattr(contact, 'displayed_profile')
        profile_uid = str(profile.key())
        userdict[profile_uid] = {}
        userdict[profile_uid]['user_or_group_name'] = profile.username
        userdict[profile_uid]['url_description'] = profile_utils.get_profile_url_description(lang_code, profile_uid)
        # The profile.key().id() should eventually be used as the key for this dictionary, but this requires 
        # changing a lot of other code to make it work. Temporarily, we just pass in as "nid" 
        userdict[profile_uid]['nid'] = utils.get_nid_from_uid(profile_uid)
        userdict[profile_uid]['num_group_members'] = "Not used" 

    return userdict

    

def get_username_from_uid(uid):
    # function that looks up the username based on the uid. 
    # This function is currently only used in the chat functions, and looks up the username in  
    # a specific uid:username memcache, and then back to the standard userobject lookup
    memcache_key = CHAT_GROUP_MEMBERS_NAMES_MEMCACHE_PREFIX + uid
    username = memcache.get(memcache_key)    
    
    if username is None:
        userobject = utils_top_level.get_object_from_string(uid)
        username = userobject.username
        memcache.set(memcache_key, username, constants.SECONDS_PER_DAY)
    
    return username

def expire_group_members_dict_memcache(group_id):
    
    for lang_tuple in settings.LANGUAGES:
        lang_code = lang_tuple[0]
        memcache.delete(lang_code + CHAT_GROUPS_MEMBERS_DICT_MEMCACHE_PREFIX + group_id)   
        
    
def delete_uid_from_group(owner_uid, group_id):
    
    # note that in this case, the "other_uid" is the identifier of the group
    
    group_tracker_object = utils_top_level.get_object_from_string(group_id)
    
    try:
        # need to make sure that the current users uid is in the list of group members
        
        idx  = group_tracker_object.group_members_list.index(owner_uid)
        
        del group_tracker_object.group_members_list[idx]
        group_tracker_object.number_of_group_members -= 1
        utils.put_object(group_tracker_object)
        
        # expire the memcache for the list of users that are currently in the group
        expire_group_members_dict_memcache(group_id)
        
    except ValueError:
        # if owner_uid is not in the list, we get an expected ValueError
        pass
    
    except:
        # Unknown error - we should investigate this
        error_reporting.log_exception(logging.critical)

def get_group_members_dict(lang_code, group_uid):
    """ 
    Returns a dictionary object containing the users that are in the group indicated by group_id.
    The dictionary will contain a dictionary with key=uid which contains a sub-dictionary with keys
    'username' and 'nid'and 'url_description' which contain associated vlaues. 
    """
    group_members_names_dict = {} # in case of exception, we return an empty dictionary
    
    try:
        memcache_key = lang_code + CHAT_GROUPS_MEMBERS_DICT_MEMCACHE_PREFIX + group_uid  
        group_members_names_dict = memcache.get(memcache_key)
        
        if group_members_names_dict is None:
        
            group_members_names_dict = {} # must initialize as a dictionary since it is currently None
        
            group_tracker_object = utils_top_level.get_object_from_string(group_uid)
            group_members_list = group_tracker_object.group_members_list
            
            for member_uid in group_members_list:
                user_presence_status = online_presence_support.get_online_status(member_uid)
                chat_boxes_status = online_presence_support.get_chat_boxes_status(member_uid)
                
                if chat_boxes_status != constants.ChatBoxStatus.IS_DISABLED and user_presence_status != constants.OnlinePresence.TIMEOUT:                    
                    group_members_names_dict[member_uid] = {}
                    group_members_names_dict[member_uid]['user_or_group_name'] = get_username_from_uid(member_uid)
                    group_members_names_dict[member_uid]['nid'] = utils.get_nid_from_uid(member_uid)
                    group_members_names_dict[member_uid]['url_description'] = profile_utils.get_profile_url_description(lang_code, member_uid)
                    group_members_names_dict[member_uid]['profile_title'] = profile_utils.get_base_userobject_title(lang_code, member_uid)
                    group_members_names_dict[member_uid]['user_presence_status'] = user_presence_status
                else:
                    delete_uid_from_group(member_uid, group_uid)
                    
            memcache.set(memcache_key, group_members_names_dict, constants.SECONDS_BETWEEN_UPDATE_CHAT_GROUPS)
        
    except:
        error_reporting.log_exception(logging.critical)
        
    return group_members_names_dict
    

def get_friends_online_dict(lang_code, owner_uid):
    
    # Returns a dictionary object containing the users that are currently online and in the 
    # "chat_friends" list of the current user. 
    #
    # The data returned will be in the form of a dictionary with the userid as the key, and the username as the value
    
    # We include the language code in the memcache key because if the user changes languages we want to ensure
    # that the URL descriptions are returned in the correct language - which means that we have to query the 
    # database if the new language has not previously been loaded.
    online_contacts_info_dict_memcache_key = lang_code + constants.ONLINE_CHAT_CONTACTS_INFO_MEMCACHE_PREFIX + owner_uid
    online_contacts_info_dict = memcache.get(online_contacts_info_dict_memcache_key)
    if online_contacts_info_dict is None:
    
        # get the uid's of *all* "chat friends"
        all_friends_dict_memcache_key = constants.ALL_CHAT_FRIENDS_DICT_MEMCACHE_PREFIX + owner_uid
        user_info_dict = memcache.get(all_friends_dict_memcache_key)
        if user_info_dict is None:
            userobject_key = db.Key(owner_uid)
            user_info_dict = get_dict_of_friends_uids_and_userinfo(lang_code, userobject_key)
            memcache.set(all_friends_dict_memcache_key, user_info_dict, constants.ALL_CHAT_FRIENDS_DICT_EXPIRY)
        
        # Scan throug the entire list of chat_friends, and create a dictionary that is keyed by the
        # uid's of the *online* "chat friends, and that contains relevant information about each 
        # user (such as name, url_description, current online status (active, idle), and possibly other stuff in 
        # in the future)"
        online_contacts_info_dict = {}
        for uid in user_info_dict:
            user_presence_status = online_presence_support.get_online_status(uid)
            chat_boxes_status = online_presence_support.get_chat_boxes_status(uid)
            
            if chat_boxes_status != constants.ChatBoxStatus.IS_DISABLED and user_presence_status != constants.OnlinePresence.TIMEOUT: # for purposes of chat list update, offline and timeout are the same
                online_contacts_info_dict[uid] = user_info_dict[uid]
                online_contacts_info_dict[uid]['user_presence_status'] = user_presence_status
                    
        memcache.add(online_contacts_info_dict_memcache_key, online_contacts_info_dict, \
                     constants.SECONDS_BETWEEN_ONLINE_FRIEND_LIST_UPDATE)
                
    return (online_contacts_info_dict);



def query_chat_groups():
    
    query_filter_dict = {}    
    
    query_filter_dict['number_of_group_members > '] = 0
    query_filter_dict['number_of_group_members <= '] =  constants.MAX_NUM_PARTICIPANTS_PER_GROUP
    order_by = "-number_of_group_members"
    
    query = models.ChatGroupTracker.all().order(order_by)
    for (query_filter_key, query_filter_value) in query_filter_dict.iteritems():
        query = query.filter(query_filter_key, query_filter_value)

    chat_groups_query_results = query.fetch(constants.MAX_NUM_CHAT_GROUPS_TO_DISPLAY)

    return chat_groups_query_results

def query_chat_group_by_name(group_name):
    
    query_filter_dict = {}    
    
    query_filter_dict['group_name = '] = group_name
    
    query = models.ChatGroupTracker.all()
    for (query_filter_key, query_filter_value) in query_filter_dict.iteritems():
        query = query.filter(query_filter_key, query_filter_value)

    chat_group = query.get()

    return chat_group    
    

def create_chat_group(group_name, group_creator_name, group_creator_uid_string):
    
    chat_group = query_chat_group_by_name(group_name)
            
    if chat_group is None:
        chat_group = models.ChatGroupTracker()
        chat_group.group_name = group_name
        chat_group.number_of_group_members = 0
        chat_group.group_creator_name = group_creator_name
        chat_group.group_creator_uid_string = group_creator_uid_string
        chat_group.put()
    else:
        # The group already exists - No need to create another with the same name
        pass
    
    return str(chat_group.key())
    
def get_chat_groups_dict(overwrite_memcache = False):
    # returns a dictionary containing the currently available chat groups 
    
    # The chat groups list is a globally accessable memcache object, and therefore the key doesn't depend
    # on uid or any other variable.
    global_chat_groups_dict_memcache_key = CHAT_GROUPS_LIST_MEMCACHE_KEY
    
    if not overwrite_memcache:
        chat_groups_dict = memcache.get(global_chat_groups_dict_memcache_key)
    else: 
        chat_groups_dict = None
        
    if chat_groups_dict is None:
        chat_groups_dict = {}
        chat_groups_query_results = query_chat_groups()
        for chat_group in chat_groups_query_results:
            group_key = str(chat_group.key())
            chat_groups_dict[group_key] = {}
            chat_groups_dict[group_key]['user_or_group_name'] = chat_group.group_name
            chat_groups_dict[group_key]['num_group_members'] = chat_group.number_of_group_members
            chat_groups_dict[group_key]['url_description'] = "Not used"
            chat_groups_dict[group_key]['nid'] = "Not used"
            
        memcache.set(global_chat_groups_dict_memcache_key, chat_groups_dict, constants.SECONDS_BETWEEN_UPDATE_CHAT_GROUPS)

    return chat_groups_dict        



def query_recent_chat_messages(owner_uid, other_uid, last_update_time_string, type_of_conversation): 
            
    (uid1, uid2) = get_ordered_uids(owner_uid, other_uid, type_of_conversation)
    memcache_message_base_key = get_memcache_key_for_chat(uid1, uid2, type_of_conversation)
    memcache_message_number_key = CHAT_MESSAGE_NUMBER_MEMCACHE_PREFIX + memcache_message_base_key   
    newest_message_number = memcache.get(memcache_message_number_key)
    if newest_message_number == None:
        # there are no memcached messages in this conversation
        return []
    
    # ensure that we don't go below zero (note: the for loop below will exit after message_number 1)
    lowest_message_number = max(newest_message_number - constants.NUM_CHAT_MESSAGES_IN_QUERY, 0)
    
    list_of_chat_messages = []
    
    
    # Order by reverse chat_msg_time_string, so that we are guaranteed to get the  NUM_CHAT_MESSAGES_IN_QUERY
    # most recent messages that are stored in the memcache    
    for message_number in range(newest_message_number, lowest_message_number, -1):
        memcache_message_object_key = CHAT_MESSAGE_OBJECT_MEMCACHE_PREFIX + memcache_message_base_key + "_" + str(message_number)
        chat_message_object = utils_top_level.deserialize_entities(memcache.get(memcache_message_object_key))
        if chat_message_object != None:
            if chat_message_object.chat_msg_time_string >= last_update_time_string:
                list_of_chat_messages.append(chat_message_object)
            else:
                # as soon as we start seeing messages that are older than the required "last_update_time_string", we break out
                break
        else:
            error_reporting.log_exception(logging.warning, error_message = "Memcache miss in query_recent_chat_messages")
            
    return list_of_chat_messages


def get_memcache_key_for_chat(uid1, uid2, type_of_conversation):
    if type_of_conversation == "one_on_one":
        memcache_key = "one_on_one_chat_key_%s_and_%s" % (uid1, uid2)
    elif type_of_conversation == "group":
        # uid1 contains the group identifier, which is unique for each group conversation and therefore can be used 
        # as a key for all conversations in the current group.
        memcache_key = "group_chat_key:%s" % uid1
        
    return memcache_key

    
def get_ordered_uids(owner_uid, other_uid, type_of_conversation):
    
    # basically sorts the two uids and returns a tuple of the two uids, such that:
    # for one-on-one conversations: the lower of the two ids will be first followed by the higher
    # for group conversations: the group_id (which is always "other_uid") will be followed by the owner_uid
    
    
    # to prevent any issues, make sure that the uids are strings. See my StackOverflow comment for more info
    # http://stackoverflow.com/questions/7572386/why-are-appengine-database-keys-sorted-differently-than-strings
    # Note: by convention variables named "uid" should always be string representations ... 
    owner_uid = str(owner_uid)
    other_uid = str(other_uid)

    if type_of_conversation == "one_on_one":
        # always assign uid1 to the lower key value, and uid2 to the higher key value
        if owner_uid < other_uid:
            uid1 = owner_uid
            uid2 = other_uid
        else:
            uid1 = other_uid
            uid2 = owner_uid
            
    elif type_of_conversation == "group": 
        uid1 = other_uid # group id
        uid2 = owner_uid  # sender id
        
    else:
        error_reporting.log_exception(logging.critical, error_message = "type_of_conversation is %s (not valid)" % type_of_conversation)
        assert(False)
        
    return (uid1, uid2)


def store_chat_message_in_memcache(memcache_message_object_key, sender_username, message_text, uid1, uid2):
    # Write the chat message to memcache. 
    # Note: there should never be a write conflict, since by design the memcache key should be unique
    # for each message that we are writing. 
    chat_message = models.ChatMessage()
    chat_message.uid1 = uid1
    chat_message.uid2 = uid2
    chat_message.chat_msg_time_string = str(datetime.datetime.now())
    chat_message.chat_msg_text = message_text
    chat_message.sender_username = sender_username
    success = memcache.set(memcache_message_object_key, utils_top_level.serialize_entities(chat_message), constants.CHAT_MESSAGE_EXPIRY_TIME)
    # returns True if successfully written to memcache, False if not set
    if not success:
        error_reporting.log_exception(logging.critical, error_message = "Failed to write chat message to memcache. Key: " + memcache_message_object_key)
    
    return success

    
def get_and_increment_message_number_with_retries(memcache_message_number_key, num_retries):
    # gets a unique monotonically increasing number corresponding to the current message that is being sent between two users.
    # just in case there is a conflict when we try incrementing the message number, we add some retries in
    
    for i in range(num_retries):
        message_number = memcache.incr(memcache_message_number_key, delta=1, initial_value=0)
        if message_number != None:
            return message_number
        
    error_reporting.log_exception(logging.critical, error_message = "Failed to get a message number key (even after several tries) for " + memcache_message_number_key)
    return None
    
    
def store_chat_message(sender_username, from_uid, to_uid, message_text, type_of_conversation):
    # Store the chat message in the database. 
    
    # In order to ensure that a given pair of users will always access
    # the same message object, we set uid1 to the lower value key (alphabetically), 
    # and uid2 to the higher value key.
    #
    # In the case that this message is being sent to a group chat, we set uid1 to the group gid, and 
    # uid2 to the sender uid.
    
    (uid1, uid2) = get_ordered_uids(from_uid, to_uid, type_of_conversation)
    memcache_message_base_key = get_memcache_key_for_chat(uid1, uid2, type_of_conversation)
    memcache_message_number_key = CHAT_MESSAGE_NUMBER_MEMCACHE_PREFIX + memcache_message_base_key
    message_number =  get_and_increment_message_number_with_retries(memcache_message_number_key, num_retries=5)
    if message_number == None:
        return False
    
    # get a unique identifier for the current message that is being sent between these two users, based on
    # the message number and their uids)
    memcache_message_object_key = CHAT_MESSAGE_OBJECT_MEMCACHE_PREFIX + memcache_message_base_key + "_" + str(message_number)
    
    # write the actual message into the memcache. 
    success = store_chat_message_in_memcache(memcache_message_object_key, sender_username, message_text, uid1, uid2)
    return success

