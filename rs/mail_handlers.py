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

import  logging
import settings
from rs import error_reporting, email_utils, constants
from django import http

def handle_bounced_email(request):
    
    raw_message = request.POST.get('raw-message', None)
    logging.warning("Bounced email:\n%s" % raw_message)
    subject = "%s Bounced Email" % settings.APP_NAME
    #email_utils.send_admin_alert_email(raw_message, subject, is_raw_text=True, to_address=constants.sender_address) 
    return http.HttpResponse("OK")
    
    
    