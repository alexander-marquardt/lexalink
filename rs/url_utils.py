
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

import logging

from rs import rendering
from rs import error_reporting
from localeurl import middleware
from django.core.urlresolvers import resolve
from django import http
import urllib

locale_url_middleware = middleware.LocaleURLMiddleware()
def resolve_ajax_hashbang_urls(request, urlpatterns):
    '''
    Allow url dispatching based on content of '_escaped_fragment_' parameter - this is used for the google crawling
    which translates !# into ?_escaped_fragment_ URLs.
    '''
    try:
        escaped_fragment = request.GET.get('_escaped_fragment_', None)
        if escaped_fragment:
            unescaped_fragment = urllib.unquote(escaped_fragment)
            
            # the url is in the format /ajax/?_escaped_fragement_=/foo/fee/?var=val....
            after_split = unescaped_fragment.split("?", 1)
            path = after_split[0]
            
            if len(after_split) >1 :
                qparams = after_split[1]
                qdict = http.QueryDict(qparams)
                request.GET = qdict    
                
            request.path_info = path
            locale_url_middleware.process_request(request)
            
            func, args, kwargs = resolve(request.path_info, urlpatterns)
            # make sure the URL has resolved - if not generate an error
            kwargs['request'] = request
            try: func(*args, **kwargs)
            except http.Http404: return error_reporting.report_bad_url(request)
                
            return func(*args, **kwargs)
        else:
            # the url does not have an _escaped_fragment_ passed in, and therefore it is just a standard
            # ajax - hashbang URL (rememeber that anything after the hash doesn't make it to the server)
            return rendering.render_main_html(request, generated_html= '', render_wrapper_only= True)

    except:
        error_reporting.log_exception(logging.critical, request = request) 
        return error_reporting.report_bad_url(request)
    
