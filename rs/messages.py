
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
This module contains functions that are involved in sending messages between users.
"""

# Django imports
from django import http
from django.utils.translation import ugettext
from django.utils import html

# Appengine imports
from google.appengine.ext import ndb 

# Standard python imports
import logging, datetime

# Lexalink imports
import models, utils, utils_top_level, constants
import captcha, error_reporting, mailbox



#############################################

def initialize_and_store_spam_tracker(current_spam_tracker):
    
    try:

        if current_spam_tracker == None:
    
            spam_tracker = SpamMailStructures()
    
            spam_tracker.datetime_first_mail_sent_today  = datetime.datetime.now()
            
            spam_tracker.num_mails_sent_today = 0
            spam_tracker.num_mails_sent_total = 0
            
            spam_tracker.num_times_reported_as_spammer_total = 0
            
            spam_tracker.num_times_blocked = 0
            
            spam_tracker.num_times_reported_as_good_today = 0
            spam_tracker.num_times_reported_as_good_total = 0
            
            spam_tracker.number_of_captchass_solved_total = 0         
            
            spam_tracker.put()
            
            return spam_tracker.key
        else:
            return current_spam_tracker.key
        
    except:
        error_reporting.log_exception(logging.critical)  

#############################################    


def update_users_have_sent_messages(sender_userobject, receiver_userobject, receiver_has_blocked_sender = False):
    # updates UsersHaveSentMessages model to ensure that all users that have previously had contact
    # will have an entry in the structure. Additionally, this structure will be updated
    # any time a new message is sent between two users, so that the results can be ordered
    # by most the date of most recent contact.
    #
    # Note that for each message, two entries are generated. One with the sender as the "owner",
    # and the other with the receiver as the "owner". This is necessary for queries that will
    # be preformed for the mailbox of a particular "owner".
    
    
    ################################ 
    def txn(sender_userobject_key, receiver_userobject_key, owner_ref, other_ref, 
            is_favorite, receiver_has_blocked_sender):

        return_val = ''
        
        have_sent_messages_obj = utils.get_have_sent_messages_object(owner_ref, other_ref)
        if not have_sent_messages_obj:
            have_sent_messages_obj = utils.get_have_sent_messages_object(owner_ref, other_ref, create_if_does_not_exist = True)
            is_new_contact = True
        else:
            is_new_contact = False

        have_sent_messages_obj.owner_ref = owner_ref
        have_sent_messages_obj.other_ref = other_ref                                
        have_sent_messages_obj.last_m_date = datetime.datetime.now()
        have_sent_messages_obj.unique_m_date = "%s_%s" % (datetime.datetime.now(), sender_userobject_key)
        have_sent_messages_obj.mailbox_to_display_this_contact_messages = "inbox"
        have_sent_messages_obj.other_is_favorite = is_favorite
        

        
        # Note: if a user sends a message to themself, this will show up as a received message due to the
        # ordering of the if/else sequence below. This is intentional, so that they can see that the
        # messaging system actually works. 
        
        if receiver_userobject_key == owner_ref:
            # new message has not been read by the receiver yet (cannot have been read yet, because they
            # just received the message)
            have_sent_messages_obj.owner_is_sender = False        
                   
            if not receiver_has_blocked_sender:
                # only increase the unread_contact_counter if the current object is the receiver, and only if this
                # is already marked as read (which means that a new *unread* message should therefore increase
                # the counter).
                if is_new_contact or have_sent_messages_obj.message_chain_has_been_read:
                    return_val = "increase_receiver_unread_contact_count"
                else:
                    return_val = "only_update_when_to_send_next_notification"
            else:
                return_val = '' # do nothing
            
            have_sent_messages_obj.message_chain_has_been_read = False
            
            if receiver_userobject_key == sender_userobject_key:
                # user has sent a message to themselves - however since the "sender_userobject_key == owner_ref" branch 
                # below will never be executed we must increase the num_messages_to_other_sent_today counter here.
                have_sent_messages_obj.num_messages_to_other_sent_today += 1          
            
        elif sender_userobject_key == owner_ref:
            have_sent_messages_obj.owner_is_sender = True
            
            have_sent_messages_obj.num_messages_to_other_sent_today += 1            

            # if the chain has not been read, but the owner is responding .. consider it to have been
            # read anyway, and decrease the unread message counter.
            if not is_new_contact and not have_sent_messages_obj.message_chain_has_been_read:
                return_val = "decrease_sender_unread_contact_count"
                
            # consider that sender has always read the message
            have_sent_messages_obj.message_chain_has_been_read = True


        else:
            raise Exception("Unknown value")
        

        have_sent_messages_obj.put()

        return return_val # end transaction
    ################################ 

    try:

        receiver_userobject_key = receiver_userobject.key
        sender_userobject_key = sender_userobject.key
        
        
        owner_other_ref_def = [(sender_userobject_key, receiver_userobject_key), 
                               (receiver_userobject_key, sender_userobject_key)]
        
    
        for (owner_ref, other_ref) in owner_other_ref_def:
            
            owner_userobject = utils_top_level.get_object_from_string(owner_ref.urlsafe())
            other_userobject = utils_top_level.get_object_from_string(other_ref.urlsafe())
            
            
            # we need to pull out the initiate_contact_object to check if the other user is a favorite, this is because 
            # favorite status must be marked both on messages, as well as on the initiate_contact_object.
            initiate_contact_object = utils.get_initiate_contact_object(owner_ref, other_ref)
            if initiate_contact_object: 
                is_favorite = initiate_contact_object.favorite_stored
            else:
                is_favorite = False
    
            # update the have_sent_messages object to reflect that these users have now had contact, and that
            # the sender has read the emails between these two users, and the receiver has not read the 
            # emails between these two users. 
            modify_count_string = ndb.transaction(lambda: txn(sender_userobject_key, receiver_userobject_key,
                                                        owner_ref, other_ref, is_favorite, receiver_has_blocked_sender))
            
            # Now, modify the counters that track the number of undread "messages" (from unique contacts)
            # This is done in a transaction to deal with conflicts. Additionally, this is done outside
            # of the previous transaction, because only a single model can be handldled in a single transaction.
            if not modify_count_string:
                pass
            
            elif modify_count_string == "increase_receiver_unread_contact_count":
                
                try:
                    hours_between_notifications = utils.get_hours_between_notifications(receiver_userobject, constants.hours_between_message_notifications)
                    increment_or_decrement_value = 1
                    receiver_userobject.unread_mail_count_ref = \
                                   mailbox.modify_user_unread_contact_count(receiver_userobject.unread_mail_count_ref, increment_or_decrement_value, \
                                                                            hours_between_notifications)
                except:
                    error_message = "User: %s counter exception" % receiver_userobject.username
                    error_reporting.log_exception(logging.error, error_message=error_message)  
                    
            elif modify_count_string == "only_update_when_to_send_next_notification":
                try:
                    hours_between_notifications = utils.get_hours_between_notifications(receiver_userobject, constants.hours_between_message_notifications)
                    increment_or_decrement_value = 0
                    receiver_userobject.unread_mail_count_ref = \
                                   mailbox.modify_user_unread_contact_count(receiver_userobject.unread_mail_count_ref, increment_or_decrement_value, \
                                                                            hours_between_notifications)
                except:
                    error_message = "User: %s counter exception" % receiver_userobject.username
                    error_reporting.log_exception(logging.error, error_message=error_message)  
                    
            elif modify_count_string == "decrease_sender_unread_contact_count":
                try:
                    increment_or_decrement_value = -1
                    sender_userobject.unread_mail_count_ref = \
                                 mailbox.modify_user_unread_contact_count(sender_userobject.unread_mail_count_ref, increment_or_decrement_value, "NA")
                except:
                    error_message = "User: %s counter exception" % sender_userobject.username
                    error_reporting.log_exception(logging.error, error_message=error_message)    
            else:
                raise Exception("Unknown mailbox counter %s" % modify_count_string)
            
            if owner_ref == other_ref:
                # user is sending a message to themself -- no need to loop again.
                break;
    
    except:
        error_reporting.log_exception(logging.critical)   
        return None
    



def store_mail_message(sender_userobject_key, receiver_userobject_key, parent_key, text):
    #
    # stores a MailModel object for the message between two users. 
    
    mail_message = models.MailMessageModel(parent=parent_key)
    mail_message.m_text  = text
    mail_message.m_date = datetime.datetime.now()
    mail_message.unique_m_date =  "%s_%s" % (datetime.datetime.now(), sender_userobject_key)
    mail_message.m_from = sender_userobject_key
    mail_message.m_to =  receiver_userobject_key                  
    mail_message.put()    



def actually_store_send_mail(sender_userobject, to_uid, text):  
    # Called from client directly to store the mail and to update the assocated data structures.
    
    try:
        sender_userobject_key = sender_userobject.key
        receiver_userobject_key = ndb.Key(urlsafe = to_uid)
        
        sender_uid = sender_userobject_key.urlsafe()
        receiver_uid = to_uid
        
        # check to make sure that the receiver has not blocked the sender. If they have been blocked, we still
        # send the message, but immediately move it to the deleted mailbox. We also do NOT want to send any
        # notifications of the new message. Note: we look this up in with in the receivers data structure, since
        # they would have stored the block (as opposed to the sender having blocked the receiver - which is irrelevant
        # right now).
        reverse_initiate_contact_object = utils.get_initiate_contact_object(receiver_userobject_key, sender_userobject_key) 
        if reverse_initiate_contact_object:
            sender_is_blocked = reverse_initiate_contact_object.blocked_stored
        else:
            sender_is_blocked = False
        
        receiver_userobject = utils_top_level.get_object_from_string(receiver_uid)
        # only update the have_sent_messages if the user is not blocked
        update_users_have_sent_messages(sender_userobject, receiver_userobject, sender_is_blocked)

        parent_key = utils.get_fake_mail_parent_entity_key(sender_uid, receiver_uid)
        
        # do not allow extremely huge messages to be sent (to prevent attacks on our storage space)
        text = text[:constants.MAIL_TEXTAREA_CUTOFF_CHARS]
        # make sure that the user hasn't entered a word that is longer than the line width
        text = utils.break_long_words(text, constants.MAX_CHARS_PER_WORD)
        
        store_mail_message(sender_userobject_key, receiver_userobject_key, parent_key, text)

        if not sender_is_blocked:
            # if the time passed since the last notification sent to the user has exceeded their mail preference, then
            # send out the email now. This must come AFTER unread_mail_count is updated.
            unread_mail_count_object = receiver_userobject.unread_mail_count_ref.get()
            if unread_mail_count_object.when_to_send_next_notification <= datetime.datetime.now():
                
                try:
                    # by construction, email_address should be valid if the when_to_send_next_notification value is not "max"
                    assert(receiver_userobject.email_address_is_valid)             
                    taskqueue.add(queue_name = 'fast-queue', url='/rs/admin/send_new_message_notification_email/', params = {
                        'uid': receiver_userobject.key.urlsafe()})
                except:
                    error_reporting.log_exception(logging.critical)
                        
        if sender_is_blocked:
            # move this message to the deleted folder in the receivers mailbox
            have_sent_messages_key = utils.get_have_sent_messages_key(receiver_userobject_key, sender_userobject_key)
            mailbox.modify_message(have_sent_messages_key, 'trash')
                    
        return http.HttpResponse('OK')     

    except: 
        error_reporting.log_exception(logging.critical)   
        return http.HttpResponse('Error')       
    
#############################################

def determine_if_captcha_is_shown(userobject, have_sent_messages_bool):
    # This function computes the statistics required for determining if this user must filll in  a captcha to send a message
    # It returnns the boolean indicating if a captcha is required, and also returns a string that is used to inform
    # the  user about their currrent spam-sending statistics.
    
    show_captcha = False
    spam_statistics_string = ''  
    
    try:

        if userobject.client_is_exempt_from_spam_captchas:
            # if this user is paid member, they do not have to see messages about spam, or to solve captchas
            # in the case that someone has indicated that they sent spam. 
            return (show_captcha, spam_statistics_string)
    
        if not userobject.spam_tracker:
            # if it doesn't exist, create it! (will only be done once in the life of every user..
            # and only for old users that were not initialized correctly -- can remove this
            # code if DB maintenance is done.
            userobject.spam_tracker = initialize_and_store_spam_tracker(userobject.spam_tracker) 
            put_userobject(userobject)  
            
        spam_tracker = userobject.spam_tracker.get()
            
        if spam_tracker.num_times_reported_as_spammer_total > spam_tracker.number_of_captchass_solved_total \
           and not have_sent_messages_bool: 
    
            # each message that is marked as a SPAM requires that the user enter a captcha.
            show_captcha = True  
          
    
        # only show spam statistics for profiles that the user has not already had contact with
        if not have_sent_messages_bool:
            
            if spam_tracker.num_mails_sent_total > 0:
                percent_total_spam = float(spam_tracker.num_times_reported_as_spammer_total)/spam_tracker.num_mails_sent_total
            else:
                percent_total_spam = 0
            
            spam_statistics_string += u"""<div><strong>%(spam_stats_string)s</strong>
            %(num_times_reported)s %(of_string)s %(num_mails_sent)s %(sent_string)s (%(percent).0f%%).<br>
            %(if_you_send_spam)s<br><br></div>"""% {
                'spam_stats_string' : ugettext("Statistics of spam sent from your account:"),    
                'of_string' : ugettext("of"), 
                'sent_string' : ugettext("sent (plural)"),
                'if_you_send_spam' : ugettext('If you send spam, you will have to write "captchas" before being allowed \
    to send more messages. Additionally, if you send a lot of spam, your messages will be sent directly to the spam mailbox.'),
                
                'num_times_reported' : spam_tracker.num_times_reported_as_spammer_total, 
                'num_mails_sent' : spam_tracker.num_mails_sent_total,
                'percent': 100*percent_total_spam}
    
        
    
    except:
        error_reporting.log_exception(logging.critical)  
        
    return (show_captcha, spam_statistics_string)

#############################################
def check_captcha(request):
    # verifies if the captcha has been solved correctly.
    
    challenge = request.POST.get('recaptcha_challenge_field')
    response  = request.POST.get('recaptcha_response_field')
    remoteip  = environ['REMOTE_ADDR']
    
    cResponse = captcha.submit(
                   challenge,
                   response,
                   remoteip)
    
    return cResponse.is_valid
            
#############################################    
    
@utils.ajax_call_requires_login
def store_send_mail(request, to_uid, text_post_identifier_string, captcha_bypass_string, have_sent_messages_string):
    # Preforms authentication on the message, and if everything is OK, it 
    # stores the sent mail message into the database 
       
    try:
    
        sender_userobject =  utils_top_level.get_userobject_from_request(request)
        from_uid =  request.session['userobject_str']
        
        response_is_valid = False
            
        # check if the correct code for bypassing the captcha has been passed in.. otherwise, verify that
        # the captcha has been solved before storing anything.
        if captcha_bypass_string == "no_bypass": # I break this portion of the if out for efficiency
            has_captcha = True
        elif captcha_bypass_string != utils.compute_captcha_bypass_string(from_uid, to_uid):
            has_captcha = True
        else: has_captcha = False
        
        if request.method != 'POST':
            # Must be a post for it to work -- this should never actually execute.
            return http.HttpResponseBadRequest()
        else:
            
            if has_captcha:
                response_is_valid = check_captcha(request)
                # CAPTCHA STUFF
    
            else:
                response_is_valid = True
          
            if response_is_valid:
                text = request.POST.get(text_post_identifier_string, '')
                # make sure that the user isnt trying to do an html/javascript injection
                text = html.strip_tags(text)
            else:
                # error = cResponse.error_code
                return http.HttpResponse(ugettext("Captcha is incorrect, try again"))
            
            spam_tracker = sender_userobject.spam_tracker.get()
            
            
            # If they are trying to send too many messages in a single day, block the extra messages. This is required to prevent
            # "disk-usages attacks" on the database (ie. prevent two users that have previously had contact from sending a million
            # messages between them)
            from_key = ndb.Key(urlsafe = from_uid)
            to_key = ndb.Key(urlsafe = to_uid)
            have_sent_messages_object = utils.get_have_sent_messages_object(from_key, to_key)
            

            if have_sent_messages_object and utils.check_if_reset_num_messages_to_other_sent_today(have_sent_messages_object):
                
                have_sent_messages_object.datetime_first_message_to_other_today = datetime.datetime.now()
                have_sent_messages_object.num_messages_to_other_sent_today = 0
                have_sent_messages_object.put()
                
            initiate_contact_object = utils.get_initiate_contact_object(from_key, to_key)            
            if not utils.check_if_allowed_to_send_more_messages_to_other_user(have_sent_messages_object, initiate_contact_object):
                error_message = u"%s" % constants.ErrorMessages.num_messages_to_other_in_time_window()
                error_reporting.log_exception(logging.warning, error_message=error_message)  
                return http.HttpResponse(error_message)                    
        
        
    
            # don't allow blank emails to be sent
            if not text:
                return http.HttpResponse(ugettext("You have not written a message. You must write something before sending it."))
             
            spam_tracker_modified = False
            # don't count messages that are sent to previous contacts in the spam statistics
            if have_sent_messages_string == "have_not_had_contact":
                if spam_tracker.datetime_first_mail_sent_today + datetime.timedelta(
                    hours = constants.WINDOW_HOURS_FOR_NEW_PEOPLE_MESSAGES - constants.RESET_MAIL_LEEWAY) <  datetime.datetime.now():
                    
                    spam_tracker.datetime_first_mail_sent_today  = datetime.datetime.now()
                    spam_tracker.num_mails_sent_today = 0
                    
                # Make sure they don't exceed the number of new contacts allowed in a single day. This condition could
                # occur if they open a bunch of windows to different profiles before using their message quota, and then attempting
                # to send messages to each user. 
                
                if not sender_userobject.client_paid_status:
                    num_emails_per_day = constants.GUEST_NUM_NEW_PEOPLE_MESSAGES_ALLOWED_IN_WINDOW
                else:
                    # VIP member has extra messages allocated
                    num_emails_per_day = constants.VIP_NUM_NEW_PEOPLE_MESSAGES_ALLOWED_IN_WINDOW
                                
            
                if spam_tracker.num_mails_sent_today >= num_emails_per_day:
                    error_message = "You have already sent messages to %(num)s new contacts." % {'num': num_emails_per_day}
                    error_reporting.log_exception(logging.warning, error_message=error_message)  
                    return http.HttpResponse(error_message)                 
                                    
                # only count the message in the spam tracker if it is to a new person
                spam_tracker.num_mails_sent_today += 1
                spam_tracker_modified = True
                
            # count all messages sent, for statistical reporting of the percentage of times this person 
            # has sent spam.
            spam_tracker.num_mails_sent_total += 1
            
            if has_captcha:
                spam_tracker.number_of_captchass_solved_total += 1
                spam_tracker_modified = True
            
            if spam_tracker_modified:
                spam_tracker.put()
                       
            return_val = actually_store_send_mail(sender_userobject, to_uid, text)

        # Mark the session as modified, which causes a new cookie to be written (with an updated expiry time)
        # Because if they are sending mails (ie they are active) we want to give extra time before session expiry
        # This also reduces the chances of a logout in the middle of sending a mail message.
        request.session.modified = True      
        
        return return_val

    except: 
        error_reporting.log_exception(logging.critical)   
        return http.HttpResponseServerError(ugettext('Internal error - this error has been logged, and will be investigated immediately')) 


def get_admin_userobject():
    # first, query for "Alex" which is the account that will send the welcome message.
    
    
    query = models.UserModel.gql("WHERE username = :username AND is_real_user = True ORDER BY last_login_string DESC " , 
                          username = constants.ADMIN_USERNAME)
    alex_object = query.get()    
    
    if not alex_object:
        error_reporting.log_exception(logging.critical, error_message="Unable to get ADMIN userobject")
        
    return alex_object


#############################################
def welcome_new_user(request):
    
    # sends a welcome message to a new user.
    userobject =  utils_top_level.get_userobject_from_request(request)
    
    alex_object = get_admin_userobject()
    
    if (alex_object):
        # make sure we don't send messages from a backup userobject!
        try:
            to_uid = userobject.key.urlsafe()
            if settings.BUILD_NAME != "Language" and settings.BUILD_NAME != "Friend":
                replacement1 = ugettext('"wink" or a "kiss"')
                replacement2 = ugettext('winks, kisses,')
            else:
                replacement1 = ugettext('"greeting"')
                replacement2 = ugettext('greetings')
                
            text = ugettext(
                u"""Welcome to %(app_name)s, and good luck with your search! %(replacement1)s %(replacement2)s""") % {
                    'app_name': settings.APP_NAME, 'replacement1':replacement1, 'replacement2':replacement2}

            actually_store_send_mail(alex_object, to_uid, text)
 
        except:
            error_reporting.log_exception(logging.critical, error_message="Unable to send welcome message")
            
            
def send_vip_congratulations_message(userobject):
    
    previous_language = translation.get_language() # remember the original language, so we can set it back when we finish 
    try:
        alex_object = get_admin_userobject()
        to_uid = userobject.key.urlsafe()
        
        # set the language to be the users preferred language
        translation.activate(userobject.search_preferences2.get().lang_code)

        date_in_current_language = utils.get_date_in_current_language(userobject.client_paid_status_expiry)
        
        text = ugettext("Congratulations, you are now a VIP member until %(date)s.") % {'date' : date_in_current_language}
        actually_store_send_mail(alex_object, to_uid, text)
    except:
        error_reporting.log_exception(logging.critical, error_message="Unable to send welcome message")
        
    finally:
        # activate the original language -- not sure if this is really necessary, but is 
        # somewhat safer (until I fully understand how multiple processes in a single thread are interacting)
        translation.activate(previous_language)        