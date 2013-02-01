
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

""" 
This module contains functions for backing up critical data "in-the-cloud".
This means that backed-up data is not protected from google server failures, 
but it is somewhat protected from our own program trashing it"""

import logging

import datetime
import models, utils
import error_reporting

# Define the backup schedule
DAYS_BETWEEN_BACKUPS = 5 # 5 days between backups, with 3 backup objects gives us (minimum) 15 days of history


def create_backup_userobject_and_update_tracker(request, userobject, backup_object_name, backup_tracker):       
    backup_userobject = utils.clone_entity(
        userobject, 
        is_real_user = False,
        #last_login_string = None, 
        #unique_last_login = None,
        # use the "last_login" to indicate when the backup was done.
        last_login =  datetime.datetime.now(),
        )
        
    # Note, the following "put" will create a new object -- and we cannot call
    # utils.put_userobject -- since the userobject doesn't yet exist and therefore doesn't
    # yet have a key.
    backup_userobject.put()
    
    setattr(backup_tracker, backup_object_name, backup_userobject.key)
    backup_tracker.most_recent_backup_name = backup_object_name
    backup_tracker.put()


def update_or_create_userobject_backups(request, userobject):
# This function will populate (and create if necessary) the backup_userobject objects.
# This is intended to take snapshots of the userobjects at periodic intervals (defined by
# DAYS_BETWEEN_BACKUPS) - as opposed to revision control of the user data. 
    
    
    try:
        backup_tracker = None
        try:
            backup_tracker_key = userobject.backup_tracker
            if backup_tracker_key:
                backup_tracker = backup_tracker_key.get()
        except:
            error_reporting.log_exception(logging.critical, error_message="User: %s error in backup_tracker - will be over-written" % userobject.username)
            backup_tracker = None
            
        if not backup_tracker:
            # if this is the principal userobject, is must have is_real_user set to True
            assert(userobject.is_real_user)
            # create the backup_tracker, store it, and update the userobject.
            backup_tracker = models.UserModelBackupTracker()
            backup_tracker.userobject_ref = userobject.key
            
            # doesn't really matter what most_recent_backup is set to since it is a rotating backup 
            # but we set it to a known value (backup_1)
            backup_tracker.most_recent_backup_name = "backup_1" 
            backup_tracker.put()
            userobject.backup_tracker = backup_tracker.key
            # give the backup_tracker a reference to the parent userobject.
            utils.put_userobject(userobject)
        
    
        current_time = datetime.datetime.now()               
    
        # the following data structure allows us to quickly rotate through the backup userobjects
        next_backup_object_name = {'backup_1': 'backup_2', 'backup_2': 'backup_3', 'backup_3':'backup_1'}
        
        most_recent_backup_object_name = backup_tracker.most_recent_backup_name
        most_recent_backup_userobject_key = getattr(backup_tracker, most_recent_backup_object_name)
        
        if not most_recent_backup_userobject_key:
            
            # if the object doesn't exist, then we have not done any backups yet, and this object should
            # be created. 
            create_backup_userobject_and_update_tracker(request, userobject, most_recent_backup_object_name, backup_tracker)
        else:
            # We know that at least one backup has been done, and so we check that an appropriate amount
            # of time has passed before doing the next backup.
            most_recent_backup_userobject = most_recent_backup_userobject_key.get()
            time_passed_since_backup = current_time - most_recent_backup_userobject.last_login
            
            if time_passed_since_backup > datetime.timedelta(days = DAYS_BETWEEN_BACKUPS):
                backup_object_name = next_backup_object_name[most_recent_backup_object_name]
                
                try:
                    backup_userobject = getattr(backup_tracker, backup_object_name)
                except:
                    error_reporting.log_exception(logging.critical, error_message="User: %s backup_userobject not found in backup_tracker" % userobject.username)
                    backup_userobject = None
                
                if backup_userobject:
                    # if the backup_userobject exists, delete it because a new object will be created
                    # (and we don't want a memory/disk-leak in the database!)
                    backup_userobject.delete()
                    
                create_backup_userobject_and_update_tracker(request, userobject, backup_object_name, backup_tracker)
                
    except:
        # since we don't know what caused the error, mark it as critical so that we investigate
        error_reporting.log_exception(logging.critical)
        
    # we don't return anything
    return
