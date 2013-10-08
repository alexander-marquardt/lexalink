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


# utility functions that don't depend on any code within rs. This is intended for 
# utilitis and defs that provide very basic functionality. Seperating these utilities from other
# functions allows us to import this file wherever we want, without worrying about 
# circular references.

from google.appengine.ext import ndb
from google.appengine.api.datastore import entity_pb
from google.appengine.api import memcache
from django.utils.translation import ugettext

import logging, pickle

import constants, settings


def get_object_from_string(object_str):
    
    """ 
    receives a string which is used to index an object in
    the database. If not in the database then "None" is returned.
    """
        
    if not object_str:
        return None   
    
    return_object = ndb.Key(urlsafe = object_str).get()
    return return_object

# Removed memcaching since NDB should take care of this.
    #memcache_key_str = constants.BASE_OBJECT_MEMCACHE_PREFIX + object_str 
    #return_object = deserialize_entities(memcache.get(memcache_key_str))
    #if return_object is not None:
        #return return_object
    #else:
        ## pull the object out of database and also update memcache
        #return_object = ndb.Key(urlsafe = object_str).get()
        #memcache.set(memcache_key_str, serialize_entities(return_object), constants.SECONDS_PER_MONTH)
        #return return_object


def get_userobject_from_request(request):
    
    """ 
    receives a request object which contains the reference string for to currently logged in userobject,
    and returns the userobject. 

    """
    
    userobject = None
    if request.session.__contains__('userobject_str'): 
        #userobject = get_object_from_string(request.session['userobject_str'])
        userobject = ndb.Key(urlsafe = request.session['userobject_str']).get()
                               
    return userobject


def get_uid_from_request(request):
    if request.session.__contains__('userobject_str'): 
        return request.session['userobject_str']
    else:
        return None
     
     
# Required for efficient memcaching: from http://blog.notdot.net/2009/9/Efficient-model-memcaching
#Usage:
#from google.appengine.api import memcache
#from google.appengine.ext import db

#entities = deserialize_entities(memcache.get("somekey"))
#if not entities:
#    entities = MyModel.all().fetch(10)
#    memcache.set("somekey", serialize_entities(entities))


def serialize_entity(obj):
    
    if obj is None:
        return None
    else:
        return pickle.dumps(obj)
    
    #if models is None:
        #return None
    #elif isinstance(models, ndb.Model):
    ## Just one instance
        #return ndb.ModelAdapter().entity_to_pb(models).Encode()
    #else:
    ## A list
        #return [ndb.ModelAdapter().entity_to_pb(x).Encode() for x in models]

def deserialize_entity(data):
    
    if data is None:
        return None
    else:
        return pickle.loads(data)
    
    #if data is None:
        #return None
    #elif isinstance(data, str):
        ## Just one instance
        #return ndb.ModelAdapter().pb_to_entity(entity_pb.EntityProto(data))
    #else:
        #return [ndb.ModelAdapter().pb_to_entity(entity_pb.EntityProto(x)) for x in data]
    


def get_additional_description_from_sex_and_preference(sex_key_val, preference_key_val, pluralize = True):
    additional_description = ''    
    
    if sex_key_val == "male" and preference_key_val == "male":
        if pluralize:
            additional_description = " (%s) " % ugettext("Gay men")
        else:
            additional_description = " Gay "
            
    elif sex_key_val == "female" and preference_key_val == "female":
        if pluralize:
            additional_description = " (%s) " % ugettext("Lesbians")
        else:
            additional_description = " %s " % ugettext("Lesbian")
        
        
    return additional_description    


def get_verification_vals_from_get(request):

    verification_vals_dict = {}

    if request.GET.get("show_verification"):
        verification_vals_dict['show_verification_dialog'] = True
        verification_vals_dict['verification_username'] = request.GET.get("verification_username", '')
        verification_vals_dict['secret_verification_code'] = request.GET.get("secret_verification_code", '')    
        verification_vals_dict['verification_email'] = request.GET.get("verification_email", '')
        verification_vals_dict['allow_empty_code'] = request.GET.get("allow_empty_code", '')
           
    return verification_vals_dict

def check_if_user_already_registered_passed_in(request):
    # this is a callback from the routines that store the user profile when an email authorization link is clicked on.
    message_for_client = None
    user_already_registered = request.GET.get('username_already_registered', '') 
    if (user_already_registered):
        username = request.GET.get('already_registered_username', '') 
        message_for_client = ugettext("""
        Your account has been correctly registered. You can enter using your username: <strong>%(username)s</strong>
        and the password that you entered when you created your account.""") % {'username' : username}

    return message_for_client