# Copyright (c) 2008 Joost Cassee
# Licensed under the terms of the MIT License (see LICENSE.txt)

import re, os
from django import http
from django.conf import settings
import django.core.exceptions
from django.core import urlresolvers
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect
from django.utils import translation
from django.utils.cache import patch_vary_headers
from rs import error_reporting
import logging
import localeurl
from localeurl import utils

# Make sure the default language is in the list of supported languages
assert utils.supported_language(settings.LANGUAGE_CODE) is not None, \
        "Please ensure that settings.LANGUAGE_CODE is in settings.LANGUAGES."


class LocaleURLMiddleware(object):
    """
    Middleware that sets the language based on the request path prefix and
    strips that prefix from the path. It will also automatically redirect any
    path without a prefix, unless PREFIX_DEFAULT_LOCALE is set to True.
    Exceptions are paths beginning with MEDIA_URL or matching any regular
    expression from LOCALE_INDEPENDENT_PATHS from the project settings.

    For example, the path '/en/admin/' will set request.LANGUAGE_CODE to 'en'
    and request.path to '/admin/'.

    Alternatively, the language is set by the first component of the domain
    name. For example, a request on 'fr.example.com' would set the language to
    French.

    If you use this middleware the django.core.urlresolvers.reverse function
    is be patched to return paths with locale prefix (see models.py).
    """
    def __init__(self):
        if not settings.USE_I18N:
            raise django.core.exceptions.MiddlewareNotUsed()
        
    def process_request(self, request):
        
        # This is custom-coded middleware that handles language codes that are passed in through the URL. 
        
        locale, path = utils.split_locale_from_request(request)  
        
        if not locale:
            # the locale was not defined in the URL, so we now check session, cookie, browser settings, and finally default language.
            # This should always result in a valid language.
            # see /Library/Python/2.5/site-packages/django/utils/translation/trans_real.py - get_language_from_request()
            locale = translation.get_language_from_request(request)
        
        # by construction, locale must be defined now
        assert(locale)
        
        locale_path = utils.locale_path(path, locale)
        if locale_path != request.path_info:
            if request.method == 'POST':
                # Error - POST cannot be re-directed. You must POST directly to a valid URL.
                error_message = "POST redirection in LocaleURLMiddleware - you *must* POST directly to valid URL"
                error_reporting.log_exception(logging.critical, error_message = error_message, request=request) 
                raise Exception(error_message)
            
            if request.META.get("QUERY_STRING", ""):
                locale_path = "%s?%s" % (locale_path, 
                        request.META['QUERY_STRING'])
                            
            return HttpResponseRedirect(locale_path)
        
        request.path_info = path
        translation.activate(locale)
        request.LANGUAGE_CODE = translation.get_language()

    def process_response(self, request, response):
        
        # original code starts here
        if 'Content-Language' not in response:
            response['Content-Language'] = translation.get_language()
        translation.deactivate()
        return response


