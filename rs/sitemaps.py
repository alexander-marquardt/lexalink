
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

try:
    from rs.proprietary import my_sitemaps
    sitemaps_code_exists = True
except:
    sitemaps_code_exists = False
    
    
def generate_sitemaps(request):
    
    if sitemaps_code_exists:
        return my_sitemaps.generate_sitemaps(request)
    else:
        return http.HttpResponse("Code for generating sitemaps is not defined. Please contact Lexabit Inc. for support.")

def get_sitemap(request, sitemap_number):
    if sitemaps_code_exists:
        return my_sitemaps.get_sitemap(request, sitemap_number)
    else:
        return http.HttpResponse("Code for generating sitemaps is not defined. Please contact Lexabit Inc. for support.")

def get_sitemap_index(request, sitemap_index_number):
    
    if sitemaps_code_exists:
        return my_sitemaps.get_sitemap_index(request, sitemap_index_number)
    else:
        return http.HttpResponse("Code for generating sitemaps is not defined. Please contact Lexabit Inc. for support.")
