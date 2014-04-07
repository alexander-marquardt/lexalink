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


from django.conf.urls.defaults import *
from django.core.validators import email_re

from django.http import Http404
import logging

from rs import error_reporting, url_utils

urlpatterns = patterns('',
    (r'^', include('rs.urls_common')),
)

urlpatterns = urlpatterns + patterns('',
    (r'^jx/$', url_utils.resolve_ajax_hashbang_urls, {'urlpatterns' : 'rs.urls_common'}),
    # The following bad_url must be after all the valid urls since it is a "catch-all"
    (r'^.*/$', error_reporting.report_bad_url), 
)



#########################
# Error handler

# If there is an error -- just direct back to the login page .. 
handler500 = 'rs.error_reporting.error_500_go_to_login'
