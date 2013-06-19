################################################################################
# LexaLink Copyright information - do not remove this copyright notice
# Copyright (C) 2012 
#
# Lexalink - a free social network and dating platform for the Google App Engine. 
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

import re
# Defines data that is imported in settings.py and constants.py. This data is then accessed from many parts of the code base.

try:
    # in order to prevent myself from accidentaly uploading sensitive data to the Git repository, I have stored 
    # all sensitive data in a seperate file called my_private_data.py, which is ignored by git and which should never
    # be uploaded to the public server. You should never see the file my_private_data.py in the repository.
    # 
    # If you are concerned about privacy, you can create a file called my_private_data.py, and copy the data fields 
    # in the "except" portion of this file below, and update them with appropriate values. 
    

    from rs.proprietary.my_private_data import *
    
except:
    # If my_private_data.py doesn't exist, then the following default values will be used. 
    
    LOGNAME = 'Enter your LOGNAME here' # compared against os.environ['LOGNAME'] to detect if you are running on a local machine 
    CYGWIN_HOSTNAME = 'ALEXANDERMA431D' # compared against os.environ['HOSTNAME'] to detect if you are running on cygwin
    SECRET_KEY = 'enter your secret cookie key here' # used to encode and decode session cookies (see gaesessions)
    
    app_name_dict = {
        # Edit the following values to reflect the names that you have chosen for each of your sites.
        'discrete_build' : 'Your-Site-Name-Here', #ie. "RomanceSecreto"
        'language_build':  'Your-Site-Name-Here', 
        'single_build' :   'lexalink-demo.appspot',
        'lesbian_build':   'Your-Site-Name-Here',
        'gay_build':       'Your-Site-Name-Here',
        'swinger_build':   'Your-Site-Name-Here',
        'friend_build':    'Your-Site-Name-Here',
        'mature_build':    'Your-Site-Name-Here',
    }
    
    domain_name_dict = {
        # Update the following values to reflect the domain of each of your sites (do *not* put www in front, since 
        # this is also used in the email addresses). Generally, this should be the same as the value in the app_name_dict
        # but lower case, and followed by the appropriate top level domain qualifier.
        'discrete_build' : 'your-site-name-here.com', #ie "romancesecreto.com"
        'language_build':  'your-site-name-here.com', 
        'single_build' :   'lexalink-demo.appspot.com',
        'lesbian_build':   'your-site-name-here.com',
        'gay_build':       'your-site-name-here.com',
        'swinger_build':   'your-site-name-here.com',
        'friend_build':    'your-site-name-here.com',    
        'mature_build':    'your-site-name-here.com',    
    }
    
    app_id_dict = {
        # update the following values to reflect the application ids that you have registered for each of your
        # applications on the AppEngine.
        'discrete_build' : 'yourappid1', 
        'language_build':  'yourappid2', 
        'single_build' :   'lexalink-demo',
        'lesbian_build':   'yourappid4',
        'gay_build':       'yourappid5',
        'swinger_build':   'yourappid6',
        'friend_build':    'yourappid7',
        'mature_build':    'yourappid8',
    }
    
    # you may wish to have an additional application id that you upload your code to for extra "in-the-cloud" testing.
    staging_appid = 'your-staging-application-id'
    
    # Used in constants.py
    ADMIN_USERNAME = "YOURUSERNAME" # This is the name of the user account that sends welcome message to new users
    COMPANY_NAME = "Your Company Name" # Shown in the footer of each page
    COMPANY_WWW = "www.your-company-website.com" # Shown in the footer of each page
    
    # the following 3 variables are used for allowing the google crawler and/or the system adminstrator 
    # to login with the special account that gives access to the page contents that are shown to each 
    # user. This is required for google to correctly target advertising. This has the potential to expose
    # private data to a hacker, so you must be careful to ensure that only the google crawler is able to
    # login using this username/password.
    CRAWLER_USERNAME = "your-google-crawler-login-name"
    CRAWLER_PASSWORD = "your-google-crawler-password"
    CRAWLER_SESSION_NAME = "crawler_session"    
    
    # In order to reduce the risk of a hacker getting access to private data, we check that the IP address
    # that is attempting to log into the crawler account comes from googles servers, or from a the home IP
    # address of the administrator, or from the loopback address.
    GOOGLE_CRAWLER_IP_PATTERN = re.compile(r'66\.249\.[6|7][0-9]\.\d{1,3}')
    MY_HOME_IP_PATTERN = re.compile(r'xx\.xx\.xx\.xxx') # you can enter the IP of your home network
    LOCAL_IP_PATTERN = re.compile(r'127\.0\.0\.1')

    # The site is currently setup to process paypal payments in English and in Spanish. In order to 
    # accept payments, you must register with PayPal and get button IDs that are assocaited with
    # your paypal account, and that will be used when communicating with PayPals servers.
    PAYPAL_EN_BUTTON_ID = 'YOUR-ENGLISH-PAYPAL-BUTTON-ID'
    PAYPAL_ES_BUTTON_ID = 'YOUR-SPANISH-PAYPAL-BUTTON-ID'
    PAYPAL_SANDBOX_BUTTON_ID = 'YOUR-PAYPAL-SANDBOX-BUTTON-ID'
    
    # PROPRIETARY_STATIC_DIR_EXISTS then we will load "customized" CSS and images
    # These will be loaded from the rs/proprietary/static directory. This directory
    # is not distrbuted with the open source code, since it contains proprietary
    # images and designes that will be customized for each implementation.
    PROPRIETARY_STATIC_DIR_EXISTS = False 
    
    GOOGLE_AD_728x90 = 'Place your Adsense code here'
    GOOGLE_AD_160x600 = 'Place your Adsense code here'
    
    
    # Setup the key values for using the recaptcha service. These must be obtained directly
    # from recaptcha by registering for an account. 
    RECAPTCHA_PUBLIC_KEY      = "YOUR PUBLIC KEY GOES HERE"
    RECAPTCHA_PRIVATE_KEY     = "YOUR PRIVATE KEY GOES HERE"    
    
    # only enable this if you have added the file rs/proprietary/search_engine_overrides.py with appropriate
    # function declarations as required by the code that is ignored by this boolean.
    SEO_OVERRIDES_ENABLED = False    
    
    
    # If you want to use google analytics to track your page statistics, you will need an 
    # identifier for each page. 
    analytics_id_dict = {
        "friend_build"   : 'UA-YOUR-IDX-X',
        "discrete_build" : 'UA-YOUR-IDX-X',
        "language_build" : 'UA-YOUR-IDX-X',
        "single_build"   : 'UA-YOUR-IDX-X',
        "lesbian_build"  : 'UA-YOUR-IDX-X',
        "swinger_build"  : 'UA-YOUR-IDX-X',
        "gay_build"      : 'UA-YOUR-IDX-X',
        "mature_build"   : 'UA-YOUR-IDX-X',
    }    
    
    
    REGISTRATION_EXEMPT_EMAIL_ADDRESSES_SET = set([])
    