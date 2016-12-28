################################################################################
# LexaLink Copyright information - do not remove this copyright notice
# Copyright (C) 2012 
#
# Lexalink - a free social network and dating platform for the Google App Engine. 
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

import re
# Defines data that is imported in settings.py and constants.py. This data is then accessed from many parts of the code base.

try:
    # in order to prevent myself from accidentaly uploading sensitive data to the Git repository, I have stored 
    # all sensitive data in a seperate folder named proprietary, in file called my_private_data.py, which is ignored by git and which should never
    # be uploaded to the public server. You should never see the file my_private_data.py in the repository.
    # 
    # If you are concerned about privacy, you can create a file called my_private_data.py, and copy the data fields 
    # in the "except" portion of this file below into my_private_data.py, and update them with appropriate values. 
    

    from rs.proprietary.my_private_data import *
    
except:
    # If my_private_data.py doesn't exist, then the following default values will be used. 
    
    LOGNAME = 'Enter your LOGNAME here' # compared against os.environ['LOGNAME'] to detect if you are running on a local machine 
    CYGWIN_HOSTNAME = 'ALEXANDERMA431D' # compared against os.environ['HOSTNAME'] to detect if you are running on cygwin
    SECRET_KEY = 'enter your secret cookie key here' # used to encode and decode session cookies (see gaesessions)
    
    app_name_dict = {
        # Edit the following values to reflect the names that you have chosen for each of your sites.
        'default_build':    'Your-Site-Name-Here',

        'discrete_build' : 'Your-Site-Name-Here', #ie. "RomanceSecreto"
        'language_build':  'Your-Site-Name-Here', 
        'single_build' :   'lexalink-demo.appspot',
        'lesbian_build':   'Your-Site-Name-Here',
        'gay_build':       'Your-Site-Name-Here',
        'swinger_build':   'Your-Site-Name-Here',
        'mature_build':    'Your-Site-Name-Here',
        
    }
    
    domain_name_dict = {
        # Update the following values to reflect the domain of each of your sites (do *not* put www in front, since 
        # this is also used in the email addresses). Generally, this should be the same as the value in the app_name_dict
        # but lower case, and followed by the appropriate top level domain qualifier.
        'default_build':    'your-site-name-here.com',    

        'discrete_build' : 'your-site-name-here.com', #ie "romancesecreto.com"
        'language_build':  'your-site-name-here.com', 
        'single_build' :   'lexalink-demo.appspot.com',
        'lesbian_build':   'your-site-name-here.com',
        'gay_build':       'your-site-name-here.com',
        'swinger_build':   'your-site-name-here.com',
        'mature_build':    'your-site-name-here.com',
        
    }
    
    app_id_dict = {
        # update the following values to reflect the application ids that you have registered for each of your
        # applications on the AppEngine.
        'default_build':   'lexalink-demo',

        'discrete_build' : 'lexalink-demo',
        'language_build':  'yourappid2', 
        'single_build' :   'lexalink-demo',
        'lesbian_build':   'yourappid4',
        'gay_build':       'yourappid5',
        'swinger_build':   'yourappid6',
        'mature_build':    'yourappid8',
        
    }


    # very similar to app_id_dict, however in some cases (for unkonwn reasons) there may be more than one app id that
    # is accessing a particlar site. For exmple RomanceSecreto.com is accessed by both romancesapp.appspot.com, as well
    # as romanceapp.appspot.com. For this reason, we use a set to represent the app ids that will need to be redirected
    # to the principle domain name. This probably happens because romancescreto.com used to be hosted on
    # romanceapp.appspot.com before we switched to the high-repliation datastore.
    redirect_app_id_dict = {}

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

    # The site is currently setup to process paypal payments - you must have a paypal account setup
    PAYPAL_ACCOUNT = 'YOUR-EMAIL-ADDRESS-FOR-PAYPAL'
    PAYPAL_SANDBOX_ACCOUNT = 'YOUR-SANDBOX-EMAIL-ADDRESS-FOR-PAYPAL'

    # Not currently used
    # PAYSAFE_HMAC_KEY = 'K34grNKPXEjREGCSGOcQ60IOyFGBtcupMYthH4Hh5jiMuWyaZ'

    PAYSAFE_SOAP_USERNAME = 'xxxxx'
    PAYSAFE_SOAP_PASSWORD = 'xxxxx'
    PAYSAFE_MID_DICT = {'EUR': '1000005878', 'USD': '1000005927', 'MXN': '1000005928'}
    PAYSAFE_CUSTOMER_PANEL_URL = 'xxxxxx'
    PAYSAFE_ENDPOINT = 'xxxxxx'

    PAYSAFE_SOAP_TEST_USERNAME = 'xxxxxx'
    PAYSAFE_SOAP_TEST_PASSWORD = 'xxxxxx'
    PAYSAFE_TEST_MID_DICT = {'EUR': '1000005878', 'USD': '1000005927', 'MXN': '1000005928'}
    PAYSAFE_CUSTOMER_PANEL_TEST_URL = 'xxxxxx'
    PAYSAFE_TEST_ENDPOINT = 'xxxxxx'

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
        "default_build"  : 'UA-YOUR-IDX-X',
        "discrete_build" : 'UA-YOUR-IDX-X',
        "language_build" : 'UA-YOUR-IDX-X',
        "single_build"   : 'UA-YOUR-IDX-X',
        "lesbian_build"  : 'UA-YOUR-IDX-X',
        "swinger_build"  : 'UA-YOUR-IDX-X',
        "gay_build"      : 'UA-YOUR-IDX-X',
        "mature_build"   : 'UA-YOUR-IDX-X',
    }    
    
    # Fortumo - Mobile Payments for Web Apps
    fortumo_web_apps_service_id = 'your fortumo service id goes here'   
    fortumo_web_apps_secret = 'your fortumo secret hash goes here'

    REGISTRATION_EXEMPT_EMAIL_ADDRESSES_SET = set([])
    REGISTRATION_EXEMPT_IP_ADDRESS_SET  = set([])
    DEFAULT_PROFILE_PASSWORD = "whatever"