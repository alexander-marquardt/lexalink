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


import re, datetime

from os import environ
import exceptions

from google.appengine.ext import ndb 
from google.appengine.api import mail
from google.appengine.api import taskqueue
from google.appengine.datastore.datastore_query import Cursor

from django.utils.encoding import smart_unicode
from django import http
from django.core.validators import email_re

import settings, localizations, urllib

from django.utils import translation
from django.utils.translation import ugettext, ungettext

from models import UserModel
from utils import return_time_difference_in_friendly_format, put_userobject
from utils import requires_login

import search_results, constants
import forms, utils, utils_top_level
import logging, error_reporting
import mailbox, store_data, user_profile_details, rendering
import html2text
import models


from google.appengine.api.datastore_errors import BadArgumentError

def footer_common():
    
    footer_html =  u"<p><p>%s" % ugettext("Cheers")
    footer_html += u"<p><a href=http://%(app_name)s.com>%(app_name)s.com</a>" % {'app_name': settings.APP_NAME }    
    return footer_html

def text_for_footer_on_registration_email(remoteip):

    footer_html = footer_common()
    footer_html += u"<p><p>* %s<br><br><br>" % ugettext("This account has been requested from the IP address: %(remoteip)s.") %\
                                                {'remoteip' : remoteip }     
    return footer_html

def text_for_footer_on_information_request_email(remoteip):

    footer_html = footer_common()
    footer_html += u"<p><p>* %s<br><br><br>" % ugettext("Someone with the IP address: %(remoteip)s has requested this.") %\
                                                {'remoteip' : remoteip }     
    
    return footer_html

def link_to_build():
    return "<a href=http://%(app_name)s.com>%(app_name)s.com</a> " % {'app_name' : settings.APP_NAME}


def send_generic_email_message(request):
       
    # Sends an email that allows the user to confirm their account
    #
    # Important: This is called from the task-queue, and therefore the language and other information related to the
    # user must be passed in, either in the POST (as is currently done), or on the command line.
    previous_language = translation.get_language() # remember the original language, so we can set it back when we finish 
    info_message = ''
    try:   
        usernmae = message_html = email_address = lang_code =  None
        if request.method == 'POST':
            username = request.POST.get('username', None)
            email_address = request.POST.get('email_address', None)
            subject = request.POST.get('subject', None)
            lang_code = request.POST.get('lang_code', None)
            message_html = request.POST.get('message_html',None)
         
        if not username or not email_address or not subject or not lang_code or not message_html:    
            error_message = "username: %s\nemail_address: %s\nsubject: %s\nlang_code: %s\nmessage_html: %s" % (\
                username, email_address, subject, lang_code, message_html)
            error_reporting.log_exception(logging.critical, error_message = error_message)   
            # return a non-errorr http response, so that this will not be re-queued -- this error will not resolve itself.
            return http.HttpResponse(error_message)
        
        # set the language to be the users preferred language
        translation.activate(lang_code)
        
        message = mail.EmailMessage(sender= constants.sender_address,
                                    subject=subject)
        
        message.to = u"%s <%s>" % (username, email_address)
        
        
        message.html = message_html
            
        message.body = html2text.html2text(message.html) 
        info_message = u"%s\n%s\n%s\n" % (message.sender, message.to, message.body)
        
        message.send()

        logging.info(info_message)
        return_val =  http.HttpResponse(info_message)

    except:
        error_message = u"Unable to send verification email. info_message: %s" % info_message
        error_reporting.log_exception(logging.critical, error_message = error_message)
        return_val =  http.HttpResponseServerError(error_message)    

    finally:
        # activate the original language -- not sure if this is really necessary, but is 
        # somewhat safer (until I fully understand how multiple processes in a single thread are interacting)
        translation.activate(previous_language)
        
    return return_val


#def send_confirmation_email(request):
    
    ## sends an email to the user after their profile/email address has been successfully registered.
    #previous_language = translation.get_language() # remember the original language, so we can set it back when we finish     
    
    #try:
        #uid =  email_address = remoteip = None
   
        #if request.method == 'POST':
            #uid = request.POST.get('uid',None)
            #email_address = request.POST.get('email_address', None)
            #remoteip = request.POST.get('remoteip', None)
            #lang_code = request.POST.get('lang_code', None)


        #if not uid or not email_address or not remoteip or not lang_code:    
            #error_message = u"uid = %s email_address = %s remoteip = %s lang_code = %s" % (uid, email_address, remoteip, lang_code)
            #error_reporting.log_exception(logging.critical, error_message = error_message, request=request)   
            ## return a non-errorr http response, so that this will not be re-queued -- this error will not resolve itself.
            #return http.HttpResponse(error_message)  
            
        ## set the language to be the users preferred language
        #translation.activate(lang_code)        
                
        #try:
            #userobject = utils_top_level.get_object_from_string(uid)
            ## don't know how/why this can happen, but it may return a None object occasionally
            #assert(userobject != None)
        #except:
            #error_message = "Error getting userobject for: uid = %s" % (uid)
            #error_reporting.log_exception(logging.error, error_message = error_message, request = request)
            ## return a non-errorr http response, so that this will not be re-queued -- this error will not resolve itself.
            #return http.HttpResponse(error_message)
        
        
        #username = userobject.username
        #logging.info("Preparing to send confirmation email to %s" % username)
        
        #message = mail.EmailMessage(sender=constants.sender_address,
                                    #subject=ugettext("Confirmation of your email address"))
        
        #message.to = u"%s <%s>" % (username, email_address)
                
        #message.html = u"<p>%s," % ugettext("Hello %(username)s") % {'username': username}
        #message.html += u"<p>%s." % ugettext("Your account has been correctly registered")
        #message.html += text_for_footer_on_registration_email(remoteip)  
        #message.html += get_notification_control_html(userobject)
        #message.body = html2text.html2text(message.html) 
        
        #message.send()
        
        #info_message = u"%s\n%s\n%s\n" % (message.sender, message.to, message.body)
        #logging.info(info_message)
        
        #return_val = http.HttpResponse(info_message)
    
    #except:
        #error_message = "Unknown error (message not configured correctly)"
        #error_reporting.log_exception(logging.error, error_message = error_message)
        #return_val = http.HttpResponseServerError(error_message)    

    #finally:
        ## activate the original language -- not sure if this is really necessary, but is 
        ## somewhat safer (until I fully understand how multiple processes in a single thread are interacting)
        #translation.activate(previous_language)
        
    #return return_val

    
    
def send_password_reset_email(userobject, new_password):
    # NOTE: if this is placed into the task queue, then the IP must manually be passed in.
    # Additionally, lang_code would have to be set to the correct setting since this will not be
    # run from the users session.
    previous_language = translation.get_language() # remember the original language, so we can set it back when we finish 
    try:
        search_preferences = userobject.search_preferences2.get()
        translation.activate(search_preferences.lang_code)        

        remoteip  = environ['REMOTE_ADDR']        
        
        message = mail.EmailMessage(sender=constants.sender_address,
                                    subject=ugettext("New password"))
        username = userobject.username
        email_address = userobject.email_address
        message.to = u"%s <%s>" % (username, email_address)
        
        message.html = u"<p>%s," % ugettext("Hello %(username)s") % {'username': username}
        message.html += u"<p>%s" % ugettext("Your new password is: %(new_password)s") % {'new_password' : new_password}
        message.html += u"<p>%s. " % ugettext("If you have not requested a new password, \
you can continue to use %(app_name)s with your current password and the new \
password will be invalidated the next time you login") % {'app_name' : settings.APP_NAME }
        message.html += u"%s. " % ugettext("If you decide to use the new password, \
it is recomendable that you change it in the administrative section of your profile")
        message.html += text_for_footer_on_information_request_email(remoteip)
        message.html += get_notification_control_html(userobject)
        message.body = html2text.html2text(message.html)  
        
        try:
            message.send()
        except:
            message.send()
        
        info_message = u"%s\n%s\n%s\n" % (message.sender, message.to, message.body)
        logging.info(info_message)
    except:
        try:
            error_message = u"Unable to send password reset email\n\nUser: %s\nEmail: %s\n" % (userobject.username, email_address)
            error_reporting.log_exception(logging.error, error_message = error_message)
        except:
            error_reporting.log_exception(logging.critical)
            
    finally:
        # activate the original language -- not sure if this is really necessary, but is 
        # somewhat safer (until I fully understand how multiple processes in a single thread are interacting)
        translation.activate(previous_language)

        

def delete_userobject_confirmation(request, username, hash_of_creation_date):
    # This function asks the user to confirm that they wish to delete their profile
    
    previous_language = translation.get_language() # remember the original language, so we can set it back when we finish 
    try:
    
        userobject = utils.get_active_userobject_from_username(username)
        
        if userobject :
            if hash_of_creation_date == userobject.hash_of_creation_date[:constants.EMAIL_OPTIONS_CONFIRMATION_HASH_SIZE]:
            
                translation.activate(userobject.search_preferences2.get().lang_code)   
                
                generated_html = u"""
                <script type="text/javascript" language="javascript">
                
                // script to handle the button submission, and re-direct to the correct pages
                $(document).ready(function(){
                    $("#id-cancel-delete_profile").click(function(){
                        self.location = "/";
                    });
                });
                </script>
        
                <div class="cl-text-large-format ">"""
                
                button_text = ugettext("Yes, I am sure I want to eliminate the profile of %(username)s") % {'username' : username }
                
                generated_html += u"<p><p>%s," % ugettext("Hello %(username)s") % {'username': username}
                generated_html += u"<p><p>%s<p>" % ugettext("Are you sure you want to eliminate your account?")
                href = "/rs/do_delete/%(username)s/%(hash_of_creation_date)s/" % {'username':username, 'hash_of_creation_date': hash_of_creation_date,}
                generated_html += u"""<form action="%(href)s" method="post" rel="form-address:%(href)s">
                <input type="submit" value="%(button_text)s" class="cl-submit">
                <input type=button class="cl-cancel" id="id-cancel-delete_profile" value="Cancelar">
                </form>
                </div>
                """ % {'href': href, 'button_text' : button_text }
            else:
                generated_html = ugettext("Error - Not authorized")
                error_message = "Error: unable to show account *delete confirmation* to username: %s hash_of_creation_date: %s" % (
                    username, hash_of_creation_date)
                error_reporting.log_exception(logging.error, error_message=error_message)  
        else:
            generated_html = """
            <div class="cl-text-large-format ">
            <p><p>%s
            </div>
            """ % ugettext("Nick: %(username)s not found - have you already deleted it?") % {'username' : username }
        
        # Note: we render the userobject, even though the user is not logged in -- this is not a security risk, since they cannot 
        # view emails or send messages etc. 
        return rendering.render_main_html(request, generated_html,
                                          link_to_hide = '', hide_page_from_webcrawler = True, 
                                          hide_why_to_register = True)

    except:
        error_reporting.log_exception(logging.error)

    finally:
        translation.activate(previous_language)
        
def change_notification_settings(request, subscription_option, username, hash_of_creation_date):
    # This function changes the user profile settings to the value passed in subscription_option for email settings.
    # Note: we just use the creation_date_string as a "secret" value that is not publicly displayed, and
    # therefore provides some security that this request is coming from the owner of the account.
    
    def userobject_txn(owner_uid, subscription_option):
        # run update of user subscription option in transaction to prevent conflicts with other writes to the userobject.
        userobject =  utils_top_level.get_object_from_string(owner_uid)
        userobject.email_options[0] = subscription_option
        put_userobject(userobject)
        return userobject

    previous_language = translation.get_language() # remember the original language, so we can set it back when we finish 

    try:
        # make sure that the subscription_option that is passed in is a valid option
        userobject = utils.get_active_userobject_from_username(username)
        translation.activate(userobject.search_preferences2.get().lang_code)
        
        # get the user language settings from the userobject
        try:
            # get lang_idx from the userobject
            lang_idx = localizations.input_field_lang_idx[userobject.search_preferences2.get().lang_code]
        except:
            # otherwise, get it from the request 
            lang_idx = localizations.input_field_lang_idx[request.LANGUAGE_CODE]
            
        options_dict = user_profile_details.UserProfileDetails.checkbox_options_dict['email_options'][lang_idx]
        
        if subscription_option in options_dict and userobject and\
           hash_of_creation_date == userobject.hash_of_creation_date[:constants.EMAIL_OPTIONS_CONFIRMATION_HASH_SIZE]:
            
            # update userobject to contain the newly selected option
            userobject = ndb.transaction(lambda: userobject_txn(userobject.key.urlsafe(), subscription_option))
            
            # update the when_to_send_next_notification to reflect the newly selected value in both the mail and contact
            # counter objects
            
            hours_between_notifications = utils.get_hours_between_notifications(userobject, constants.hours_between_message_notifications)
            ndb.transaction (lambda: utils.when_to_send_next_notification_txn(userobject.unread_mail_count_ref, hours_between_notifications))
            hours_between_notifications = utils.get_hours_between_notifications(userobject, constants.hours_between_new_contacts_notifications)
            ndb.transaction (lambda: utils.when_to_send_next_notification_txn(userobject.new_contact_counter_ref, hours_between_notifications))
            
            option_in_current_language = options_dict[subscription_option]
            
            generated_html = u"<p><p><p>%s," % ugettext("Hello %(username)s") % {'username': username}
            generated_html += u"<p>%s: " % ugettext("We have changed your notification options to")
            generated_html += u"""<strong><em>%(option)s</em></strong><p><p><p>%(link_to_build)s\
            """ % {'username':username, 'option': option_in_current_language, 'app_name': settings.APP_NAME,
                   'link_to_build': link_to_build()}
        else:
            generated_html = u"%s." % ugettext("Error: we have not been able to change the notification options for %(username)s") % {
                'username': username}
            generated_html += u"%s." % ugettext("You can change your notification settings by entering into %(link_to_build)s and directly \
modifying your profile") % {'link_to_build' : link_to_build() }
                        
            logging.warning("%s option: %s username: %s hash_of_creation_date: %s" % (generated_html, subscription_option, username, hash_of_creation_date))
    except:
        error_reporting.log_exception(logging.critical)
        generated_html = "Error - unable to update notification settings"
        
    finally:
        translation.activate(previous_language)
        
    # Note: we render the information, even though the user is not logged in -- this is not a security risk, since they cannot 
    # view emails or send messages etc. 
    return rendering.render_main_html(request, generated_html, link_to_hide = '', 
                                      hide_page_from_webcrawler = True, hide_why_to_register = True)


def get_notification_control_html(userobject):
    # generates the html that will be appended to user messages so that the user can change their notification settings.
    #
    # This might be called from the task queue, so the language must be explicitly looked up. 
    
    previous_language = translation.get_language() # remember the original language, so we can set it back when we finish    
    
    try:

        username = userobject.username
        email_address = userobject.email_address
        subscription_option = userobject.email_options[0]
        hash_of_creation_date = userobject.hash_of_creation_date[:constants.EMAIL_OPTIONS_CONFIRMATION_HASH_SIZE]
        assert(hash_of_creation_date)
        
        search_preferences = userobject.search_preferences2.get()
        lang_code = search_preferences.lang_code
        lang_idx = localizations.input_field_lang_idx[lang_code]
        translation.activate(lang_code)

        generated_html = ''
        
        choices_tuple_list = user_profile_details.UserProfileDetails.checkbox_fields['email_options']['choices']
        options_dict = user_profile_details.UserProfileDetails.checkbox_options_dict['email_options'][lang_idx]
        option_in_current_language = options_dict[subscription_option]
        
        generated_html += utils.html_to_request_new_password(email_address)
                
        generated_html += u"<strong>%s:</strong><br><br>" % ugettext("Email notification settings")
        generated_html += u"%s:" % ugettext("You have currently selected")
        generated_html += u'<strong>"%(current_option)s"</strong> ' % {'current_option': option_in_current_language }
        generated_html += u"%s " % ugettext('You can change this option by clicking on one of the options below, \
or by directly modifying "My profile" in')
        generated_html += link_to_build()
        generated_html += u".<ul>"
        
        option_count = 1
        for choices_tuple in choices_tuple_list:
            choice_key = choices_tuple[0]    
            option_in_current_language = choices_tuple[lang_idx + 1]
            option_href = u"http://%s.com/rs/cns/%s/%s/%s/" %(settings.APP_NAME, choice_key, username, hash_of_creation_date)
            
            generated_html += u"<li><a href = %s>%s %s:</a> %s</li>" % (option_href, ugettext("Option"), option_count,  option_in_current_language)
            option_count += 1
            
        generated_html += u"</ul><br><br>"
        
        would_you_like_to_eliminate_profile_text = "%s " % ugettext("Would you like to eliminate the profile of")
        generated_html += u"<strong>%s %s?</strong>" % (would_you_like_to_eliminate_profile_text, username)
        link_for_eliminate_profile = "<a href=http://www.%(app_name)s.com/rs/confirm_delete/%(username)s/%(hash_of_creation_date)s/>\
        %(here)s</a>" % {'app_name' : settings.APP_NAME, 'username' : username, 
                         'hash_of_creation_date': hash_of_creation_date, 'here': ugettext("Here")}
        generated_html += u"<ul><li>%(link)s %(you_can)s.<br><br></li></ul>" % {
            'link' : link_for_eliminate_profile, 'you_can' : ugettext("you can eliminate it")}
     
        
    except:
        error_reporting.log_exception(logging.critical)
        generated_html = 'Error'
        
    finally:
        translation.activate(previous_language)        
        
    return generated_html

def render_notification_control_html(request):
    # Test function, only used for displaying the resulting html. Assumes that we are logged in,
    # and will print information depending on the current language selection.
    
    generated_html = get_notification_control_html(utils_top_level.get_userobject_from_request(request))
    return http.HttpResponse(generated_html)
                                    
        
    
def send_new_message_notification_email(request):
    # This function will send an email the the user, to let them know the status of 
    # their messages, kisses, winks, and private access.
    # 
    # This function is called from the task queue, and therefore is called as a URL.     
    
    is_test_mode = False
    
    try:
        userobject = None
        uid = request.POST.get('uid', None)
        userobject = utils_top_level.get_object_from_string(uid) # if uid is not found or doesn't exist this will trigger an exception
        if  userobject.user_is_marked_for_elimination:
            # Not necessarily an error, since eliminated profiles can now receive winks, keys, etc. 
            # Instead of sending an email, just return with a standard (non-error) HttpResponse
            # so that this task doesn't get re-queued.
            error_message = u"cannot send emails to eliminated users"
            logging.info(error_message)
            return http.HttpResponse(error_message)
        
    except:
        # catch the exception so that it is not returned to the taskqueue handler (that would re-queue this request 
        # which is not desired)
        error_message = u"Error in retreiving userobject"
        error_reporting.log_exception(logging.critical, error_message = error_message, request = request)
        return http.HttpResponse(error_message)
    
    try:
        search_preferences = userobject.search_preferences2.get()
        lang_code = search_preferences.lang_code
    except:
        # can happen on old profiles that don't have search_preferences2 defined - need to run maintenance one
        # day to fix this.
        lang_code = "es"
        error_message = u"Error in retreiving lang_code -setting to es"
        error_reporting.log_exception(logging.critical, error_message = error_message, request = request)
    
    
    previous_language = translation.get_language()# remember the original language, so we can set it back when we finish         
    try:
        translation.activate(lang_code) # set to the language for the user that we are now mailing
        
        if settings.BUILD_NAME == "discrete_build" or settings.BUILD_NAME == "single_build" or \
           settings.BUILD_NAME == "lesbian_build" or settings.BUILD_NAME == "swinger_build":
            bar_color = ugettext("violet")
        elif  settings.BUILD_NAME == "gay_build":
            bar_color = ugettext("gray")
        elif settings.BUILD_NAME == "language_build" or settings.BUILD_NAME == "friend_build" or \
             settings.BUILD_NAME == "mature_build":
            bar_color = ugettext("green")
        else:
            raise Exception("Unknown build")        

        email_should_be_sent = False
        user_has_unread_messages = False
        
        # make sure that this user actually has an email address and that they have not eliminated their account
        error_message = ''
        if  userobject.user_is_marked_for_elimination:
            error_message = u"Attempting to send message to eliminated user %s" % userobject.username
        if not userobject.email_address_is_valid:
            error_message = u"Attempting to send message to user %s with invalid email" % userobject.username
        if error_message:
            # don't raise an exception, because we do not want this task to be automatically be re-queued
            error_reporting.log_exception(logging.critical, error_message = error_message)
            return http.HttpResponse(error_message)
    
        message_text = ''   

        # One of the following must be true, otherwise  - why are we in this function (if this error ever triggers, it is likely
        # that the when_to_send_next_notification not being synchronized with the when_to_send_next_notification_string values .
        # This can also (potentially) trigger if aser has instant notification settings set for "contacts" (winks etc.), and someone
        # quickly retracts the contact before the message is sent. - In fact, we intentionally add a small delay before sending a 
        # notification email so that this "error" condition can be caught here - and the user will not be notified.
        unread_mail_count_obj = userobject.unread_mail_count_ref.get()
        new_contact_counter_obj = userobject.new_contact_counter_ref.get()
        if unread_mail_count_obj.when_to_send_next_notification > datetime.datetime.now() and \
           new_contact_counter_obj.when_to_send_next_notification > datetime.datetime.now():
            error_message = 'Error on userobject %s\n\
            \tnew message notification time: %s and the string is: %s\n\
            \tnew contacts notification time: %s and the string is: %s\n\
            - NOT SENT' % (userobject.username, 
                           unread_mail_count_obj.when_to_send_next_notification, \
                           unread_mail_count_obj.when_to_send_next_notification_string,\
                           new_contact_counter_obj.when_to_send_next_notification,
                           new_contact_counter_obj.when_to_send_next_notification_string)
            error_reporting.log_exception(logging.warning, error_message=error_message)
            return http.HttpResponse(error_message)
        
        # make sure that the user has received a new message or contact since the last notification - otherwise, why are we in this function?
        if unread_mail_count_obj.num_new_since_last_notification == 0 and \
           new_contact_counter_obj.num_new_since_last_notification == 0:
            error_message =  'Error on userobject %s - new message notification is attempting to send email to a user who has not received any \
            messages or contacts since the last update - NOT SENT' % (userobject.username)
            error_reporting.log_exception(logging.critical, error_message = error_message)
            return http.HttpResponse(error_message)        
            
        
        # if the user has unread messages, we will prepare the message text that indicates that they have unread messages. 
        if unread_mail_count_obj.unread_contact_count:
            user_has_unread_messages = True
                    
            message_text += u"<p>%s!" % ungettext('You have <strong>%(num_mail)s new/unread message</strong> ',
                    'You have <strong>%(num_mail)s new/unread messages</strong>',
                    unread_mail_count_obj.unread_contact_count
            ) % {
                'num_mail': unread_mail_count_obj.unread_contact_count,
            }     
            

            
            message_text += u"<p>%s " % ugettext("You can read your messages after entering in")
            message_text += link_to_build()
            message_text += u"%s. " % ugettext('by clicking on "%(field)s" in the %(bar_color)s bar just below the logo of %(app_name)s') % {
                'field' : ugettext('Messages'), 'bar_color' : bar_color, 'app_name' : settings.APP_NAME}
            message_text += "%s.</p> " % ugettext('You can mark the new messages as "read" by opening (clicking on) each message, or \
by marking the checkbox beside multiple messages and clicking "Mark as read"')
            

            
        new_contact_counter_obj = userobject.new_contact_counter_ref.get()
                            
        new_kiss_count = new_contact_counter_obj.num_received_kiss_since_last_reset
        new_wink_count = new_contact_counter_obj.num_received_wink_since_last_reset
        new_key_count = new_contact_counter_obj.num_received_key_since_last_reset
        new_friend_request_count = new_contact_counter_obj.num_received_chat_friend_since_last_reset
        new_friend_connected_count = new_contact_counter_obj.num_connected_chat_friend_since_last_reset
        
        new_initiate_contact_bool = (new_kiss_count or new_wink_count or new_key_count or \
                                     new_friend_request_count or new_friend_connected_count)    
        
        if new_initiate_contact_bool:
            
            # Check if the first part of the message contains a notification about unread messages.
            if user_has_unread_messages:
                start_of_next_paragraph = u"<p>%s <strong>" % ugettext("Additionally, you have received")
            else:
                start_of_next_paragraph = u"<p>%s <strong>" % ugettext("You have received")     
                
            # we set this value up just in case email_should_be_sent is set to true (based on new messages OR
            # new initiate_contact items)
            message_text += start_of_next_paragraph
            
            initiate_contact_list = []

            initiate_contact_list.append(u" %d %s" %  (new_wink_count, constants.ContactIconText.plural_icon_name['wink']))
            if settings.BUILD_NAME != "language_build" and settings.BUILD_NAME != "friend_build":
                initiate_contact_list.append(u" %d %s" %  (new_kiss_count, constants.ContactIconText.plural_icon_name['kiss']))
            initiate_contact_list.append(u" %d %s" %  ( new_key_count, constants.ContactIconText.plural_icon_name['key']))
            initiate_contact_list.append(u" %d %s" %  ( new_friend_request_count, constants.ContactIconText.chat_friend_plural_text['request_received']))
            initiate_contact_list.append(u" %s %d %s" %  (ugettext("and"), new_friend_connected_count, constants.ContactIconText.chat_friend_plural_text['connected']))
            
            
            message_text += u",".join(initiate_contact_list)
            message_text += u"</strong>.</p>"
        
            message_text += u"<p>%s " % ugettext('You can see who has contacted you in %(link_to_build)s') % {
                'link_to_build' : link_to_build() }
            message_text +=   u"%s.</p>\n\n" % ugettext('by clicking on "%(field)s" in the %(bar_color)s bar just below the logo of %(app_name)s') % {
                'field' : ugettext('Contacts'), 'bar_color' : bar_color, 'app_name' : settings.APP_NAME}
            
            
        # Prepare the message 
        if user_has_unread_messages and new_initiate_contact_bool:
            message = mail.EmailMessage(sender=constants.sender_address,
                                    subject=ugettext("New messages and new contacts"))
        elif user_has_unread_messages:
            message = mail.EmailMessage(sender=constants.sender_address,
                                    subject=ugettext("New messages"))            
        elif new_initiate_contact_bool:
            message = mail.EmailMessage(sender=constants.sender_address,
                                subject=ugettext("New contacts"))    
        else:
            # there are *no* new unread messages or contacts - this is an error, and we should not be trying to send a notification
            # reset the notification settings so that this is not re-queued in the future.
            store_data.reset_new_contact_or_mail_counter_notification_settings(userobject.unread_mail_count_ref)        
            store_data.reset_new_contact_or_mail_counter_notification_settings(userobject.new_contact_counter_ref)            
            raise Exception("Unknown state in send_new_message_notification_email")
        
        message.html = u"<p>%s," % ugettext("Hello %(username)s") % {'username': userobject.username}
        message.html += "%(message_text)s<br>%(cheers)s<br>" % {'message_text' : message_text, 'cheers' : ugettext("Cheers")}
                                              
        message.html += u"Alex (%(support_email_address)s)<br>%(link_to_build)s<br><br><br><br>" % {
            'support_email_address' : constants.support_email_address,
            'app_name': settings.APP_NAME, 'link_to_build': link_to_build()}
        message.html += u"<p>%(notification_control)s" % {'notification_control': get_notification_control_html(userobject)}     
        
        userobject_key = userobject.key.urlsafe()
        

        
        if not is_test_mode:

            # This message will be sent to real users.
            message.to = u"%s <%s>" % (userobject.username, userobject.email_address)  
            
            # get the text-only version of the message for compatibility with non-html enabled mail readers.
            message.body = html2text.html2text(message.html) 
            
            message.send()

            logging.info("Successfully sent email to %s\n" % userobject.username)
        
            # don't update if "is_test_mode" since this is just a test run, and nothing
            # was really sent to the client.
            store_data.reset_new_contact_or_mail_counter_notification_settings(userobject.unread_mail_count_ref)        
            store_data.reset_new_contact_or_mail_counter_notification_settings(userobject.new_contact_counter_ref)
        else:
            error_message = "Running server with is_test_mode=True -- emails not being sent out. "
            error_reporting.log_exception(logging.error, error_message = error_message)
        
        # for debugging purposes return the message contents.
        # The message contents can be removed at some point in the future for better efficiency. 
        return_val = http.HttpResponse(message.html)

    except:
        error_message = "Error sending message to %s - Not sent" % userobject.username
        error_reporting.log_exception(logging.critical, error_message=error_message, request=request)
        # Do not return HttpResponseServerError because we don't want to re-queue. The construction of this function
        # means that (as long as the error occured before reseting the counters) the message will be automatically 
        # re-queued, since the when_to_send_next_notification time will have passed. 
        return_val =  http.HttpResponse(error_message)
    
    finally:
        translation.activate(previous_language)
        
    return return_val
    
def send_batch_email_notifications(request,  object_type, key_type_on_usermodel):
    
    """ This function scans the database for users who need to be notified of new messages or new contacts. 
    
    object_type is either : models.UnreadMailCount or models.CountInitiateContact:
    key_type_on_usermodel is either: models.UserModel.unread_mail_count_ref or models.UserModel.new_contact_counter_ref
    
    """
    PAGESIZE = 50
    
    # Note: to user cursors, filter parameters must be the same for all queries. 
    # This means that the cutoff_time must be remain constant as well (confused me for a few hours while figuring out
    # why the code wasn't working).
    
    try:
        
        batch_cursor = None
        cutoff_time = None        
        
        if request.method == 'POST':
            try:
                cursor_str = request.POST.get('batch_cursor', None)
                batch_cursor = Cursor(urlsafe = cursor_str) # this may generate an exception if the string is not formatted correctly
            except:
                error_reporting.log_exception(logging.critical, 
                                              error_message = "Unable to extract batch_cursor from POST. Set to None.")
                batch_cursor = None
                
            cutoff_time = request.POST.get('cutoff_time', None)
            

            
        if not cutoff_time:
            # only send messages who need to be send before "now".
            # make it a string so that it is compatible with the values that we receive in a POST (they come in as string)
            cutoff_time = str(datetime.datetime.now())
            
        generated_html = 'Emails queued for:<br><br>'
                
        q = object_type.query().order(object_type.when_to_send_next_notification_string)    
        
        # only send email messages to clients whose notification time has already passed.
        q = q.filter(object_type.when_to_send_next_notification_string <= cutoff_time)
        

        if batch_cursor:
            try:
                counter_object_batch, batch_cursor, get_more = q.fetch_page(PAGESIZE, start_cursor = batch_cursor )
            except BadArgumentError:
                # we will temporarily see this error when upgrading from db to ndb - this is due to the incompatible cursor
                # types. In this case, just get without the cursor and it should be OK for the next round of fetches.
                # This try/except can be removed after the transition to ndb is fully complete.
                error_reporting.log_exception(logging.critical, error_message = "*** cursor = %s" % batch_cursor)
                counter_object_batch, batch_cursor, get_more = q.fetch_page(PAGESIZE)
                
        else:
            counter_object_batch, batch_cursor, get_more = q.fetch_page(PAGESIZE)
        
        if not counter_object_batch:
            # there are no more objects - break out of this function.
            info_message = "No more counter objects found - Exiting function"
            return http.HttpResponse(info_message)

        for counter_object in counter_object_batch:  

            
            # the counter objects should have a one-to-one mapping to the userobjects that they are keeping track of .. therefore
            # we just do a reverse lookup on UserModel to that references the current counter_object, and get() 
            
            q = UserModel.query()
            q = q.filter(key_type_on_usermodel == counter_object.key)
            q_not_eliminated_user = q.filter(UserModel.user_is_marked_for_elimination == False)
            userobject = q_not_eliminated_user.get()
            
            if userobject and userobject.email_address_is_valid:
            
                try:   
                    try:
                        # If a user has never logged in since we added the lang_code to the search_preferences2, then
                        # they will not have a language code object. Eventually this exception handling can be removed.
                        search_preferences = userobject.search_preferences2.get()
                        lang_code = search_preferences.lang_code
                    except exceptions.AttributeError:
                        if search_preferences:
                            error_reporting.log_exception(logging.warning)
                            search_preferences.lang_code = 'es'
                            search_preferences.put()
                        else: 
                            error_reporting.log_exception(logging.critical, error_message = "search_preferences object not found")
                            
                        lang_code = "es"
                        
                    taskqueue.add(queue_name = 'mail-queue', url='/rs/admin/send_new_message_notification_email/', params = {
                        'uid': userobject.key.urlsafe(), 'lang_code': lang_code})
                    generated_html += "%s<br>" % (userobject.username)
                except:
                    error_message = "send_new_message_notification_email unexpected exception. userobject: %s" % (repr(userobject))
                    error_reporting.log_exception(logging.critical, error_message = error_message)
                    return http.HttpResponseServerError()
            else:
                if not userobject:
                    # check if the user has been marked for elimination. -- report as an warning for now, but later this can probably be removed
                    # the important thing is that eliminated users are also removed from the message queue. This is accomplished
                    # by the call to "reset_new_contact_or_mail_counter_notification_settings" which is called below.
                    q_eliminated_user = q.filter(UserModel.user_is_marked_for_elimination == True)
                    userobject = q_eliminated_user.get()
                    
                    if userobject: 
                        error_message = "User %s is marked for elimination but is in message queue\n\
                        userobject: %s\n\counter_object: %s\n" % (userobject.username, repr(userobject), repr(counter_object))
                        error_reporting.log_exception(logging.warning, error_message = error_message)
                    else:
                        error_message = "Userobject pointed to by counter is not valid\n\
                        counter_object KEY: %s. Obect: %s\n" % ( counter_object.key, counter_object)
                        error_reporting.log_exception(logging.critical, error_message = error_message)
                elif not userobject.email_address_is_valid:
                    error_message = "Userobject does have an email address\n\
                        userobject: %s\n\counter_object: %s\n" % (repr(userobject), repr(counter_object))
                    error_reporting.log_exception(logging.critical, error_message = error_message)
                else:
                    error_message = "send_new_message_notification_email unexpected exception. userobject: %s" % (repr(userobject))
                    error_reporting.log_exception(logging.critical, error_message = error_message)
                    return http.HttpResponseServerError()
                    
                # do not return an error http response from this, because we do not want to re-queue this task       
                store_data.reset_new_contact_or_mail_counter_notification_settings(counter_object.key) 
                
        # queue up more jobs
        if get_more:
            path = request.path_info
            taskqueue.add(queue_name = 'mail-queue', url=path, params={'batch_cursor': batch_cursor.urlsafe(), 'cutoff_time': cutoff_time})

        return http.HttpResponse(generated_html)
    
    except:
        error_reporting.log_exception(logging.critical)
        return http.HttpResponseServerError()
   
    
def batch_email_notification_launcher(request):
    # control task for queuing up batch notification jobs. This is called as a cron job (see cron.yaml for schedule)
    
    # Queue up the profiles that have new messages
    try:
        # queue emails to users that have a new message 
        taskqueue.add(queue_name = 'mail-queue', url='/rs/admin/email_new_message/')
        
        # Queue up the profiles that have new contacts (winks etc.). - if they 
        # recieved a message and were already notified, then by construction of the email routines, they will
        # not be double-notified.
        countdown_time = 5 * 60 # we wait for 5 minutes before running this job, to increase probability that the previous
                                 # task has completed and finished updating all of the notification status/trackers. 
        taskqueue.add(queue_name = 'mail-queue', countdown = countdown_time, url='/rs/admin/email_new_contacts/')
        
        return http.HttpResponse("batch emails launched OK")
    except:
        error_reporting.log_exception(logging.critical)
        return http.HttpResponseServerError()    
    
def send_admin_alert_email(message_content, subject, is_raw_text = False, to_address = constants.admin_address):
    # send a critical system status/warning message to the admin email address
    try:
        message = mail.EmailMessage(sender=constants.sender_address,
                                    subject=subject)
        message.to = to_address
        
        if not is_raw_text:
            message.html = message_content
            message.body = html2text.html2text(message.html)  
        else: 
            message.body = message_content
        
        try:
            message.send()
        except:
            message.send()
        
        info_message = u"%s\n%s\n%s\n" % (message.sender, message.to, message.body)
        logging.info(info_message)
    except:
        error_message = u"Unable to send message\n\n%s\n%s\n%s\n" % (message.sender, message.to, message.body)
        error_reporting.log_exception(logging.critical, error_message = error_message)

