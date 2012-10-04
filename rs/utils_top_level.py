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

from google.appengine.ext import db 
from google.appengine.api.datastore import entity_pb
from google.appengine.api import memcache

import logging

import constants, settings


def get_object_from_string(object_str):
    
    """ 
    receives a string which is used to index an object in
    the database. If not in the database then "None" is returned.
    """
        
    if not object_str:
        return None           

    memcache_key_str = object_str + settings.VERSION_ID
    return_object = deserialize_entities(memcache.get(memcache_key_str))
    if return_object is not None:
        #logging.debug("get_object_from_string HIT **********")
        return return_object
    else:
        # pull the object out of database and also update memcache
        return_object = db.get(db.Key(object_str))
        memcache.set(memcache_key_str, serialize_entities(return_object), constants.SECONDS_PER_MONTH)
        #logging.debug("get_object_from_string MISS **********")
        return return_object


def get_userobject_from_request(request):
    
    """ 
    receives a request object which contains the reference string for to currently logged in userobject,
    and returns the userobject. 

    """
    
    userobject = None
    if request.session.__contains__('userobject_str'): 
        #userobject = db.get(db.Key(request.session['userobject_str']))
        userobject = get_object_from_string(request.session['userobject_str'])
                               
    return userobject


# Required for efficient memcaching: from http://blog.notdot.net/2009/9/Efficient-model-memcaching
#Usage:
#from google.appengine.api import memcache
#from google.appengine.ext import db

#entities = deserialize_entities(memcache.get("somekey"))
#if not entities:
#    entities = MyModel.all().fetch(10)
#    memcache.set("somekey", serialize_entities(entities))


def serialize_entities(models):
    if models is None:
        return None
    elif isinstance(models, db.Model):
    # Just one instance
        return db.model_to_protobuf(models).Encode()
    else:
    # A list
        return [db.model_to_protobuf(x).Encode() for x in models]

def deserialize_entities(data):
    if data is None:
        return None
    elif isinstance(data, str):
        # Just one instance
        return db.model_from_protobuf(entity_pb.EntityProto(data))
    else:
        return [db.model_from_protobuf(entity_pb.EntityProto(x)) for x in data]
    
