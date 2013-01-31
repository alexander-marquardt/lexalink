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


# the following code snippet is from the rapid_development_with_djang_gae presentation, p19.
from google.appengine.ext import db , ndb
from user_profile_main_data import UserSpec
from user_profile_details import UserProfileDetails

import settings, text_fields

import datetime, time

# Important- memcache note:
# The python/django/app-engine implementation of memcache appears to not only store the object that you are
# trying to cache, but it also includes objects that are pointed to from the current object. This creates
# a lot of difficulties (bloat) in properly using memcache, and therefore it should be avoided until it is understood
# how to work around this behaviour.

############# ALL DJANGO MODELS SHOULD DERIVE FROM db.Model ############

class SpamMailStructures(ndb.Model):
    # Tracks various statistics that can indicate if the owner userobject is a spammer
    #
    
    """ This following variables are used for keeping track of how many messages a user 
    has sent in a single day. If the number is high, we will make them enter a captcha for every
    new message beyond the limit. Note: we only count messages sent to new contacts, meaning that
    the message
    """
    
    datetime_first_mail_sent_today  = ndb.DateTimeProperty(indexed = False) 
    
    # this only counts number of messages sent to new contacts. This is used for limiting the number
    # of new contacts that can be messaged in a given time limit.
    num_mails_sent_today = ndb.IntegerProperty(default = 0, indexed = False) 
    
    # count number of messages sent in total, including multiple count for multiple messages sent to
    # the same user.
    num_mails_sent_total = ndb.IntegerProperty(default = 0, indexed = False) 
    
    """Use feedback from other users to determine if this is a SPAMMER -- if so,
    increase the number of times captcha is shown .. also, after a certian limit
    their messages should be directly sent to trash, and an email sent to admin. """
    num_times_reported_as_spammer_total = ndb.IntegerProperty(default = 0, indexed = False) 
        
    number_of_captchass_solved_total = ndb.IntegerProperty(default = 0, indexed = False) 
    
    num_times_blocked = ndb.IntegerProperty(default = 0, indexed = False) 
    
    # keep track of when each object is last written - needed if for some reason we need to see objects
    # that were recently modified. 
    last_write_time = ndb.DateTimeProperty(auto_now = True)
    

class UniqueLastLoginOffsets(ndb.Model):
    # Contains the offsets that will be applied to the unique_last_login value in UserMode objects.
    # Since all query results on UnserModel are ordered according to unique_last_login, we can use
    # these offsets to give certian users priority. For example, a user who has posted a profile
    # photo might be bumped up by 5 days, someone with private photos by 2 days, someone with an 
    # "about me" secion +2 days .. etc.
    # It is expected that this will be a reference property of UserModel, and therefore each
    # userobject should only contain a single one of this object.
    
    
    # Note: we store these as boolean values so that if we decide to change the weight of any of the
    # values in the future, the database will remain unaffected (it will only be a code modification)
    has_profile_photo_offset = ndb.BooleanProperty(default=False, indexed = False)
    has_private_photo_offset = ndb.BooleanProperty(default=False, indexed = False)
    has_public_photo_offset = ndb.BooleanProperty(default=False, indexed = False)
    has_about_user_offset =  ndb.BooleanProperty(default=False, indexed = False)
    has_languages_offset = ndb.BooleanProperty(default=False, indexed = False)
    has_entertainment_offset = ndb.BooleanProperty(default=False, indexed = False)
    has_athletics_offset = ndb.BooleanProperty(default=False, indexed = False)
    has_turn_ons_offset = ndb.BooleanProperty(default=False, indexed = False)
    has_erotic_encounters_offset = ndb.BooleanProperty(default=False, indexed = False)
    has_email_address_offset = ndb.BooleanProperty(default=False, indexed = False)

    
class UserSearchPreferences2(ndb.Model):
    # This classs contain the stored parameters from the last search that the user has done.
    # This allows the search boxes to be set to appropriate values (based on the last settings)
    # for a given user. (This is given a "2" suffix because we used to have a different UserSearchPrefernces
    # model, which we instantiated as a chile of UserModel -- but this made the gaebar backups fail.
    # So .. all search storage was re-written.


    # sex refers to the sex that the user is searching for
    sex = ndb.StringProperty(required=True, indexed = False)
    age = ndb.StringProperty(required=True, indexed = False)

    country = ndb.StringProperty(required=False,  indexed = False)
    region = ndb.StringProperty(required=False,  indexed = False)
    sub_region = ndb.StringProperty(required=False,  indexed = False)
    
    query_order = ndb.StringProperty(default="unique_last_login", indexed = False)

    # the following variable is used to inform new users that they can now do a search.
    user_has_done_a_search = ndb.BooleanProperty(default = False, indexed = False)

    
    if settings.BUILD_NAME != "Language" and settings.BUILD_NAME != "Friend":
        relationship_status = ndb.StringProperty(default="----", indexed = False)
        # preference refers to the sex that other users are looking for (ie. the sex that the current user is claiming to be)
        preference = ndb.StringProperty(default="----", indexed = False)
    if settings.BUILD_NAME == "Language":
        #native_language = ndb.StringProperty(required=False, default="----")
        language_to_teach = ndb.StringProperty(default="----", indexed = False)
        language_to_learn = ndb.StringProperty(default="----", indexed = False) 
    if settings.BUILD_NAME == "Friend":
        for_sale = ndb.StringProperty(required=True,  indexed = False)
        for_sale_sub_menu = ndb.StringProperty(required=True, indexed = False)
        friend_price = ndb.StringProperty(required=True, indexed = False)
        friend_currency = ndb.StringProperty(required=True,  indexed = False)

        
    # Note: the following value is not a search-vale -- but, it did not make sense to create a new structure 
    # just for storing this, and I didn't want to write it onto the main userobject.
    if settings.BUILD_NAME != 'Language' and settings.BUILD_NAME != "Friend":
        lang_code = ndb.StringProperty(default = 'es', indexed = False)
    else:
        lang_code = ndb.StringProperty(default = 'en', indexed = False)
    
    
############################################
class UnreadMailCount(ndb.Model):
    # Note: objects of this class should be updated inside transactions, since they can be modified by various
    # sources at the same time.
   
    # this counts the number of messages from unique contacts -- ie. a single user who sends 
    # 5 messages will only be counted once. (this is displayed as the number of unread messages)
    unread_contact_count = ndb.IntegerProperty(required=True) 
    
    # count the number of unread new messages since the last time we sent this user an email about
    # unread messages. Note: due to implementation issues,
    # in reality, this value corresponds to the number of new messages received since the last
    # time a notification email was sent out *minus* the number of messages that the user has marked as 
    # read in the same time period (even if they were older messages). However, it basically allows 
    # us to only mail users who have received new messages since the last email update. 
    # We also reset this value each time the user logs in - since they should at least see/know that
    # they have a bunch of unread messages, and therefore we don't need to inform them about
    # messages received before their most recent login.
        
    num_new_since_last_notification = ndb.IntegerProperty(default = 0) 
    
    # date of last notification indicates when we previously sent this user an email about new messages
    # auto_now_add means that this will be assigned the current time, the first time that this object
    # is written to the database. 
    date_of_last_notification = ndb.DateTimeProperty(auto_now_add = True) 
    
    # date/time that the next notification should be sent to the user. This is computed based on their
    # preferences, and allows us to perform a query on the "when_to_send_next_notification" to see if the 
    # current time is greater than the time at which the notification needs to be sent. 
    when_to_send_next_notification = ndb.DateTimeProperty(default = datetime.datetime.max) 
    
    # in order to be able to pass notification values through URLs it is convenient to have them as strings
    # This allows us to do queries directly on the string field, as opposed to on the datetime field. 
    when_to_send_next_notification_string = ndb.StringProperty(default = str(datetime.datetime.max))

    
class CountInitiateContact(ndb.Model):
    # Keeps track of the number of "Initiate Contact" (kisses, winks, keys) that the user has received.
    # This counter will be reset each time the user logs in.
    
    # The num_received_xxx_stored_last_login is the value that is accumulated, since the last time the user
    # logged in to the system. The value is reset to 0 each time the client logs in.
    # *previous*_num_received_xxx take the value of num_received_xxx_since_last_login
    # each time the user logs in. 
    #
    # The value shown to the user will be the summation of the two values. This provides us with a continuasly
    # rolling set of "new" contact requests, that reflect what the user has received since his last (previous)
    # login.

    num_received_kiss_since_last_login = ndb.IntegerProperty(default = 0, indexed = False) 
    previous_num_received_kiss = ndb.IntegerProperty(default = 0, indexed = False) 

    num_received_wink_since_last_login = ndb.IntegerProperty(default = 0, indexed = False) 
    previous_num_received_wink = ndb.IntegerProperty(default = 0, indexed = False) 

    num_received_key_since_last_login = ndb.IntegerProperty(default = 0, indexed = False) 
    previous_num_received_key = ndb.IntegerProperty(default = 0, indexed = False) 
    
    num_received_friend_request_since_last_login = ndb.IntegerProperty(default = 0, indexed = False) 
    previous_num_received_friend_request = ndb.IntegerProperty(default = 0, indexed = False) 
    
    num_received_friend_confirmation_since_last_login = ndb.IntegerProperty(default = 0, indexed = False) 
    previous_num_received_friend_confirmation = ndb.IntegerProperty(default = 0, indexed = False) 
    
    # date of last notification indicates when we previously sent this user an email about new 
    # initiate-contact requests (eg. kiss, wink, key)
    # auto_now_add means that this will be assigned the current time, the first time that this object
    # is written to the database. 
    date_of_last_notification = ndb.DateTimeProperty(auto_now_add = True, indexed = False) 
    
    
    # count number of new initiate_contact requests since the last time a notification was sent out. This is a summation
    # of kisses, winks, and keys received.
    num_new_since_last_notification = ndb.IntegerProperty(default = 0, indexed = False)

    # date/time that the next notification should be sent to the user. This is computed based on their
    # preferences, and allows us to perform a query on the "when_to_send_next_notification" to see if the 
    # current time is greater than the time at which the notification needs to be sent. 
    when_to_send_next_notification = ndb.DateTimeProperty(default = datetime.datetime.max, indexed = False)    
    
    # in order to be able to pass notification values through URLs it is convenient to have them as strings
    # This allows us to do queries directly on the string field, as opposed to on the datetime field. 
    when_to_send_next_notification_string = ndb.StringProperty(default = str(datetime.datetime.max))
    
    
    # Some types of requests need to have limits placed on them, such as number of "chat friends", or number of "keys" 
    # shared with other users. We track these counters here
    num_sent_key = ndb.IntegerProperty(default = 0, indexed = False) 
    num_sent_wink = ndb.IntegerProperty(default = 0, indexed = False) 
    num_sent_key = ndb.IntegerProperty(default = 0, indexed = False) 
    num_sent_chat_friend = ndb.IntegerProperty(default = 0, indexed = False)        
    
    
class UserModelBackupTracker(ndb.Model):    

    # This data structure contains pointers to a principal userobject and the backup objects for that
    # principal object.  Additionally, the principal userobject and the backup objects all will contain
    # pointers back to the object instantiated from this class. 
    
    # The following contains a pointer to the main userobject. Note, we set the reference_class to None so that
    # we can later assign a pointer to the userobject (of class UserModel).
    #userobject_ref = ndb.ReferenceProperty(reference_class=None, collection_name = 'userobject_pointer_set', indexed = False)
    userobject_ref = ndb.KeyProperty(indexed = False)
    
    
    # contains the name of the most recent backup (backup_1, backup_2 ... ), which allows us to track
    # which of the references (below) contains the most recent copy of the userobject.
    most_recent_backup_name = ndb.StringProperty(default = None, indexed = False)
    
    # The following structures will contain copies of the userobject.  We periodically (on a rotating basis)
    # copy the userobject into an object referenced by one of the following properties.
    #backup_1 = ndb.ReferenceProperty(reference_class=None, collection_name = 'backup_1_set', indexed = False)
    #backup_2 = ndb.ReferenceProperty(reference_class=None, collection_name = 'backup_2_set', indexed = False)
    #backup_3 = ndb.ReferenceProperty(reference_class=None, collection_name = 'backup_3_set', indexed = False)
    
    backup_1 = ndb.KeyProperty(indexed = False)
    backup_2 = ndb.KeyProperty(indexed = False)
    backup_3 = ndb.KeyProperty(indexed = False)
    
class UserTracker(ndb.Model):
    
    # This model provides us with information that will allow us to come back and check on user
    # logins in case it is necessary to provide information to law enforcement etc.
    
    # We store the login IPs as a list of strings, where each unique IP will only appear once
    track_ip_list = ndb.StringProperty(repeated = True, indexed = False)
    
    # Track the number of times that the user has logged in from each IP. There is a positional association
    # between this list and the track_ip list. (note: we defined this as a parallel structure to the track_ip
    # so that we can efficiently perform queries on the login_ip data, which could be necessary for fraud 
    # detection and prevention)
    num_times_ip_used_list = ndb.IntegerProperty(repeated = True, indexed = False)
    
    # keep track of the first and last time that a given IP address has been used -- this will allow us to 
    # more or less understand the time frame which a user has logged in from a given IP. Again, this 
    # is parallel to the track_ip list.
    first_time_ip_used_list = ndb.DateTimeProperty(repeated = True, indexed = False)
    last_time_ip_used_list = ndb.DateTimeProperty(repeated = True, indexed = False)
    
    # if the user clicks on an email that we have sent to their email address, we add the email address to
    # the following data structure (if it is not already stored) - this provides us with a history of verified email 
    # addresses that the user has used to access their account data.
    verified_email_addresses_list = ndb.StringProperty(repeated = True, indexed = False)
    # parallel structures for tracking the dates that the email address has been verified 
    # It is not totally clear that this is useful at this point in time, but the cost is relatively low.
    first_time_email_address_verified_list = ndb.DateTimeProperty(repeated = True,  indexed = False)
    last_time_email_address_verified_list = ndb.DateTimeProperty(repeated = True,  indexed = False)
    
    # List of sessions that this userobject currently has open (ie. multiple logins from different computers/browsers)
    # This will be stored as a circular queue that is indexed by list_of_session_ids_index - when MAX_STORED_SESSIONS
    # is reached, we will wrap this value back to 0 - if we wish to ensure that a user is logged out, we will cycle
    # through the past MAX_STORED_SESSIONS session_id values, and clear them from the database. 
    list_of_session_ids = ndb.StringProperty(repeated = True, indexed = False)
    list_of_session_ids_last_index = ndb.IntegerProperty(default = None, indexed = False)    
    
    
    # keep track of when each object is last written - this gives us a fighting chance of going back
    # and repairing objects that have been corrupted due to programmer error or other unforseen events.
    last_wite_time = ndb.DateTimeProperty(auto_now = True)    
    
    # TODO: In the future, it may be useful to write cookies to individual computers, to verify if a single user
    # is entering with multiple accounts. This is the only way to truly track user behaviour.
        
    
class OnlineStatusTracker(ndb.Model):
    # This data structure is currently only used for memcache storage (not written to database). Previously we
    # were writing the data to the database, but found that this cost money without much benefit since we don't 
    # need permanent storage of the chat friend status. 
    
    # This is the class that keeps track of the current users chat and online presence status
    # Due to the fact that this structure will be accessed frequently, it should be memcached.
    
    # For efficiency, we should key this object with the uid string of the owner userobject - this
    # will allows us to retrieve the object without having to look at the associated userobject to get the key.
    
    # The code that will maintain these data structures will act in the following manner:
    # 
    # When a user is logged-in, the browser will periodically ping the server for messages
    # and for connection lists. During this ping, the users "connection_verified_time" will
    # be updated (in an efficient manner using memory caching, and only periodic updates 
    # to minimize database writes). 
    #
    # Updates to other users contact lists will periodically view the "connection_verified_time" of 
    # each of their contacts to determine if that contact should be considered online, or if
    # that contact appears to be offline.
    
    
    # We update this with a new time every time the client javascript checks-in to let us know that the user is 
    # still connected. -- this is the value that we use to determine if the user is "online"!
    connection_verified_time = ndb.DateTimeProperty(auto_now_add = True, indexed = False) 

    # Track user preference for online status. 
    user_presence_status = ndb.StringProperty(default="active", indexed = False)
        
    
class ChatMessage(ndb.Model):
    # Currently only written to memcache (not to database)
    # 
    # Contains a single chat message sent to/from the current user and another user (indicated by other_uid)
    # If a new window/tab is opened, and the current user has a chatbox
    # open to the "other_uid", then we will load the history that we have stored between these two users. This
    # will contain the last NUM_CHAT_MESSAGES_ALLOWED messages between these two users, and should be sorted by 
    # chat_msg_time. 
    
    # We DO NOT WRITE this to the database - we used to write this to the database, and the costs add up quickly. 
    # For our application, it is not critical that we might lose a small number of messages occasionally. Additionally
    # once we move to the comet server, it will become much less likely to lose messages since they will be sent
    # immediately to the destination.
        
    type_of_conversation = ndb.StringProperty(default = "one_on_one", indexed = False)  # either "one_on_one" or "group"

    # if this message is sent in a "one_on_one" conversation, then we set uid1 to the lower
    # of the two user IDs, and uid2 to the higher. This gives us an un-ambiguous manner of retreiving
    # a conversation/message between two users.
    # If this is a "group" conversation, then uid1 is the group id, and uid2 is the sender uid.
    uid1 = ndb.StringProperty(default = None, indexed = False)
    uid2 = ndb.StringProperty(default = None, indexed = False)
    
    chat_msg_text =  ndb.StringProperty(default = None, indexed = False)
    
    # set the time to the current time when this object is written (or overwritten) - this can be used for 
    # sorting messages and returning to the client in order. 
    chat_msg_time_string = ndb.StringProperty(default = None, indexed = False)
    
    # The following is required for displaying the name of the correct user beside the message text
    sender_username = ndb.StringProperty(default = None, indexed = False)
        

        
class OpenConversationsTracker(ndb.Model):
    # Data structure for tracking the conversations that are currently open.
    # Effectively, it is used to build a list of chatboxes that are currently open, and will 
    # also be upated to contain a new uid if another user 
    # sends a message to the current user.  If the current user hits the "X" (close) button on a given chatbox, 
    # then we remove the UID from this list (however, it can be re-added if the other user sends a new message). 
    # If a user re-loads a window/tab or opens a new window/tab, this list will be used to indicate which 
    # chatboxes need to be opened. 
    #
    #
    
    type_of_conversation = ndb.StringProperty(default = "one_on_one", indexed = False)  # either "one_on_one" or "group"
    
    owner_uid = ndb.StringProperty(default = None, indexed = False) 
    other_uid = ndb.StringProperty(default = None, indexed = False) 
    
    # other username is required for modifying the display on the top of each chatbox, and for providing a link totheir profile.
    # in the case that this is a group conversation, this will be set to the group name
    chatbox_title = ndb.StringProperty(default = None, indexed = False) 
    
    # This structure allows us to quickly compare the date of the last message that is contained in the browswer
    # with the last message sent/received by the current user, and to therefore retrieve messages only when
    # the browser is not up-to-date. This should be memcached for efficiency since it will be polled quite often.
    current_chat_message_time_string = ndb.StringProperty(default = None, indexed = False)    
    
    # track if the conversation should be shown minimized or maximized,
    # valid values are "minimized" or "maximized".
    chatbox_minimized_maximized = ndb.StringProperty(indexed = False, default = "maximized")
    

class ChatGroupTracker(ndb.Model):
    # Data structure that tracks *all* chat groups that are currently in existance. These groups will show
    # up in the "groups" chatbox, which will allow the user to select a group to join and/or create a new group.
    
    # Eventually, when the number of groups gets too large, we should limit the display list to only
    # include groups that are not full (since they can't be joined anyway), and sorted by largest to 
    # smallest group size. -- later (farther in the future), we will have to implement search capabilities
    # to allow users to search for a group.
    
    group_name = ndb.StringProperty(default = None) 
    
    # We will place a limit on the number of members allowed for each group, to keep the conversations 
    # manageable, and to keep queries efficient. (will probably log out users after a certian period 
    # of inactivity)
    number_of_group_members = ndb.IntegerProperty(default = 0)
    
    # List of group members UIDs
    group_members_list = ndb.StringProperty(repeated = True, indexed = False)
    
    # creator name for showing to other users, as well as for administrative 
    group_creator_name = ndb.StringProperty(default = None, indexed = False)
    
    # store the string of the creators UID to provide a link to their profile 
    group_creator_uid_string = ndb.StringProperty(default = None, indexed = False) 
    

    
    
############################################
class UserModel(ndb.Model):
    # Defines the User Model (ie. the data-structure that contains all relevant information about a 
    # client that is logged into the system.
    
    # Note: if new input fields are added, then required must be set to false until it is guaranteed that the database 
    # has the required field -- otherwise any queries on an object that is missing the field will result in an
    # exception. An article on updating schema is given here: http://code.google.com/appengine/articles/update_schema.html
    
    # Additionally, I would have prefered to not have so many properties in this model, and would rather have
    # used ReferenceProperties to split some of the data out, but this would make queries that 
    # include data in ReferenceProperties much more difficult and probablly inefficient.   
    
    #### Structures required for backing up userobjects "in-the-cloud" 
    # We will keep daily, weekly, and monthly bakups of userobjects so that in the case of an emergency,
    # we can quickly restore the user profiles to a previously known good state. This is intended mostly
    # for the case that our program starts trashing the database, as opposed to a massive failure of 
    # googles servers. We currently do not backup messages or photos (these are less critical).
    # 
    # Backups will be 
    # written to only when the user signs in (and only if the appropriate amount of time has passed since
    # the last time the particular backup object was written to). We will use "last_login"
    # on the backup objects to indicate when the backup occured. 
    # Furthermore, to ensure that backup objects to not appear in search results, we set is_real_user to False. 
    
    # Boolean to distinguish "backup" copies
    # of the userobject versus the "real" copy -- in the case of a backup, this value will be set to False.
    is_real_user = ndb.BooleanProperty(default=False)
    
    
    # The backup tracker provides us with a single node that is in common with a particular user object
    # and it's backups. The primary userobject as well as the backups all contain pointers to the same 
    # backup tracker, and the backup_tracker then contains pointers to the userobject and all of it's backups.
    # This will allow us to easily navigate between userobject and backups if this becomes necessary due to
    # some kind of destruction of data in the database. 
    backup_tracker = ndb.KeyProperty(kind=UserModelBackupTracker, required=False)
    
    #### values defined in signup fields (defined in constants.py)
    # This part of the class  defines the sign-up fields, such 
    # as gender, what they are looking for age, etc.
    
    # Note: we store the principal user data fields as StringLists to simplify and reduce the number of indexes required for 
    # searches. -- By including a value of "----" as an guaranteed entry in each list. This allows us to effectively
    # ignore a field by searching for "----" in that field, which will be contained in every signup field  value list by construction. 
    # The naming convention "ix_list" refers to the fact that this list is created for search index optimization
    # purposes (and these values would normally not need to be stored as a list)- "ix" is an abbreviation for "index"
        
    
    # NOTE: Eventually, we should be able to remove the base value for each of these lists - but not clear if there is 
    #       much of a benefit to doing this. 
    
    sex = ndb.StringProperty(default = None)  
    sex_ix_list = ndb.StringProperty(repeated = True) 
    
    age = ndb.StringProperty(default = None)    
    age_ix_list = ndb.StringProperty(repeated = True)
    
    username = ndb.StringProperty(default = None ) 
    
    # The username_combinations_list is used for partial matching of the username -- to do this, we have to store a list
    # that is made up of the username[:], username[1:], username[2:], etc.
    username_combinations_list = ndb.StringProperty(repeated = True)
    
    password = ndb.StringProperty(default = None)   
    password_verify = ndb.StringProperty(default = None)   
    password_reset = ndb.StringProperty(default = None)  
    email_address = ndb.StringProperty(default = "----")
    
    if settings.BUILD_NAME != "Language" and settings.BUILD_NAME != "Friend":
        preference = ndb.StringProperty(default = None)    
        preference_ix_list = ndb.StringProperty(repeated = True)
        relationship_status = ndb.StringProperty(default = None) 
        relationship_status_ix_list = ndb.StringProperty(repeated = True)
    else:
        if settings.BUILD_NAME == "Language":
        # The following values will be copied into lists so  that the user can specify multiple values for each of the fields.
            native_language = ndb.StringProperty(default = None)    
            language_to_learn = ndb.StringProperty(default = None) # only used while user is signing up - will be copied into array of
                                                                                 # languages spoken by the user, and ignored thereafter.
        if settings.BUILD_NAME == "Friend":
            pass

                                                                             
    # location requires special storage, because we break up the input into
    # three seperate fields - country, country+region, and country+region+sub-region 
    # this is necessary for doing searches at whatever level of granularity is desired 
    country = ndb.StringProperty(default="----")
    country_ix_list = ndb.StringProperty(repeated = True)
    region = ndb.StringProperty(default="----")
    region_ix_list = ndb.StringProperty(repeated = True)
    sub_region = ndb.StringProperty(default="----")
    sub_region_ix_list = ndb.StringProperty(repeated = True)
    
    if settings.BUILD_NAME == "Friend":
        for_sale_ix_list = ndb.StringProperty(repeated = True)
        friend_price = ndb.StringProperty(default="----")
        friend_price_ix_list = ndb.StringProperty(repeated = True)
        friend_currency = ndb.StringProperty(default="----")
        friend_currency_ix_list = ndb.StringProperty(repeated = True)
        

    # Status (what am I thinking) allows the user to enter in their thought for the day
    current_status = ndb.StringProperty(default='----')
    # store the time of the status update -- but also assign a default time of when user profile is "created".
    current_status_update_time = ndb.DateTimeProperty(auto_now_add = True) 
    
    #### values to specify in user details (defined in profile_details.py)     
    # This part of the class contains extra profile details for each user. 
    # These are the "optional" details that describe the caracteristics of the user, 
    # preferences, what they are looking for, etc. Most of these values
    # are based on the fields/values defined in UserProfileSpec class.
    
    email_address_is_valid = ndb.BooleanProperty(default = False)
    change_password_is_valid = ndb.BooleanProperty(default = False)
    password_attempted_change_date = ndb.DateTimeProperty(auto_now_add=True) # initially gets set to when the user profile is created
        
    about_user = ndb.TextProperty(default = '----')
    
    # this variable is used as an indicator that the user has put enough characters of 
    # description in their profile ... otherwise, they are given a warning.
    has_about_user = ndb.BooleanProperty(default = False)

    height = ndb.StringProperty(default = '----')
    body_type = ndb.StringProperty(default = '----')
    hair_color = ndb.StringProperty(default = '----')
    hair_length = ndb.StringProperty(default = '----')
    eye_color = ndb.StringProperty(default = '----')
    drinking_habits = ndb.StringProperty(default = '----')
    smoker = ndb.StringProperty(default = '----')
 
        
    # The following loop is a *big* part of the UserModel - we dynamically build this part of the model 
    # depending on the settings in the UserProfileDetails definitions. 
    for category in UserProfileDetails.checkbox_fields.keys():
        vars()[category] = ndb.StringProperty(repeated = True) 
            
                
    #### fields for keeping track of photos that have been uploaded
    # set up an anonymous reference to the photos -- so that we automatically have a reference
    # to the profile photo, without having to do a query. Read about it at:
    # http://www.appenginetips.com/2008/05/anonymous-refer.html. 
    # It will be assigned after photos are uploaded.
    #profile_photo = ndb.ReferenceProperty() #anonymous reference -- set later to key of the main profile photo
    
    #### other fields
    last_login = ndb.DateTimeProperty() 
    
    # we write the last_login into a string, because this allows for passing the data
    # as a bookmark, without requiring costly conversion of the received
    # values into datetime objects.
    last_login_string = ndb.StringProperty(default=None)

    # unique_last_login is a combination of the last login time, along with "weighting" factors
    # such as if the user has photos, a description, etc. Each of these factors make the user profile
    # show up earlier in the search results.
    unique_last_login = ndb.StringProperty(default=None)
    unique_last_login_offset_ref = ndb.KeyProperty(kind=UniqueLastLoginOffsets, required=False)
    
    creation_date = ndb.DateTimeProperty(auto_now_add=True) 
    
    # every time this object is written, the auto_now will be updated. This should be useful for error recovery if 
    # it ever becomes necessary.
    last_write = ndb.DateTimeProperty(auto_now=True) 
    
    # we create a hash of the creation date, so that we have a "secret" value. This can be used for example in
    # emails that allow the user to change settings on their account -- they have to have the correct hash in
    # order for the change to be accepted as valid.
    hash_of_creation_date = ndb.StringProperty(default=None,  indexed = False)
    
    # previous_last_login is used for showing user updates that are "new" since the last time they logged in
    # This is necessary, because the last_login is set immediately when the user logs into the system.   
    previous_last_login = ndb.DateTimeProperty() 
        
    # This will indicate how many new mails the user has. This must be updated when the mail is
    # sent. Keep seperate from UserModel, because we don't want to lock the entire usermodel to update
    # this value. 
    unread_mail_count_ref = ndb.KeyProperty(kind=UnreadMailCount, required=False)
                                            
    # store the users previous search for default settings in the future
    # required=False, because it does not exist when the model is initially created. 
    search_preferences2 = ndb.KeyProperty(kind = UserSearchPreferences2, default = None)
    
    # Keep track of how many "new" contact attempts have been made to the current user.
    new_contact_counter_ref = ndb.KeyProperty(kind = CountInitiateContact, required = False)
    
    # Keep track of if this user is spamming people
    spam_tracker = ndb.KeyProperty(kind = SpamMailStructures, required = False)
     
    # The following variable indicates that users account should be eliminated the next
    # time a batch elimination is run. 
    user_is_marked_for_elimination = ndb.BooleanProperty(default = False)

    # user_tracker will allow us to permanently log ip addresses and verified email addresses that have been used
    # for logging into this profile. 
    user_tracker = ndb.KeyProperty(kind = UserTracker, default = None)
    
    registration_ip_address = ndb.StringProperty(default=None)
    registration_city = ndb.StringProperty(default=None, indexed = False)
    registration_country_code = ndb.StringProperty(default=None, indexed = False)
    
    last_login_ip_address = ndb.StringProperty(default=None)
    last_login_country_code = ndb.StringProperty(default=None, indexed = False)
    last_login_region_code = ndb.StringProperty(default=None, indexed = False)
    last_login_city = ndb.StringProperty(default=None, indexed = False)
    
    # when we eliminate profiles, sometimes it is because they are a scammer etc. We will use this as a flag to indicate to
    # other users why a particular profile has been removed. 
    # Current values used are:
    #    "scammer" - African scams
    #    "terms" - Rude/vulgar/etc.
    #    "fake" - fake profile used to bait someone to pay site
    reason_for_profile_removal = ndb.StringProperty(default=None)
    
    # client_paid_status - if this is any value other than None, then the client is a VIP. In the future, we may
    # wish to include special status for different VIP levels, in which case we will write specific strings into 
    # this data field.
    client_paid_status = ndb.StringProperty(default = None)
    client_paid_status_expiry = ndb.DateTimeProperty(auto_now_add = True)
    
    # if client has paid money for their status, we exempt them from captchas (for the duration of their status)
    client_is_exempt_from_spam_captchas = ndb.BooleanProperty(default=False)
    
    
class PaymentInfo(ndb.Model):
    # This class keeps track of how much a user has paid/donated, what date the donation was made, etc.
    
    # The following declaration creates a (virtual) property on the associated UserModel object that can be accessed such as:
    # userobject.payments_set[0] - Note: we can therefore also keep track of multiple payments for a single user. 
    #owner_userobject = ndb.ReferenceProperty(reference_class = UserModel, required = False, default = None, collection_name="payments_set")
    owner_userobject = ndb.KeyProperty(kind = UserModel, default = None)
    
    # The username is stored here just for convenience, so that we can query by username (in the admin console) to see what payments
    # a given user has made, in case of any disputes or confusion.
    username = ndb.StringProperty(default=None)
    amount_paid_times_100 = ndb.IntegerProperty(default=0)
    date_paid = ndb.DateTimeProperty(required=False)
    num_credits_awarded = ndb.IntegerProperty(default=0)
    
    txn_id = ndb.StringProperty(required = False, default=None)
    
            
class WatermarkPhotoModel(ndb.Model):
    # Will contain the watermark that will be used for marking all uploaded photos. This data structure is intended to
    # only have a single element, which means that a simple get() should be possible without having to filter results
    image = ndb.BlobProperty(required = False)

class PhotoModel(ndb.Model):
    # This class contains the data and images for a single photo. If a user has multiple photos, then
    # this class will be instantiated multiple times.
    # NOTE: since this model has a reference to UserModel, AppEngine automatically creates
    #       backlinks in UserModel that link back to the photos that it contains. These
    #       are contained in a variable called photomodel_set, which is a query object. 

    # DO NOT SET required to "True", without a defalut value, this will break the code.
    small = ndb.BlobProperty(required = False) # this is where we store the compressed/thumbnail photo
    medium = ndb.BlobProperty(required = False) # This is where we store the medium-sized photo
                                               # which is useful for profile picture.
    large = ndb.BlobProperty(required = False)  #large version of the picture, for showing more details
                                               # will be displayed when cursor is hovered over a small or medium image.
                                
       
    # The following two photos will only be stored temporarily. These are used for verifying that
    # the original image does not have a watermark. Once verified, the watermarked small, medium, and large images
    # will be the only ones permanently stored and these original images can be erased.
    medium_before_watermark = ndb.BlobProperty(required = False)
    large_before_watermark = ndb.BlobProperty(required = False)

    name = ndb.StringProperty(default = '') 
    is_profile = ndb.BooleanProperty(default = False)
    is_private = ndb.BooleanProperty(default = False)
    
    # The following allows us to leave photos that will be made public displayed as private until they are approved. 
    is_approved = ndb.BooleanProperty(default = False)
    
    # Indicate if we have previously reviewed this photo - allows us to filter query results to
    # only show photos that have not previously reviewed.
    has_been_reviewed = ndb.BooleanProperty(default = True)
    
    # Note: "creation_date" refers to the last time that the photo was updated -- including
    # changing from private to public.
    creation_date = ndb.DateTimeProperty(auto_now=True) 
    
    # the following provides a link from the Photos to the user. This will create 
    # backlinks in the user model, that can be used to show the photos.
    #parent_object = ndb.ReferenceProperty(reference_class = UserModel, required = False)
    parent_object = ndb.KeyProperty(kind=UserModel, required = False)

class MailMessageModel(ndb.Model):
    """ 
    New model for the mailbox
    """
    
    """ 
    Every message sent between a unique pair of users will be assigned a unique parent key as a means of identifying
    all messages between these two users. To ensure that the key is the same for a pair of users, we will always generate this
    key as a combination of the key values of the user objects, with the "lower" key value appearing first. 
    
    This also has the additional benefit of ensuring database  consistency in the High Replication data store, since all messages 
    between two users are members of the same entity group.
    
    """
    m_text = ndb.TextProperty(default = None)   
    
    
    # Note, collection_name refers to the name this this class will appear as on the model which is referenced.
    # Therefore, the receiver of the message (addressed by the "to" field), could look up his messages in 
    # the "messages_received" structure. These names are not used by our code, but must appear in order to dis-ambiguate
    # how these will appear on the referenced object.
    # m_to and m_from refer to the receiver and the sender of the current message. 
    #m_from = ndb.ReferenceProperty(reference_class = UserModel, required = False, collection_name = 'mmm_sent')
    m_from = ndb.KeyProperty(kind = UserModel, required=False)
    
    # if we ever decide to allow multiple recipients, this could be changed to a list of keys. 
    #m_to = ndb.ReferenceProperty(reference_class = UserModel, required = False, collection_name = 'mmm_received')
    m_to = ndb.KeyProperty(kind = UserModel, required = False)
    
    # date/time the message was sent/received
    m_date = ndb.DateTimeProperty(required=False)
    
    # unique_m_date will be a concatenation of the date with the sender username. This ensures uniquenes
    # as required to guarantee that paging through results will work correctly. (otherwise, two messages
    # received at the exact same milisecond could cause problems when paging through data).
    unique_m_date =  ndb.StringProperty(default=None)
    

class UsersHaveSentMessages(ndb.Model):
    # This class contains a list of pairs of users who have had contact (via messages) in the past. This is necessary for
    # tracking and presenting messages for a particular user mailbox, in which each "other" contact will appear
    # only once. Note that unlike the MailMessageModel data structure, which contains an entry for each message, this 
    # structure contains a single (but duplicate -- one on each user) entry for each pair of users.
    # This can be thought of as a sort of indicator
    # that allows us to extract the "top" message between each pair of users, by performing another query (once
    # we actually know that the two users have had previous contact)
    #owner_ref = ndb.ReferenceProperty(reference_class = UserModel, required = False, collection_name = 'have_sent_messages_owner')
    #other_ref = ndb.ReferenceProperty(reference_class = UserModel, required = False, collection_name = 'have_sent_messages_other')
    owner_ref = ndb.KeyProperty(kind = UserModel, required = False)
    other_ref = ndb.KeyProperty(kind = UserModel, required = False)
    
    last_m_date = ndb.DateTimeProperty(required=False)
    
    # unique_mail_date will be a concatenation of the date with the sender username. This ensures uniquenes
    # as required to guarantee that paging through results will work correctly. 
    unique_m_date =  ndb.StringProperty(default=None)
    
    # Allow users to delete and/or filter the message -- which means that it will not show in their mailbox
    # Options are extendable, with currently envisioned "inbox" (which actually means all sent and received that
    # have not been eliminated),  "new", "received", "sent", "trash", "spam"
    mailbox_to_display_this_contact_messages = ndb.StringProperty(default = "inbox")
    
    # We use a boolean to keep track of if the "owner" of this message was the sender or 
    # the receiver. If true, is sender, false receiver.
    owner_is_sender =  ndb.BooleanProperty(default = True)
    
    # We check if the message has been read by owner. This is used to display the message with the appropriate icon 
    # as well as for counting number of unread "messages" (really number of un-opened "conversations" -- meaning
    # that 5 messages from a single person will count as a single message)  
    message_chain_has_been_read = ndb.BooleanProperty(default = False)
    
    # Mark this message chain as a "favorite" so that it can be viewed in it's own special menu.
    # This structure should mirror the value stored in InitiateContact_model -- but since we allow mail messages
    # to be queried based on this value -- it MUST appear here as well.
    other_is_favorite = ndb.BooleanProperty(default = False)    


    # In order to limit the number of messages sent from "owner" to "other" in a single day, we need to keep track
    # of when the first message of the day was sent - and then start counting the number of messages from
    # that time.
    datetime_first_message_to_other_today  = ndb.DateTimeProperty(indexed = False, auto_now_add = True) 
    
    # Keep track of the number of messages that the "owner" has sent to the "other" profile in the current day.
    num_messages_to_other_sent_today = ndb.IntegerProperty(default = 0, indexed = False) 
    

class InitiateContactModel(ndb.Model):
    # This class contains the data structures that indicate when a user has made contact with another
    # user. This includes adding another user to favorites, sending a kiss, giving a key, etc.
    # It is intended for being able to efficiently access the contact settings for display on the profile
    # that is being visited. 
    
    
    # Note: displayed_profile refers to the profile that is/was displayed when the option to send wink/key/etc. is shown
    #       and the viewer profile refers to the person looking at the profile. 
    #       However, later on (in the case of the key), when determining if the user has access to the private photos of another user, we
    #       access the key_stored for the "viewer_profile" (this means that the viewer has been given a key) - this could be a potential
    #       source of confusion since we are viewing the "displayed_profile" but checking the "viewer_profile" data structure for access to 
    #       the private photos.
    #displayed_profile = ndb.ReferenceProperty(reference_class = UserModel, required = True, collection_name = 'contact_model_displayed_profile')
    #viewer_profile = ndb.ReferenceProperty(reference_class = UserModel, required = True, collection_name = 'contact_model_viewer_profile')
    displayed_profile = ndb.KeyProperty(kind = UserModel, required = True)
    viewer_profile = ndb.KeyProperty(kind = UserModel, required = True)
       
        
    favorite_stored = ndb.BooleanProperty(default = False)
    favorite_stored_date =  ndb.DateTimeProperty()
    
    wink_stored = ndb.BooleanProperty(default = False)
    wink_stored_date = ndb.DateTimeProperty()
    
    kiss_stored = ndb.BooleanProperty(default = False)
    kiss_stored_date = ndb.DateTimeProperty()
    
    key_stored = ndb.BooleanProperty(default = False)
    key_stored_date = ndb.DateTimeProperty()
    
    # allow the user to block other people from sending them messages.
    blocked_stored = ndb.BooleanProperty(default = False)
    blocked_stored_date = ndb.DateTimeProperty()
    
    # chat_friend_stored will contain a string that indicates the following possible conditions:
    #    None: Neither the viewer or displayed profile have made any request to add to each others chat list
    #    "request_sent": the displayed profile has been sent a request to add to chat contacts
    #    "request_received": the viewer profile has been sent a chat request from the users whose profile is being viewed
    #    "connected": the viewer and displayed profile have agreed to add each other to their chat contacts.
    chat_friend_stored = ndb.StringProperty(default = None)
    chat_friend_stored_date = ndb.DateTimeProperty()

class EmailAutorizationModel(ndb.Model):
    # model that will store login/registration information while we are waiting for the user to verify their
    # email registration
    username = ndb.StringProperty(default = None)   
    secret_verification_code = ndb.StringProperty(default = "----")   
    pickled_login_get_dict = ndb.BlobProperty(default = None)   
    creation_date = ndb.DateTimeProperty(auto_now_add=True) 
    
    # the following information will be used for preventing an attack -- if a single IP or a single email
    # address registers an excessive number of times, it will not be permitted to register more accounts.
    ip_address = ndb.StringProperty(default=None)
    email_address =  ndb.StringProperty(default = None)
    
    # the following variable will contain a string representation of the day that the registration takes place
    # which will allow us to do database queries for all registrations in the current day.
    creation_day =  ndb.StringProperty(default=None)
    
    # track if someone has referred this user to our website
    referring_code = ndb.StringProperty(default=None)

# The following classes allow us to keep track of profiles that other users consider to be unacceptable.
class CountUnacceptableProfile(ndb.Model):
    # keeps track of the number of unique times that this user has been marked as unacceptable.
    #profile_ref = ndb.ReferenceProperty(reference_class = UserModel, required = False)
    profile_ref = ndb.KeyProperty(kind = UserModel, required = False)
    
    count = ndb.IntegerProperty(default=0)
    
    # Track how many times profile is reported as unacceptable in the "small time window" - which 
    # is defined as the number of hours in which we will ban an account if they receive too many 
    # reports.
    datetime_first_reported_in_small_time_window  = ndb.DateTimeProperty(auto_now_add=True, indexed = False) 
    num_times_reported_in_small_time_window = ndb.IntegerProperty(indexed = False, default=0)
    
    
class CountReportingProfile(ndb.Model):
    # keeps track of the number of  times that this user has marked another profile as unacceptable.
    # profile_ref = ndb.ReferenceProperty(reference_class = UserModel, required = False)
    profile_ref = ndb.KeyProperty(kind = UserModel, required = False)
    
    count = ndb.IntegerProperty(default=0)    
    
class TemporarilyBlockedIPAddresses(ndb.Model):
    # contains IP addresses that we have blocked due to malicious behaviour of users
    blocked_ip = ndb.StringProperty(required=True)
    time_blocked = ndb.DateTimeProperty(auto_now_add=True) 
    
    
class MarkUnacceptableProfile(ndb.Model):
    # we will create an object that indicates that this viewing profile has reported the displayed_profile as being 
    # unacceptable. If this object already exists, then counters will not be modified since we don't want a single user
    # to be able to mark the same profile as unacceptable hundreds of times.
    #displayed_profile = ndb.ReferenceProperty(required=False,reference_class = UserModel,  collection_name = 'unacceptable_model_displayed_profile')
    #reporter_profile = ndb.ReferenceProperty(required=False,reference_class = UserModel, collection_name = 'unacceptable_model_viewer_profile')
    displayed_profile = ndb.KeyProperty(kind = UserModel, required=False)
    reporter_profile = ndb.KeyProperty(kind = UserModel, required=False)
    
    creation_date = ndb.DateTimeProperty(auto_now_add=True) 
    unacceptable = ndb.BooleanProperty(default=True)

class VideoPhoneUserInfo(ndb.Model):
    m_window_identifier = ndb.StringProperty(default="")
    m_identity = ndb.StringProperty(default="")
    m_updatetime =  ndb.DateTimeProperty(auto_now = True) 
            
            

            
class SiteMap(ndb.Model):
    # Contains XML sitemap data. This can used as a base class for both sitemaps, as well as for 
    # sitemap indexes. 
    
    # Since we have multiple sitemaps, we give each sitemap a unique and user-readable number. This
    # will be used in the URL for accessing the sitemap -- ie http://www.foo.com/sitemap-[site_map_number].xml
    sitemap_number = ndb.IntegerProperty(default = None)  # default to None to hard crash if we have code error
    
    # track how many URLs have been written to this object - this is used for detecting when we have 
    # reached the limit for the number of URLs permitted per sitemap, at which point a new sitemap
    # will be created.
    num_entries = ndb.IntegerProperty(default = 0) 
    
    # the following two values are really only for debugging in the future, should anything strange happen
    creationtime =  ndb.DateTimeProperty(auto_now_add = True) # track creation time of this object
    updatetime =  ndb.DateTimeProperty(auto_now = True) # track the last time that this object is written
    
    # This is the actual contents of the sitemap - but it only includes the "<url>"-related xml - does not contain
    # the xml version declaration or the "urlset" definition - these will be dynamically added when the 
    # xml is requested. These are intentionally left out because it would make it more complex to add
    # new URLs to the sitemap (would not be a simple concatenation of the new "<url>" data - it would require
    # removing closing tags for the xml that we have excluded before adding the new <url> data, and then 
    # re-writing the closing tags)
    internal_xml = ndb.TextProperty(default = '')

    # we store a reference to the key of the last userobject - mostly for informational purposes 
    # If this is a container for user profiles, then this contains a string representation of the object key
    # If this is a container for sitemap objects, then this contains the number of the most recent sitemap object
    last_object_id = ndb.StringProperty(default = None)
    
    # Track the creation time of the last object (or sitemap) that has been included in the internal_xml. This 
    # allows us to then start the next query immediately after this object.
    creation_time_of_last_id =  ndb.DateTimeProperty(default = None)
       
    
class SiteMapUserModel(SiteMap):
    # Note: inherits from SiteMapXMLContainer, which defines most of the important structures that
    # are required.
    # This class specifically contains sitemap data for URLs of User Profiles. 
    pass


class SiteMapUserModelIndex(SiteMap):
    # This class specifically contains sitemap index data that indicates the UserModel sitemap files
    pass


class FakeParent(ndb.Model):
    # Used by any models that require a parent (in order to be considered in the same entity group)
    pass


class ViewerTracker(ndb.Model):
    displayed_profile = ndb.KeyProperty(kind = UserModel)
    viewer_profile = ndb.KeyProperty(kind = UserModel)
    view_time =  ndb.DateTimeProperty(auto_now = True) 
        
        
class ViewedCounter(ndb.Model):
    displayed_profile = ndb.KeyProperty(kind = UserModel)
    viewed_counter = ndb.IntegerProperty(default = 0) 