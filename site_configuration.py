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

import os, datetime

from rs.private_data import *

VERSION_ID = '2013-02-07-1615'
# The following must be set to True before uploading - can be set to False for debugging js/css as modifications are made
USE_TIME_STAMPED_STATIC_FILES = True

# We use the JAVASCRIPT_VERSION_ID to force a hard reload of the javascript on the client if we make a change
# to the javascript code. We do this by checking if the javascript that the user is running matches the 
# version id of the javascript that we are currently serving for the server. Change this number if you
# want to force the client to re-load all javascript. (this is really only relevant when we are running the ajax
# version of this code, in which page reloads are done via ajax calls, as opposed to fully reloading the page
# each time the user navigates to a new page)
JAVASCRIPT_VERSION_ID = VERSION_ID # for now, force a reload everytime we update the website code. 

ENABLE_APPSTATS = False # this enables tracking/profiling code - has some overhead so set to False if it is not actively being used

# Other debugging/build-related flags
TESTING_PAYPAL_SANDBOX = False
BUILD_STAGING = False # forces upload to staging server as opposed to the real server

# The following variable reates to the flash/video conference code, which is almost done, but not activated and
# without any current plans for additional coding hours to get it to release quality. 
FLASH_FILES_DIR = "bin-release" # Generally the flash bin-debug version is the most up-to-date, but for release, we should use bin_release.
                              # Note: this requires that we explicitly re-build the bin-release flash version.
                              

# this is used by the batch uploader to automatically change the name of the build that we will configure and upload. 
# If this is set to a value, then this value will indicate the current site. 
BATCH_BUILD_NAME = ''

if BATCH_BUILD_NAME == '':
    # Since we are currently running 7 sites using the same code base, we just un-comment whichever build 
    # we are interested in executing. Be sure to re-boot the development server each time you change
    # the build name.
    
    BUILD_NAME = 'Single'   # originally used for SingletonSearch.com
    BUILD_NAME = 'Language'  # originally used for LikeLanguage.com
    BUILD_NAME = 'Discrete'     # originally used for RomanceSecreto.com
    BUILD_NAME = 'Swinger'   # originally used for SwingerPlex.com
    #BUILD_NAME = 'Lesbian'   # originally used for LesbianHeart.com
    #BUILD_NAME = 'Gay'       # originally used for GaySetup.com
    #BUILD_NAME = 'Friend'    # originally used for FriendBazaar.com

else:
    BUILD_NAME = BATCH_BUILD_NAME


APP_NAME = app_name_dict[BUILD_NAME]
DOMAIN_NAME = domain_name_dict[BUILD_NAME]
ANALYTICS_ID = analytics_id_dict[BUILD_NAME]

# In order to avoid browser (and possibly) server side caching of static files when we update new versions,
# we define a new static directory which will contain all of the static files for the project. This is simply
# a VERSION_ID-stamped copy of the static directory.
# For development, it may sometimes be desirable to directly use the source static dir as opposed to a copy of 
# the static dir, so that we don't have to re-start the server every time a change to a static file is made. In
# these cases, we will un-comment the *second* LIVE_STATIC_DIR declaration below.
if USE_TIME_STAMPED_STATIC_FILES:
    LIVE_STATIC_DIR = "rs/static/auto-generated-" + VERSION_ID
    
    # use the same diretory for the "proprietary" files, since they will have been copied into the same
    # directory by the build scripts.
    LIVE_PROPRIETARY_STATIC_DIR = "rs/static/auto-generated-" + VERSION_ID
else:
    # This will cause the code to directly access the static files, as opposed to accessing a VERSION_ID-stamped copy
    LIVE_STATIC_DIR = "rs/static"
    LIVE_PROPRIETARY_STATIC_DIR = "rs/proprietary/static"

if BUILD_STAGING:
    # we are uploading the code for the "Discrete" website to a staging appid - this is used for debugging the code
    # in the actual AppEngine (in-the-cloud) environment without uploading it to the live server. 
    app_id_dict['Discrete'] = staging_appid, 
    
if TESTING_PAYPAL_SANDBOX:
    VERSION_ID = 'pp'


# Use the following for maintenance - if no shutdown is scheduled, set shutdown_time to False or DURATION to 0
shutdown_time = datetime.datetime(2012, 06, 05, 8, 30) 
if BUILD_NAME == 'Friend':
    SHUTDOWN_DURATION = 0 # minutes
else:
    SHUTDOWN_DURATION = 0
    
# For some reason that I have not yet investigated, settings.py is called multiple times, and the environment changes 
# between calls, so that in some cases "SERVER_SOFTWARE" is available, and in other cases 'LOGNAME' is available.
# Both of these are indicators that I am running locally, and therefore I set up for local development. 
    
IS_CYGWIN = False

if ('SERVER_SOFTWARE' in os.environ and os.environ['SERVER_SOFTWARE'] == 'Development/1.0' or \
    'LOGNAME' in os.environ and os.environ['LOGNAME'] == LOGNAME):
    # we are running on the local/test server
    LOCAL = True
    DEBUG = True 
elif 'HOSTNAME' in os.environ and os.environ['HOSTNAME'] == CYGWIN_HOSTNAME:
    # cygwin/windows
    LOCAL = True
    DEBUG = True 
    IS_CYGWIN = True
else:
    # probably running on production server - disable all debugging and LOCAL outputs etc.
    LOCAL = False
    DEBUG = False
    
if DEBUG:
    TEMPLATE_DEBUG = True
    TEMPLATE_STRING_IF_INVALID = '************* ERROR in template: %s ******************'


