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
import settings, constants

# NOTE: for lazy translations, it seems that variables cannot be passed in. For this reason, any comments that need
# a variable (such as the name of the current build) will be instantiated using ugettext directly in the code 
# where they are required.

# contains default text that we may wish to display in various text fields
share_thinking = ugettext_lazy(u"""Share what you are thinking by clicking on "edit" to the left.""") 

welcome_text = ugettext_lazy(u"""You are now registered! You can immediately start to view other profiles by using the 
gray search box just above this message.""")
    
cookies_not_enabled_text = ugettext_lazy(u"""(If you have entered with a registered account and you are still seeing
this message, please ensure that you have "cookies" enabled in your browser.)""")

no_photo = ugettext_lazy("No photo")


user_has_no_photo_text = ugettext_lazy(u"""It is recommendable that you <strong>upload a photo now</strong>. Without
photos in your profile, many people will ignore your messages.""")

# overwritten in english translation file
email_is_not_entered_text = ugettext_lazy(u"""You have <strong>not yet entered your email address</strong>.""") 
email_encouragement_text = ugettext_lazy("""Click on "edit" to enter your email address.""")
   
photo_encouragement_text = ugettext_lazy("<strong>You still haven't selected a principal photo (not private) for your profile.<strong>\n")
photo_is_private_text = ugettext_lazy("This photo is private")

change_password_text = ugettext_lazy('Click on "edit" to change your password.')
success_change_password_text = ugettext_lazy("You have changed your password!")
failed_change_password_text = ugettext_lazy("You have not changed your password, try again.")


loosening_search_criteria = ugettext_lazy("""There are no more people that match your search 
criteria, we are re-doing the search with the following settings:""")
people_that_live_in = ugettext_lazy("People that live in")


has_private_and_public_photos = ugettext_lazy("""Has public and private photos! View their profile to see them!""")
has_public_photos = ugettext_lazy("""Has public photos! Click on their profile to see them!""")
has_private_photos = ugettext_lazy("""Has private photos! You need to ask for their \"key\" to see them!""")
has_no_photos = ugettext_lazy("""Doesn't have any photos""")

conversation_between = ugettext_lazy("Conversation between")
and_you = ugettext_lazy("and you")
see_or_respond_to_conversation = ugettext_lazy('Open')
sent = ugettext_lazy("Sent")
received = ugettext_lazy("Received")
#there_is_no_history = ugettext_lazy("There is no message history. Write a message in the textbox below!")
profile_reported = ugettext_lazy("You have reported this profile")
profile_unreported = ugettext_lazy("You have un-reported this profile")

