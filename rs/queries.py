
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

import settings

from google.appengine.ext import db 
from models import InitiateContactModel 
import error_reporting, logging
    

def query_initiate_contact_by_type_of_contact(userobject_key, contact_type, sent_or_received, num_objects_to_get, query_value_to_match):
    # performs query on the InitiateContact model. 
    # contact_type: wink, kiss, favorite, key
    # send_or_receive: is the current user the sender of the receiver of the current "contact_type"
    # Returns a list of the users that match the query. 
    # Should be ordered by date for each contact_type.
    # 
    # Explained in words: could be used to query for all the users that have sent the current users a "kiss" for example.
    #
    
    q = InitiateContactModel.query().order(-InitiateContactModel._properties["%s_stored_date" % contact_type])
    
    if sent_or_received == 'sent' or contact_type == 'chat_friend':
        # Note: chat_friend is a special case because all of the information about the status is stored on the "primary" 
        # userobject, which is equivalent to the sent/viewer object.
        q = q.filter(InitiateContactModel.viewer_profile == userobject_key)
    elif sent_or_received == 'received':
        q = q.filter(InitiateContactModel.displayed_profile == userobject_key)
    else:
        # Error: should never get here -- unexpected code is the only reason for this
        assert(False)
    
    q = q.filter(InitiateContactModel._properties["%s_stored" % contact_type] == query_value_to_match)

    query_results = q.fetch(num_objects_to_get)
    return query_results



    
    
    
    
    