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
from constants import offset_values, ABOUT_USER_MIN_DESCRIPTION_LEN
from google.appengine.ext import db 
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
            lang_code = userobject.search_preferences2.lang_code
            
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
                
        message.html = ugettext("Friend welcome %(username)s %(app_name)s") % {
            'username': username, 'app_name' : settings.APP_NAME}
        
        # Now, get a description of what Friend is:
        template = loader.get_template("common_helpers/welcome_message.html")
        context = Context({'build_name': 'Friend',
                           'app_name' : 'FriendBazaar', 
                           'site_type' : ugettext('website to meet people, make friends, and to earn money'),
                           'num_messages_for_free_clients' : constants.MAX_EMAILS_PER_DAY,
                           'num_messages_for_vip_clients' : constants.vip_num_messages_allowed,
                           'num_chat_friends_for_free_clients' : constants.GUEST_NUM_CHAT_FRIEND_REQUESTS_ALLOWED,
                           'num_chat_friends_for_vip_clients' : constants.MAX_CHAT_FRIEND_REQUESTS_ALLOWED,
                           })
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

        query_filter_dict['is_real_user = '] = True
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
   


    
#from django.forms.fields import email_re
    
#def batch_fix(request):

    
    #""" This function scans the database for profiles that need to be fixed
    #"""
    #PAGESIZE = 20
    
    ## Note: to user cursors, filter parameters must be the same for all queries. 
    ## This means that the cutoff_time must be remain constant as well (confused me for a few hours while figuring out
    ## why the code wasn't working).
    
    #try:
        
        #batch_cursor = None
        
        #if request.method == 'POST':
            #batch_cursor = request.POST.get('batch_cursor',None)          
            
        #generated_html = 'Fixing profiles:<br><br>'
        
        #logging.info("Paging new page with cursor %s" % batch_cursor)
                
        #query_filter_dict = {}    

        #query_filter_dict['is_real_user = '] = True
        ##query_filter_dict['user_is_marked_for_elimination = '] = False
        ## NOTE: Normally this should be false .. .but we are running this over eliminated profiles
        ## so the profile summary can be displayed correctly in mailbox of other people
        ## (even though they are eliminated)
        #query_filter_dict['user_is_marked_for_elimination = '] = True
        
        #order_by = "-last_login_string"
        
        #query = UserModel.all().order(order_by)
        #for (query_filter_key, query_filter_value) in query_filter_dict.iteritems():
            #query = query.filter(query_filter_key, query_filter_value)

 
        #if batch_cursor:
            #query.with_cursor(batch_cursor)
                                   
        #userobject_batch = query.fetch(PAGESIZE)
        
        #match_GB_region = re.compile(r'EN,(.{1,3}),')
        
        #if not userobject_batch:
            ## there are no more objects - break out of this function.
            #info_message = "No more objects found - Exiting function<br>\n"
            #logging.info(info_message)
            #return http.HttpResponse(info_message)

        #for userobject in userobject_batch:  
            #try:
                #info_message = "Checking %s<br>\n" % userobject.username
                #generated_html += info_message
                #logging.debug(info_message)
    
                #languages_list = userobject.languages
                #dirty = False
                #for idx, language in enumerate(languages_list):
                    #if languages_list[idx] == "arab":
                        #dirty = True
                        #new_language = "arabic"
                        #info_message = "**Changing %s from %s to %s<br>\n" % (userobject.username, languages_list[idx], new_language)
                        #languages_list[idx] = "arabic"

                        #generated_html += info_message
                        #logging.debug(info_message)
                        
                #if userobject.country == "EN,,":
                    #dirty = True
                    #new_country = "GB,,"
                    #info_message = "**Changing %s to %s <br>\n" % (userobject.country, new_country)
                    #userobject.country = new_country
                    #generated_html += info_message
                    #logging.debug(info_message)
                    #match = match_GB_region.match(userobject.region)
                    #if match:
                        #region = match.group(1)
                        #new_region = "GB,%s," % region
                        #info_message = "**Changing '%s' to '%s' <br>\n" % (userobject.region, new_region)
                        #userobject.region = new_region
                        #generated_html += info_message
                        #logging.debug(info_message)      
                
                #if userobject.region == "ES,AD,":
                    #dirty = True
                    #new_country = "AD,,"
                    #new_region = "----"
                    #new_sub_region = "----"
                    
                    #info_message = "**Changing %s to country: %s regions: %s sub_region: %s" % (
                        #userobject.region, new_country, new_region, new_sub_region)
                    #userobject.country = new_country
                    #userobject.region = new_region
                    #userobject.sub_region = new_sub_region
                    #generated_html += info_message
                    #logging.debug(info_message)  
                    
                    
                #if dirty:
                    #info_message = "**Writing %s userobject<br>\n" % userobject.username
                    #generated_html += info_message
                    #logging.info(info_message)     
                    #userobject.languages = languages_list
                    #utils.put_userobject(userobject)
                    
                ##sp_dirty = False
                ##search_preferences2 = userobject.search_preferences2
                
                ##if search_preferences2.sex == 'dont_care':
                    ##sp_dirty = True
                    ##search_preferences2.sex = '----'
                    ##info_message = "**Changing search_preferences2.sex from dont_care to ----"
                    ##generated_html += info_message
                    ##logging.debug(info_message)  
                    
                ##if search_preferences2.relationship_status == 'dont_care':
                    ##sp_dirty = True
                    ##search_preferences2.relationship_status = '----'
                    ##info_message = "**Changing search_preferences2.relationship_status from dont_care to ----"
                    ##generated_html += info_message
                    ##logging.debug(info_message)                      
                    
                ##if search_preferences2.country == 'dont_care':
                    ##sp_dirty = True
                    ##search_preferences2.country = '----'
                    ##info_message = "**Changing search_preferences2.country from dont_care to ----"
                    ##generated_html += info_message
                    ##logging.debug(info_message)    
                    
                ##if search_preferences2.region == 'dont_care':
                    ##sp_dirty = True
                    ##search_preferences2.region = '----'
                    ##info_message = "**Changing search_preferences2.region from dont_care to ----"
                    ##generated_html += info_message
                    ##logging.debug(info_message)    
                    
                ##if search_preferences2.sub_region == 'dont_care':
                    ##sp_dirty = True
                    ##search_preferences2.sub_region = '----'
                    ##info_message = "**Changing search_preferences2.sub_region from dont_care to ----"
                    ##generated_html += info_message
                    ##logging.debug(info_message)    
                    
                ##if search_preferences2.age == 'dont_care':
                    ##sp_dirty = True
                    ##search_preferences2.age = '----'
                    ##info_message = "**Changing search_preferences2.age from dont_care to ----"
                    ##generated_html += info_message
                    ##logging.debug(info_message)                                                     
                    
                    
                ##if search_preferences2.preference == 'dont_care':
                    ##sp_dirty = True
                    ##search_preferences2.preference = '----'
                    ##info_message = "**Changing search_preferences2.preference from dont_care to ----"
                    ##generated_html += info_message
                    ##logging.debug(info_message)   
                    
                ##if sp_dirty:
                    ##info_message = "**Writing search_preferences2 object for %s<br>" % userobject.username
                    ##generated_html += info_message
                    ##logging.info(info_message)                       
                    
                    ##search_preferences2.put()
                    
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

#def batch_fix(request):
    
    #from appengine_django.sessions.models import Session
    
    #""" Code to delete all of the "Session" objects from the datastore - they have been replaced by the new
        #session handling code, which stores data in the "SessionModel" objects."""

    #try:
        #msg = "Starting code to remove Session entries from datastore"
        #logging.debug(msg)        
        
        #q = db.Query(Session, keys_only=True)
        #results = q.fetch(500)
        #len_results = len(results)
        
        #if len_results:
            #db.delete(results)
           
            #msg = "Deleted %s Session entries from datastore on this pass" % len_results
            #logging.debug(msg)
            #path = request.path_info
            #time.sleep(0.1) # just in case it takes a few milliseconds for the DB to get updated
            #taskqueue.add(queue_name = 'background-processing-queue', url=path)
        #else:
            #msg = "No more entries to delete"
            #logging.debug(msg)
            #return http.HttpResponse(msg)

        #return http.HttpResponse("Seems to be working")
    #except:
        #error_reporting.log_exception(logging.critical)
        #return http.HttpResponseServerError()
   
 

import login_utils
def batch_fix_unique_last_login(request):

    
    """ This function scans the database for profiles that need to be fixed
    """
    PAGESIZE = 100 # don't make this much more than 100 or we start overusing memory and get errors
    
    # Note: to use cursors, filter parameters must be the same for all queries. 
    # This means that the cutoff_time must be remain constant as well (confused me for a few hours while figuring out
    # why the code wasn't working).
    
    
    try:
        
        batch_cursor = None
        
        if request.method == 'POST':
            batch_cursor = request.POST.get('batch_cursor',None)          
            
        generated_html = 'Updating userobjects:<br><br>'
        
        logging.info("Paging new page with cursor %s" % batch_cursor)
                
        query_filter_dict = {}    

        query_filter_dict['is_real_user = '] = True
        query_filter_dict['user_is_marked_for_elimination = '] = False
        
        order_by = "__key__"       
        
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
                info_message = "**Checking %s userobject<br>\n" % userobject.username
                logging.info(info_message)     
                (userobject.unique_last_login, userobject.unique_last_login_offset_ref) = \
                 login_utils.get_or_create_unique_last_login(userobject, userobject.username)
                utils.put_userobject(userobject)
                info_message = "**Wrote %s userobject<br>\n" % userobject.username
                logging.info(info_message)   
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
    
    
def deferred_copy_have_had_contact(request):
    
    try:
        have_had_contact_key = None
        if request.method == 'POST':
            have_had_contact_key = request.POST.get('have_had_contact_key',None) 
        if not have_had_contact_key:
            error_reporting.log_exception(logging.critical)
            return http.HttpResponse("Unknown Error")
            
        info_message = "**Copying HaveSentMessages %s object<br>\n" % have_had_contact_key
        logging.debug(info_message)     
                        
        myobject = db.get(have_had_contact_key)
        
        if myobject.copied_to_users_have_sent_messages_model != "ready_for_hr_datastore_v7" and \
           myobject.copied_to_users_have_sent_messages_model != "copied_to_hr_datastore_v7":
            
            try:
                owner_key = myobject.owner_ref.key()
                other_key = myobject.other_ref.key()
            
                have_sent_messages_object = utils.get_have_sent_messages_object(owner_key, other_key, create_if_does_not_exist = True)
           

                klass = myobject.__class__
                props = dict((k, v.__get__(myobject, klass)) for k, v in klass.properties().iteritems())
                for k in props.keys():
                    setattr(have_sent_messages_object, k, getattr(myobject, k))

                    
                info_message = "**Writing have_sent_messages_object %s object<br>\n" % str(have_sent_messages_object.key())
                logging.debug(info_message)     
    
                have_sent_messages_object.put()
                myobject.copied_to_users_have_sent_messages_model = "copied_to_hr_datastore_v7"
                myobject.put()
            
            except:
                error_message = "have_had_contact = %s\nmodel = %s" % (have_had_contact_key, myobject)
                error_reporting.log_exception(logging.critical, error_message = error_message) 
                # we continue processing - this have_sent_messages object cannot be reproduced and is now lost
                return http.HttpResponse("Un-fixable error")
   
    except :
        error_reporting.log_exception(logging.critical) 
        return http.HttpResponseServerError()
    
    return http.HttpResponse("OK")
        
    
import datetime
def write_mail_txn(myobject, props, text):
    
    try:
        info_message = "**Considering copying MailMessageModel %s object<br>\n" % str(myobject.key())
        logging.debug(info_message)     
                        

            
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
            logging.debug(info_message)
            return "copied_to_hr_datastore_v7"
        else:
            return "previously_copied_v7"


    except:
        error_reporting.log_exception(logging.critical) 
        return None
        
        
def deferred_copy_mailbox_model(request):
    
    try:
        mailbox_model_key = None
        if request.method == 'POST':
            mailbox_model_key = request.POST.get('mailbox_model_key',None) 
        if not mailbox_model_key:
            error_reporting.log_exception(logging.critical, request = request)
            return http.HttpResponse("Unknown Error")      
        
        myobject = db.get(mailbox_model_key)
        
        
        #if myobject.copied_to_mail_message_model != "ready_for_hr_datastore_v7" and \
           #myobject.copied_to_mail_message_model != "copied_to_hr_datastore_v7" and \
           #myobject.copied_to_mail_message_model != "previously_copied_v7":
            
        try:
            klass = myobject.__class__
            props = dict((k, v.__get__(myobject, klass)) for k, v in klass.properties().iteritems())
            copied_string = db.run_in_transaction_custom_retries(10, write_mail_txn, myobject, props,  myobject.m_text_ref.text)       
            #if copied_string:
                #myobject.copied_to_mail_message_model = copied_string
                #myobject.put()
        except:
            error_message = "mailbox_model_key = %s\nmailbox model = %s" % (mailbox_model_key, myobject)
            error_reporting.log_exception(logging.critical, error_message = error_message) 
            # We continue processing -- this message is permanently lost .. 
            return http.HttpResponseServerError("Error")
            
    except :
        error_reporting.log_exception(logging.critical) 
        return http.HttpResponseServerError("Error")
    
    return http.HttpResponse("OK")
               
        
def deferred_fix_initiate_contact_model(request):
    
    try:
        initiate_contact_model_key = None
        if request.method == 'POST':
            initiate_contact_model_key = request.POST.get('initiate_contact_model_key',None) 
        if not initiate_contact_model_key:
            error_reporting.log_exception(logging.critical, request = request)
            return http.HttpResponse("Unknown Error")      
        
        myobject = db.get(initiate_contact_model_key)
        
        viewer_userobject_key = myobject.viewer_profile.key()
        display_userobject_key = myobject.displayed_profile.key()
        correct_key_name = str(viewer_userobject_key) + str(display_userobject_key) 
        

        original_key_name = myobject.key().id_or_name()
        logging.debug("Checking initiate_contact_model with key %s into new key %s" % (original_key_name, correct_key_name))

        if original_key_name != correct_key_name:
            # we need to copy this object into a new object with the correct key name        
            logging.info("**Copying initiate_contact_model with key %s into new key %s" % (original_key_name, correct_key_name))

            try:
                klass = myobject.__class__
                props = dict((k, v.__get__(myobject, klass)) for k, v in klass.properties().iteritems())
                correct_initiate_contact_key = db.Key.from_path('InitiateContactModel', correct_key_name)
                initiate_contact_object = models.InitiateContactModel(key = correct_initiate_contact_key,
                                                                      displayed_profile = display_userobject_key, 
                                                                      viewer_profile = viewer_userobject_key)
            
                for k in props.keys():
                    setattr(initiate_contact_object, k, getattr(myobject, k))
                
                    
                logging.info("**Writing key %s\nobject %s\n" % (initiate_contact_object.key().id_or_name(), initiate_contact_object))                    
                initiate_contact_object.put()
                
                logging.info("**Deleting key %s\nobject %s\n" % (myobject.key().id_or_name(), myobject))
                myobject.delete()
                
                
            except:
                error_message = "initiate_contact_model_key = %s\n initiate_contact_model = %s" % (initiate_contact_model_key, myobject)
                error_reporting.log_exception(logging.critical, error_message = error_message) 
                # We continue processing -- this message is permanently lost .. 
                return http.HttpResponse("Un-fixable error")
            
    except :
        error_reporting.log_exception(logging.critical) 
        return http.HttpResponseServerError()
    
    return http.HttpResponse("OK")


    
def batch_fix_initiate_contact_model(request):
    
    
    """ This function scans the database for profiles that need to be fixed
    """
    PAGESIZE = 200 # don't make this much more than 100 or we start overusing memory and get errors
    
    # Note: to use cursors, filter parameters must be the same for all queries. 
    # This means that the cutoff_time must be remain constant as well (confused me for a few hours while figuring out
    # why the code wasn't working).
    
    
    try:
        
        batch_cursor = None
        
        if request.method == 'POST':
            batch_cursor = request.POST.get('batch_cursor',None)          
            
        generated_html = 'Updating InitiateContact objects:<br><br>'
        
        logging.info("Paging new page with cursor %s" % batch_cursor)
                

        order_by = "__key__"
        query = models.InitiateContactModel.all(keys_only = True).order(order_by)            
                   
        if batch_cursor:
            query.with_cursor(batch_cursor)
                                   
        object_batch_keys = query.fetch(PAGESIZE)
                
        if not object_batch_keys:
            # there are no more objects - break out of this function.
            info_message = "No more objects found - Exiting function<br>\n"
            logging.info(info_message)
            return http.HttpResponse(info_message)

        for initiate_contact_model_key in object_batch_keys:  
            try:
                assert(initiate_contact_model_key)
                taskqueue.add(queue_name ="deferred-queue", url= '/rs/admin/deferred_fix_initiate_contact_model/', 
                              params = {'initiate_contact_model_key' : initiate_contact_model_key})
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

        #query_filter_dict['is_real_user = '] = True
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
                #logging.debug(info_message)   
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
        

    
    
def batch_fix_remove_all_users_with_given_ip_or_name(request, ip_to_remove = None, name_to_remove = None, reason_for_removal = 'terms'):

    
    """ This function scans the database for profiles that need to be fixed
    """
    PAGESIZE = 100 # don't make this much more than 100 or we start overusing memory and get errors
    
    # Note: to use cursors, filter parameters must be the same for all queries. 
    # This means that the cutoff_time must be remain constant as well (confused me for a few hours while figuring out
    # why the code wasn't working).
    
    
    try:
        
        batch_cursor = None
        
        if request.method == 'POST':
            batch_cursor = request.POST.get('batch_cursor',None)          
            
        generated_html = 'Updating userobjects:<br><br>'
        
        logging.info("Paging new page with cursor %s" % batch_cursor)
                
        query_filter_dict = {}    
        
        if not (reason_for_removal == "scammer" or reason_for_removal == "terms" or reason_for_removal == "fake"):
            return http.HttpResponse("Called with incorrect URL")

        if ip_to_remove:
            query_filter_dict['registration_ip_address'] = ip_to_remove
        elif name_to_remove:
            query_filter_dict['username'] = name_to_remove.upper()
        else:
            return http.HttpResponse("Called with incorrect URL")
        
        query = UserModel.all()
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
                info_message = "** Eliminating %s userobject<br>\n" % userobject.username
                generated_html += info_message
                logging.info(info_message)                    
                login_utils.delete_or_enable_account_and_generate_response(
                    request, userobject, delete_or_enable = "delete", reason_for_profile_removal = reason_for_removal)
                    
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

        #query_filter_dict['is_real_user = '] = True
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
                #logging.debug(info_message)   
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
        