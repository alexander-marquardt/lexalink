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

import re

from django.utils.translation import check_for_language
from django import http

import error_reporting, logging, utils_top_level, settings

from localeurl import utils as localeurl_utils

PATH_INFO_RE = re.compile(r'^http://.*?(?P<path>/.*)$')

def get_base_path(calling_url):
    
    try:
        re_check = PATH_INFO_RE.match(calling_url)
        if re_check:
            path = re_check.group('path')
            locale, path_info = localeurl_utils.strip_path(path) # get rid of locale from the path if necessary
        else:
            # this condition should not happen - indicates a problem with the code
            error_reporting.log_exception(logging.critical)
            path_info = "/"
        
    except:
        path_info = "/"
        error_message = "error parsing URL: %s" % calling_url
        error_reporting.log_exception(logging.critical, error_message = error_message, request=request)   
    
    return path_info


def set_language_in_session(request, lang_code):
    # set the session on both the request, the session,
    
    session_lang_set = False
    
    if lang_code and check_for_language(lang_code):
        session_lang_set = True
        if hasattr(request, 'session'):
            request.session['django_language'] = lang_code
            
    return session_lang_set


def set_language_and_redirect_back(request, lang_code):
    
    # receives a language code, and re-directs back to the page from which this function was called but
    # with the user settings modified (preferences, cookies) as well as the redirect containing the 
    # lang_code in the URL.
    #
    # Based on set_language located in /Library/Python/2.5/site-packages/django/views/i18n.py
    # Note: they state that because this is changing the configuration of how the user will interact
    # with the website, that this should be sent via a post. However, we send it via a get because
    # it is easier (and for the moment, I don't see any problems caused by using a get)
    

    try:
        
        userobject = utils_top_level.get_userobject_from_request(request)
        # if userobject exists, then update its language settings to reflect then new value
        if userobject:
            search_preferences = userobject.search_preferences2.get()
            if search_preferences.lang_code != lang_code:
                # only write it if it has changed, since db writes are expensive
                search_preferences.lang_code = lang_code
                search_preferences.put()

        calling_url = request.META.get('HTTP_REFERER', None) # get the calling URL  
        if calling_url:
            calling_path = get_base_path(calling_url)
        else:
            # Could potentially happen if someone executes the langage selector URL directly without viewing another 
            # page first. 
            error_message = "Referer URL not found when setting language - re-directing to home" 
            error_reporting.log_exception(logging.warning, error_message = error_message, request=request) 
            calling_path = "/"
            
        locale_path = localeurl_utils.locale_path(calling_path, lang_code)  
        
        if not request.is_ajax():        
            response = http.HttpResponseRedirect(locale_path) # need to define the HttpResponse before we can write the cookie
        else:
            # This is an ajax request, and therefore the re-direction takes place in the client-side
            # javascript code. For ajax, just return a standard "OK" response (which is ignored)
            response = http.HttpResponse("OK")
            
        if set_language_in_session(request, lang_code):
            request.LANGUAGE_CODE = lang_code
            # Also set language in the cookie ..
            # I couldn't get the language settings working properly in IE, since it seemed to
            # be erasing or losing the data, so the cookie acts as a backup.
            response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang_code)
                
        return response
    except:
        error_reporting.log_exception(logging.critical, request=request)  
        if not request.is_ajax():
            http.HttpResponseRedirect("/") # send to login page
        else:
            # let the client side know that an error occurred (alghough the resonse is currently ignored)
            http.HttpResponseServerError("Error")
        
        
        