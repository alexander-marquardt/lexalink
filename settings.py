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

# Original settings.py Copyright 2008 Google Inc.

# Django settings for google-app-engine-django project.

import os, socket, shutil, re, datetime
from rs.private_data import *

VERSION_ID = '2012-10-04-1850'

# We use the JAVASCRIPT_VERSION_ID to force a hard reload of the javascript on the client if we make a change
# to the javascript code. We do this by checking if the javascript that the user is running matches the 
# version id of the javascript that we are currently serving for the server. Change this number if you
# want to force the client to re-load all javascript. (this is really only relevant when we are running the ajax
# version of this code, in which page reloads are done via ajax calls, as opposed to fully reloading the page
# each time the user navigates to a new page)
JAVASCRIPT_VERSION_ID = VERSION_ID # for now, force a reload everytime we update the website code. 


# The following must be set to True before uploading - can be set to False for debugging js/css as modifications are made
USE_TIME_STAMPED_STATIC_FILES = True
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
    #BUILD_NAME = 'Language'  # originally used for LikeLanguage.com
    BUILD_NAME = 'Discrete'     # originally used for RomanceSecreto.com
    #BUILD_NAME = 'Swinger'   # originally used for SwingerPlex.com
    #BUILD_NAME = 'Lesbian'   # originally used for LesbianHeart.com
    #BUILD_NAME = 'Gay'       # originally used for GaySetup.com
    #BUILD_NAME = 'Friend'    # originally used for FriendBazaar.com

else:
    BUILD_NAME = BATCH_BUILD_NAME


APP_NAME = app_name_dict[BUILD_NAME]
DOMAIN_NAME = domain_name_dict[BUILD_NAME]

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





ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'appengine'  # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = ''             # Or path to database file if using sqlite3.
DATABASE_USER = ''             # Not used with sqlite3.
DATABASE_PASSWORD = ''         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'UTC'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
if BUILD_NAME == "Language":
    LANGUAGE_CODE = 'en'
else:
    # dating sites are primarily focussed on Spanish speaking market - we therefore want
    # google to default to viewing the pages in Spanish. Normal browsers will have a language
    # defined and LANGUAGE_CODE will therefore probably be ignored for most "normal" browsing cases. 
    LANGUAGE_CODE = 'es'

LANGUAGES = (
    ('en', u'English'),
    ('es', u'Español'),
)

LANGUAGE_COOKIE_NAME = 'Language'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Ensure that email is not sent via SMTP by default to match the standard App
# Engine SDK behaviour. If you want to sent email via SMTP then add the name of
# your mailserver here.
EMAIL_HOST = ''

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

if ENABLE_APPSTATS:
    APPSTAT_MIDDLEWARE = ('google.appengine.ext.appstats.recording.AppStatsDjangoMiddleware',)
else:
    APPSTAT_MIDDLEWARE = ()

MIDDLEWARE_CLASSES = APPSTAT_MIDDLEWARE +  (
    # keep the following line before CommonMiddleware, or APPEND_SLASH will not work
    'localeurl.middleware.LocaleURLMiddleware',
    
    'django.middleware.common.CommonMiddleware',
    #'django.contrib.sessions.middleware.SessionMiddleware',
    'gaesessions.DjangoSessionMiddleware',
#    'django.middleware.locale.LocaleMiddleware',
#    'django.contrib.auth.middleware.AuthenticationMiddleware',
#    'django.middleware.doc.XViewMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
#   'django.core.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
#    'django.core.context_processors.media',  # 0.97 only.
#    'django.core.context_processors.request',
)

ROOT_URLCONF = 'urls'

ROOT_PATH = os.path.dirname(__file__)
TEMPLATE_DIRS = (
    os.path.join(ROOT_PATH, r'rs/templates'),
    os.path.join(ROOT_PATH, r'rs/proprietary/templates'), 
)

INSTALLED_APPS = (
    'appengine_django',
    'localeurl',
#    'django.contrib.auth',
#    'django.contrib.contenttypes',
#    'django.contrib.sessions',
    'django.contrib.admin',
#    'django.contrib.sites',
    # include the rometo application, in diretory rs
    'rs',
)

#SESSION_ENGINE = ('django.contrib.sessions.backends.cached_db')
#SESSION_ENGINE = ('django.contrib.sessions.backends.db')
#SESSION_ENGINE = ('appengine_django.sessions.backends.db')
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = False


DEBUG_PROPAGATE_EXCEPTIONS = False

# The following declarations are used by the locale middleware - defines paths that will not be
# re-mapped to contain the locale code in the URL
LOCALE_INDEPENDENT_PATHS = (
    re.compile(r'^/jx/'),        
    re.compile(r'^/rs/ajax/'),    
    re.compile(r'^/rs/channel_support/'),
    re.compile(r'^/rs/admin/'),
    re.compile(r'^/rs/store_'),
    re.compile(r'^/rs/blobstore_photo_upload/'),
    re.compile(r'^/rs/sitemap/'),
    re.compile(r'^/setlang/'),
    re.compile(r'^/rs/do_delete/'),
    re.compile(r'^/rs/crawler_auth/'),
    re.compile(r'^/sitemap'),
    re.compile(r'^/bing_site_auth/'),
    re.compile(r'^/paypal/ipn/'),
    re.compile(r'^/rs/apply_unused_vip_credits/'),
    re.compile(r'^/videochat_server/'),
    re.compile(r'^/videochat_window/'),
)



