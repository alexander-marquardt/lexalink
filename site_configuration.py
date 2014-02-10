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

import os, datetime, logging

from rs.private_data import *

VERSION_ID = '2014-01-23-1437'

# The following must be set to True before uploading - this will combine and minimize javascript 
# and css files. This combining/minimizing is only done on upload or on  development server initialization, so this will
# mask any changes that are made to jss/css between server restarts -- therefore this value 
# should be set to False for developing/debugging js/css on the local development server (the original
# js/css files would be accessed instead of the combined/minimized js/css files).
USE_COMPRESSED_STATIC_FILES = False

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
TESTING_FORTUMO_PAYMENTS = False
BUILD_STAGING = False # forces upload to staging server as opposed to the real server

# The following variable reates to the flash/video conference code, which is almost done, but not activated and
# without any current plans for additional coding hours to get it to release quality. 
FLASH_FILES_DIR = "bin-release" # Generally the flash bin-debug version is the most up-to-date, but for release, we should use bin_release.
                              # Note: this requires that we explicitly re-build the bin-release flash version.
                              

# this is used by the batch uploader to automatically change the name of the build that we will configure and upload. 
# If this is set to a value, then this value will indicate the current site. 
BATCH_BUILD_NAME = ''

if os.path.isdir('rs/proprietary'):
    if BATCH_BUILD_NAME == '':
        # Since we are currently running 7 sites using the same code base, we just un-comment whichever build 
        # we are interested in executing. Be sure to re-boot the development server each time you change
        # the build name.
        
        BUILD_NAME = 'discrete_build'     # originally used for RomanceSecreto.com
        #BUILD_NAME = 'single_build'   # originally used for SingletonSearch.com
        #BUILD_NAME = 'lesbian_build'   # originally used for LesbianHeart.com
        #BUILD_NAME = 'language_build'  # originally used for LikeLanguage.com
        #BUILD_NAME = 'swinger_build'   # originally used for SwingerSetup.com
        #BUILD_NAME = 'gay_build'       # originally used for GaySetup.com
        #BUILD_NAME = 'friend_build'    # originally used for FriendBazaar.com
        #BUILD_NAME = 'mature_build' # originallly used for MellowDating.com
    
    else:
        BUILD_NAME = BATCH_BUILD_NAME
else:
    # We have not defined any of the proprietary builds, so just default to the standard "single" dating platform configuration
    BUILD_NAME = 'single_build'

APP_NAME = app_name_dict[BUILD_NAME]
DOMAIN_NAME = domain_name_dict[BUILD_NAME]
ANALYTICS_ID = analytics_id_dict[BUILD_NAME]

# In order to avoid browser (and possibly) server side caching of static files when we update new versions,
# we distribute css/js files which contain a unique hash identifier appended to the name. This is 
# done by the node.js/grunt build system, which is externally called. 
# For development, it may sometimes be desirable to directly use the source static dir as opposed to a copy of 
# the static dir, so that we don't have to re-start the server every time a change to a static file is made. In
# these cases, we will un-comment the *second* LIVE_STATIC_DIR declaration below.
if USE_COMPRESSED_STATIC_FILES:
    LIVE_STATIC_DIR = "client/dist"
    
    # use the same diretory for the "proprietary" files, since they will have been copied into the same
    # directory by the build scripts.
    LIVE_PROPRIETARY_STATIC_DIR = "client/dist/proprietary"
else:
    # This will cause the code to directly access the static files, as opposed to accessing concatenated/minified/uglified copies
    LIVE_STATIC_DIR = "client/app"
    LIVE_PROPRIETARY_STATIC_DIR = "client/app/proprietary"

if BUILD_STAGING:
    # we are uploading the code for the "discrete_build" website to a staging appid - this is used for debugging the code
    # in the actual AppEngine (in-the-cloud) environment . 
    app_id_dict[BUILD_NAME] = staging_appid, 
    
if TESTING_PAYPAL_SANDBOX:
    VERSION_ID = 'pp'
if TESTING_FORTUMO_PAYMENTS:
    VERSION_ID = 'fortumo-test'


# Use the following for maintenance - if no shutdown is scheduled, set shutdown_time to False or DURATION to 0
shutdown_time = datetime.datetime(2012, 06, 05, 8, 30) 
if BUILD_NAME == 'friend_build':
    SHUTDOWN_DURATION = 0 # minutes
else:
    SHUTDOWN_DURATION = 0

if BUILD_NAME == 'discrete_build' or BUILD_NAME == 'lesbian_build' or BUILD_NAME == 'swinger_build' or BUILD_NAME == 'single_build':
    BUILD_NAME_USED_FOR_MENUBAR = 'discrete_build'
elif BUILD_NAME == 'language_build' or BUILD_NAME == 'mature_build':
    BUILD_NAME_USED_FOR_MENUBAR = 'language_build'
else:
    BUILD_NAME_USED_FOR_MENUBAR = BUILD_NAME
    
    
# For some reason that I have not yet investigated, settings.py is called multiple times, and the environment changes 
# between calls, so that in some cases "SERVER_SOFTWARE" is available, and in other cases 'LOGNAME' is available.
# Both of these are indicators that I am running locally, and therefore I set up for local development. 
    
IS_CYGWIN = False

if 'HOSTNAME' in os.environ and os.environ['HOSTNAME'] == CYGWIN_HOSTNAME:
    # cygwin/windows
    logging.info("Running on Cygwin - DEBUG disabled")    
    DEBUG = False 
    IS_CYGWIN = True
    TEMPLATE_DEBUG = False
    DEVELOPMENT_SERVER = True
    
    
elif ("alexandermarquardt" in os.environ.get('PWD','')):
    # we are running on the local/test server
    logging.info("Running on local server %s" % os.environ.get('SERVER_SOFTWARE',''))
    DEBUG = False  # Disable django debug messages - is easier to look at the log messages
    TEMPLATE_DEBUG = True
    TEMPLATE_STRING_IF_INVALID = '************* ERROR in template: %s ******************'    
    DEVELOPMENT_SERVER = True

else:
    # probably running on production server - disable all debugging and LOCAL outputs etc.
    logging.info("Appears to be running on production server" )
    DEBUG = False
    TEMPLATE_DEBUG = False
    DEVELOPMENT_SERVER = False

