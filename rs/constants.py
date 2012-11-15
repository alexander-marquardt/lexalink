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


from django.utils.translation import ugettext_lazy

import re
import datetime

from rs.private_data import *
import settings

# This file contains all the declarations for constant values that are used at various places in the code
# This should help to keep the code more maintainable, and consistent.

if settings.LANGUAGE_CODE == 'en':
    default_languages_field_value = "english"
elif settings.LANGUAGE_CODE == 'es':
    default_languages_field_value = "spanish"
else:
    raise Exception("Unknown settings.LANGUAGE_CODE")

SESSION_EXPIRE_HOURS = 7 * 24
    
if settings.BUILD_NAME == "Language" : 
    minimum_registration_age = 14
elif settings.BUILD_NAME == "Friend":
    minimum_registration_age = 16
else:
    minimum_registration_age = 18
    
if settings.BUILD_NAME == "Discrete":
    MAX_EMAILS_PER_DAY = 2 # after this number of messages, sending messages is blocked for non-paying members.
else:
    MAX_EMAILS_PER_DAY = 4
    
# the number of activities  that the user can select in the various affictions/activities/etc. checkboxes. This is currently only used
# in Friend. This limit is required to prevent index explosion
MAX_CHECKBOX_VALUES_IN_COMBINED_IX_LIST = 40
    
SMALL_IMAGE_X = SMALL_IMAGE_Y = 65
MEDIUM_IMAGE_X = MEDIUM_IMAGE_Y = 120
LARGE_IMAGE_X = LARGE_IMAGE_Y = 400 

MAX_NUM_PHOTOS = 6
PHOTOS_PER_ROW = 6

CHECKBOX_INPUT_COLS_PER_ROW = 4

MAX_KEYS_SENT_ALLOWED = 40

# Define constants that are used for caching and other stuff - Note: the values for month and year are approximate.
SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 60 * SECONDS_PER_MINUTE
SECONDS_PER_DAY = 24 * SECONDS_PER_HOUR
SECONDS_PER_WEEK = 7 * SECONDS_PER_DAY
SECONDS_PER_MONTH = 30 * SECONDS_PER_DAY
SECONDS_PER_YEAR = 365 * SECONDS_PER_DAY


MAX_REGISTRATIONS_SINGLE_EMAIL_IN_TIME_WINDOW = 2 # If they exceed this number of attempted registrations with a single email address in one day
                                   # then they will not be sent any more registration emails. 
                                   # This prevents someone from spamming an email address with multiple registration requests. 
                                   
MAX_REGISTRATIONS_SINGLE_IP = 4 # single IP address will be denied if this number is exceeded within a single day. 


NUM_CHAT_MESSAGES_IN_QUERY = 30 # how many chat messages will we return in a query - Note: this limit is not only about memory utilization, but
                                # also about how many messages we want to send to the user every time they re-load the chatbox. 
MAX_CHAT_FRIEND_REQUESTS_ALLOWED = 200 # requests + accepted friends cannot exceed this number - keep queries to manageable size

# this is the limit on the number of chat_friends for non-registered users
if settings.BUILD_NAME == 'Discrete':
    GUEST_NUM_CHAT_FRIEND_REQUESTS_ALLOWED = 3 
else:
    GUEST_NUM_CHAT_FRIEND_REQUESTS_ALLOWED = 10 

    
SMALL_TIME_WINDOW_HOURS_FOR_COUNT_UNACCEPTABLE_PROFILE_REPORTS = 3 # hours
SMALL_TIME_WINDOW_MAX_UNACCEPTABLE_PROFILE_REPORTS_BEFORE_BAN = 4 # if this number of reports is received within the window, profile and IP banned
BANNED_IP_NUM_HOURS_TO_BLOCK = 48 #hours (not used yet)


MAX_ACTIVE_POLLING_DELAY_IN_CLIENT = 30 # Cap on the number of *scheduled* seconds between polls from the server (reality can take more time)
# taking into account javascript single-threadedness and client loading, polling does not always happen as fast as we scheduled.
MAX_ACTIVE_POLLING_RESPONSE_TIME_FROM_CLIENT = 1.5 * MAX_ACTIVE_POLLING_DELAY_IN_CLIENT  

IDLE_POLLING_DELAY_IN_CLIENT = 60 # when user status is idle, how many seconds between polls
IDLE_POLLING_RESPONSE_TIME_FROM_CLIENT = 1.5 * IDLE_POLLING_DELAY_IN_CLIENT # amount of time server waits for a response before marking user as offline
AWAY_POLLING_DELAY_IN_CLIENT = 300 # when user is away, how much delay between polls
AWAY_POLLING_RESPONSE_TIME_FROM_CLIENT = 1.5 * AWAY_POLLING_DELAY_IN_CLIENT # amount of time server waits for a response before marking user as offline

INACTIVITY_TIME_BEFORE_IDLE = SECONDS_PER_MINUTE # how many seconds before we mark the user as "idle"
INACTIVITY_TIME_BEFORE_AWAY = 10 * SECONDS_PER_MINUTE # seconds before marking the user as "away"

#SECONDS_BETWEEN_CHAT_FRIEND_TRACKER_DB_WRITE = 30 # to control how often we write the current users online status to the database
SECONDS_BETWEEN_ONLINE_FRIEND_LIST_UPDATE = 10 # for memcaching the *online* friends list, before re-checking the database to see who is still online
SECONDS_BETWEEN_GET_FRIENDS_ONLINE = 10 # for limiting the number of times that we send the list to the client. Note, we send the list
                                        # more often than the list is "updated" (from DB) -- this is good for ensuring that multiple tabs, 
                                        # etc will periodically receive a list of contacts, even if it is not totally up-to-date.
SECONDS_BETWEEN_CHAT_GROUP_MEMBERS_CLEANUP = 10 * SECONDS_PER_MINUTE # every 10 minutes we will verify that all of the members of each chat group are still online,
                                                 # and if they are no longer online, they will be removed from the group
MAX_CHARS_IN_GROUP_NAME = 20
                                        
SECONDS_BETWEEN_UPDATE_CHAT_GROUPS = 5 # we can frequently update this memcache, because it is common for all users (cost is amortized across all users)
SECONDS_BETWEEN_GET_CHAT_GROUPS = 20   # This value determines how often we send an updated group list to each client
SECONDS_BETWEEN_SEND_CHAT_GROUP_MEMBERS_TO_USER = 5 # if the user has the dialog box open that tells who is in a chat group, this tell how often to update it

MAX_CHAT_GROUPS_PER_USER = 5 # if the user tries to create more than this number of chat groups, an error is returned
SECONDS_BETWEEN_EXPIRE_MAX_CHAT_GROUPS_PER_USER = SECONDS_PER_HOUR # when to reset the constraint on the number of chat groups that the user can create

MAX_NUM_CHAT_GROUPS_TO_DISPLAY = 120 # keep the size of the list manageable.
MAX_NUM_PARTICIPANTS_PER_GROUP = 40 # If a group has more than this number of participants it will not allow new registrants

ALL_CHAT_FRIENDS_DICT_EXPIRY = SECONDS_PER_HOUR # How often will we hit the database for *all* "chat friends" of a user, versus pulling out of memcache
CHAT_MESSAGE_CUTOFF_CHARS = 200 #allow this many chars at a time in a single text message

ALL_FRIENDS_DICT_MEMCACHE_PREFIX = "all_friends_dict_"
ONLINE_CONTACTS_INFO_MEMCACHE_PREFIX = "online_contacts_names_dict_"
CHECK_FRIENDS_ONLINE_LAST_UPDATE_MEMCACHE_PREFIX = "check_friends_online_last_update_"

NUM_LANGUAGES_IN_PROFILE_SUMMARY = 8 # only for Language - number of languages to show

MAIL_TEXTAREA_ROWS = 8
MAIL_TEXTAREA_CUTOFF_CHARS = 10000
MAIL_DISPLAY_CHARS = 300
MAIL_SNIP_CHARS = 400
MAIL_SUMMARY_NUM_LINES_TO_SHOW = 2

ABOUT_USER_MAX_ROWS = 15

MAX_CHARS_PER_WORD = 30 # this is used for breaking long (probably fake) words, to ensure that they don't overrrun div boundaries

MAX_NUM_INITIATE_CONTACT_OBJECTS_TO_DISPLAY = 40

MAX_TEXT_INPUT_LEN = 100 # default value for text inputs if not defined.
MAX_USERNAME_LEN = 16 # max number of chars allowed in a username

MAX_LEN_CHANNEL_ID = 64 # the lenght of the channel identifier token, which is used for chat and other real-time communications to client

rematch_non_alpha = re.compile(r'\W+') #match one or more non-alphanumeric characters

# Number of characters to display for the "about me" section, and the cutoff for being considered to have
# entered enough data.
ABOUT_USER_MIN_DESCRIPTION_LEN = 100
ABOUT_USER_MAX_DESCRIPTION_LEN = 5000
ABOUT_USER_SEARCH_DISPLAY_DESCRIPTION_LEN = 1000

# we just take a piece of the hash of the creation date for including in URLs that should be 
# secure (such as changing user options or deleting the profile)--- 
# This length *should* be more than sufficient for the limited security that we need, but we can make it longer 
# in the future if necessary.
EMAIL_OPTIONS_CONFIRMATION_HASH_SIZE = 15 

NUM_HOURS_TO_RESET_MAIL_COUNT = 24
RESET_MAIL_LEEWAY = 2 # we tell the user that they can only send every X hours, but in reality it is X - RESET_MAIL_LEEWAY hours

NUM_HOURS_WINDOW_TO_RESET_MESSAGE_COUNT_TO_OTHER_USER = 24 # to prevent a pair of users from overloading the servers by sending infinite messages between them - put a limit
NUM_MESSAGES_TO_OTHER_USER_IN_TIME_WINDOW = 3 # can only send X messages to another user in a single 24 hour period (or whatever the time window is)

MAX_STORED_SESSIONS = 5 # used for limiting the number of session ids that we will store for a single profile in the UserTracker object.

# Define how many user profiles will be linked to in a single sitemap file.
SITEMAP_MAX_ENTRIES_FOR_USERMODEL = 2000
# Define how many user profile sitemap files will be linked within a single index file.
SITEMAP_INDEX_MAX_ENTRIES_FOR_USERMODEL = 2000


# define the list of pages which we want to advertise
pages_to_advertise = []

if settings.BUILD_NAME == 'Discrete':
    # Swinger, Gay, and Lesbian ads will be dynamically added depending on the search criteria.
    # Since we show AshleyMadison ads here, we only show ads to our other pages if they are 
    # relevant
    pages_to_advertise.append('Single')

if settings.BUILD_NAME == 'Gay':
    pages_to_advertise.append('Discrete')
    pages_to_advertise.append('Swinger')
    
if settings.BUILD_NAME == 'Single':
    # Gay, and Lesbian ads will be dynamically added depending on the search criteria.
    pages_to_advertise.append('Friend')
    pages_to_advertise.append('Language')
    
if settings.BUILD_NAME == 'Lesbian':
    pages_to_advertise == pages_to_advertise.append('Single')
    pages_to_advertise.append('Friend')
    pages_to_advertise.append('Language')
    
if settings.BUILD_NAME == "Swinger":
    pages_to_advertise.append('Discrete')
    pages_to_advertise.append('Gay')
    pages_to_advertise.append('Lesbian')
    
if settings.BUILD_NAME == 'Friend':
    pages_to_advertise == pages_to_advertise.append('Single')
    pages_to_advertise.append('Language')
    
if settings.BUILD_NAME == 'Language':
    pages_to_advertise == pages_to_advertise.append('Single')
    pages_to_advertise.append('Friend')
    

# set a flag that determines if google ads will be shown - we don't attempt to show ads
# on the more edgy sites since this could cause problems / risk of removal from the adsense program
if settings.BUILD_NAME == 'Single' or settings.BUILD_NAME == 'Language' \
   or settings.BUILD_NAME == 'Friend' or settings.BUILD_NAME == 'Lesbian':
    enable_google_ads = True
else:
    enable_google_ads = False
    
enable_internal_ads = True

if settings.BUILD_NAME == 'Gay' or settings.BUILD_NAME == 'Swinger' :
    MAX_NUM_PAGES_TO_ADVERTISE = 4
else:
    MAX_NUM_PAGES_TO_ADVERTISE = 2


    
# set a flag that determines if ashley madison ads will be shown
if settings.BUILD_NAME == 'Discrete':
    enable_ashley_madison_ads = True
else:
    enable_ashley_madison_ads = False
    
# The following data structure is used for converting between the named values for the amount of time between
# message notifications and numerical values which can be looked up. The values reflect the number of hours
# between notifications.

# The following structure is looked at each time that the user receives a new message to see if enough time has 
# passed since the last time that the user has been sent a notification. If sufficient time has passed, then
# a notification email will be immediatly sent. If not enough time has passed, then a "when_to_send_next_notification"
# value will be set, and background task-queue tasks will periodically send out messages after their time is ready. 
hours_between_message_notifications = {
    # The hash key reflects the 
    # value that the user has selected for their notification preference, and the hash value reflects how often they will
    # be sent a notification when they receive a new message.     
    'immediate_notification_of_new_messages': 0.3,  # set to X instead of 0 so that we don't send more than one notification per X hours
    'immediate_notification_of_new_messages_or_contacts' : 0.2,               
    'daily_notification_of_new_messages':24, 
    'daily_notification_of_new_messages_or_contacts':24, 
    'weekly_notification_of_new_messages': 24*7, 
    'weekly_notification_of_new_messages_or_contacts': 24*7, 
    'monthly_notification_of_new_messages': 24*30, 
    'monthly_notification_of_new_messages_or_contacts': 24*30, 
    'only_password_recovery': None,}

# The following structure is similar to the above, but this structure is used for checking if a notification email
# should be sent to the client when they receive a new "contact" (key, wink, kiss) request. 
hours_between_new_contacts_notifications = {
    # how often to notify of winks, kisses, keys.. 
    # Note: if the user has not explicitly specified that they wish to receive "new contacts" notifications, we send them anyway but on
    # a reduced schedule. For example, if someone wants to receive "new message" notifications every day, then it is probable that they would
    # be interested in receiving "new contact" notifications at least once a week. 
    
    # The hash key reflects the 
    # value that the user has selected for their notification preference, and the hash value reflects how often they will
    # be sent a notification when they receive a new "contact" request.    
    'immediate_notification_of_new_messages': 24, #daily notification of "new contacts"
    'immediate_notification_of_new_messages_or_contacts' : 0.3, # set to X instead of 0 so that we don't send more than one notification X hours            
    'daily_notification_of_new_messages': 24*7, # once a week "new contacts" notification
    'daily_notification_of_new_messages_or_contacts':24, 
    'weekly_notification_of_new_messages': 24*30, # monthly "new contact" notification
    'weekly_notification_of_new_messages_or_contacts': 24*7, 
    'monthly_notification_of_new_messages': 24*90, # every three month "new contacts" notification 
    'monthly_notification_of_new_messages_or_contacts': 24*30, 
    'only_password_recovery': None,}

IS_ADULT = False # used in determining what sort of behavior (ie. photo uploads) is allowed, and instructions that will be shown

if settings.BUILD_NAME == "Discrete":
    # Special case for the "discrete" site, because we don't want to explicitly say the name of the site in the address field
    sender_address = u"RS - Customer Support <support@%s>" % domain_name_dict[settings.BUILD_NAME]
    sender_address_html = u"RS - Customer Support &lt;support@%s&gt;" % domain_name_dict[settings.BUILD_NAME]
    admin_address = u"Admin <admin@%s>" % domain_name_dict[settings.BUILD_NAME]
else:
    sender_address = u"%s - Customer Support <support@%s>" % (app_name_dict[settings.BUILD_NAME], domain_name_dict[settings.BUILD_NAME])
    sender_address_html = u"%s - Customer Support &lt;support@%s&gt;" % (app_name_dict[settings.BUILD_NAME], domain_name_dict[settings.BUILD_NAME])
    admin_address = u"Admin <admin@%s>" % domain_name_dict[settings.BUILD_NAME]
    
    
if settings.BUILD_NAME == "Discrete":
    SITE_TYPE = ugettext_lazy('confidential dating website')
    IS_ADULT = True    
    
elif settings.BUILD_NAME == "Single":
    SITE_TYPE = ugettext_lazy('serious dating website')
    
elif settings.BUILD_NAME == "Language":
    SITE_TYPE = ugettext_lazy('website to learn languages and meet people')

elif settings.BUILD_NAME == "Lesbian": 
    SITE_TYPE = ugettext_lazy('lesbian dating website')
    IS_ADULT = True
    
elif settings.BUILD_NAME == "Gay":
    SITE_TYPE = ugettext_lazy('gay dating website')    
    IS_ADULT = True
      
elif settings.BUILD_NAME == "Swinger":
    SITE_TYPE = ugettext_lazy('swingers website')
    IS_ADULT = True

elif settings.BUILD_NAME == "Friend":
    SITE_TYPE = ugettext_lazy('website to meet people, make friends, and to earn money')
    
else:
    raise Exception("Unknown settings.BUILD_NAME")

#following are just formatting options for use in drop-down menus, and other
# form settings.
field_formats = {'right_align_login' :         'cl-td-right-align-login',
                 'left_align_login' :          'cl-td-left-align-login',
                 'right_align_user_main':      'cl-td-right-align-user_main',
                 'left_align_user_main':       'cl-td-left-align-user_main',
                 'text_field_length' :   50,
                 'status_field_length' : 100,}




client_paid_status_num_credits_awarded_for_euros = {
    # credits are multiplied by 100 so that we can represent fractions up to tenths and hundredth. Ie.
    # 500 credits (internally) will be represented to the user as 5 credits. 
    # 450 credits (internally) would be represented to the user as 4.5 credits.
    0 : 0 , # for testing, sometimes we pass in small amounts - this prevents an exception from being raised
    10: 1000, # Euros: Credits - ie. 10 euros gives 1000 credits 
    20: 2000,
    30: 3000,
    40: 4000,
    50: 5000,
    }

reverse_lookup_client_paid_status_num_credits_awarded_for_euros = {}
for k,v in client_paid_status_num_credits_awarded_for_euros.iteritems():
    reverse_lookup_client_paid_status_num_credits_awarded_for_euros[v] = k

max_status_allowed = 'five_diamond'
credits_required_for_each_level_beyond_max = 1000
days_awarded_for_each_level_beyond_max = 90

client_paid_status_credit_amounts = {
    1000: 'single_diamond',
    2000: 'double_diamond',
    3000: 'triple_diamond',
    4000: 'four_diamond' ,
    5000: 'five_diamond',
    }

reverse_lookup_client_paid_status_credit_amounts = {}
for k,v in client_paid_status_credit_amounts.iteritems():
    reverse_lookup_client_paid_status_credit_amounts[v] = k

FREE_STATUS_LEVEL = 'single_diamond'
CREDITS_AWARDED_FOR_A_REFERRAL = reverse_lookup_client_paid_status_credit_amounts[FREE_STATUS_LEVEL]


client_paid_status_number_of_days = {
    'single_diamond' : 31,
    'double_diamond' : 92,
    'triple_diamond' : 182,
    'four_diamond'   : 274,
    'five_diamond'   : 365,
    }

no_diamond_status_text = ugettext_lazy("No VIP")

#diamond_status_text = {
    #'single_diamond' : ugettext_lazy("One Diamond"),
    #'double_diamond' : ugettext_lazy("Two Diamond"),
    #'triple_diamond' : ugettext_lazy("Three Diamond"),
    #'four_diamond'   : ugettext_lazy("Four Diamond"),
    #'five_diamond'   : ugettext_lazy("Five Diamond"),
    #}

diamond_status_num_messages_allowed = {
    'single_diamond' : 10,
    'double_diamond' : 10,
    'triple_diamond' : 10,
    'four_diamond'   : 10,
    'five_diamond'   : 10,
    
}

type_of_site_for_vip_invite = {
    'Discrete' : ugettext_lazy('confidential dating'),
    'Single' : ugettext_lazy('dating'),
    'Language' : ugettext_lazy('language exchange'),
    'Swinger': ugettext_lazy('swingers'),
    'Gay': ugettext_lazy('gay dating'),
    'Lesbian': ugettext_lazy('lesbian dating'),
    'Friend': '',
}
    
    

# This data structure is used for offsetting the unique_last_login value so that search order will be
# modified based on profile characteristics that are considered to be important.
# offsets are given in hours

# Note: to avoid double counting only on of the photo-related offsets will be counted. See code in login_utils - 
# get_or_create_unique_last_login() for how these special cases are counted.
offset_values = {'has_profile_photo_offset':24, 
                 'has_private_photo_offset':12,
                 #Note, it is possible to have public photos without having a profile photo -- but you cannot have a
                 # profile photo without having a public photo.
                 'has_public_photo_offset':12,
                 'has_about_user_offset': 24, 
                 'has_languages_offset': 0, 
                 'has_entertainment_offset': 0.1, 
                 'has_athletics_offset': 0.1,
                 'has_turn_ons_offset': 0.1,
                 'has_erotic_encounters_offset':0.1,
                 'has_email_address_offset': 0,
                 #'has_single_diamond_offset' : 1,
                 #'has_double_diamond_offset' : 1.5,
                 #'has_triple_diamond_offset' : 2,
                 #'has_four_diamond_offset' : 2.5,
                 #'has_five_diamond_offset' : 3,
                 }


############################################
class ErrorMessages():
    # all user-oriented error messages should appear here, so that translations into 
    # other languages will be easier in the future.

    username_alphabetic = ugettext_lazy("Username needs at least 3 characters and can only contain letters \
and numbers. Additionally, it may not contain any spaces.")
    password_required = ugettext_lazy("Password required")
    password_alphabetic = ugettext_lazy("Password may only contain letters and numbers, and cannot contain spaces.")
    passwords_not_match = ugettext_lazy("The password and the verification must be the same.")
    username_taken = ugettext_lazy("The username that you have selected is not available.")
    incorrect_username_password = ugettext_lazy("Username/email + password is incorrect")
    email_address_invalid = ugettext_lazy("The email address is not valid")

    @classmethod
    def num_messages_to_other_in_time_window(cls, num, window):
        return ugettext_lazy("""You can only send %(num)s messages to another user in a single %(hours)s-hour period. 
                    Please use the chat functionality if you wish to have more frequent contact.""") % {'num': num,
                                                                                                        'hours': window}



############################################


    
class ContactIconText():
    the_last = ugettext_lazy("only the last")
    sent = ugettext_lazy("Sent")
    received = ugettext_lazy("Received")
    saved = ugettext_lazy("Saved")
    
    if settings.BUILD_NAME == "Language" or settings.BUILD_NAME == "Friend":
        plural_winks = ugettext_lazy('Greetings')
        wink_text = ugettext_lazy("Send them a greeting")
    else:
        plural_winks = ugettext_lazy('Winks')
        wink_text = ugettext_lazy("Send them a wink")    
    
    plural_icon_name = {
        'favorite': ugettext_lazy('My favorites'),
        'wink': plural_winks,
        'kiss': ugettext_lazy('Kisses'),
        'key': ugettext_lazy('Keys'),
        'chat_friend' : ugettext_lazy('Chat friends'),
        'blocked' : ugettext_lazy('Blocked (plural)'),
    }

    chat_friend_plural_text = {
        'request_sent' : ugettext_lazy('Chat requests'),
        'request_received': ugettext_lazy('Chat requests'),
        'connected': ugettext_lazy('Chat connections'),
    }
        
    icon_message = {
        'favorite': ugettext_lazy("Add them to your list of favorites"),
        'wink': wink_text,
        'kiss': ugettext_lazy("Send them a kiss"),
        'key': ugettext_lazy("Give them access to your private photos"),
        'chat_friend': ugettext_lazy("Invite them to chat with you"),
        'blocked' : ugettext_lazy("Block this user (delete new messages automatically)"),
    }
    if settings.BUILD_NAME != "Language" and settings.BUILD_NAME != "Friend":
        wink_icon = "wink.png"
    else:
        wink_icon = "greeting.png"
        
    icon_images = {'favorite': 'star.png', 'wink':wink_icon, 'kiss':'kiss.png', 'key':'key.png', 'chat_friend' : 'chat_bubble.png', 'blocked' : 'stop.png'}

    
class PassDataToTemplate():
    # Dummy (empty) class that we can fill in with whatever we want
    pass


template_common_fields = {'build_name': settings.BUILD_NAME,
                          'app_name' : settings.APP_NAME,
                          'domain_name' : settings.DOMAIN_NAME,
                          'site_type' : SITE_TYPE,
                          'company_name' : COMPANY_NAME,
                          'company_www' : COMPANY_WWW,
                          'live_static_dir': settings.LIVE_STATIC_DIR,  
                          'live_proprietary_static_dir': settings.LIVE_PROPRIETARY_STATIC_DIR,  
                          'proprietary_static_dir_exists': settings.PROPRIETARY_STATIC_DIR_EXISTS,
                          'num_messages_for_free_clients': MAX_EMAILS_PER_DAY,
                          'num_messages_for_vip_clients' : diamond_status_num_messages_allowed['single_diamond'],
                          'num_chat_friends_for_free_clients' :  GUEST_NUM_CHAT_FRIEND_REQUESTS_ALLOWED,
                          'num_chat_friends_for_vip_clients' : MAX_CHAT_FRIEND_REQUESTS_ALLOWED,  
                          'google_ad_160x600' : GOOGLE_AD_160x600,
                          'google_ad_728x90' : GOOGLE_AD_728x90,
                          'analytics_id' : settings.ANALYTICS_ID,
                          }