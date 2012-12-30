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


import urllib, settings
from google.appengine.api import urlfetch

"""
    Adapted from http://pypi.python.org/pypi/recaptcha-client
    to use with Google App Engine
    by Joscha Feth <joscha@feth.com>
    Version 0.1
"""

"""
The following values are obtained from the recaptcha site
"""

API_SSL_SERVER  = "https://api-secure.recaptcha.net"
API_SERVER      = "http://api.recaptcha.net"
API_SERVER      = "http://www.google.com/recaptcha/api/js/recaptcha_ajax.js"
VERIFY_SERVER   = "api-verify.recaptcha.net"
PUBLIC_KEY      = settings.RECAPTCHA_PUBLIC_KEY
PRIVATE_KEY     = settings.RECAPTCHA_PRIVATE_KEY

class RecaptchaResponse(object):
    def __init__(self, is_valid, error_code=None):
        self.is_valid   = is_valid
        self.error_code = error_code

        
        
def displayhtml (use_ssl = False,
                 error = None):
    """Gets the HTML to display for reCAPTCHA

    use_ssl -- Should the request be sent over ssl?
    error -- An error message to display (from RecaptchaResponse.error_code)"""


    error_param = ''
    if error:
        error_param = '&error=%s' % error

    if use_ssl:
        server = API_SSL_SERVER
    else:
        server = API_SERVER

    return """
    <div id="id-recaptcha"></div>   
    
    <script type="text/javascript">

    var showRecaptcha = function() {
        $.getScript("%(ApiServer)s", function() {
            Recaptcha.create("%(PublicKey)s", "id-recaptcha", {
                 theme : 'white',
                 tabindex : 2,
                 lang : 'es',
                 callback: Recaptcha.focus_response_field
            });    
        });
    } ();
    </script>
    
    <noscript>
      <iframe src="%(ApiServer)s/noscript?k=%(PublicKey)s%(ErrorParam)s" height="300" width="500" frameborder="0"></iframe><br />
      <textarea name="recaptcha_challenge_field" rows="3" cols="40"></textarea>
      <input type='hidden' name='recaptcha_response_field' value='manual_challenge' />
    </noscript>

""" % {
        'ApiServer' : server,
        'PublicKey' : PUBLIC_KEY,
        'ErrorParam' : error_param,
        }


def submit (recaptcha_challenge_field,
            recaptcha_response_field,
            remoteip):
    """
    Submits a reCAPTCHA request for verification. Returns RecaptchaResponse
    for the request

    recaptcha_challenge_field -- The value of recaptcha_challenge_field from the form
    recaptcha_response_field -- The value of recaptcha_response_field from the form
    remoteip -- the user's ip address
    """
    

    if not (recaptcha_response_field and recaptcha_challenge_field and
            len (recaptcha_response_field) and len (recaptcha_challenge_field)):
        return RecaptchaResponse (is_valid = False, error_code = 'incorrect-captcha-sol')
    
    headers = {
               'Content-type':  'application/x-www-form-urlencoded',
               "User-agent"  :  "reCAPTCHA GAE Python"
               }         
    
    try:
        params = urllib.urlencode ({
                'privatekey': PRIVATE_KEY,
            'remoteip' : remoteip,
                'challenge': recaptcha_challenge_field,
                'response' : recaptcha_response_field,
                })
    except UnicodeEncodeError:
        return RecaptchaResponse (is_valid=False, error_code = "unicode-not-supported")
    
    httpresp = urlfetch.fetch(
                   url      = "http://%s/verify" % VERIFY_SERVER,
                   payload  = params,
                   method   = urlfetch.POST,
                   headers  = headers
                    )     
    
    if httpresp.status_code == 200:
        # response was fine
        
        # get the return values
        return_values = httpresp.content.splitlines();
        
        # get the return code (true/false)
        return_code = return_values[0]
        
        if return_code == "true":
            # yep, filled perfectly
            return RecaptchaResponse (is_valid=True)
        else:
            # nope, something went wrong
            return RecaptchaResponse (is_valid=False, error_code = return_values [1])
    else:
        # recaptcha server was not reachable
        return RecaptchaResponse (is_valid=False, error_code = "recaptcha-not-reachable")