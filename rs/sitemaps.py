
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

from django import http
from rs import error_reporting
import logging, os


try:
    if os.path.isdir('rs/proprietary'):    
        from rs.proprietary.my_sitemaps import * 
    else:
        def generate_sitemaps(request):
            return http.HttpResponse("Code for generating sitemaps is not defined. Please contact Lexabit Inc. for support.")
        
        def get_sitemap(request, sitemap_number):
            return http.HttpResponse("Code for generating sitemaps is not defined. Please contact Lexabit Inc. for support.")
        
        def get_sitemap_index(request, sitemap_index_number):
            return http.HttpResponse("Code for generating sitemaps is not defined. Please contact Lexabit Inc. for support.")
    
        def get_highest_sitemap_index_number():
            # If this function is called here (as opposed to from my_sitemaps) then sitemaps are not defined
            # and therefore the number returned is zero.
            return 0
except:
    # Notify of all other errors
    error_reporting.log_exception(logging.warning)