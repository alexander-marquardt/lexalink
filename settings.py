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


# Initialize App Engine and import the default settings (DB backend, etc.).
# If you want to use a different backend you have to remove all occurences
# of "djangoappengine" from this file.
from djangoappengine.settings_base import *
from site_configuration import *


# Activate django-dbindexer for the default database
DATABASES['native'] = DATABASES['default']
DATABASES['default'] = {'ENGINE': 'dbindexer', 'TARGET': 'native'}
AUTOLOAD_SITECONF = 'indexes'

TIME_ZONE = 'UTC'

# language_build code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
if BUILD_NAME == "language_build":
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

LANGUAGE_COOKIE_NAME = 'language_build'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True


INSTALLED_APPS = (
    #'django.contrib.admin',
    'localeurl',
    'django.contrib.contenttypes',
    #'django.contrib.auth',
    #'django.contrib.sessions',
    'djangotoolbox',
    'autoload',
    'dbindexer',

    # djangoappengine should come last, so it can override a few manage.py commands
    'djangoappengine',
)

MIDDLEWARE_CLASSES = (
    'google.appengine.ext.ndb.django_middleware.NdbDjangoMiddleware', 

    # This loads the index definitions, so it has to come first
    'autoload.middleware.AutoloadMiddleware',    
    # keep LocaleURLMiddleware before CommonMiddleware, or APPEND_SLASH will not work
    'localeurl.middleware.LocaleURLMiddleware',
    'django.middleware.common.CommonMiddleware',
    'gaesessions.DjangoSessionMiddleware',    
    #'django.contrib.sessions.middleware.SessionMiddleware',
    #'django.contrib.auth.middleware.AuthenticationMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    #'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.request',
    #'django.core.context_processors.media',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',    
)

# This test runner captures stdout and associates tracebacks with their
# corresponding output. Helps a lot with print-debugging.
TEST_RUNNER = 'djangotoolbox.test.CapturingTestSuiteRunner'

#ADMIN_MEDIA_PREFIX = '/media/admin/'

ROOT_PATH = os.path.dirname(__file__)

if PROPRIETARY_BUILDS_AVAILABLE:
    TEMPLATE_DIRS = (
        os.path.join(ROOT_PATH, STATIC_DIR + r'/html'),
        os.path.join(ROOT_PATH, STATIC_DIR + r'/xml'),
        os.path.join(ROOT_PATH, PROPRIETARY_STATIC_DIR + r'/html'),
    )
else:
    TEMPLATE_DIRS = (
        os.path.join(ROOT_PATH, STATIC_DIR + r'/html'),
        os.path.join(ROOT_PATH, STATIC_DIR + r'/xml'),
    )
    
ROOT_URLCONF = 'urls'


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
    re.compile(r'^/rs/process_login/'),
    re.compile(r'^/rs/process_registration/'),
    re.compile(r'^/rs/store_'),
    re.compile(r'^/rs/blobstore_photo_upload/'),
    re.compile(r'^/rs/sitemap/'),
    re.compile(r'^/setlang/'),
    re.compile(r'^/rs/do_delete/'),
    re.compile(r'^/rs/crawler_auth/'),
    re.compile(r'^/sitemap'),
    re.compile(r'^/bing_site_auth/'),
    re.compile(r'^/paypal/ipn/'),
    re.compile(r'^/paysafecard/'),
    re.compile(r'^/rs/apply_unused_vip_credits/'),
    re.compile(r'^/rs/set_show_online_status_trial/'),
    re.compile(r'^/robots.txt'), 
    re.compile(r'^/_ah/'), 
)



