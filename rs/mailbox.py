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


from django.core.urlresolvers import reverse

import datetime, logging

from google.appengine.ext import ndb 

from django.utils.encoding import smart_unicode
from django.http import HttpResponseRedirect
from django import http
from django.utils.translation import ugettext

import settings

from forms import FormUtils
from utils import requires_login
from constants import MAIL_DISPLAY_CHARS, MAIL_SNIP_CHARS, MAIL_SUMMARY_NUM_LINES_TO_SHOW
from utils import return_time_difference_in_friendly_format, get_new_contact_count_sum, \
     compute_captcha_bypass_string
import email_utils
import queries
import ajax, admin, utils, utils_top_level
import user_profile_main_data
import localizations
import error_reporting
import rendering, text_fields
import models, constants, http_utils
from rs import profile_utils

CONTACTS_PAGESIZE = 10 # number of contacts to show on a page.
SINGLE_CONVERSATION_PAGESIZE = 10 # show X sent/received messages

###########################################################################
    
def setup_and_run_conversation_mailbox_query(bookmark_key_str, userobject, other_userobject , num_results_needed):
    # Queries the database for the messages between the user and the other_user.

    top_date = ''
    
    if bookmark_key_str:
        bookmark_key = ndb.Key(urlsafe = bookmark_key_str)
        bookmarked_mailbox_object = bookmark_key.get()
        top_date = bookmarked_mailbox_object.unique_m_date

        
    # Note: Using "uid's" instead of "nid's" was a mistake - if we ever need to restore mail messages to a different
    # application id, the parent will not be consistent, and the maill messages will not be found. 
    # If we ever migrate to a new app ID, this could temporarily
    # be fixed by manually creating the uid's used for the parent based on the old app name... 
    uid = userobject.key.urlsafe()
    other_uid = other_userobject.key.urlsafe()
    
    parent_key = utils.get_fake_mail_parent_entity_key(uid, other_uid)
    
    q = models.MailMessageModel.query(ancestor = parent_key).order(-models.MailMessageModel.unique_m_date)
    if top_date:
        q = q.filter(models.MailMessageModel.unique_m_date <=  top_date)
    query_results = q.fetch(num_results_needed)
    
    return query_results

    
###########################################################################

def query_for_which_users_owner_has_contacted(bookmark, userobject, num_results_needed, mailbox_name = "inbox"):
    # Queries the database to determine which other users the current client has sent or received messages in the past.
    # This information is obtained from the UsersHaveSentMessages data structure. Also, checks to make sure that
    # the message is appropriate for the current mailbox view ("inbox", "trash", "spam", etc)

    try:
        q = models.UsersHaveSentMessages.query().order(-models.UsersHaveSentMessages.unique_m_date)
    
        q = q.filter(models.UsersHaveSentMessages.owner_ref == userobject.key)
        
        if mailbox_name == "inbox" :
            q = q.filter(models.UsersHaveSentMessages.mailbox_to_display_this_contact_messages == "inbox")
        elif mailbox_name == "trash":
            q = q.filter(models.UsersHaveSentMessages.mailbox_to_display_this_contact_messages == "trash")
        elif mailbox_name == "favorites":
            q = q.filter(models.UsersHaveSentMessages.other_is_favorite == True )
        elif mailbox_name == "new":
            q = q.filter(models.UsersHaveSentMessages.message_chain_has_been_read == False )
        elif mailbox_name == "received":
            q = q.filter(models.UsersHaveSentMessages.mailbox_to_display_this_contact_messages == "inbox")
            q = q.filter(models.UsersHaveSentMessages.owner_is_sender == False)
        elif mailbox_name == "sent":
            q = q.filter(models.UsersHaveSentMessages.mailbox_to_display_this_contact_messages == "inbox")
            q = q.filter(models.UsersHaveSentMessages.owner_is_sender == True)
        elif mailbox_name == "spam":
            q = q.filter(models.UsersHaveSentMessages.mailbox_to_display_this_contact_messages == "spam")
        else:
            raise Exception("Unknown mailbox_name: %s" % mailbox_name)
        
        if bookmark:
            bookmark_key = ndb.Key(urlsafe = bookmark)
            users_have_sent_messages_bookmark = bookmark_key.get()
            q = q.filter(models.UsersHaveSentMessages.unique_m_date <=  users_have_sent_messages_bookmark.unique_m_date)
            
        query_results = q.fetch(num_results_needed)
        return query_results
    
    except:
        error_reporting.log_exception(logging.critical)

###########################################################################
def get_mail_history_summary(request, owner_userobject, display_userobject, show_checkbox_beside_summary=False):
    # gets a summarized history of the messages sent between two users. This is used both
    # in the mailbox, as well as for showing the history on each profile as the profiles are
    # being browsed.
    
    generated_html = ''
    have_sent_messages_bool = False
    
    try:
        

        have_sent_messages_object = utils.get_have_sent_messages_object(owner_userobject.key, display_userobject.key)
        
        if have_sent_messages_object:
            (generated_html, have_sent_messages_bool) = display_conversation_summary(request, have_sent_messages_object, show_checkbox_beside_summary)
        else:
            generated_html = ''
            
    except:
        error_reporting.log_exception(logging.critical)
            
    return (generated_html, have_sent_messages_object)


###########################################################################

#def reset_unread_new_messages_since_last_notification(unread_mail_count_obj_key):
    ## called when we send out email notifications. Allows us to track when the user last
    ## received a notification that they have new messages. 
    ## Also, call this function when user logges in, since this is effectively the same as
    ## them receiving a notification of new messages.
    
    #def txn(unread_mail_count_obj):
        #unread_mail_count_obj = db.get(unread_mail_count_obj_key)
        #unread_mail_count_obj.num_new_since_last_notification = 0
        #unread_mail_count_obj.date_of_last_notification = datetime.datetime.now()
        #unread_mail_count_obj.when_to_send_next_notification = datetime.datetime.max
        #unread_mail_count_obj.when_to_send_next_notification_string = str(unread_mail_count_obj.when_to_send_next_notification)
        #unread_mail_count_obj.put()
        #return unread_mail_count_obj
    
    #return_val = db.run_in_transaction (txn, unread_mail_count_obj_key)
    #return return_val

############################################################################
    

def modify_user_unread_contact_count(unread_mail_count_ref, increment_or_decrement_value, hours_between_notifications = "NA"):
    
    # modifies the number of "unique" messages that the user has received .. meaning from
    # unique other users .. a single user that sends 5 messages is counted only once.
    #
    # Note: hours_between_notifications is only used in the case that we are modifying when to send the next notification.
    # therefore, this value is ignored when we are marking messages as read (ie. we are passed in a negative 
    # increment_or_decrement_value value). 
    
    def txn(unread_mail_count_ref, increment_or_decrement_value):
        # updates the userobject.unread_mail_count value based on the value passed in. Must
        # be run in a transaction to ensure that only a single update can take place at a time.
        
        unread_mail_count_obj = unread_mail_count_ref.get()
        unread_mail_count_obj.unread_contact_count += increment_or_decrement_value
        unread_mail_count_obj.num_new_since_last_notification += increment_or_decrement_value
        
        if increment_or_decrement_value >= 0: 
            # A new message has been received (since the value is positive or zero). Update the data structure for defining when
            # notifications should be sent out. Note, in the case of a "0", this means that we not modifying the unread_contact_count
            # but that we are purposfully calling this function to update the "when_to_send_next_notification" value
            if hours_between_notifications != None:
                unread_mail_count_obj.when_to_send_next_notification = \
                                     unread_mail_count_obj.date_of_last_notification + \
                                     datetime.timedelta(hours = hours_between_notifications)
            else:
                unread_mail_count_obj.when_to_send_next_notification = datetime.datetime.max
                            
        try:
            if unread_mail_count_obj.unread_contact_count < 0:
                unread_mail_count_obj.unread_contact_count = 0
                raise Exception("Negative unread_contact_count encountered")
            
        except:
            error_reporting.log_exception(logging.error)
            raise #re-throw the exception
        
        finally:
            # run the following code in all cases (exception or not)
                
            if unread_mail_count_obj.num_new_since_last_notification <= 0:
                # This is not necessarily an exception, because this count is being reset each time we 
                # send out emails about the number of unread messages -- this value can easily go negative
                # if the user marks a bunch of old messages as read. More details in models.py. 
                unread_mail_count_obj.num_new_since_last_notification = 0
                
                # don't send a notification if there are no new messages since last notification
                unread_mail_count_obj.when_to_send_next_notification = datetime.datetime.max
                
            unread_mail_count_obj.when_to_send_next_notification_string = str(unread_mail_count_obj.when_to_send_next_notification)  
            unread_mail_count_obj.put()
            return unread_mail_count_obj.key
         
    unread_mail_count_key = ndb.transaction(lambda: txn(unread_mail_count_ref, increment_or_decrement_value))    
    return unread_mail_count_key
    
###########################################################################
    
def generate_messages_html(query_for_message, is_first_message, userobject, other_uid, lang_code):
    # Loops over the passed in query results, and prints out the corresponding individual messsages.
    # Individual messages here refer to messages sent between a pair of users. The seriese of individual
    # messaages is a conversation between two users.
    
    
    try:
        generated_html = ''
        
        for message in query_for_message[:SINGLE_CONVERSATION_PAGESIZE]:
           
            profile_key = message.m_from
            profile = profile_key.get()
            # get the key for the m_from profile, without doing a full lookup:            
            m_to_key = message.m_to
            if m_to_key == userobject.key:
                is_receiver = True
                text_color = "black";
            else: 
                is_receiver = False
                text_color = "gray";      
     
            # the short divider line between messages
            if not is_first_message:
                generated_html += u'<div class="grid_3 alpha omega cl-divider-line"></div>'
            is_first_message = False
            
            generated_html += u'<div class="grid_9 alpha omega cl-mailbox_results cl-mail_seperator">\n'
            profile_href = profile_utils.get_userprofile_href(lang_code, profile, is_primary_user=False)

        
            # get profile photo
            generated_html += '<div class="grid_2 alpha "><br>\n'
            # divider line
            generated_html += u'<strong>%s: <a class="cl-mailbox_anchor_format" href="%s" rel="address:%s">%s</a></strong>\n' % (
                ugettext("From"), profile_href, profile_href, profile.username)     
            generated_html += FormUtils.generate_profile_photo_html(lang_code, profile, text_fields.no_photo, profile_href, "small")
            generated_html += u'</div> <!-- end grid2 -->\n'
     
     
            # container for all the message information
            generated_html += u'<div class= "grid_7 alpha omega"><br>\n' #message text container
            date_sent =  return_time_difference_in_friendly_format(message.m_date)
            generated_html += u'<strong>%s</strong><br>\n' % (date_sent)
                
            generated_html += u'<span class="cl-literally-display-user-text" style="color:%s;">%s</span>\n' % (text_color, message.m_text)
            generated_html += u'</div>' # message text container
            
            generated_html += u'</div> <!-- end cl-mailbox_results -->\n'
            
        if len(query_for_message) == SINGLE_CONVERSATION_PAGESIZE + 1:
            
            bookmark_key_str = query_for_message[-1].key.urlsafe()
            
            generated_html += """
            
            <script type="text/javascript" language="javascript">
            
            // javascript code for displaying additional mail history
            $(document).ready(function(){
    
                $("#id-mail-history-container-%(bookmark_key_str)s a").click(function() {
                    $("#id-mail-history-container-%(bookmark_key_str)s").load("/rs/ajax/load_mail_history/%(bookmark_key_str)s/%(other_uid)s/");
                    return false; // ensure that browser doesn't navigate to href page.
                });
            });
            
            </script>
            """ % {'bookmark_key_str' : bookmark_key_str, 'other_uid':other_uid}
            
            
            generated_html += """
            <div id="id-mail-history-container-%(bookmark_key_str)s" class="grid_9 alpha omega">
            <div class = "grid_9 alpha omega cl-right-text">
            <br><br><br><a href="#display-mail-history-%(bookmark_key_str)s">Ver mas historia&nbsp;&nbsp;</a><br><br>
            </div>
            </div>"""  % {'bookmark_key_str' : bookmark_key_str}
            
        return generated_html
    
    except:
        error_reporting.log_exception(logging.critical)
        return ''
        
    
    
def  mark_new_have_sent_messages_object(userobject, other_userobject):
    # TEMPORARY code, to be left in until we have transitioned to the new datasture ... 
    
    
    have_sent_messages_object = utils.get_have_sent_messages_object(userobject.key, other_userobject.key)
    # have_sent_messages_object must be defined for the rest of this code to work.
    if have_sent_messages_object:
        if not have_sent_messages_object.message_chain_has_been_read:
            have_sent_messages_object.message_chain_has_been_read = True
            have_sent_messages_object.put()
           
      
      
def generate_mail_textarea(textarea_section_name, from_uid, to_uid, have_sent_messages_object, show_captcha = False, 
                           spam_statistics_string = '', vip_status = None):
    
    
    """
    Generates the html that describes the textbox and buttons for sending a message to another member.
    
    textarea_section_name: "send_mail" - send mail from within the mailbox
                           "send_mail_from_profile_checkbox_no" - send mail directly while viewing the profile
    """
    
    generated_html = ''
    try:
        
        initiate_contact_object = utils.get_initiate_contact_object(ndb.Key(urlsafe = from_uid), ndb.Key(urlsafe = to_uid))
        (is_allowed, txt_for_when_quota_resets) =  utils.check_if_allowed_to_send_more_messages_to_other_user(
            have_sent_messages_object, initiate_contact_object, vip_status)
        if  is_allowed or utils.check_if_reset_num_messages_to_other_sent_today(have_sent_messages_object):
            
            if show_captcha:
                captcha_bypass_string = "no_bypass"
            else:
                captcha_bypass_string = compute_captcha_bypass_string(from_uid, to_uid)
                        
            generated_html += FormUtils.define_html_for_mail_textarea(
                textarea_section_name, to_uid, captcha_bypass_string, have_sent_messages_object,
                spam_statistics_string)
        else:
            generated_html += u"<div>%s</div>" % constants.ErrorMessages.num_messages_to_other_in_time_window(txt_for_when_quota_resets)
    except:
        error_reporting.log_exception(logging.critical)
    
    return generated_html
    
###########################################################################
def generate_mail_message_display_html(userobject, other_userobject, lang_code):
    # This routine generates the display of a "conversation" between users in the system.
    # Ie. It shows all messages exchanged between two users.


    try:
        generated_html = """<script type="text/javascript">
        $(document).ready(function() {
        fancybox_setup($("a.cl-fancybox-profile-gallery"));
        });
        </script>"""
    
        query_for_message = setup_and_run_conversation_mailbox_query('', userobject, other_userobject, SINGLE_CONVERSATION_PAGESIZE+1)
    
        # mark this conversation as read for the user that is currently logged in.
        # Note, this is marking it as read on the "have_sent_messages" object.
        have_sent_messages_object = utils.get_have_sent_messages_object(userobject.key, other_userobject.key)
        # have_sent_messages_object must be defined for the rest of this code to work.
        assert(have_sent_messages_object)

        if not have_sent_messages_object.message_chain_has_been_read:
            have_sent_messages_object.message_chain_has_been_read = True
            have_sent_messages_object.put()
            try:
                userobject.unread_mail_count_ref = modify_user_unread_contact_count(userobject.unread_mail_count_ref, -1, "NA")
            except:
                error_message = "User: %s counter exception" % userobject.username
                error_reporting.log_exception(logging.error, error_message=error_message)            
    
                    
        # Make sure that a message is found -- if not, how did we get here?
        assert(query_for_message)
        
        message = query_for_message[0]
        
        textarea_section_name = u"send_mail"
        
        other_profile_key = have_sent_messages_object.other_ref
        other_profile = other_profile_key.get()
    
        to_uid = other_profile_key.urlsafe()
        other_profile_href = profile_utils.get_userprofile_href(lang_code, other_profile, is_primary_user=False)
        
        
        from_uid = userobject.key.urlsafe()
        
        generated_html += '<div class="grid_9 alpha omega cl-mailbox_results" id="id-display-send_mail-section">' # wrapper for JS

        # The following section defines the html for the "response" text area
        generated_html += u'<div class="cl-clear"></div>\n'
        generated_html += u'<div class="grid_2 alpha ">\n'
        generated_html += u'<div id="id-edit-%s-link">&nbsp;' % textarea_section_name
        
        generated_html += u'<strong>%s: <a class="cl-mailbox_anchor_format" href="%s" rel="address:%s" >%s</a> </strong> ' % (
            ugettext("To"), other_profile_href, other_profile_href, other_profile.username)
                
        
        
        generated_html += FormUtils.generate_profile_photo_html(lang_code, other_profile, text_fields.no_photo, "", "small")
        generated_html += u'</div> <!-- div id="id-edit-%(section_name)s-link -->'
        generated_html += u'</div> <!-- end grid2 -->\n'
        
        if not other_userobject.user_is_marked_for_elimination:

            # This is where the text input and associated buttons are added in.
            # Dont show the captcha, because they are responding to someone they have already
            # had contact with, and therefore unlikely to be Spam, additionally 
            # have_sent_messages_object exists (because if it didn't, they wouldn't enter this function.
            
            # Note: even if they have had contact, we put a limit on the number of messages they can send to each other in a single day 
            # This is required to prevent an attack on our database in which millions of messages are sent from one user to another.
            
            generated_html += generate_mail_textarea(textarea_section_name, from_uid, to_uid, have_sent_messages_object,
                                                     vip_status = userobject.client_paid_status)            
        
        else:
            generated_html += "<br><br>%s" % utils.get_removed_user_reason_html(other_userobject)

        # The following defines the html for the chain of messages. Note, we place this inside a "box" so that
        # it is clear to the user that they are looking at a chain of messages, as opposed to a list. 
        
        generated_html += u'<div class="cl-clear"></div>\n'
        
        # add in the table for kisses, winks, etc.
        generated_html += """
        <div class = "grid_9 alpha omega">&nbsp;<br>
        <div class = "grid_2 alpha">&nbsp;</div>
        <div class = "grid_7 omega" id="id-contact-div">
        %(contact_table)s
        </div>
        </div>
        """ % {'contact_table' : FormUtils.contact_table(to_uid)}
        
        generated_html += u'<div class="grid_9 alpha omega" >' # outer-container
    
        generated_html += u'<div class="grid_9 alpha omega cl-gray-box" id="id-highlight-div">' # message container
        
        # used for determining if a seperating line will be placed above the message
        is_first_message = True
        
        generated_html += generate_messages_html(query_for_message, is_first_message, userobject, to_uid, lang_code)
            
        generated_html += u'</div>' # gray message container
        generated_html += u'</div>' # outer container
        
        generated_html += u'<div class="grid_9 alpha omega"> &nbsp;</div>\n' #spacer
        
        generated_html += u'</div>' # close wrapper for JS
        
        return generated_html
    
    except:
        error_reporting.log_exception(logging.critical)
        return ''
        
        
###########################################################################
@requires_login
def mail_message_display(request, owner_uid, other_uid):
    # generates the view of a single mail message (including children in the chain). 
    # Also, geneates a textbox  that allows the 
    # client to respond immediately if desired (without an additional button press)
    # Might consider displaying photos/profile info (if they have any)

    try:
        if not utils.access_allowed_to_page(request, owner_uid):
            return http_utils.redirect_to_url(request, "/%s/" % request.LANGUAGE_CODE)
    
        userobject =  utils_top_level.get_object_from_string(owner_uid)
            
        username = userobject.username
        other_userobject =utils_top_level.get_object_from_string(other_uid)
    
        
        generated_html = ''
        generated_html += generate_mail_message_display_html(userobject, other_userobject, request.LANGUAGE_CODE)
            
        return rendering.render_main_html(request, generated_html, userobject)
    except:
        error_reporting.log_exception(logging.critical)
        return ''

###########################################################################

def display_conversation_summary(request, have_sent_messages_object,
                                 show_checkbox_beside_summary = False,
                                 show_vip_info = False):
    # Display the summary of a conversation between two users. Used for display in the mailbox view,
    # as well as at the bottom of each profile that is viewed (so that each user always knows what
    # previous contact they have had with each client)
    #
    # have_sent_messages_object: contains the information that allows us to retrieve the conversation
    # history between two users. 
    #
    # show_checkbox_beside_summary: If the summary is shown in the mailbox view (as opposed to
    # when viewing another users profile), then we add a checkbox beside the message, which 
    # is used for form submission that allows deletion, marking as spam, marking as read, etc
    # of the selected messages.
    #
    # Returns a summary of the history of the conversation between two users, and a boolean indicating
    # if a history between these two users exists (history, boolean)
    
    
    try:
    
        lang_code =  request.LANGUAGE_CODE
        generated_html = ''
        num_lines_to_show = MAIL_SUMMARY_NUM_LINES_TO_SHOW
        some_messages_not_shown = False
    
        # Check if have_sent_messages was found in the database. If not, then return with the appropriate
        # html indicating that these two users have no conversation history.
    
        assert(have_sent_messages_object)       
    
        # Make sure that the have_sent_messages_object is not corrupted - this should only possibly happen
        # on the staging server, or if we restore from a backup -- but, check in all cases to prevent
        # pain in the future.
        try:
            have_sent_messages_owner = have_sent_messages_object.owner_ref.get()
            have_sent_messages_other = have_sent_messages_object.other_ref.get()
            
            query_for_message = setup_and_run_conversation_mailbox_query('', have_sent_messages_owner, 
                                                                         have_sent_messages_other, num_lines_to_show + 1)
                
            if len(query_for_message) > num_lines_to_show:
                some_messages_not_shown = True
                query_for_message = query_for_message[:-1]
                
        except:      
            try:
                # this is inside a "try" because it could be the fact that the owner_ref and other_ref do not exist on the object, which
                # could be the reason that the exception is triggering. 

                if have_sent_messages_owner and have_sent_messages_other:
                    error = "setup_and_run_conversation_mailbox_query between: %s %s" % (have_sent_messages_owner.username, have_sent_messages_other.username)               
                else:
                    error = "Unknown error"
                    
                error_reporting.log_exception(logging.critical, error_message=error)
                    
            except:
                error = "have_sent_messages_object.owner_ref and/or have_sent_messages_object.other_ref does not exist. \
                have_sent_messages_object = %s" % repr(have_sent_messages_object)
                error_reporting.log_exception(logging.critical, error_message=error)
                
            # delete the have_sent_messages_object -- to prevent future errors
            #have_sent_messages_object.delete()
            return (u"", False)
    
            
        if not query_for_message:
            # This deals with a potential database instability issue, caused by a previous code error. In rare cases
            # it is possible that the have_sent_messages object exists, but no message is associated.
            
            error = "User %s and User %s have_sent_messages object exists, but no messages found. Consider deleting" % (
                have_sent_messages_owner.username, 
                have_sent_messages_other.username)

            error_reporting.log_exception(logging.critical, error_message=error)
            
            return (u"" , False)
        
        message = query_for_message[0]
    
        
        # Always display the "other person" profile beside the message so that the user can
        # click on the link/photo to see who they are conversing with.
        userobject = have_sent_messages_object.owner_ref.get()
        other_userobject = have_sent_messages_object.other_ref.get()
    
        have_sent_messages_key = ''
        assert(have_sent_messages_object)
        have_sent_messages_key =  have_sent_messages_object.key
        have_sent_messages_key_str = have_sent_messages_key.urlsafe()
    
        if show_checkbox_beside_summary:
            show_checkbox_js_val = "yes"
        else:
            show_checkbox_js_val = "no"
        
        generated_html += u"""
        <script type="text/javascript" language="javascript">
            $(document).ready(function(){
                handle_click_on_update_message_action_icon("%(have_sent_messages_key_str)s", "%(to_uid)s", "favorite", "%(show_checkbox_js_val)s")
                handle_click_on_update_message_action_icon("%(have_sent_messages_key_str)s", "%(to_uid)s", "inbox", "%(show_checkbox_js_val)s")
                handle_click_on_update_message_action_icon("%(have_sent_messages_key_str)s", "%(to_uid)s", "read", "%(show_checkbox_js_val)s")
                handle_click_on_update_message_action_icon("%(have_sent_messages_key_str)s", "%(to_uid)s", "spam", "%(show_checkbox_js_val)s")
                handle_click_on_update_message_action_icon("%(have_sent_messages_key_str)s", "%(to_uid)s", "trash", "%(show_checkbox_js_val)s")
         });
         </script>
         """ % {'have_sent_messages_key_str':have_sent_messages_key_str, 'to_uid': have_sent_messages_object.other_ref.urlsafe(),
                                                                           'show_checkbox_js_val': show_checkbox_js_val}        
        
                
        date_sent =  return_time_difference_in_friendly_format(have_sent_messages_object.last_m_date, capitalize = False)
        
        if have_sent_messages_object.mailbox_to_display_this_contact_messages == "trash":      
            mail_icon = "trash_mail.png"
            mail_status = ugettext("Deleted (mail)")
            status_for_time = ugettext("Received") # the time shown is when it was received, not when read
        elif have_sent_messages_object.mailbox_to_display_this_contact_messages == "spam":
            mail_icon = "spam_mail.png"
            mail_status = ugettext("Spam")
            status_for_time = ugettext("Received (mail)") # the time shown is when it was received, not when read
        else:    
            if have_sent_messages_object.owner_is_sender:
                mail_icon = "sent_mail.png"
                mail_status = ugettext("Sent")
                status_for_time = mail_status
            else:
                if have_sent_messages_object.message_chain_has_been_read:
                    mail_icon = "open_mail.png"
                    mail_status = ugettext("Read (mail)")
                    status_for_time = ugettext("Received") # the time shown is when it was received, not when read
                else:
                    mail_icon = "new_mail.png"
                    mail_status = ugettext("New (mail)")
                    status_for_time = mail_status

        date_sent = "%s %s" % (status_for_time, date_sent)
                       
        if show_checkbox_beside_summary:
            generated_html += u'<div id="id-have_sent_messages-%s" class="grid_9 alpha omega \
            cl-mailbox_results cl-mail_seperator"><br>\n' % (have_sent_messages_key_str)            
            
        else:
            generated_html += u'<div id="id-have_sent_messages-%s" class="grid_9 alpha omega \
            cl-mailbox_results"><br>\n' % have_sent_messages_key_str
            
        # if the checkbox is shown, then we are in the mailbox view of the message. Therefore, indicate additional information
        # about the user who has sent the message.
        if show_checkbox_beside_summary:
            summary_table = utils.generate_profile_summary_table(request, other_userobject)
        else:
            summary_table = ''
                        
        icon_html = '<td class="cl-first-mail-icon-td"><img src="/%(live_static_dir)s/img/%(icon)s" align=middle alt=""><br>%(status)s</td>' \
                  % {'icon': mail_icon, 'status' : mail_status, "live_static_dir": settings.LIVE_STATIC_DIR}
        
        # add in the checkbox for marking messages for management (deletion, spam, etc.)
        if show_checkbox_beside_summary:
            generated_html += u'<div class="grid_9 alpha omega">' # internal grid_9
            generated_html += u'<div class="grid_2  alpha">%s</div>\n' % date_sent
            generated_html += u'<div class="grid_7 omega">%s</div>\n' % summary_table
            generated_html += u'</div>' #end internal grid_9
            generated_html += u'<div class="grid_9 alpha omega">' # internal grid_9            
            
            other_userobject_href = profile_utils.get_userprofile_href(request.LANGUAGE_CODE, other_userobject, is_primary_user=False)

            
            generated_html += '<div class="cl-grid_160px  grid_custom alpha omega">\n'
            generated_html += u'<a href="%s" class="cl-mailbox_anchor_format" rel="address:%s"><span><strong>%s</strong></span></a>\n' % (
                other_userobject_href, other_userobject_href, other_userobject.username)
            
            if show_vip_info:
                generated_html += u"<br>%s" % utils.get_vip_online_status_string(other_userobject.key.urlsafe())
        

            checkbox_html = '<td class="cl-mark_conversation-td"><input type = "checkbox" name="mark_conversation" \
            class = "cl-mark_conversation_checkbox" \
            value="%(have_sent_messages_key_str)s"> </td>\n '  % {'have_sent_messages_key_str':have_sent_messages_key_str}

            
            generated_html += FormUtils.generate_profile_photo_html(lang_code, other_userobject, text_fields.no_photo, \
                                other_userobject_href, "small", checkbox_html = checkbox_html, icon_html = icon_html)

                
            generated_html += u'</div> <!-- end grid_160px -->\n'
        
            # container for message and icons
            generated_html += u'<div class="grid_7 alpha omega" id = "id-highlight-div">\n'
            generated_html += u'<div>' # not in this view, but necessary because it is used
                                       # in profile view to draw box around message summary (see cl-gray-box below)       
            # container for all the message information
            generated_html += u'<div id="id-wrap-text-and-control-icons"><br><div class="cl-grid_410px grid_custom alpha">\n'
            mail_control_table_class = "cl-mail-icon-table-120px"
            right_grid_def = u'<div class="cl-grid_120px grid_custom alpha omega cl-center-text">\n'
            new_row_html = "</tr><tr>"

        else:
            
            generated_html += u'<div class="grid_9 alpha omega">' # internal grid_9            
            generated_html += '<div class="grid_2 alpha ">\n'
            generated_html += u'<strong>%s</strong>\n' % ugettext("Message history (click on the message text to see more detailed history)")
            generated_html += u'</div> <!-- end grid2 -->\n'
            generated_html += u'<div class="grid_7 omega" >\n'
            # this is a bit strange -- the folloing div is necessary to allow us to draw a border a without 
            # increasing the size of the grid_7.
            generated_html += u'<div id = "id-highlight-div" class="cl-gray-box alpha omega grid_custom">\n' 
            generated_html += u'<div class="cl-grid_60px grid_custom alpha omega"><br><table class = "cl-mail-icon-table-60px"><tr>'
            generated_html += icon_html
            generated_html += u'</tr></table></div>' # 40px grid
            generated_html += u'<div id="id-wrap-text-and-control-icons" class="cl-grid_478px grid_custom alpha omega"><br>'
            generated_html += u'<div class="cl-grid_458px grid_custom">\n' 
            mail_control_table_class = u"cl-table-no-margin"
            right_grid_def = u'<div class="grid_custom cl-center-text cl-float_right">'
            new_row_html = ''

        
        short_owner_name = userobject.username
        short_other_name = other_userobject.username
        

        
        first_pass = True
    
        # The summary just loops over a small subset of the messages between two users.
        # As of writing only 2 messages are displayed in the summary.
        href =  reverse('mail_message_display', kwargs={'owner_uid' : have_sent_messages_object.owner_ref.urlsafe(), 
                        'other_uid' : have_sent_messages_object.other_ref.urlsafe()})        
        href_open = u'<a href = "%(href)s" class="cl-mailbox_anchor_format" rel="address:%(href)s">' % {'href' : href}
        
        generated_html += href_open
        
        if other_userobject.user_is_marked_for_elimination:
            # provide feedback to the user about why this profile was eliminated
            generated_html += utils.get_removed_user_reason_html(have_sent_messages_object.other_ref.get())

        
        for message in query_for_message: 
    
            # get the key for the m_from profile, without doing a full lookup:
            m_from_key = message.m_from
            if userobject.key == m_from_key:
                # means this is a message sent by the user
                text_color_class = "cl-gray-text";
                sender_name = short_owner_name
                add_emphasis_open = "<em>"
                add_emphasis_close = "</em>"
            else: 
                # received message
                text_color_class = "cl-black-text";
                sender_name = short_other_name
                add_emphasis_open = ""
                add_emphasis_close = ""
         

            if len(message.m_text) >= MAIL_SNIP_CHARS:
                message_text = message.m_text[:MAIL_SNIP_CHARS] + "  ... "
                some_messages_not_shown = True
            else: 
                message_text = message.m_text                
                
                
            generated_html += u'<span class = "%s %s">%s %s %s: %s%s</span><br>\n' % (
               "cl-literally-display-user-text", text_color_class, add_emphasis_open, ugettext("From"), sender_name, message_text, add_emphasis_close)    
            
        generated_html += u'</a>'
        
        if some_messages_not_shown:
            click_for_more_text = "[%s]" % ugettext("click on the message to see more")
            generated_html += u'<span class = "%s %s">%s</span><br>' % ("cl-gray-text", 'cl-bold-text', click_for_more_text)
            
        # container for all the message information
        generated_html += u'</div> <!--grid_5-->\n'
        
        
        #generated_html += u'<div class="cl-grid_8px grid_custom alpha omega">&nbsp;</div>' # a vertical spacer
        generated_html += right_grid_def
        
        # put the mail icon and the eliminate/spam/blocked buttons inside a table.
        generated_html += u'<table class="%s"><tr>' % mail_control_table_class   
        
        def mailbox_magage_html(action, have_sent_messages_key_str, img_html, status, new_row_html):
            return """
            <td class="cl-mail-icon-td">
            <a class="cl-mailbox_anchor_format" id="id-%(action)s-have_sent_messages-%(have_sent_messages_key_str)s" href="#">
            %(img_html)s
            %(status)s
            </a></td>%(new_row_html)s""" \
                           % {"action": action, "have_sent_messages_key_str": have_sent_messages_key_str, "img_html": img_html,
                              'status': status, 'new_row_html' : new_row_html}  
            
        if not have_sent_messages_object.message_chain_has_been_read:
            # allow user to mark message as read
            img_html = '<img src="%s" align=middle alt="Read">' % "/%s/img/checkmark.png" % settings.LIVE_STATIC_DIR
            generated_html += mailbox_magage_html("read", have_sent_messages_key_str, img_html, ugettext("Mark as read"), new_row_html)  
            
        if have_sent_messages_object.mailbox_to_display_this_contact_messages != "trash" and\
           have_sent_messages_object.mailbox_to_display_this_contact_messages != "spam":
            # allow user to mark  this message as trash
            img_html = '<img src="%s" align=middle alt="Delete">' % "/%s/img/mark_trash_mail.png" % settings.LIVE_STATIC_DIR
            generated_html += mailbox_magage_html("trash", have_sent_messages_key_str,  img_html, ugettext("Delete"), new_row_html)
        else: # it is either trash or Spam -- allow the user to move it back to the normal mailbox
            if have_sent_messages_object.owner_is_sender: # show icon to move to "sent" mail
                img_html = '<img src="%s" align=middle alt="Sent">' % "/%s/img/mailbox.png" % settings.LIVE_STATIC_DIR
                status = ugettext("Move to sent mailbox")
            else:
                img_html = '<img src="%s" align=middle alt="Sent">' % "/%s/img/mailbox.png" % settings.LIVE_STATIC_DIR
                status = ugettext("Move to received mailbox")
            generated_html += mailbox_magage_html("inbox", have_sent_messages_key_str, img_html, status, new_row_html)

        if not have_sent_messages_object.owner_is_sender and have_sent_messages_object.mailbox_to_display_this_contact_messages != "spam":
            # allow user to mark  this message as spam
            img_html = '<img src="%s" align=middle alt="Spam">' % "/%s/img/mark_spam_mail.png" % settings.LIVE_STATIC_DIR
            generated_html += mailbox_magage_html("spam", have_sent_messages_key_str, img_html, ugettext("Mark as spam"), new_row_html)
            
        
        # only show the "favorites" icon if the checkbox is shown too -- since having the
        # checkbox indicates that we are looking at the summary from the users mailbox,
        # as opposed to on the profile of another user. Otherwise, if the message has not
        # yet been read, show the "Mark as read" icon so that the user can directly mark the
        # message as having been read, while viewing the other users profile. 
        
        if show_checkbox_beside_summary:

            if have_sent_messages_object.other_is_favorite:
                fav_image = "/%s/img/star_selected.png" % settings.LIVE_STATIC_DIR
                favorite_status = ugettext("Favorite")
            else:
                fav_image = "/%s/img/star_not_selected.png" % settings.LIVE_STATIC_DIR
                favorite_status = ugettext("Add to your favorites")
            img_html = '<img src="%s" align=middle alt=''>' % fav_image

            # allow the user to mark a message as a favorite
            generated_html += mailbox_magage_html("favorite", have_sent_messages_key_str, img_html, favorite_status, new_row_html)            
            
        generated_html += u'</tr></table>'
        
        generated_html += u'</div> <!-- end right grid -->'
        generated_html += u'</div> <!-- end id="id-wrap-text-and-control-icons" -->'
        generated_html += u'</div> <!-- end gray-gox -->'
        generated_html += u'</div> <!-- end grid_7 -->'
        generated_html += u'</div> <!-- end internal grid_9 -->\n'        
        generated_html += u'</div> <!-- end grid_9 -->\n'
        
        # Divider line
        if show_checkbox_beside_summary:
            generated_html += utils.generate_profile_information_for_administrator(other_userobject, utils.user_is_admin(userobject))            
            generated_html += u'<div class="grid_9 alpha omega cl-divider-line"></div>'
            
        return (generated_html, True)

    except:
        error_reporting.log_exception(logging.error, error_message = "object = %s" % repr(have_sent_messages_object))
        return ('', False)
        
###########################################################################



@requires_login
def generate_mailbox(request, bookmark = '', mailbox_name='inbox', owner_uid=''):
    # code for displaying the mailbox of the client. This shows the user that the owner has
    # had contact with, and a summary of their conversation.

    try:
        if not utils.access_allowed_to_page(request, owner_uid):
            return http_utils.redirect_to_url(request, "/%s/" % request.LANGUAGE_CODE)
    
        userobject =  utils_top_level.get_object_from_string(owner_uid)
        username = userobject.username
        show_vip_info = utils.do_display_online_status(owner_uid)
            
        
        generated_html = """<script type="text/javascript">
        $(document).ready(function() {
        fancybox_setup($("a.cl-fancybox-profile-gallery"));
        });
        </script>"""
    
        
        generated_mail_html = '' 
        
        contact_query_results = query_for_which_users_owner_has_contacted(bookmark, userobject, CONTACTS_PAGESIZE+1, mailbox_name)
        
        #generated_mail_html += '<div class="grid_9 alpha omega">&nbsp;</div>\n'
        # add a divider line
        
        generated_mail_html += u'<div class="grid_9 alpha omega cl-divider-line" ></div>'
        
        if not contact_query_results:
            # we did not find any results for the current query. 
            generated_mail_html += u'<div class="cl-clear"></div>\n'
            generated_mail_html += u'%s<br><br><br><br>' % ugettext("You don't have any messages in this mailbox")
            
            # the following code simply resets the unread message counter to zero if we are viewing the 
            # 'new' messages and the query is empty. This is to fix datastore errors that may occasionally
            # cause the counters to be off.
            unread_mail_count_obj = userobject.unread_mail_count_ref.get()
            if mailbox_name == 'new':
                amount_off_by = unread_mail_count_obj.unread_contact_count
                if amount_off_by != 0:
                    try:
                        modify_user_unread_contact_count(userobject.unread_mail_count_ref, -amount_off_by, "NA")
                    except:
                        error_message = "User: %s counter exception" % userobject.username
                        error_reporting.log_exception(logging.error, error_message=error_message)    
       
        show_checkbox_beside_summary = True        
        for have_sent_messages in contact_query_results[:CONTACTS_PAGESIZE]:
            (conversation_html, have_sent_messages_bool) = \
             display_conversation_summary(request, have_sent_messages, show_checkbox_beside_summary, show_vip_info)
            generated_mail_html += conversation_html
    
        generated_mail_html += u'<div class="cl-clear"></div>\n'
    
    
        
        # use the current page bookmark to re-generate the current page after the user has made their modifications
        generated_mail_html += u'<input type=hidden name="current_page_bookmark" value="%s">\n' % bookmark
        generated_mail_html += u'<input type=hidden name="mailbox_name" value="%s">\n' % mailbox_name
        
        
    
        message_controls_html = ''
        message_controls_html += u'<div class="cl-clear"></div>\n'
        
    
        if mailbox_name != "trash" and mailbox_name != "spam":
            message_controls_html += smart_unicode("""
            <div class="grid_9 alpha omega cl-manage_messages-links">
            %(select)s: 
            <a class="cl-mailbox_anchor_format" id="id-mark_all_mesages" href = "#mark_all_mesages">%(all)s&nbsp;</a>,
            <a class="cl-mailbox_anchor_format" id="id-unmark_all_mesages" href = "#unmark_all_mesages">%(none)s&nbsp;</a><br><br>
            </div>
            
            <script type="text/javascript">
            $(document).ready(function() {
               $("#id-mark_all_mesages").click(function() {
                        $("input[name=mark_conversation]").each(function(){
                                this.checked = true;
                        });
                        return false;
                });					
                
                $("#id-unmark_all_mesages").click(function() {
                        $("input[name=mark_conversation]").each(function(){
                                this.checked = false;
                        });
                        return false;
                });		
            });
            
            if (!disable_jquery_address)
                handle_ajax_form_submission_with_button_values('.cl-manage_messages-button', '#id-mark_conversation-form', '#id-body_main_html'); 
            
            </script>""") % {'select': ugettext("Select"), 'all' : ugettext("All (messages - override)"), 'none' : ugettext("None (messages - override)")}
          
        message_controls_html += u'<div class="grid_7 alpha">'
        
        if mailbox_name != "trash" and mailbox_name != "spam":
            message_controls_html += u'<input type="submit" name="mark_delete" id="id-mark_delete" class="cl-manage_messages-button" value="%s">\n' % ugettext("Delete")
            if mailbox_name != "sent":
                message_controls_html += u'<input type="submit" name="mark_read" id="id-mark_read" class="cl-manage_messages-button" value="%s">\n'% ugettext("Mark as read")
        
        message_controls_html += """
        <script type="text/javascript">
        $(document).ready(function() {
            $('.cl-manage_messages-button').button();  
        });
        </script>"""
        
        message_controls_html += u'</div>'
        
        message_controls_html += u'<div class="grid_2 omega">&nbsp;'
        bottom_next_link_html = ''
        if len(contact_query_results) == CONTACTS_PAGESIZE + 1:
            next_page_bookmark = contact_query_results[-1].key.urlsafe()
            next_href = reverse('generate_mailbox_with_bookmark', kwargs = {'bookmark' : next_page_bookmark, 'mailbox_name': mailbox_name, 'owner_uid' : owner_uid})
            next_button = u'<a class="cl-mailbox_anchor_format" href="%s" rel="address:%s">%s >></a>\n' % (next_href, next_href, ugettext("Next"))
            message_controls_html += next_button
            bottom_next_link_html = u'<div class="grid_7 alpha">&nbsp;</div><div class="grid_2 omega">%s</div>' % next_button
    
        message_controls_html += u'</div>\n' # end grid_2
        message_controls_html += u'<div class="cl-clear"></div>\n'        
      
        action_href = reverse('manage_mailbox', kwargs = {"owner_uid" : owner_uid})
        form_open_html = '<form method = "POST" id="id-mark_conversation-form" action="%s"> ' % (
            action_href)
        form_close_html = '</form> '    
    
        be_polite_html = u"""
        <div class="grid_9 alpha omega"><br></div>
        <div class="grid_9 alpha omega cl-light-gray-box">
        <div class="cl-padding-3px">
        **%(please_be_polite)s <strong>%(doesnt_count)s</strong> %(if_spam)s </div></div>
        """ % {'please_be_polite' : ugettext('Please be polite and respond to the people that have made an honest effort to \
contact you.'), 
               'doesnt_count': ugettext('Responding to messages does not count in your daily message quota.'),
               'if_spam' : ugettext('If the message that they have sent to you is not courteous and related to what \
you have specified in your profile, then mark the message as spam without responding.')
               }
        
        
        generated_html += form_open_html + message_controls_html + generated_mail_html + \
                       be_polite_html + bottom_next_link_html + form_close_html
            
        return rendering.render_main_html(request, generated_html, userobject)
    
    except:
        error_reporting.log_exception(logging.critical)
        return http_utils.redirect_to_url(request, "/%s/" % request.LANGUAGE_CODE)
        
        
def modify_message(have_sent_messages_key, mailbox_to_move_message_to):
    # This function  marks the given mesage as "read", and moves it to the indicated mailbox
    #
    # mailbox_to_move_message_to: either "inbox" (if we are just marking it as read), "trash" or "spam".
    
    
    ###################################
    
    # This is in a transaction, because the unread_contact_count must be modified, and this can be 
    # affected by incoming messages at the same time that the user is reading the current message. 
    def txn(have_sent_messages_key):
        
        return_val = ''
        is_dirty = False
        have_sent_messages_object = have_sent_messages_key.get()
        previous_mailbox = have_sent_messages_object.mailbox_to_display_this_contact_messages
        
        if have_sent_messages_object.mailbox_to_display_this_contact_messages != mailbox_to_move_message_to:
            is_dirty = True
            have_sent_messages_object.mailbox_to_display_this_contact_messages = mailbox_to_move_message_to
            
        if not have_sent_messages_object.message_chain_has_been_read:
            have_sent_messages_object.message_chain_has_been_read = True
            return_val = "decrease_unread_contact_count"
            is_dirty = True
        
        if is_dirty:
            have_sent_messages_object.put()  
            
        return(have_sent_messages_object, return_val, previous_mailbox)
    ###################################
    
    try:

        (have_sent_messages_object, return_val, previous_mailbox) =  ndb.transaction(lambda: txn(have_sent_messages_key))
                              
        owner_userobject = have_sent_messages_object.owner_ref.get()
        other_userobject = have_sent_messages_object.other_ref.get()   
        

        if not return_val:
            pass
        elif return_val == "decrease_unread_contact_count":
            try:
                owner_userobject.unread_mail_count_ref = modify_user_unread_contact_count(owner_userobject.unread_mail_count_ref, -1, "NA")
            except:
                error_message = "User: %s counter exception" % owner_userobject.username
                error_reporting.log_exception(logging.error, error_message=error_message)    
        else:
            raise Exception("Unknown return val %s" % return_val)
            
        spam_tracker = other_userobject.spam_tracker.get()
            
        if previous_mailbox == "spam": 
            # we are moving this message out of the spam mailbox -- reduce the spam count on the sender           
            spam_tracker.num_times_reported_as_spammer_total -= 1
            spam_tracker.put()
    
        # if this is a spam message, then keep track of the number of spams that this user has sent
        if mailbox_to_move_message_to == "spam":
            
            # only allow counting of spam if the message was received (not sent), and no response sent --
            # otherwise, the user could jack-up the spam count for another user by repeatedly
            # sending messages, and marking them as Spam
            if not have_sent_messages_object.owner_is_sender:
            
                spam_tracker.num_times_reported_as_spammer_total += 1
                spam_tracker.put()
            
    except:
        error_reporting.log_exception(logging.critical)

    return


def manage_mailbox(request, owner_uid):
    # This function is responsible for moving mail messages between different mailboxes.
    
    try:
        bookmark = request.REQUEST.get('current_page_bookmark', '')
        mailbox_name = request.REQUEST.get('mailbox_name', '')
        
        if mailbox_name:
            mailbox_to_move_message_to = ''
            if request.REQUEST.__contains__("mark_read"):
                mailbox_to_move_message_to = "inbox"
            elif request.REQUEST.__contains__("mark_delete"):
                mailbox_to_move_message_to = "trash"
            elif request.REQUEST.__contains__("mark_spam"):
                mailbox_to_move_message_to = "spam"
            else:
                raise Exception("Post does not contain a valid mailbox to move the messages into")
            
            list_of_have_sent_messages_id = request.POST.getlist('mark_conversation')
            
            for have_sent_messages_id in list_of_have_sent_messages_id:
                have_sent_message_key = ndb.Key(urlsafe = have_sent_messages_id)
                modify_message(have_sent_message_key, mailbox_to_move_message_to)
                
            if not bookmark:
                href = reverse('generate_mailbox', kwargs = {'mailbox_name': mailbox_name, 'owner_uid' : owner_uid})
            else:
                href = reverse('generate_mailbox_with_bookmark', kwargs = {'bookmark' : bookmark, 'mailbox_name': mailbox_name, 'owner_uid' : owner_uid})
            
            return http_utils.redirect_to_url(request, href)
                
        else:
            error_reporting.log_exception(logging.info, error_message = "Expected post data.", request=request)
            return http.HttpResponseServerError("Error")
    except:
        error_reporting.log_exception(logging.critical)
        return http_utils.redirect_to_url(request, "/%s/" % request.LANGUAGE_CODE)
