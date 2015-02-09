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


from django.utils.translation import ugettext_lazy

import re
import datetime, logging, math

from rs.private_data import *
import settings, site_configuration

# This file contains all the declarations for constant values that are used at various places in the code
# This should help to keep the code more maintainable, and consistent.

if settings.LANGUAGE_CODE == 'en':
    default_languages_field_value = "english"
elif settings.LANGUAGE_CODE == 'es':
    default_languages_field_value = "spanish"
else:
    raise Exception("Unknown settings.LANGUAGE_CODE")


# The following "SHOW_VIP_UPGRADE_OPTION" is at the top because it is used in some of the other 
# constant declarations. If we don't allow the users to purchase a VIP option for a particular build,
# then we treat all the users of that build as VIP (to some degree). 
if site_configuration.BUILD_NAME == 'discrete_build':
    SHOW_VIP_UPGRADE_OPTION = True
else:
    # currently, only discrete_build build allows users to upgrade to VIP. 
    # Other sites are supported by advertising.
    SHOW_VIP_UPGRADE_OPTION = False

    
if settings.BUILD_NAME == "language_build" : 
    minimum_registration_age = 14
else:
    minimum_registration_age = 18
    
    
# if the user attempts to register from one of the following URLs then during the secret code verification step they will be directed
# to a different page (instead of the default behaviour of showing the page that they activated the registration box on). 
# As of Nov 5 2013, members will be directed to the "edit_profile" page if they have registered from one of the
# following urls.
URLS_THAT_NEED_REDIRECT_AFTER_ENTRY = set(["/", "/rs/admin/login/", "/rs/submit_email_for_reset_password/",
                                           "/rs/welcome/", "/rs/press/", "/rs/delete_account/"])


# Define the number of new people that the user can send messages to in a given time window.

# if this is a site where SHOW_VIP_UPGRADE_OPTION is true, then this is a site that we want the user to upgrade
# to a paying status. Therefore, there are more restrictions/limitations on the number of messages and people that
# they are allowed to contact, as opposed to the totally free sites that have less restrictions.
if SHOW_VIP_UPGRADE_OPTION:
    # They have the option of purchasing VIP - therefore the quota is lower (pay if they want more)
    GUEST_NUM_NEW_PEOPLE_MESSAGES_ALLOWED_IN_WINDOW = 1 # after this number of messages, sending messages is blocked for non-paying members.
    GUEST_WINDOW_DAYS_FOR_NEW_PEOPLE_MESSAGES = 2  # days before the counters will be reset

# Else, this is a totally free website, and therefore we have more generous quotas.
else:
    GUEST_NUM_NEW_PEOPLE_MESSAGES_ALLOWED_IN_WINDOW = 10
    GUEST_WINDOW_DAYS_FOR_NEW_PEOPLE_MESSAGES = 1  # days before the counters will be reset
    
GUEST_WINDOW_HOURS_FOR_NEW_PEOPLE_MESSAGES = GUEST_WINDOW_DAYS_FOR_NEW_PEOPLE_MESSAGES * 24

# if this member is VIP, then they will be allowed to send messages to more people in the "window", and the window
# is smaller (meaning it resets more often)
VIP_WINDOW_HOURS_FOR_NEW_PEOPLE_MESSAGES = 24 # X hours before the counters will be reset
VIP_NUM_NEW_PEOPLE_MESSAGES_ALLOWED_IN_WINDOW = 10
    
    
NUM_HOURS_WINDOW_TO_RESET_MESSAGE_COUNT_TO_OTHER_USER = 36 # to prevent a pair of users from overloading the servers by sending infinite messages between them - put a limit

if SHOW_VIP_UPGRADE_OPTION:
    # VIP purchase is available - this user should pay if they want to send more messages.
    STANDARD_NUM_MESSAGES_TO_OTHER_USER_IN_TIME_WINDOW = 1 # can only send X messages to another user in a window period
    # If the users are "chat friends" or one of them is VIP, then they can send more messages between them in time window period.
    VIP_AND_CHAT_FRIEND_NUM_MESSAGES_TO_OTHER_USER_IN_TIME_WINDOW = 50
else:
    STANDARD_NUM_MESSAGES_TO_OTHER_USER_IN_TIME_WINDOW = 20
    # no special benefit for being chat friends in the free sites.
    VIP_AND_CHAT_FRIEND_NUM_MESSAGES_TO_OTHER_USER_IN_TIME_WINDOW = STANDARD_NUM_MESSAGES_TO_OTHER_USER_IN_TIME_WINDOW

    
RESET_MAIL_LEEWAY = 2 # we tell the user that they can only send every X hours, but in reality it is X - RESET_MAIL_LEEWAY hours

SMALL_IMAGE_X = SMALL_IMAGE_Y = 65
MEDIUM_IMAGE_X = MEDIUM_IMAGE_Y = 120
LARGE_IMAGE_X = LARGE_IMAGE_Y = 400 

MAX_NUM_PHOTOS = 6
PHOTOS_PER_ROW = 6

CHECKBOX_INPUT_COLS_PER_ROW = 4

MAX_KEYS_SENT_ALLOWED = 40

######################################################################
## START - Time Constants

# Define constants that are used for caching and other stuff - Note: the values for month and year are approximate.
SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 60 * SECONDS_PER_MINUTE
SECONDS_PER_DAY = 24 * SECONDS_PER_HOUR
SECONDS_PER_WEEK = 7 * SECONDS_PER_DAY
SECONDS_PER_MONTH = 30 * SECONDS_PER_DAY
SECONDS_PER_YEAR = 365 * SECONDS_PER_DAY

## END - Time Constants
######################################################################


######################################################################
## START - Session and Malicious User Controls

SESSION_EXPIRE_HOURS = 90 * 24 # 90 days before sessions expire (if we need to manually kill all current sessions, change site_configuration.SECRET_KEY)

MAX_STORED_SESSIONS = 5 # used for limiting the number of session ids that we will store for a single profile in the UserTracker object.

# If a user exceeds the following number of attempted registrations with a single email address in one day
# then they will not be sent any more registration emails. This prevents someone from spamming an email address 
# with multiple registration requests. 
MAX_REGISTRATIONS_SINGLE_EMAIL_IN_TIME_WINDOW = 2 
# single IP address will be denied if this number is exceeded within a single day. This is necessary to 
# prevent an attack in which someone attempts to register a large number of email addresses that do not
# belong to them.
MAX_REGISTRATIONS_SINGLE_IP = 20  

SMALL_TIME_WINDOW_HOURS_FOR_COUNT_UNACCEPTABLE_PROFILE_REPORTS = 3 # hours
SMALL_TIME_WINDOW_MAX_UNACCEPTABLE_PROFILE_REPORTS_BEFORE_BAN = 4 # if this number of reports is received within the window, profile and IP banned

## START - Malicious User Controls
######################################################################

######################################################################
## START - General Memcache Constants
# include the version identifier in the memcache prefix for objects that have a probability of changing
# between version upates - currently this is done for the userobject and any other objects that use
# utils.put_object() for writing to the database
BASE_OBJECT_MEMCACHE_PREFIX = "_base_object_" + site_configuration.VERSION_ID + "_"
PROFILE_URL_DESCRIPTION_MEMCACHE_PREFIX = "_profile_url_description_"  + site_configuration.VERSION_ID + "_"
PROFILE_TITLE_MEMCACHE_PREFIX = "_profile_title_"  + site_configuration.VERSION_ID + "_"
NID_MEMCACHE_PREFIX = "_nid_memcache_prefix_" + site_configuration.VERSION_ID
INITIATE_CONTACT_MEMCACHE_PREFIX = "_initiate_contact_" + site_configuration.VERSION_ID + "_"

## END - General Memcache Constants
######################################################################
# We want to remove all EmailAuthorizationModel objects that are older than X days.
REMOVE_EMAIL_AUTHORIZATION_OBECTS_OLDER_THAN_DAYS = 30
######################################################################
## START Sitemap Constants

# Define how many user profiles will be linked to in a single sitemap file.
SITEMAP_MAX_ENTRIES_FOR_USERMODEL = 50
# Define how many user profile sitemap files will be linked within a single index file.
SITEMAP_INDEX_MAX_ENTRIES_FOR_USERMODEL = 5000

## END Sitemap Constants
######################################################################

######################################################################
## Chat Functionality Constants

# In general we don't want to clear all of the chat related memcaches every time that we update the version
# of code - however, if we have been modifying the chat functionality then we do wish to force an update. 
# Change the following value if you want to force all chat-related memcaches to be refreshed when this
# version of code is uploaded
FORCE_UPDATE_CHAT_MEMCACHE_STRING = "2014-02-13-0153-" 
NUM_CHAT_MESSAGES_IN_QUERY = 30 # how many chat messages will we return in a query - Note: this limit is not only about memory utilization, but
                                # also about how many messages we want to send to the user every time they re-load the chatbox. 
MAX_CHAT_FRIEND_REQUESTS_ALLOWED = 200 # requests + accepted friends cannot exceed this number - keep queries to manageable size

# this is the limit on the number of chat_friends for non-registered users
if SHOW_VIP_UPGRADE_OPTION:
    GUEST_NUM_CHAT_FRIEND_REQUESTS_ALLOWED = 1
else:
    GUEST_NUM_CHAT_FRIEND_REQUESTS_ALLOWED = 50 

class OnlinePresenceConstants(object):
    MAX_ACTIVE_POLLING_DELAY_IN_CLIENT = 30 # Cap on the number of *scheduled* seconds between polls from the client (reality can take more time)
    IDLE_POLLING_DELAY_IN_CLIENT = 60 # when user status is idle, how many seconds between polls
    AWAY_POLLING_DELAY_IN_CLIENT = 300 # when user is away, how much delay between polls

    INACTIVITY_TIME_BEFORE_IDLE = 2 * SECONDS_PER_MINUTE # time before we mark the user as "idle"
    INACTIVITY_TIME_BEFORE_AWAY = 10 * SECONDS_PER_MINUTE # time before marking the user as "away"


class ChatBoxStatus(object):
    # disable is when the user explicity closes their chat (will not go online if they become active
    # until they click on "enable/open chat" button)
    IS_DISABLED = 'chatDisabled'
    IS_ENABLED = 'chatEnabled' # Indicates that the user has opened the chatboxes and chat is enabled

    
    CHAT_BOX_STATUS_MEMCACHE_TRACKER_PREFIX = "_chat_box_status_memcache_tracker_" + FORCE_UPDATE_CHAT_MEMCACHE_STRING
    
    
class OnlinePresence(object): 
    # Define the values that will be used to define the chat online presence for each user that has 
    # their chatboxes open.
    # When chat is enabled, user status can be one of the following values.
    ACTIVE = 'userPresenceActive' # user is actively using the website (not only chat, but also navigating or moving the mouse)
    IDLE = 'userPresenceIdle'     # user has not moved the cursor across the page in INACTIVITY_TIME_BEFORE_IDLE seconds
    AWAY = 'userPresenceAway'    # user has not moved the cursor across the page in INACTIVITY_TIME_BEFORE_AWAY seconds
    
    # OFFLINE is when the user has either explicity logged off, or if we have not received a ping from the client javascript
    # code in such a long time, that it is likely that they closed the window without logging off. 
    OFFLINE = 'userPresenceOffline'
 
    presence_text_dict = {
        ACTIVE: ugettext_lazy("(Active)"),
        IDLE: ugettext_lazy("(Idle)"),
        AWAY: ugettext_lazy("(Away)"),
        OFFLINE: ugettext_lazy("(Offline)"),
    }
    
    presence_color_dict = {
        ACTIVE: '1-green',
        IDLE: '2-yellow',
        AWAY: '3-red',
        OFFLINE: '4-black'
        }
    
    STATUS_MEMCACHE_TRACKER_PREFIX = "_online_status_memcache_tracker_" + FORCE_UPDATE_CHAT_MEMCACHE_STRING

    # taking into account javascript single-threadedness and client loading, polling does not always happen as fast as we scheduled.
    MAX_ACTIVE_POLLING_RESPONSE_TIME_FROM_CLIENT = 1.5 * OnlinePresenceConstants.MAX_ACTIVE_POLLING_DELAY_IN_CLIENT  
    MAX_IDLE_POLLING_RESPONSE_TIME_FROM_CLIENT = 1.5 * OnlinePresenceConstants.IDLE_POLLING_DELAY_IN_CLIENT # amount of time server waits for a response before marking user as offline
    MAX_AWAY_POLLING_RESPONSE_TIME_FROM_CLIENT = 1.5 * OnlinePresenceConstants.AWAY_POLLING_DELAY_IN_CLIENT # amount of time server waits for a response before marking user as offline

class SessionStatus(object):
    
    # If the session has expired, then we want the javascript code to stop polling the server. Returning an
    # EXPIRED_SESSION string to the client javascript allows it to detect that the session has expired, and
    # therfore to stop polling.
    EXPIRED_SESSION = "session_expired_session"   
    
    # If we have an error condition we should stop the client from polling -- but we should not log the client off.
    SERVER_ERROR = "session_server_error"
    

SECONDS_BETWEEN_ONLINE_FRIEND_LIST_UPDATE = 10 # for memcaching the *online* friends list, before re-checking the database to see who is still online
SECONDS_BETWEEN_GET_FRIENDS_ONLINE = 10 # for limiting the number of times that we send the list to the client. Note, we send the list
                                        # more often than the list is "updated" (from DB) -- this is good for ensuring that multiple tabs, 
                                        # etc will periodically receive a list of contacts, even if it is not totally up-to-date.

SECONDS_BETWEEN_CHAT_GROUP_MEMBERS_CLEANUP = 5 # every X seconds we will verify that all of the members of each chat group are still online,
                                               # and if they are no longer online, they will be removed from the group. This is split across
                                               # many group members, and so updating often has an amortized cost.

CHAT_MESSAGE_EXPIRY_TIME = 24 * SECONDS_PER_HOUR # expire chat messages after X hours 

MAX_CHARS_IN_GROUP_NAME = 20
                                        
SECONDS_BETWEEN_UPDATE_CHAT_GROUPS = 5 # we can frequently update this memcache, because it is common for all users (cost is amortized across all users)

MAX_CHAT_GROUPS_PER_USER = 5 # if the user tries to create more than this number of chat groups, an error is returned
SECONDS_BETWEEN_EXPIRE_MAX_CHAT_GROUPS_PER_USER = SECONDS_PER_HOUR # when to reset the constraint on the number of chat groups that the user can create

MAX_NUM_CHAT_GROUPS_TO_DISPLAY = 120 # keep the size of the list manageable.
MAX_NUM_PARTICIPANTS_PER_GROUP = 40 # If a group has more than this number of participants it will not allow new registrants

ALL_CHAT_FRIENDS_DICT_EXPIRY = SECONDS_PER_HOUR # How often will we hit the database for *all* "chat friends" of a user, versus pulling out of memcache
CHAT_MESSAGE_CUTOFF_CHARS = 200 #allow this many chars at a time in a single text message

ALL_CHAT_FRIENDS_DICT_MEMCACHE_PREFIX = "_all_friends_dict_" + FORCE_UPDATE_CHAT_MEMCACHE_STRING
ONLINE_CHAT_CONTACTS_INFO_MEMCACHE_PREFIX = "_online_contacts_info_dict_" + FORCE_UPDATE_CHAT_MEMCACHE_STRING
CHECK_CHAT_FRIENDS_ONLINE_LAST_UPDATE_MEMCACHE_PREFIX = "_check_friends_online_last_update_" + FORCE_UPDATE_CHAT_MEMCACHE_STRING

## End Chat Functionality Constants

######################################################################
## AcceptTermsAndRules Constants
# if the userobject AcceptTermsAndRules show_photo_rules_string does not match this value, then
# the user will be shown the photo rules again.
SHOW_PHOTO_RULES_CURRENT_RULES = "July 11 2013" 

######################################################################
## Database (Google Cloud Storage) Backup Constants
CLOUD_STORE_NUM_BACKUPS_TO_KEEP = 3


###################################################
## START Advertising related constants
# define the list of pages which we want to advertise
lexabit_self_publicity_ads = []

# If this is True, then we include the javascript and text that will be shown which the user clicks on "show me more info" 
# with respect to purchasing advertising on our websites.
append_more_advertising_info_dialog = False

# Pages with Google Ads (ie. family friendly) first.
# Note: these lists may not represent the final advertisements that are shown to the user. We post-process this information
# to include criteria such as users search parameters and profile information - ie. if a man is looking for a man, we may
# show them gay advertisements in addition to what is listed below (see: get_additional_ads_to_append() for implementation)

enable_amazon_ads = False

if settings.BUILD_NAME == 'default_build':
    enable_google_ads = False
    
elif settings.BUILD_NAME == 'language_build':
    enable_google_ads = True
    
elif settings.BUILD_NAME == 'mature_build':
    enable_google_ads = True
    
elif settings.BUILD_NAME == 'single_build':
    enable_google_ads = True


elif settings.BUILD_NAME == 'lesbian_build':
    enable_google_ads = True
    
    
# Pages that are more adult oriented.
elif settings.BUILD_NAME == 'discrete_build':
    # Additional ads will be dynamically added depending on the search criteria -- this happens in rendering.py
    enable_google_ads = False
    lexabit_self_publicity_ads.append('single_build')
    lexabit_self_publicity_ads.append('lesbian_build')
    lexabit_self_publicity_ads.append('mature_build')
    #lexabit_self_publicity_ads.append('Client_Ad1')
    #append_more_advertising_info_dialog = True
    

elif settings.BUILD_NAME == 'gay_build':
    enable_google_ads = False
    lexabit_self_publicity_ads.append('discrete_build')
    lexabit_self_publicity_ads.append('single_build')
    lexabit_self_publicity_ads.append('lesbian_build')
    lexabit_self_publicity_ads.append('mature_build')


    
elif settings.BUILD_NAME == "swinger_build":
    enable_google_ads = False
    lexabit_self_publicity_ads.append('discrete_build')
    lexabit_self_publicity_ads.append('lesbian_build')
    lexabit_self_publicity_ads.append('single_build')
    lexabit_self_publicity_ads.append('mature_build')


else:
    logging.error("Unknown BUILD_NAME")
    
    
if enable_google_ads:
    # we are showing google ads, we don't want to distract too with our own advertising.
    MAX_NUM_LEXABIT_ADS_TO_SHOW = 0

elif enable_amazon_ads:
    # After trying amazon ads for a while, this value should be re-visited
    MAX_NUM_LEXABIT_ADS_TO_SHOW = 3

else:
    MAX_NUM_LEXABIT_ADS_TO_SHOW = 4

        
## END Advertising related constants
###################################################
    

###################################################
## START Email Notification settings
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


## END Email Notification settings
###################################################

    
###################################################
## START Site-description 
ADULT_ORIENTED_SITE = False # used in determining what sort of behavior (ie. photo uploads) is allowed, and instructions that will be shown
SITE_IS_TOTALLY_FREE = True    

if settings.BUILD_NAME == "default_build":
    SITE_TYPE = ugettext_lazy('Your very own dating website')
    ADULT_ORIENTED_SITE = False    
    SITE_IS_TOTALLY_FREE = False
    
elif settings.BUILD_NAME == "discrete_build":
    SITE_TYPE = ugettext_lazy('confidential dating website')
    ADULT_ORIENTED_SITE = True    
    SITE_IS_TOTALLY_FREE = False
    
elif settings.BUILD_NAME == "single_build":
    SITE_TYPE = ugettext_lazy('serious dating website')
    
elif settings.BUILD_NAME == "language_build":
    SITE_TYPE = ugettext_lazy('website to learn languages and meet people')

elif settings.BUILD_NAME == "lesbian_build": 
    SITE_TYPE = ugettext_lazy('lesbian dating website')
    ADULT_ORIENTED_SITE = True
    
elif settings.BUILD_NAME == "gay_build":
    SITE_TYPE = ugettext_lazy('gay dating website')    
    ADULT_ORIENTED_SITE = True
      
elif settings.BUILD_NAME == "swinger_build":
    SITE_TYPE = ugettext_lazy('swingers website')
    ADULT_ORIENTED_SITE = True

elif settings.BUILD_NAME == "mature_build":
    SITE_TYPE = ugettext_lazy('dating website to meet mature adults over 40 years old')
    
else:
    raise Exception("Unknown settings.BUILD_NAME")

## END Site-description    
###################################################


###################################################
## START VIP/Paid Client Related


# Memcache object to store the VIP (client_paid_status) for each user 
# We don't set a timeout on this, since we will manually expire it if the userobject is updated. 
HIDDEN_ONLINE_STATUS = "hidden_online_status"

# Define how many minutes of viewing others online status they will be allowed in a time window
SHOW_ONLINE_STATUS_TRIAL_TIMEOUT_MINUTES = 5
SHOW_ONLINE_STATUS_TRIAL_TIMEOUT_SECONDS = SHOW_ONLINE_STATUS_TRIAL_TIMEOUT_MINUTES * SECONDS_PER_MINUTE

# define when the time window resets - they will not be allowed to use this trial feature until 
# this memcache value is no longer set (it may get flushed earlier than expected, in which case
# they will be given another free trial)
BLOCK_ONLINE_STATUS_TRIAL_RESET_HOURS = 24
BLOCK_ONLINE_STATUS_TRIAL_RESET_SECONDS = BLOCK_ONLINE_STATUS_TRIAL_RESET_HOURS * SECONDS_PER_HOUR

# memcache value that will determine if we should show online status
SHOW_ONLINE_STATUS_TRIAL_TIMEOUT_MEMCACHE_PREFIX = "_SHOW_ONLINE_STATUS_TRIAL_TIMEOUT_MEMCACHE_PREFIX_" + site_configuration.VERSION_ID + "_"

# memcache value that indicates that the user has already used a free trial of online status
BLOCK_ONLINE_STATUS_TRIAL_TIMEOUT_MEMCACHE_PREFIX = "_BLOCK_ONLINE_STATUS_TRIAL_TIMEOUT_MEMCACHE_PREFIX_" + site_configuration.VERSION_ID + "_"


NUMER_OF_DAYS_PROFILE_VIEWS_STORED = 30



###################################################
## START Formatting Options

NUM_LANGUAGES_IN_PROFILE_SUMMARY = 8 # only for language_build - number of languages to show

MAIL_TEXTAREA_ROWS = 8
MAIL_TEXTAREA_CUTOFF_CHARS = 10000
MAIL_DISPLAY_CHARS = 300
MAIL_SNIP_CHARS = 400
MAIL_SUMMARY_NUM_LINES_TO_SHOW = 2

ABOUT_USER_MAX_ROWS = 15

MAX_NUM_INITIATE_CONTACT_OBJECTS_TO_DISPLAY = 40
NUM_INITIATE_CONTACT_OBJECTS_PER_PAGE = 6

MAX_TEXT_INPUT_LEN = 100 # default value for text inputs if not defined.
MAX_USERNAME_LEN = 16 # max number of chars allowed in a username

rematch_non_alpha = re.compile(r'\W+', re.UNICODE) #match one or more non-alphanumeric characters

# Number of characters to display for the "about me" section, and the cutoff for being considered to have
# entered enough data.
ABOUT_USER_MIN_DESCRIPTION_LEN = 300
ABOUT_USER_MAX_DESCRIPTION_LEN = 10000
TYPICAL_NUM_CHARS_PER_LINE = 90 # used for computing how many lines of a description they must write
ABOUT_USER_MIN_NUM_LINES_FLOAT = ABOUT_USER_MIN_DESCRIPTION_LEN / float(TYPICAL_NUM_CHARS_PER_LINE)
ABOUT_USER_MIN_NUM_LINES_INT = int(math.ceil(ABOUT_USER_MIN_NUM_LINES_FLOAT)) # round up to nearest integer
ABOUT_USER_SEARCH_DISPLAY_DESCRIPTION_LEN = 1000

# we just take a piece of the hash of the creation date for including in URLs that should be 
# secure (such as changing user options or deleting the profile)--- 
# This length *should* be more than sufficient for the limited security that we need, but we can make it longer 
# in the future if necessary.
EMAIL_OPTIONS_CONFIRMATION_HASH_SIZE = 15 


#following are just formatting options for use in drop-down menus, and other
# form settings.
field_formats = {'right_align_login' :         'cl-td-right-align',
                 'left_align_login' :          'cl-td-left-align',
                 'right_align_user_main':      'cl-td-right-align-user_main',
                 'left_align_user_main':       'cl-td-left-align-user_main',
                 'text_field_length' :   50,
                 'status_field_length' : 100,}

## END Formatting Options
###################################################
# This is a bit confusing, but because of the lazy translation of the VIP member text, we cannot include it 
# into the vip_member_anchor until it is requied and has the language correctly defined for the current user.
vip_member_anchor = u"""<a class="cl-see_all_vip_benefits" href="#">%s</a>"""
vip_member_txt = ugettext_lazy("VIP member") 

############################################
class ErrorMessages():
    # all user-oriented error messages should appear here, so that translations into 
    # other languages will be easier in the future.

    username_alphabetic = ugettext_lazy("<strong>Username</strong> can only contain letters and numbers, and must not contain spaces.")    
    username_too_short = ugettext_lazy("<strong>Username</strong> needs at least 3 characters.")
    password_required = ugettext_lazy("<strong>Password</strong> required")
    passwords_not_match = ugettext_lazy("The <strong>Password</strong> and the <strong>Verification Password</strong> must be the same.")
    username_taken = ugettext_lazy("The <strong>Username</strong> that you have selected is not available.")
    incorrect_username_password = ugettext_lazy("<strong>Username/email + Password</strong> is incorrect")
    email_address_invalid = ugettext_lazy("The <strong>Email Address</strong> is not valid")

    @classmethod
    def num_messages_to_other_in_time_window(cls, txt_for_when_quota_resets, vip_status):

        generated_html = ''
            
        if not vip_status:
            if SHOW_VIP_UPGRADE_OPTION:
                generated_html += ugettext_lazy("""
                Given that neither you nor the person that you would like to contact is %(vip_member)s,
                you can only send them %(guest_num)s message in each %(hours)s-hour period.
                However, if the you or the other user become a %(vip_member)s, or if they become a "chat friend" of yours,
                then you can send them up to %(chat_friend_num)s messages in each
                %(hours)s-hour period.<br><br>""") % \
                       {'guest_num': STANDARD_NUM_MESSAGES_TO_OTHER_USER_IN_TIME_WINDOW,
                        'chat_friend_num' : VIP_AND_CHAT_FRIEND_NUM_MESSAGES_TO_OTHER_USER_IN_TIME_WINDOW,
                        'hours': NUM_HOURS_WINDOW_TO_RESET_MESSAGE_COUNT_TO_OTHER_USER,
                        'vip_member' : vip_member_anchor % vip_member_txt,}
            else:
                generated_html += ugettext_lazy("""You can only send %(guest_num)s messages to each member each %(hours)s-hour period.<br><br>""") % \
                       {'guest_num': STANDARD_NUM_MESSAGES_TO_OTHER_USER_IN_TIME_WINDOW,
                        'hours': NUM_HOURS_WINDOW_TO_RESET_MESSAGE_COUNT_TO_OTHER_USER,}
        else:
            generated_html += ugettext_lazy("""As a VIP member, you can send up to %(vip_num)s messages to each member in each %(hours)s
            hour period. You have now reached this limit.<br><br>""") % {
                'vip_num' : VIP_AND_CHAT_FRIEND_NUM_MESSAGES_TO_OTHER_USER_IN_TIME_WINDOW,
                'hours' : NUM_HOURS_WINDOW_TO_RESET_MESSAGE_COUNT_TO_OTHER_USER}
                    
        generated_html += ugettext_lazy("""You can send more messages to this member %(txt_for_when_quota_resets)s.""") % {
                    'txt_for_when_quota_resets' : txt_for_when_quota_resets
                    }
        
        return generated_html
    

# The following variable is passed to javascript as a text string, and therefore must *not* contain any line breaks.
MUST_REGISTER_TO_SEND_MESSAGES_MSG = ugettext_lazy("""\
You must register for a <strong>free account</strong> in order to contact our members. \
""")

############################################
if settings.BUILD_NAME != "language_build":
    list_of_contact_icons = [ 'favorite', 'wink', 'kiss',  'key', 'chat_friend','blocked']
    menu_items_list = ['wink', 'kiss', 'key', 'chat_friend']
else:
    # Notes: 1) we remove "kisses" completely. 2) we overload "wink" to mean greeting (but the code refers to it as a wink)
    list_of_contact_icons = [ 'favorite', 'wink', 'key', 'chat_friend', 'blocked']
    menu_items_list = ['wink', 'key', 'chat_friend']

    
class ContactIconText():
    
    contacts_action_gender = {
        'favorite': 'masculine',
        'wink': 'masculine',
        'kiss': 'masculine',
        'key': 'feminine',
        'chat_friend' : 'masculine',
        'blocked' : 'masculine',
    }
    
    the_last = ugettext_lazy("only the last")
    singular_contacts_actions_text = {
        'sent' : ugettext_lazy("sent (singular)"),
        'received' : ugettext_lazy("received (singluar)"),
        'saved' : ugettext_lazy("saved (singular)"),
        'connected' : ugettext_lazy("confirmed (singular)"),
        '': '',
    }
    
    plural_contacts_actions_text = {}
    plural_contacts_actions_text['masculine'] = {
        'sent' : {'no_capitalize' : ugettext_lazy("sent (plural)"), 'capitalize' : ugettext_lazy("Sent (plural)")},
        'received' : {'no_capitalize' : ugettext_lazy("received (plural)"), 'capitalize' : ugettext_lazy("Received (plural)")},
        'saved' : {'no_capitalize' : ugettext_lazy("saved (plural)"),'capitalize' : ugettext_lazy("Saved (plural)")}, 
        'connected' : {'no_capitalize' : ugettext_lazy("confirmed (plural)"), 'capitalize' :  ugettext_lazy("Confirmed (plural)")},
        #'': '',
    }    
    
    plural_contacts_actions_text['feminine'] = {
        'sent' : {'no_capitalize' : ugettext_lazy("sent (plural feminine)"), 'capitalize' : ugettext_lazy("Sent (plural feminine)")},
        'received' : {'no_capitalize' : ugettext_lazy("received (plural feminine)"), 'capitalize' : ugettext_lazy("Received (plural feminine)")}, 
        'saved' : {'no_capitalize' : ugettext_lazy("saved (plural feminine)"), 'capitalize' : ugettext_lazy("Saved (plural feminine)")},
        'connected' : {'no_capitalize' : ugettext_lazy("confirmed (plural feminine)"), 'capitalize' : ugettext_lazy("Confirmed (plural feminine)")}, 
        #'': '',
    }       
    
    if settings.BUILD_NAME == "language_build":
        plural_winks = ugettext_lazy('Greetings')
        wink_text = ugettext_lazy("Send them a greeting")
        singular_wink = ugettext_lazy('Greeting')
    else:
        plural_winks = ugettext_lazy('Winks')
        wink_text = ugettext_lazy("Send them a wink")    
        singular_wink = ugettext_lazy('Wink')
    
    plural_icon_name = {
        'favorite': ugettext_lazy('My favorites'),
        'wink': plural_winks,
        'kiss': ugettext_lazy('Kisses'),
        'key': ugettext_lazy('Keys'),
        'chat_friend' : ugettext_lazy('Chat friends'),
        'blocked' : ugettext_lazy('Blocked (plural)'),
    }

    
    singular_icon_name = {
        'favorite': ugettext_lazy('My favorite'),
        'wink': singular_wink,
        'kiss': ugettext_lazy('Kiss'),
        'key': ugettext_lazy('Key'),
        'chat_friend' : ugettext_lazy('Chat friend'),
        'blocked' : ugettext_lazy('Blocked (singular)'),
    }

    chat_friend_plural_text = {
        'request_sent' : ugettext_lazy('Chat requests sent'),
        'request_received': ugettext_lazy('Chat requests received'),
        'connected': ugettext_lazy('Chat connections confirmed'),
    }
        
    icon_message = {
        'favorite': ugettext_lazy("Add them to your list of favorites"),
        'wink': wink_text,
        'kiss': ugettext_lazy("Send them a kiss"),
        'key': ugettext_lazy("Give them access to your private photos"),
        'chat_friend': ugettext_lazy("Invite them to chat with you"),
        'blocked' : ugettext_lazy("Block this user (delete new messages automatically)"),
    }
    if settings.BUILD_NAME != "language_build":
        wink_icon = "wink.png"
    else:
        wink_icon = "greeting.png"
        
    icon_images = {'favorite': 'star.png', 'wink':wink_icon, 'kiss':'kiss.png', 'key':'key.png', 'chat_friend' : 'chat_bubble.png', 'blocked' : 'stop.png'}




MONTH_NAMES = {
    1: ugettext_lazy('January'),
    2: ugettext_lazy('February'),
    3: ugettext_lazy('March'),
    4: ugettext_lazy('April'),
    5: ugettext_lazy('May'),
    6: ugettext_lazy('June'),
    7: ugettext_lazy('July'),
    8: ugettext_lazy('August'),
    9: ugettext_lazy('September'),
    10: ugettext_lazy('October'),
    11: ugettext_lazy('November'),
    12: ugettext_lazy('December'),
}


        
###################################################
## START Administrator/Site Email Addresses

domain_name = domain_name_dict[settings.BUILD_NAME]
appspot_match = re.match(r'(.*).appspot.com', domain_name)
if appspot_match:
    domain_name = "%s.appspotmail.com" % appspot_match.group(1)
    logging.info("Changing mailing doman name to %s" % domain_name)

if settings.BUILD_NAME == "discrete_build":
    # Special case for the "discrete" site, because we don't want to explicitly say the name of the site in the address field
    support_email_address = "support@%s" % domain_name
    sender_address = u"RS - Customer Support <%s>" % support_email_address
    sender_address_html = u"RS - Customer Support &lt;%s&gt;" % support_email_address
    
elif settings.BUILD_NAME == "language_build":
    support_email_address = 'ilikelanguages@lexabit.com'
    sender_address = u"I Like Languages - Customer Support <%s>" % support_email_address
    sender_address_html = u"I Like Languages - Customer Support &lt;%s&gt;"  % support_email_address
    
else:
    support_email_address = "support@%s" % domain_name
    sender_address = u"%s - Customer Support <%s>" % (app_name_dict[settings.BUILD_NAME], support_email_address)
    sender_address_html = u"%s - Customer Support &lt;%s&gt;" % (app_name_dict[settings.BUILD_NAME], support_email_address)
    
admin_address = sender_address


## END Administrator/Site Email Addresses
###################################################
        
        
template_common_fields = {'build_name': site_configuration.BUILD_NAME,
                          'use_compressed_static_files': site_configuration.USE_COMPRESSED_STATIC_FILES,
                          'build_name_used_for_menubar' : site_configuration.BUILD_NAME_USED_FOR_MENUBAR,
                          'proprietary_styles_dir' : site_configuration.PROPRIETARY_STYLES_DIR,
                          'PROPRIETARY_BUILDS_AVAILABLE' : site_configuration.PROPRIETARY_BUILDS_AVAILABLE,
                          'app_name' : site_configuration.APP_NAME,
                          'domain_name' : site_configuration.DOMAIN_NAME,
                          'support_email_address' : support_email_address,
                          'site_type' : SITE_TYPE,
                          'company_name' : COMPANY_NAME,
                          'company_www' : COMPANY_WWW,                          
                          'guest_num_new_people_messages_allowed_in_window': GUEST_NUM_NEW_PEOPLE_MESSAGES_ALLOWED_IN_WINDOW,
                          'guest_window_days' : GUEST_WINDOW_DAYS_FOR_NEW_PEOPLE_MESSAGES,
                          'vip_num_new_people_messages_allowed_in_window' : VIP_NUM_NEW_PEOPLE_MESSAGES_ALLOWED_IN_WINDOW,
                          'vip_window_hours' : VIP_WINDOW_HOURS_FOR_NEW_PEOPLE_MESSAGES,
                          'NUM_HOURS_WINDOW_TO_RESET_MESSAGE_COUNT_TO_OTHER_USER' : NUM_HOURS_WINDOW_TO_RESET_MESSAGE_COUNT_TO_OTHER_USER,
                          'STANDARD_NUM_MESSAGES_TO_OTHER_USER_IN_TIME_WINDOW': STANDARD_NUM_MESSAGES_TO_OTHER_USER_IN_TIME_WINDOW,
                          'CHAT_FRIEND_NUM_MESSAGES_TO_OTHER_USER_IN_TIME_WINDOW' : VIP_AND_CHAT_FRIEND_NUM_MESSAGES_TO_OTHER_USER_IN_TIME_WINDOW,
                          'NUMER_OF_DAYS_PROFILE_VIEWS_STORED' : NUMER_OF_DAYS_PROFILE_VIEWS_STORED,
                          'num_chat_friends_for_free_clients' :  GUEST_NUM_CHAT_FRIEND_REQUESTS_ALLOWED,
                          'num_chat_friends_for_vip_clients' : MAX_CHAT_FRIEND_REQUESTS_ALLOWED,  
                          'google_ad_160x600' : GOOGLE_AD_160x600,
                          'google_ad_728x90' : GOOGLE_AD_728x90,
                          'analytics_id' : site_configuration.ANALYTICS_ID,
                          'SHOW_ONLINE_STATUS_TRIAL_TIMEOUT_MINUTES' : SHOW_ONLINE_STATUS_TRIAL_TIMEOUT_MINUTES,
                          'BLOCK_ONLINE_STATUS_TRIAL_RESET_HOURS' : BLOCK_ONLINE_STATUS_TRIAL_RESET_HOURS,
                          'SHOW_VIP_UPGRADE_OPTION' : SHOW_VIP_UPGRADE_OPTION,
                          'ADULT_ORIENTED_SITE' : ADULT_ORIENTED_SITE, 
                          'SITE_IS_TOTALLY_FREE' : SITE_IS_TOTALLY_FREE, 
                          'MANUALLY_VERSIONED_IMAGES_DIR' : site_configuration.MANUALLY_VERSIONED_IMAGES_DIR,
                          'ENABLE_GRUNT' : site_configuration.ENABLE_GRUNT,
                          }        