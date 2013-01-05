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


from os import environ

import traceback, sys, os, StringIO, re
import settings
import logging

from rs import utils_top_level, http_utils

def log_exception(logging_function, *args, **kwds):
    """Signal handler to log an exception or error condition for which we want further details 
    in the log files. 
    logging_function should be one of the logging.* (ie. logging.error) functions"""
    
    # get the exception -- however, we also use this function for general error logging
    # and therefore exc_info might return (None, None, None). 
    excinfo = sys.exc_info()
    cls, err = excinfo[:2]
    
    error_message = ''
    
    if 'stack_limit' in kwds:
        stack_limit = kwds['stack_limit']
    else: 
        stack_limit = 5
    
    if err:
        exception_name = cls.__name__
        subject = 'Exception: %s: %s\n' % (exception_name, err)
        traceback_info = ''.join(traceback.format_exception(*excinfo))
        
        if exception_name == 'DeadlineExceededError':
            # if the exception is a Deadline, lower the warning level -- this is generally
            # caused by google issues, and we cannot do much about it. 
            logging_function = logging.warning
               
    else: 
        subject = 'Status (non Exception)\n'
        traceback_info_file = StringIO.StringIO()
        traceback.print_stack(limit=stack_limit, file = traceback_info_file)
        traceback_info = traceback_info_file.getvalue()
        traceback_info_file.close()
        
        
    if check_if_trend_micro_scanning():
        # If this is from Trend Micro, remove the error message - they seem to make all
        # URLs lower case, which basically makes all entity keys invalid, as well as
        # country codes etc. Additionally, they try scanning URLs that require the
        # user to be logged in - which generates a "session not found" error message
        logging_function = logging.info
        error_message = "Trend Micro Scanning Error:\n" + error_message
        
        
    # Check if request information is passed in
    if 'request' in kwds:
        try:
            repr_request = repr(kwds['request'])
        except:
            repr_request = 'log_exception error: Request repr() not available.'
    else:
        repr_request = 'Request not available.'
        
    if 'error_message' in kwds:
        error_message += kwds['error_message']
    else:
        error_message += "No additional error information included"
        
    msg = (u"""
    Status Message: %s
    ***********
    Version: %s
    ***********
    Traceback: %s
    ***********
    Request: %s
    """
           % (error_message,
              os.getenv('CURRENT_VERSION_ID'),
              traceback_info,
              repr_request))
    
    exception_message = "%s%s" %(subject, msg)
    
    logging_function(exception_message)
        
        
def error_500_go_to_login(request):
    # This function is called if a 500 error occurs while users is browsing the website.
    #
    # Log the error, and send user to the login page.
    # extracts information about the error, and then calls the logger to record it.
    error_url = request.path    
    
    userobject = utils_top_level.get_userobject_from_request(request)
    if userobject:
        username = userobject.username
          
        error_message = u"Error 500:\nUser: %s\nURL: %s" % (username, error_url)
        log_exception(logging.critical, error_message=error_message, request=request)    
    else:
        # 500 errors for non-logged-in users are given lower priority because it can
        # be triggered by just going to a URL that they are not authorized access to
        # Eventually, we should prevent bad URLs from generating exceptions. 
        # Mark 500 errors as critical, so that we write code to catch them earlier. 
        error_message = u"Error 500:\nURL: %s" % error_url
        log_exception(logging.error, error_message=error_message, request=request)    
        
    return http_utils.redirect_to_url(request, "/%s/" % request.LANGUAGE_CODE)


def report_bad_url(request):
    error_url = request.path
    
    username = ''
    userobject = utils_top_level.get_userobject_from_request(request)
    if userobject:
        username = userobject.username
    else: username = "N/A"
    
    remoteip  = environ['REMOTE_ADDR']
    
    msg = "BAD URL: %s remoteip: %s username: %s" % (error_url, remoteip, username)
    logging.warning(msg)
    
    if settings.DEBUG == True:
        # if we are running in debug mode, then we don't want to mask the fact that 
        # a bad URL was generated -- however, in production this will show up in the logs
        raise Exception(msg)
    
    return http_utils.redirect_to_url(request, "/%s/" % request.LANGUAGE_CODE)


def check_if_trend_micro_scanning():
    remoteip  = os.environ['REMOTE_ADDR']
    
    # Check to see if TREND MICRO (antivirus/anti-malware) is scanning - don't bother reporting this as an error, as they seem to be 
    # receiving information from user activity about the profile that the user is viewing, and then trying to 
    # re-load the profile on their server - they historically mess-up URLs by making them lower-case, which causes errors 
    # on our servers - consider blacklisting Trend Micro.
    if  (re.match(r'150\.70\.64\..+', remoteip) or \
         re.match(r'150\.70\.75\..+', remoteip) or \
         re.match(r'150\.70\.172\..+', remoteip) or \
         re.match(r'216\.104\.15\..+', remoteip)):
        logging.info("matched remote ip %s as a trend micro address" % remoteip)
        
        return True # it *is* (probably) Trend Micro
    
    else:
        logging.info("remote ip %s did not match trend micro address" % remoteip)

        return False
    
    