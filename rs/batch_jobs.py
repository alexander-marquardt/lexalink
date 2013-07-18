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


""" This file contains functions that will be ran as batch jobs (offline processing). This can include 
maintenance, sending email updates to users, etc.

These can be triggered by accessing a "secret" URL."""

import logging, re
import time
from google.appengine.ext import ndb 
from google.appengine.api import mail
from google.appengine.api import taskqueue

from django.utils import translation
from django.utils.translation import ugettext, ungettext
from django import http
from django.core.validators import email_re
from django.template import loader, Context

from models import UserModel
import models
import email_utils
from constants import offset_values
import store_data, login_utils, utils_top_level



import sharding
import mailbox
import models
import utils, error_reporting
import html2text
import constants, settings
    
from google.appengine.runtime import DeadlineExceededError



def send_new_feature_email(userobject, return_message_html = False):
    
    # sends an email to person indicated in the .
    
    try:
        # set the language to be the users preferred language
        previous_language = translation.get_language() # remember the original language, so we can set it back when we finish         
     
        if userobject:
            username = userobject.username
            email_address = userobject.email_address
            lang_code = userobject.search_preferences2.get().lang_code
            
        else:
            username = 'TESTING CODE'
            email_address = 'alexander.marquardt@gmail.com'
            lang_code = 'en'
            
        translation.activate(lang_code)     
            
        logging.info("Preparing to send new feature email to %s" % username)
        
        subject = ugettext("FriendBazaar.com - from the creators of %(app_name)s") % {'app_name' : settings.APP_NAME}
                           
        message = mail.EmailMessage(sender=constants.sender_address,
                                    subject=subject)
        
        message.to = u"%s <%s>" % (username, email_address)
                
        message.html = ugettext("friend_build welcome %(username)s %(app_name)s") % {
            'username': username, 'app_name' : settings.APP_NAME}
        
        # Now, get a description of what friend_build is:
        template = loader.get_template("common_helpers/welcome_message.html")
        context = Context(constants.template_common_fields)
                
        message.html += template.render(context)
        
        message.body = html2text.html2text(message.html) 
        
        message.send()
        
        info_message = "%s\n%s\n%s\n" % (message.sender, message.to, message.body)
        #info_message = "%s\n%s\n" % (message.sender, message.to)
        logging.info(info_message)
        
        if not return_message_html:
            return_val = http.HttpResponse(info_message)
        else:
            return_val = message.html
    
    except:
        error_message = "Unknown error (message not configured correctly)"
        error_reporting.log_exception(logging.error, error_message = error_message)
        return_val = http.HttpResponseServerError(error_message)  
        
    finally:
        # activate the original language -- not sure if this is really necessary, but is 
        # somewhat safer (until I fully understand how multiple processes in a single thread are interacting)
        translation.activate(previous_language)
        
    return return_val

def view_message(request):
    # a test function that allows us to view the generated message html
    userobject = utils_top_level.get_userobject_from_request(request) 
    message_html = send_new_feature_email(userobject, return_message_html = True)
    return http.HttpResponse(message_html)
     

def batch_send_email(request):

    # send mail
    
    """ This function scans the database for profiles that we wish to send an email to, and calls 
        an appropriate function to send the message.
    """
    PAGESIZE = 20
    
    # Note: to user cursors, filter parameters must be the same for all queries. 
    # This means that the cutoff_time must be remain constant as well (confused me for a few hours while figuring out
    # why the code wasn't working).
    
    try:
        
        batch_cursor = None
        
        if request.method == 'POST':
            batch_cursor = request.POST.get('batch_cursor',None)          
            
        generated_html = 'Starting batch email - see logs for progress.<br><br>'
        
        logging.info("Paging new page with cursor %s" % batch_cursor)
                
        query_filter_dict = {}    

        query_filter_dict['user_is_marked_for_elimination = '] = False        
        order_by = "-last_login_string"
        
        query = UserModel.all().order(order_by)
        for (query_filter_key, query_filter_value) in query_filter_dict.iteritems():
            query = query.filter(query_filter_key, query_filter_value)

 
        if batch_cursor:
            query.with_cursor(batch_cursor)
                                   
        userobject_batch = query.fetch(PAGESIZE)
                
        if not userobject_batch:
            # there are no more objects - break out of this function.
            info_message = "No more objects found - Exiting function<br>\n"
            logging.info(info_message)
            return http.HttpResponse(info_message)

        for userobject in userobject_batch:  
            try:
                if userobject.email_address_is_valid and userobject.email_address != "----":
                    send_new_feature_email(userobject)
                    #logging.info("Testing - would have sent message to %s" % userobject.username)
                else:
                    logging.info("User %s does not have a valid email address. Currently set to: %s" % (userobject.username, userobject.email_address))
                
                    
            except:
                error_reporting.log_exception(logging.critical)  
                
                    
        # queue up more jobs
        batch_cursor = query.cursor()
        path = request.path_info
        taskqueue.add(queue_name = 'background-processing-queue', url=path, params={'batch_cursor': batch_cursor})

        return http.HttpResponse(generated_html)
    except:
        error_reporting.log_exception(logging.critical)
        return http.HttpResponseServerError()
   



def set_photo_rules_on_userobject(userobject):
    
        
    if not userobject.accept_terms_and_rules_key :
        # we need to create the photo_tracker object and add it to the userobject.
        terms_and_rules_object = models.AcceptTermsAndRules()
        terms_and_rules_object.last_photo_rules_accepted = "not accepted yet"
        terms_and_rules_object.put()
        userobject.accept_terms_and_rules_key = terms_and_rules_object.key
        utils.put_userobject(userobject)  
        logging.info("Adding AcceptTermsAndRules to %s" % userobject.username)
        
    else:
        logging.info("User %s has AcceptTermsAndRules already" % userobject.username)
        


def create_and_update_photo_tracker(userobject):

    try:
        
        user_photos_tracker_key = userobject.user_photos_tracker_key 
        if not user_photos_tracker_key:     
            # This userobject doesn't have a photo tracker setup yet. Create one now. 
            user_photos_tracker = models.UserPhotosTracker()
        
            profile_photo_key = None
            public_photos_keys_list = []
            private_photos_keys_list = []
             
            # Loop over all photos, and mark them appropriately based on the inputs. 
            all_user_photo_keys = models.PhotoModel.query().filter(models.PhotoModel.parent_object == userobject.key).fetch(constants.MAX_NUM_PHOTOS, keys_only = True)  
            for photo_key in all_user_photo_keys:
                photo_key_str = photo_key.urlsafe()
                photo_object = photo_key.get()

                if photo_object:
                    if photo_object.is_private:
                        private_photos_keys_list.append(photo_key)
                    else:
                        # photo is public
                        public_photos_keys_list.append(photo_key)
                    if photo_object.is_profile:
                        assert(not photo_object.is_private)
                        profile_photo_key = photo_key
            
            user_photos_tracker.profile_photo_key = profile_photo_key
            user_photos_tracker.public_photos_keys = list(public_photos_keys_list)
            user_photos_tracker.private_photos_keys = list(private_photos_keys_list)
            user_photos_tracker.put() 
            
            userobject.user_photos_tracker_key = user_photos_tracker.key
            userobject.put()            
            
            info_message = "**Updated user_photos_tracker on %s's object<br>\n" % userobject.username
        else:
            info_message = "No update to user_photos_tracker on %s - already up-to-date\n" % userobject.username
            
        logging.info(info_message)   
        

    
    except:
        error_reporting.log_exception(logging.critical)       
           
    return        
         
         

def fix_items_sub_batch (request):
    
    if request.method == 'POST':
        userobject_batch_keys_strs = request.POST.getlist('userobject_batch_keys_strs')     
    else:
        return http.HttpResponse('No post received')
    
    for userobject_key_str in userobject_batch_keys_strs:  
        userobject = ndb.Key(urlsafe = userobject_key_str).get()
            
        try:
            create_and_update_photo_tracker(userobject)
            
        except:
            error_reporting.log_exception(logging.critical)  
            
    return http.HttpResponse('OK')

                
def batch_fix_object(request):

    from google.appengine.datastore.datastore_query import Cursor
    
    """ This function scans the database for profiles that need to be fixed
    """
    PAGESIZE = 30 # don't make this much more than 100 or we start overusing memory and get errors
    
    # Note: to use cursors, filter parameters must be the same for all queries. 
    # This means that the cutoff_time must be remain constant as well (confused me for a few hours while figuring out
    # why the code wasn't working).
    
    
    try:
        
        batch_cursor = None
        
        if request.method == 'POST':
            batch_cursor = request.POST.get('batch_cursor',None)          
        paging_cursor = Cursor(urlsafe = batch_cursor)
        
        generated_html = 'Updating userobjects:<br><br>'
        
        logging.info("Paging new page with cursor %s" % batch_cursor)
                
        q = UserModel.query().order(UserModel._key)
        q = q.filter(UserModel.user_is_marked_for_elimination == False)
        
        if paging_cursor:
            (userobject_batch_keys, new_cursor, more_results) = q.fetch_page(PAGESIZE, start_cursor = paging_cursor, keys_only = True)
        else:
            (userobject_batch_keys, new_cursor, more_results) = q.fetch_page(PAGESIZE, keys_only = True)               
                
        userobject_batch_keys_strs = []
        for userobject_key in userobject_batch_keys:
            userobject_batch_keys_strs.append(userobject_key.urlsafe())
            
            
        taskqueue.add(queue_name = 'background-processing-queue', url='/rs/admin/fix_items_sub_batch/', 
                      params={'userobject_batch_keys_strs': userobject_batch_keys_strs})
            
        # queue up more jobs
        if more_results:
            path = request.path_info
            taskqueue.add(queue_name = 'background-processing-queue', url=path, params={'batch_cursor': new_cursor.urlsafe()})

        return http.HttpResponse(generated_html)
    except:
        error_reporting.log_exception(logging.critical)
        return http.HttpResponseServerError()
    
#def batch_fix(request):

    
    #""" This function scans the database for profiles that need to be fixed
    #"""
    #PAGESIZE = 100 # don't make this much more than 100 or we start overusing memory and get errors
    
    ## Note: to use cursors, filter parameters must be the same for all queries. 
    ## This means that the cutoff_time must be remain constant as well (confused me for a few hours while figuring out
    ## why the code wasn't working).
    
    
    #try:
        
        #batch_cursor = None
        
        #if request.method == 'POST':
            #batch_cursor = request.POST.get('batch_cursor',None)          
            
        #generated_html = 'Updating InitiateContact objects:<br><br>'
        
        #logging.info("Paging new page with cursor %s" % batch_cursor)
                

        #order_by = "__key__"
        #query = models.InitiateContactModel.all().order(order_by)            
                   
        #if batch_cursor:
            #query.with_cursor(batch_cursor)
                                   
        #object_batch = query.fetch(PAGESIZE)
                
        #if not object_batch:
            ## there are no more objects - break out of this function.
            #info_message = "No more objects found - Exiting function<br>\n"
            #logging.info(info_message)
            #return http.HttpResponse(info_message)

        #for myobject in object_batch:  
            #try:
                #current_object_key_name = myobject.key().id_or_name()
                #info_message = "**Checking %s object<br>\n" % current_object_key_name
                #logging.info(info_message)     

                #viewer_userobject_key = myobject.viewer_profile.key()
                #display_userobject_key = myobject.displayed_profile.key()
                #desired_object_key_name = str(viewer_userobject_key) + str(display_userobject_key) 
                
                #current_object_key_name = myobject.key().name()
                
                #if current_object_key_name != desired_object_key_name:
                    ## we need to copy the entity, and over-ride the key name.
                    #new_object = utils.clone_entity(myobject, key_name=desired_object_key_name)
                    #logging.info("**Cloning object to key %s and deleting original\n" % desired_object_key_name)
                    #new_object.put()
                    
                    #logging.info("**Deleting object %s\n" % myobject)
                    #myobject.delete()
 
            #except:
                #error_reporting.log_exception(logging.critical)  
                
        ## queue up more jobs
        #batch_cursor = query.cursor()
        #path = request.path_info
        #taskqueue.add(queue_name = 'background-processing-queue', url=path, params={'batch_cursor': batch_cursor})

        #return http.HttpResponse(generated_html)
    #except:
        #error_reporting.log_exception(logging.critical)
        #return http.HttpResponseServerError()
    

    
import datetime
def write_mail_txn(myobject, props, text):
    
    try:
        info_message = "**Considering copying MailMessageModel %s object<br>\n" % myobject.key.urlsafe()
        logging.info(info_message)     
                        

            
        owner_key = myobject.owner_ref.key()
        other_key = myobject.other_ref.key()
        
        parent_key = utils.get_fake_mail_parent_entity_key(owner_key, other_key)
        
        def check_if_already_copied():
            query_filter_dict = {}    

            query_filter_dict['m_to = '] = myobject.m_to.key()
            query_filter_dict['m_from = '] = myobject.m_from.key()
            query_filter_dict['m_date <= '] = myobject.m_date + datetime.timedelta(seconds = 2)
            query_filter_dict['m_date >= '] = myobject.m_date + datetime.timedelta(seconds = -2)
             
            query = models.MailMessageModel.all().ancestor(parent_key)
            for (query_filter_key, query_filter_value) in query_filter_dict.iteritems():
                query = query.filter(query_filter_key, query_filter_value)
            
            existing_object = query.get()
            if existing_object:
                return True
            else:
                return False

        if not check_if_already_copied():
            mail_message = models.MailMessageModel(parent=parent_key)
            
            for k in props.keys():
                setattr(mail_message, k, getattr(myobject, k))
            mail_message.m_text = text
                
            mail_message.put()
            info_message = "**Wrote mail_message object %s<br>\n"  % mail_message.key()
            logging.info(info_message)
            return "copied_to_hr_datastore_v7"
        else:
            return "previously_copied_v7"


    except:
        error_reporting.log_exception(logging.critical) 
        return None
        
        
        

    
#def batch_fix_initiate_contact_model(request):
    
    
    #""" This function scans the database for profiles that need to be fixed
    #"""
    #PAGESIZE = 200 # don't make this much more than 100 or we start overusing memory and get errors
    
    ## Note: to use cursors, filter parameters must be the same for all queries. 
    ## This means that the cutoff_time must be remain constant as well (confused me for a few hours while figuring out
    ## why the code wasn't working).
    
    
    #try:
        
        #batch_cursor = None
        
        #if request.method == 'POST':
            #batch_cursor = request.POST.get('batch_cursor',None)          
            
        #generated_html = 'Updating InitiateContact objects:<br><br>'
        
        #logging.info("Paging new page with cursor %s" % batch_cursor)
                

        #order_by = "__key__"
        #query = models.InitiateContactModel.all(keys_only = True).order(order_by)            
                   
        #if batch_cursor:
            #query.with_cursor(batch_cursor)
                                   
        #object_batch_keys = query.fetch(PAGESIZE)
                
        #if not object_batch_keys:
            ## there are no more objects - break out of this function.
            #info_message = "No more objects found - Exiting function<br>\n"
            #logging.info(info_message)
            #return http.HttpResponse(info_message)

        #for initiate_contact_model_key in object_batch_keys:  
            #try:
                #assert(initiate_contact_model_key)
                #taskqueue.add(queue_name ="deferred-queue", url= '/rs/admin/deferred_fix_initiate_contact_model/', 
                              #params = {'initiate_contact_model_key' : initiate_contact_model_key})
            #except:
                #error_reporting.log_exception(logging.critical)  
                
        ## queue up more jobs
        #batch_cursor = query.cursor()
        #path = request.path_info
        #taskqueue.add(queue_name = 'background-processing-queue', url=path, params={'batch_cursor': batch_cursor})

        #return http.HttpResponse(generated_html)
    #except:
        #error_reporting.log_exception(logging.critical)
        #return http.HttpResponseServerError()

    
#def batch_fix_empty_checkboxes(request):

    
    #""" This function scans the database for profiles that need to be fixed
    #"""
    #PAGESIZE = 100 # don't make this much more than 100 or we start overusing memory and get errors
    
    ## Note: to use cursors, filter parameters must be the same for all queries. 
    ## This means that the cutoff_time must be remain constant as well (confused me for a few hours while figuring out
    ## why the code wasn't working).
    
    
    #try:
        
        #batch_cursor = None
        
        #if request.method == 'POST':
            #batch_cursor = request.POST.get('batch_cursor',None)          
            
        #generated_html = 'Updating userobjects:<br><br>'
        
        #logging.info("Paging new page with cursor %s" % batch_cursor)
                
        #query_filter_dict = {}    

        #query_filter_dict['user_is_marked_for_elimination = '] = False
        
        #order_by = "__key__"
        
        #query = UserModel.all().order(order_by)
        #for (query_filter_key, query_filter_value) in query_filter_dict.iteritems():
            #query = query.filter(query_filter_key, query_filter_value)

 
        #if batch_cursor:
            #query.with_cursor(batch_cursor)
                                   
        #userobject_batch = query.fetch(PAGESIZE)
                
        #if not userobject_batch:
            ## there are no more objects - break out of this function.
            #info_message = "No more objects found - Exiting function<br>\n"
            #logging.info(info_message)
            #return http.HttpResponse(info_message)

        #for userobject in userobject_batch:  
            #try:
                #info_message = "**Checking %s userobject<br>\n" % userobject.username
                #logging.info(info_message)   
                #is_dirty = False

                #if not userobject.entertainment:
                    #userobject.entertainment = ["prefer_no_say"]
                    #is_dirty = True
                #if not userobject.athletics:
                    #userobject.athletics = ["prefer_no_say"]
                    #is_dirty = True
                    
                #if is_dirty:
                    #info_message = "** Writing %s userobject<br>\n" % userobject.username
                    #logging.info(info_message)                    
                    
                    #utils.put_userobject(userobject)
                    
            #except:
                #error_reporting.log_exception(logging.critical)  
                
        ## queue up more jobs
        #batch_cursor = query.cursor()
        #path = request.path_info
        #taskqueue.add(queue_name = 'background-processing-queue', url=path, params={'batch_cursor': batch_cursor})

        #return http.HttpResponse(generated_html)
    #except:
        #error_reporting.log_exception(logging.critical)
        #return http.HttpResponseServerError()
        



   
#def batch_create_username_combinations_list(request):

    
    #""" This function scans the database for profiles that need to be fixed
    #"""
    #PAGESIZE = 100 # don't make this much more than 100 or we start overusing memory and get errors
    
    ## Note: to use cursors, filter parameters must be the same for all queries. 
    ## This means that the cutoff_time must be remain constant as well (confused me for a few hours while figuring out
    ## why the code wasn't working).
    
    
    #try:
        
        #batch_cursor = None
        
        #if request.method == 'POST':
            #batch_cursor = request.POST.get('batch_cursor',None)          
            
        #generated_html = 'Updating userobjects:<br><br>'
        
        #logging.info("Paging new page with cursor %s" % batch_cursor)
                
        #query_filter_dict = {}    

        #query_filter_dict['user_is_marked_for_elimination = '] = False
        
        #order_by = "__key__"
        
        #query = UserModel.all().order(order_by)
        #for (query_filter_key, query_filter_value) in query_filter_dict.iteritems():
            #query = query.filter(query_filter_key, query_filter_value)

 
        #if batch_cursor:
            #query.with_cursor(batch_cursor)
                                   
        #userobject_batch = query.fetch(PAGESIZE)
                
        #if not userobject_batch:
            ## there are no more objects - break out of this function.
            #info_message = "No more objects found - Exiting function<br>\n"
            #logging.info(info_message)
            #return http.HttpResponse(info_message)

        #for userobject in userobject_batch:  
            #try:
                #info_message = "**Checking %s userobject<br>\n" % userobject.username
                #logging.info(info_message)   
                #is_dirty = False

                #userobject.username_combinations_list = utils.get_username_combinations_list(userobject.username)
                #is_dirty = True
        
                #info_message = "** Writing %s userobject<br>\n" % userobject.username
                #logging.info(info_message)                    
                 
                #utils.put_userobject(userobject)
                    
            #except:
                #error_reporting.log_exception(logging.critical)  
                
        ## queue up more jobs
        #batch_cursor = query.cursor()
        #path = request.path_info
        #taskqueue.add(queue_name = 'background-processing-queue', url=path, params={'batch_cursor': batch_cursor})

        #return http.HttpResponse(generated_html)
    #except:
        #error_reporting.log_exception(logging.critical)
        #return http.HttpResponseServerError()
        