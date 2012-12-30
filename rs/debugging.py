
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

import constants


def get_html_for_unique_last_login_calculations(userobject):
    
    
    generated_html = ''
    
    
    generated_html += "Previous last login: %s\n" % userobject.previous_last_login
    generated_html += "Last login: %s\n" % userobject.last_login
    generated_html += "Unique last login: %s\n" % userobject.unique_last_login
    
    offset = 0 # the offset is in Days.
    # make sure it has the attribute, and that the attribute is set
    if hasattr(userobject, 'unique_last_login_offset_ref') and userobject.unique_last_login_offset_ref:
        unique_last_login_offset_ref = userobject.unique_last_login_offset_ref
        
        # loop over all possible offsets, and assign the value if the boolean in offset_ref indicates
        # that it should be assigned.
        for (offset_name, value) in constants.offset_values.iteritems():
            has_offset = getattr(unique_last_login_offset_ref, offset_name)
            
            if has_offset:
                has_offset_str = "YES"
            else:
                has_offset_str = "NO"
            generated_html += "%30s %8s %8s\n" % (offset_name, value, has_offset_str)

    return generated_html