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

import os, datetime, logging

from rs.private_data import *

VERSION_ID = 'debug-build-1'


# Enable the Grunt before uploading code to the cloud (or your clients will experience slower page loads). 
# Enabling Grunt requires a local copy of node as well as a local opy of npm (node package manager). 
# In order to initially configure the grunt build system (after installing node and npm), 
# you need to cd to the "client" directory and run "npm install".
# This will install all of the node packages that are required for compressing, minimizing, combining, etc. 
# of the html, css, and javascript.
# Additionally, during development (when not using grunt to compress files), our grunt scripts provide functionality such
# as automatically running jshint when a file changes, automatic reloading of web pages when html changes, etc. 
ENABLE_GRUNT = True

# The following must be set to True before uploading - this will combine and minimize javascript 
# and css files. This combining/minimizing is only done on upload or on  development server initialization, so this will
# mask any changes that are made to jss/css between server restarts -- therefore this value 
# should be set to False for developing/debugging js/css on the local development server (the original
# js/css files would be accessed instead of the combined/minimized js/css files).
USE_COMPRESSED_STATIC_FILES = False

if USE_COMPRESSED_STATIC_FILES and not ENABLE_GRUNT:
    # Compression of static and client-side files is done using grunt, therefore ENABLE_GRUNT must be set before USE_COMPRESSED_STATIC_FILES
    # can be set.
    logging.error("You cannot set USE_COMPRESSED_STATIC_FILES in site_configuration.py without enabling Grunt (ENABLE_GRUNT)")
    exit(1)

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
TESTING_PAYSAFECARD = True

BUILD_STAGING = False # forces upload to staging server as opposed to the real server


# this is used by the batch uploader to automatically change the name of the build that we will configure and upload. 
# If this is set to a value, then this value will indicate the current site. 
BATCH_BUILD_NAME = ''

if os.path.isdir('rs/proprietary'):
    # if the rs/proprietary directory exists, then propriatary builds are enabled (ie. this is my personal build setup which contains
    # private images, keys, passwords, etc.). If this proprietary information is not available, then we just build the "single" build
    # and we will use generic images etc. It is expected that anyone using this code will then either modify the default build information
    # to customize their website, or that they will alternatively setup a proprietary directory with their own customizations
    # that will allow them to generate multiple websites. 
    PROPRIETARY_BUILDS_AVAILABLE = True
else:
    PROPRIETARY_BUILDS_AVAILABLE = False
    
    
if PROPRIETARY_BUILDS_AVAILABLE:
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
    BUILD_NAME = 'default_build'

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
    # use the same diretory for the "proprietary" files, since they will have been copied into the same
    # directory by the build scripts.
    STATIC_DIR = "client/dist"
    PROPRIETARY_STATIC_DIR = "client/dist/proprietary"
else:
    # This will cause the code to directly access the static files, as opposed to accessing concatenated/minified/uglified copies
    STATIC_DIR = "client/app"
    PROPRIETARY_STATIC_DIR = "client/app/proprietary"

if not PROPRIETARY_BUILDS_AVAILABLE: 
    # If proprietary files are not available, then search in the "open" static directory to see if they are available there.
    PROPRIETARY_STATIC_DIR = STATIC_DIR
    
    
if PROPRIETARY_BUILDS_AVAILABLE:
    # when we import css files from the syles directory,  we need to pre-process the html
    # to be sure that it pulls the CSS from the correct location. If we are not using proprietary builds,
    # then we pull the CSS out of the standard styles directory as opposed to the proprietary/styles 
    # directory. This will be written to to a file that is pre-processed by the grunt/node build system.
    PROPRIETARY_STYLES_DIR = "/proprietary/styles"
else:
    PROPRIETARY_STYLES_DIR = "/styles"


# Some images are accessed from python code, and therefore the grunt build scripts are not allowed to give them new hash identifier names when they change.
# Therefore, we manually force a new path every time we upload the code so that the images will not be cached. This is a more brute force
# than is desirable, and should be fixed at some point in the future.
MANUALLY_VERSIONED_IMAGES_DIR = "/images/manually_versioned_images/" + VERSION_ID 

if BUILD_STAGING:
    # we are uploading the code for the "discrete_build" website to a staging appid - this is used for debugging the code
    # in the actual AppEngine (in-the-cloud) environment . 
    app_id_dict[BUILD_NAME] = staging_appid, 
    
if TESTING_PAYPAL_SANDBOX:
    VERSION_ID = 'pp'
if TESTING_PAYSAFECARD:
    VERSION_ID = 'paysafecard'


# Use the following for maintenance - if no shutdown is scheduled, set shutdown_time to False or DURATION to 0
shutdown_time = datetime.datetime(2012, 06, 05, 8, 30) 
if BUILD_NAME == 'friend_build':
    SHUTDOWN_DURATION = 0 # minutes
else:
    SHUTDOWN_DURATION = 0

if PROPRIETARY_BUILDS_AVAILABLE:
    if BUILD_NAME == 'discrete_build' or BUILD_NAME == 'lesbian_build' or BUILD_NAME == 'swinger_build' or BUILD_NAME == 'single_build':
        BUILD_NAME_USED_FOR_MENUBAR = 'discrete_build'
    elif BUILD_NAME == 'language_build' or BUILD_NAME == 'mature_build':
        BUILD_NAME_USED_FOR_MENUBAR = 'language_build'
    else:
        BUILD_NAME_USED_FOR_MENUBAR = BUILD_NAME
else:
    BUILD_NAME_USED_FOR_MENUBAR = 'default_build'
    


# For some reason that I have not yet investigated, settings.py is called multiple times, and the environment changes
# between calls, so that in some cases "SERVER_SOFTWARE" is available, and in other cases 'LOGNAME' is available.
# Both of these are indicators that I am running locally, and therefore I set up for local development.
if ('SERVER_SOFTWARE' in os.environ):
    if ("Development" in os.environ.get('SERVER_SOFTWARE','')):
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
