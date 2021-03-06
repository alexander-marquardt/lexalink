# -*- coding: utf-8 -*- 

################################################################################
# LexaLink Copyright information - do not remove this copyright notice
# Copyright (C) 2012 
#
# Lexalink - a free social network and dating website platform for the Google App Engine. 
#
# Original author: Alexander Marquardt
# Documentation and additional information: http://www.LexaLink.com
# Git source code repository: https://github.com/alexander-marquardt/lexalink 
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

import datetime

from django.utils.translation import ugettext, ungettext

from forms import FormUtils
from user_profile_main_data import UserSpec
from user_profile_details import UserProfileDetails
from html_container import UserMainHTML
from constants import GUEST_NUM_NEW_PEOPLE_MESSAGES_ALLOWED_IN_WINDOW
from utils import get_photo_message, compute_captcha_bypass_string

import utils, localizations, error_reporting, logging, text_fields, settings, constants, store_data, mailbox, messages

###############################
class MyHTMLCallbackGenerator():
    
    # Provides callback functions from the HTML code in the main user page. 
       
    def __init__(self, request, display_userobject, is_primary_user, primary_userobject, have_sent_messages_object):
        
        try:
            self.request = request
            self.lang_code = request.LANGUAGE_CODE
            self.lang_idx = localizations.input_field_lang_idx[request.LANGUAGE_CODE]
            self.is_primary_user = is_primary_user
            
            # display_userobject_ref is object of the user profile that is currently being viewed
            self.display_userobject_ref = display_userobject
            self.display_uid = display_userobject.key.urlsafe()
            
            
            self.primary_userobject_ref = primary_userobject
            if primary_userobject:
                self.owner_uid = primary_userobject.key.urlsafe()
            else:
                self.owner_uid = ''
            
            # the following value is used for tracking if the user is viewing another profile, if these
            # two users have previously had contact. If so, then we dont show all the spam warning stuff.
            self.have_sent_messages_object = have_sent_messages_object

            # if the user is marked for elimination, then due to changes in the code, the
            # checkbox_fields might have invalid values. In any case, there is no point in showing
            # these values since the user has been eliminated.
            if not display_userobject.user_is_marked_for_elimination:
                # To save use from having to declare a bunch of functions, we dynamically create the response
                # to (some of) the html callback functions.
                for field_name in UserProfileDetails.enabled_checkbox_fields_list:
                    setattr(self, field_name, self.standard_checkbox_html(field_name))
                
        except:
            error_reporting.log_exception(logging.critical) 
            
    def signup_fields(self):
        section_label = ugettext("Important data about me")
        generated_html =  UserMainHTML.\
                       define_html_for_main_body_input_section(self.lang_idx,
                           self.display_userobject_ref, "signup_fields", section_label, UserSpec, self.display_uid, "dropdown", self.is_primary_user) 
        return generated_html
    
    def details_fields(self):
        section_label = ugettext("More details about me")
        generated_html =  UserMainHTML.\
                       define_html_for_main_body_input_section(self.lang_idx,
                           self.display_userobject_ref, "details_fields", section_label, UserProfileDetails, self.display_uid, "dropdown", self.is_primary_user) 
        return generated_html  
    
    def languages(self):
        try:
            section_label = UserProfileDetails.checkbox_fields['languages']['label'][self.lang_idx]
            if settings.BUILD_NAME == "language_build":
                if not self.is_primary_user:
                    # Override the label for people that are viewing the profile -- it doesn't need to be so 
                    # informative.
                    section_label = ugettext('Languages I speak')
                    
            generated_html =  UserMainHTML.\
                           define_html_for_main_body_input_section(self.lang_idx,
                               self.display_userobject_ref, "languages", section_label, None, self.display_uid, "checkbox", self.is_primary_user) 
            return generated_html
        except:
            error_reporting.log_exception(logging.critical)       
            return '' 
        
    def standard_checkbox_html(self, field_name):
        try:
            section_label = UserProfileDetails.checkbox_fields[field_name]['label'][self.lang_idx]
            generated_html =  UserMainHTML.\
                           define_html_for_main_body_input_section(self.lang_idx,
                               self.display_userobject_ref, field_name, section_label, None, self.display_uid, "checkbox", self.is_primary_user) 
            return generated_html
        except:
            error_reporting.log_exception(logging.critical)       
            return '' 


    def email_address(self):
        section_label = ugettext("Email")
        generated_html =  UserMainHTML.\
                       define_html_for_main_body_input_section(self.lang_idx,
                           self.display_userobject_ref, "email_address", section_label, None, self.display_uid, "email_address", self.is_primary_user)     
        return generated_html
    
    def about_user(self):
        section_label = ugettext("About myself and what I am looking for")
        generated_html =  UserMainHTML.\
                       define_html_for_main_body_input_section(self.lang_idx,
                           self.display_userobject_ref, "about_user", section_label, None, self.display_uid, "about_user", self.is_primary_user)     
        return generated_html   
    
        
    def current_status(self):
        generated_html = ''
        if self.is_primary_user:
            section_label = ugettext("Headline")
            generated_html =  UserMainHTML.\
                           define_html_for_main_body_input_section(self.lang_idx,
                               self.display_userobject_ref, "current_status", section_label, None, self.display_uid, "current_status", self.is_primary_user)     
        return generated_html

    def current_status_value(self):
        # returns just the value stored in the "current_status" for the profile currently being viewed
        generated_html = ''
        if not self.display_userobject_ref.user_is_marked_for_elimination and self.display_userobject_ref.current_status != "----":
            generated_html = self.display_userobject_ref.current_status
        return generated_html
    
    def current_status_time_in_friendly_format(self):
        generated_html = utils.return_time_difference_in_friendly_format(self.display_userobject_ref.current_status_update_time)
        return generated_html
    
    def email_options(self):
        section_label = UserProfileDetails.checkbox_fields['email_options']['label'][self.lang_idx]
        generated_html =  UserMainHTML.\
                       define_html_for_main_body_input_section(self.lang_idx,
                           self.display_userobject_ref, "email_options", section_label, None, self.display_uid, "checkbox", self.is_primary_user) 
        return generated_html
    
    def change_password_fields(self):
        section_label = ugettext("Modify my password")
        generated_html = UserMainHTML.\
                       define_html_for_main_body_input_section(self.lang_idx,
                           self.display_userobject_ref, "change_password_fields", section_label, None, self.display_uid, "change_password", self.is_primary_user)
        return generated_html
    
    def photos(self):
        return FormUtils.generate_photos_html(self.lang_code, self.display_userobject_ref, self.primary_userobject_ref, 
                                              is_primary_user = self.is_primary_user)

    def profile_photo(self):
        if self.is_primary_user:
            return FormUtils.generate_profile_photo_html(self.lang_code, self.display_userobject_ref, text_fields.photo_encouragement_text, 
                                                         is_primary_user = self.is_primary_user)
        else: # this is a profile that is being viewed by non-owner
            photo_message = get_photo_message(self.display_userobject_ref)
            return FormUtils.generate_profile_photo_html(self.lang_code, self.display_userobject_ref, photo_message)
        

    
    def mail_textarea(self):
        # note, self.display_uid in this case refers to the profile being viewed, not the owner
        # (however, if the owner is viewing their own profile, then this does refer to the owner).
        # This is intended for displaying a textarea for sending mail, right on the profile page
        # of another user. 
        
        try:
            userobject = self.primary_userobject_ref
            if userobject:
                owner_uid = self.owner_uid
                
                spam_tracker = userobject.spam_tracker.get()
                num_messages_sent_in_window = spam_tracker.num_mails_sent_in_window
                num_messages_sent_in_total = spam_tracker.num_mails_sent_total
                num_times_reported_as_spammer_total = spam_tracker.num_times_reported_as_spammer_total
                
               
                generated_html = ""
                will_be_reset = ""


                # Check if the user is a VIP and has extra message quota
                if not utils.get_client_vip_status(userobject):
                    max_num_new_people_messaged_in_window = constants.GUEST_NUM_NEW_PEOPLE_MESSAGES_ALLOWED_IN_WINDOW
                    hours_before_reset = constants.GUEST_WINDOW_HOURS_FOR_NEW_PEOPLE_MESSAGES
                else:
                    # VIP member has extra messages allocated
                    max_num_new_people_messaged_in_window = constants.VIP_NUM_NEW_PEOPLE_MESSAGES_ALLOWED_IN_WINDOW
                    hours_before_reset = constants.VIP_WINDOW_HOURS_FOR_NEW_PEOPLE_MESSAGES
                                    
                
                when_to_reset_new_people_contacted_counter = spam_tracker.datetime_first_mail_sent_in_window + \
                   datetime.timedelta(hours = hours_before_reset) 
                time_left_to_reset_new_people_contacted_counter = when_to_reset_new_people_contacted_counter -  datetime.datetime.now()
    
                
                if time_left_to_reset_new_people_contacted_counter - datetime.timedelta(hours = constants.RESET_MAIL_LEEWAY) >\
                   datetime.timedelta(seconds = 0):
                    restart_spam_counter = False
                else:
                    # Reset the spam counter since the time limit (since the first message of the day was sent) has passed. 
                    restart_spam_counter = True
                    
                if not self.have_sent_messages_object:
                    if num_messages_sent_in_window >= max_num_new_people_messaged_in_window and not restart_spam_counter:
                    
                        time_to_reset_txt = utils.return_time_difference_in_friendly_format(when_to_reset_new_people_contacted_counter, capitalize = False, 
                                                              data_precision = 2, time_is_in_past = False, show_in_or_ago = True)                

                        will_be_reset = u"%s" % ugettext("Your quota will be reset %s") % time_to_reset_txt
                    
                        generated_html = """<div id="id-num_messages_sent_feedback_and_count">"""
                        
                        num_new_people_txt = ungettext("%(num)s new person",
                                                       "%(num)s new people",max_num_new_people_messaged_in_window) % {
                                                           'num': max_num_new_people_messaged_in_window}                

                        people_in_the_past = ugettext("People that you have already exchanged messages with in the past do not count in this limit, and responding to messages does not use any of this quota")


                        if utils.get_client_vip_status(userobject):
                            vip_member_is_allowed_to_contact = u"%s" % ugettext(
                                "As a VIP Member, you are allowed to message %(num_new_people_txt)s every %(hr)s hours") % {
                                                         'num_new_people_txt' : num_new_people_txt, 'hr':hours_before_reset, }
                            generated_html += u"%s<br><br>" %  """
                            %(vip_member_is_allowed_to_contact)s.
                            %(people_in_the_past)s. %(will_be_reset)s.
                            """ % {'vip_member_is_allowed_to_contact': vip_member_is_allowed_to_contact,
                                    'people_in_the_past' : people_in_the_past,
                                    'will_be_reset' : will_be_reset }
                        else:
                            if constants.THIS_BUILD_ALLOWS_VIP_UPGRADES:
                                you_are_allowed_to_contact_prefix = ugettext("Since you are not yet a %(vip_member)s, you can") % {
                                    'vip_member' : constants.vip_member_anchor % constants.vip_member_txt}
                            else:
                                you_are_allowed_to_contact_prefix = ugettext("You can")

                            you_are_allowed_to_contact = u"%s" % ugettext(
                                "%(you_are_allowed_to_contact_prefix)s contact %(num_new_people_txt)s every %(num_days)s days") % {
                                                            'you_are_allowed_to_contact_prefix' : you_are_allowed_to_contact_prefix,
                                                            'num_new_people_txt' : num_new_people_txt,
                                                            'num_days': constants.GUEST_WINDOW_DAYS_FOR_NEW_PEOPLE_MESSAGES,
                                                            'vip_member' : constants.vip_member_anchor % constants.vip_member_txt}

                            generated_html += u"%s<br><br>" % """
                            %(you_are_allowed_to_contact)s.
                            %(people_in_the_past)s. %(will_be_reset)s.
                            """ % {'you_are_allowed_to_contact' : you_are_allowed_to_contact,
                                    'people_in_the_past':people_in_the_past,
                                    'will_be_reset' : will_be_reset,}

                        if constants.THIS_BUILD_ALLOWS_VIP_UPGRADES:
                                generated_html += u" %s.<br><br>" % ugettext("""If you wish to increase this limit, read about the benefits of becoming a %(vip_member)s""") % {
                                    'vip_member' : constants.vip_member_anchor % constants.vip_member_txt}


                        
                        generated_html += "</div>"
                
                # if they have already sent num_new_people_messaged_per_day, they cannot send to any new clients, only
                # people they have already had contact with.
                
                if num_messages_sent_in_window < max_num_new_people_messaged_in_window or self.have_sent_messages_object or restart_spam_counter:
                    (show_captcha, spam_statistics_string) = messages.determine_if_captcha_is_shown(userobject, self.have_sent_messages_object)
                    generated_html += mailbox.generate_mail_textarea(u"send_mail_from_profile_checkbox_no", owner_uid, self.display_uid, 
                                                                     self.have_sent_messages_object, show_captcha, spam_statistics_string)
                    
                generated_html += "<!-- messages sent in window: %s sent int total %s -->" % (num_messages_sent_in_window, num_messages_sent_in_total)
            else:
                # no userobject - this is probably a user that is just browsing. Show the textbox input, but they cannot send messages
                # until after they have registered.
                generated_html = FormUtils.define_html_for_mail_textarea(
                    u"send_mail_from_profile_checkbox_no", self.display_uid, captcha_bypass_string="dummy", 
                    have_sent_messages_object = None, show_registration_dialog_on_click_send = True)
              
            return generated_html
        except:
            error_reporting.log_exception(logging.critical)       
            return ''    
        
    def contact_table(self):
        generated_html = FormUtils.contact_table(self.display_uid, self.owner_uid)     
        return generated_html
    
    def verify_new_user(self):
        generated_html = FormUtils.define_html_for_verify_new_captcha("verify_new_user")
        return generated_html
    
    def report_unacceptable_profile(self):
        generated_html = FormUtils.html_for_report_unacceptable_profile("report_unacceptable_profile", self.owner_uid, self.display_uid)
        return generated_html
