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


from os import environ

from google.appengine.ext import ndb
from google.appengine.api import memcache, users

import hashlib, re, urllib
import datetime
import string, random, sys

from django import http
from django.utils.translation import ugettext, ungettext
from django.template import loader, Context

import settings, site_configuration


from rs import constants
from rs import text_fields
from rs import online_presence_support
from rs import user_profile_main_data, localizations, models, utils_top_level, user_profile_details

from rs.models import UnreadMailCount, CountInitiateContact
from rs.utils_top_level import serialize_entity, deserialize_entity
from rs.import_search_engine_overrides import *
from rs.models import UserModel

from rs.localization_files import currency_by_country

#############################################
def requires_login(view):
    # this function will wrap other functions such that if the user is not logged-in, 
    # all accesses to the website should be re-directed to login screen.
    def new_login_view(request, *args, **kwargs):
         #make sure that there is a current session object that points to a particular userobject
        if request.session.__contains__('userobject_str'):
            return view(request, *args, **kwargs)
        
        elif request.session.__contains__(constants.CRAWLER_SESSION_NAME):
            # this is a special case -- google crawler has access to many private pages as required 
            # for correctly displaying advertisements.
            remoteip  = environ['REMOTE_ADDR']      
            
            if constants.GOOGLE_CRAWLER_IP_PATTERN.match(remoteip) or \
               constants.MY_HOME_IP_PATTERN.match(remoteip) or \
               constants.LOCAL_IP_PATTERN.match(remoteip):
                error_reporting.log_exception(logging.info, error_message = 'Google crawler page access') 
                return view(request, *args, **kwargs)
            else:
                error_reporting.log_exception(logging.warning, error_message = 'Crawler session invalid IP') 
                return http.HttpResponseForbidden()
        else: 
            
            # check the IP address to see if it is the google web-crawler .
            remoteip  = environ['REMOTE_ADDR']
            
            if constants.GOOGLE_CRAWLER_IP_PATTERN.match(remoteip):
                # if it is the web-crawler - let then know that they need authorization to view the page.
                error_reporting.log_exception(logging.warning, error_message = 'Google crawler unauthorized access (No session)')
                return http.HttpResponseForbidden()
                
            else:
                error_reporting.log_exception(logging.warning, error_message = 'Error: Non-logged in user unauthorized access - redirect to /') 
                return http.HttpResponseRedirect("/%s/" % request.LANGUAGE_CODE)

    return new_login_view
  

def ajax_call_requires_login(view):
    # this function will wrap other functions such that if the user is not logged-in, 
    # all accesses to the website should be re-directed to login screen.
    def new_login_view(request, *args, **kwargs):
         #make sure that there is a current session object that points to a particular userobject
        if request.session.__contains__('userobject_str'):
            return view(request, *args, **kwargs)
        else: #direct to login page
            error_message = """Error, hemos perdido tu session - deberias 
            <a href="/">entrar</a> en %(app_name)s otra vez.""" % {'app_name': settings.APP_NAME}
            error_reporting.log_exception(logging.warning, error_message = error_message) 
            return http.HttpResponse(error_message)

    return new_login_view

####
def generic_html_generator_for_list(lang_idx, field_name, list_of_field_vals, max_num_entries = sys.maxint):

    # prints out the list of checkbox-selected values in a format appropriate for display
    # in the user_main page. 
    
    from user_profile_details import UserProfileDetails
    
    try:
        generated_html = ''
        
        for (idx, field_val) in enumerate(list_of_field_vals):
            
            if field_val == "----":
                continue
            
            option_in_current_language = UserProfileDetails.checkbox_options_dict[field_name][lang_idx][field_val]
                
            if idx >= max_num_entries - 1:
                    # we are breaking out early .. should indicate that there are more values
                if field_val != list_of_field_vals[-1]:
                    if settings.BUILD_NAME == 'language_build':
                        generated_html += u"%s" % ugettext('and other (languages)...')
                    else:
                        assert(0)
                else:
                    generated_html += u'%s' % option_in_current_language
                break
            
            elif field_val != list_of_field_vals[-1]: # check to see if it is the last entry, and if so don't follow by a comma
                generated_html += u'%s, ' % option_in_current_language
            else:
                # we could try to make this more gramatically correct in the future, however this requires applying additional
                # logic to determin if an "and" or an "or" should be inserted before the last entry - for now, leave it as comma seperated
                generated_html += u'%s' % option_in_current_language

        return generated_html
    except:
        error_reporting.log_exception(logging.critical)       
        return ''
    
#############################################

def generate_profile_summary_table(request_lang_code, profile):

    current_language = request_lang_code
    lang_idx = localizations.input_field_lang_idx[current_language]
    
    generated_html = ''
    
    try:
        if settings.BUILD_NAME != "language_build" and settings.BUILD_NAME != "friend_build":        
            relationship_status_def = "%s"\
                % user_profile_main_data.UserSpec.signup_fields_options_dict['relationship_status'][lang_idx][profile.relationship_status]
            preference_def =  u"%s" % user_profile_main_data.UserSpec.signup_fields_options_dict['preference'][lang_idx][profile.preference]

        else:
            if settings.BUILD_NAME == "language_build":
            
                languages_spoken_list = generic_html_generator_for_list(lang_idx, 'languages', profile.languages, max_num_entries = constants.NUM_LANGUAGES_IN_PROFILE_SUMMARY)
                languages_to_learn_list = generic_html_generator_for_list(lang_idx, 'languages_to_learn', profile.languages_to_learn, max_num_entries = constants.NUM_LANGUAGES_IN_PROFILE_SUMMARY)
                
                native_language_def = "%s"\
                    % user_profile_main_data.UserSpec.signup_fields_options_dict['native_language'][lang_idx][profile.native_language]
                #language_to_learn_def = "%s"\
                 #   % user_profile_main_data.UserSpec.signup_fields_options_dict['language_to_learn'][lang_idx][profile.language_to_learn]

        sex_def = u"%s" % user_profile_main_data.UserSpec.signup_fields_options_dict['sex'][lang_idx][profile.sex]
        
        country = profile.country
        region = profile.region
        sub_region = profile.sub_region
        
        if sub_region and sub_region != "----": 
            location_def = u"%s, %s, %s" % (localizations.location_dict[lang_idx][sub_region],
                                          localizations.location_dict[lang_idx][region], 
                                          localizations.location_dict[lang_idx][country])    
        elif region and region != "----" :
            location_def = u"%s, %s" % (localizations.location_dict[lang_idx][region], 
                                            localizations.location_dict[lang_idx][country])
            
        elif country:
            location_def = u"%s" % localizations.location_dict[lang_idx][country]
    
      
        else:
            error_message = "While displaying summary of: %s - Unable to decipher location: country: %s region: %s sub_region: %s" % (
                profile.username, country, region, sub_region)
            error_reporting.log_exception(logging.error, error_message = error_message) 
            location_def = ""
    
            
            
        age_def = u"%s" % user_profile_main_data.UserSpec.signup_fields_options_dict['age'][lang_idx][profile.age]
    
        
        generated_html += '<table class="cl-table-user-summary"><tr>'
        
        sex_text = u"%s:" % ugettext("I am")
        preference_text = u"%s:" % ugettext("Preference")
        relationship_status_text = u"%s:" % ugettext("Relationship status") #override this in the english translation dict
        languages_spoken_text = u"%s:" % ugettext("I fluently speak")
        languages_to_learn_text = u"%s:" % ugettext("I want to practice")
        looking_for_text = u"%s:" % ugettext("Looking for")
        age_text = u"%s:" % ugettext("My age")
        price_text = u"%s:" % ugettext("My price")

        if settings.BUILD_NAME != "language_build" and settings.BUILD_NAME != "friend_build":
            location_text = u"%s:" % ugettext("In location") # override this for english (and obviously for others as well)
        else:
            location_text = u"%s:" % ugettext("I am currently in")
        

        first_row_html = second_row_html = ''
        if settings.BUILD_NAME != "language_build" and settings.BUILD_NAME != "friend_build":
            first_row_html += '<td class = "cl-left-align-user-summary-text-normal"><strong>%s</strong></td>' % sex_text
            second_row_html += '<td class = "cl-summary-info">%s</td>' % sex_def
            
            first_row_html += '<td class = "cl-left-align-user-summary-text-normal"><strong>%s</strong>' % preference_text
            second_row_html += '<td class = "cl-summary-info">%s</td>' % preference_def

            if settings.BUILD_NAME == 'discrete_build' or settings.BUILD_NAME == 'swinger_build' or settings.BUILD_NAME == 'gay_build':
                first_row_html += '<td class = "cl-left-align-user-summary-text-normal"><strong>%s</strong></td>' % relationship_status_text
            elif settings.BUILD_NAME == 'single_build' or settings.BUILD_NAME == 'lesbian_build' or settings.BUILD_NAME == "mature_build" or settings.BUILD_NAME == "default_build": 
                first_row_html += '<td class = "cl-left-align-user-summary-text-normal"><strong>%s</strong></td>' % looking_for_text
            else: assert(0)
            second_row_html += '<td class = "cl-summary-info">%s</td>' % relationship_status_def
                
            first_row_html += '<td class = "cl-left-align-user-summary-text-narrower"><strong>%s</strong></td>' % age_text
            second_row_html += '<td class = "cl-summary-info">%s</td>' % age_def
            
            first_row_html += '<td class = "cl-left-align-user-summary-text-230px"><strong>%s</strong></td>' % location_text
            second_row_html += '<td class = "cl-summary-info">%s</td>' % location_def
            
        else:
            if settings.BUILD_NAME == "language_build":
                first_row_html += '<td class = "cl-left-align-user-summary-text-for-languages"><strong>%s</strong></td>' % languages_spoken_text
                second_row_html += '<td class = "cl-summary-info">%s</td>' % languages_spoken_list
    
                first_row_html += '<td class = "cl-left-align-user-summary-text-for-languages"><strong>%s</strong></td>' % languages_to_learn_text
                second_row_html += '<td class = "cl-summary-info">%s</td>' % languages_to_learn_list

            first_row_html += '<td class = "cl-left-align-user-summary-text-normal"><strong>%s</strong></td>' % sex_text
            second_row_html += '<td class = "cl-summary-info">%s</td>' % sex_def
                        
            first_row_html += '<td class = "cl-left-align-user-summary-text-narrower"><strong>%s</strong></td>' % age_text
            second_row_html += '<td class = "cl-summary-info">%s</td>' % age_def           
            
            first_row_html += '<td class = "cl-left-align-user-summary-text-170px"><strong>%s</strong></td>' % location_text
            second_row_html += '<td class = "cl-summary-info">%s</td>' % location_def

            
        generated_html += first_row_html + '</tr><tr>' + second_row_html
        generated_html += '</tr></table>'
        
        return generated_html

    except:
        error_reporting.log_exception(logging.critical, error_message = 'Unable to generate summary for %s' % profile.username)       
        return ''
    
    


def get_username_from_userobject(userobject):
    
    if userobject: 
        userobject_name = userobject.username
    else: 
        userobject_name = "No userobject found"
    return userobject_name

def get_username_from_request(request):
    
    userobject = utils_top_level.get_userobject_from_request(request)
    return get_username_from_userobject(userobject)


def access_allowed_to_page(request, profile_uid, ):
    # make sure that the person who is trying to view the current page has been authorized to view the current page
    # Private pages can only be viewed by the owner of the profile, or by the google crawler (as required for 
    # correctly displaying advertisements)
    
    if request.session.__contains__('userobject_str') and (profile_uid == request.session['userobject_str']): 
        return True    
    
    elif request.session.__contains__(constants.CRAWLER_SESSION_NAME):
        # This is a crawler session, and therefore is allowed to see the page.
        return True
    
    else:
        error_reporting.log_exception(logging.error, error_message = "Invalid page access")
        return False

    
##############################################
        
def put_object(object_to_put):
    """ 
    Function to write an object and ensure that memcache is written at the same time.
    Do *not* use this to write userobjects - user put_userobject() which has additional error checking
    and memcache related functionality .
    
    Objects written with this function can be extracted with: utils_top_level.get_object_from_string(object_str)
    """
    
    object_to_put.put()
    
    # Removed - NDB should be automatically caching 
    # memcache_key_str = constants.BASE_OBJECT_MEMCACHE_PREFIX + object_to_put.key.urlsafe()
    # memcache.set(memcache_key_str, serialize_entities(object_to_put), constants.SECONDS_PER_MONTH)
    

def put_userobject(userobject):
    # writes the userobject. 
    
    # make sure that we are not accidently erasing critical information (as has happened in the past)
    # We know that the following fields should *never* be empty. (Note: email_address is set to "----"
    # if it is not used).
    
    error = ""
    if not userobject.username:
        error += "Error in put_user_object: attempt to clear username %s\n" % userobject.username

    if not userobject.password:
        error += "Error in put_user_object: attempt to clear user password %s\n" % userobject.username
        
    if not userobject.email_address:
        error += "Error in put_user_object: attempt to clear user email_address %s\n" % userobject.username
        
    if error:
        logging.critical(error)
        # return without writing the userobject!!
        return
        
    put_object(userobject)
                 
    # Invalidate the memcached url_description for this userprofile since it has potentially changed.
    uid = userobject.key.urlsafe()
    
    
    for lang_tuple in settings.LANGUAGES:
        lang_code = lang_tuple[0]
        url_description_memcache_key_str = lang_code + constants.PROFILE_URL_DESCRIPTION_MEMCACHE_PREFIX + uid
        memcache_status = memcache.delete(url_description_memcache_key_str)
        
        profile_title_memcache_key_str = lang_code + constants.PROFILE_TITLE_MEMCACHE_PREFIX + uid
        memcache_status = memcache.delete(profile_title_memcache_key_str)
        

    
def get_active_userobject_from_username(username):
    
    try:
        q = UserModel.query().order(-UserModel.last_login_string)
        # ensure that unique_last_login None values are removed -- these are backup objects
        q = q.filter(UserModel.user_is_marked_for_elimination == False)
        q = q.filter(UserModel.username == username)
                            
        if q.count(2) > 1:
            logging.critical("User %s has more than one active userobject" % username)
    
        userobject = q.get()
        if userobject:
            # use memcache.add since we don't need to invalidate old data if the key is already valid
            memcache_key_str = userobject.key.urlsafe() + settings.VERSION_ID
            memcache.add(memcache_key_str, serialize_entity(userobject), constants.SECONDS_PER_MONTH)
            return userobject
        else:
            return None
    except:
        error_reporting.log_exception(logging.critical, error_message = 'Error in get_active_userobject_from_username') 
        return None
    
def old_passhash(raw_password, salt=''):
    
    # hash the password so that it is unreadable
    if not salt:
        salt = ''
    pwhash = hashlib.sha1()
    pwhash.update(raw_password.encode('utf-8') + salt.encode('utf-8'))
    return pwhash.hexdigest()

def new_passhash(raw_password, salt):
    
    # hash the password so that it is unreadable
    if not salt:
        salt = ''
    pwhash = hashlib.sha512()
    pw_with_salt = raw_password.encode('utf-8') + salt.encode('utf-8')
    pwhash.update(pw_with_salt)
    return pwhash.hexdigest()

def html_to_request_new_password(email_address):
    generated_html = ''
    generated_html += u"<p><strong>%s</strong> " % ugettext("Have you forgotten your password?")
    url_encoded_email_address = urllib.quote(email_address)
    text_link_for_new_password = "<a href=http://www.%(app_name)s.com/rs/reset_password/%(url_encoded_email_address)s/>%(here)s</a> " % {
        'app_name' : settings.APP_NAME, 'here' : ugettext("Here"), 'url_encoded_email_address' : url_encoded_email_address}
    generated_html += u"<ul><li>%s %s.</li></ul><br><br>" % (text_link_for_new_password, ugettext("you can request a new password"))    
    return generated_html


def get_new_contact_count_sum(new_contact_counter):
    # simply counts up the total number of contact items received since the previous last time the user has logged in
    # This also adds in the values since the current login, so that the value will reflect the total count since 
    # previous last login, up to the current minute.
    
    counter_postfix = "_since_last_reset"
    sum = 0

    sum += getattr(new_contact_counter, 'num_received_kiss' + counter_postfix)
    sum += getattr(new_contact_counter, 'num_received_wink' + counter_postfix)
    sum += getattr(new_contact_counter, 'num_received_key' + counter_postfix)
    sum += getattr(new_contact_counter, 'num_received_chat_friend' + counter_postfix)
    sum += getattr(new_contact_counter, 'num_connected_chat_friend' + counter_postfix)
    
    return sum


def create_unread_mail_object():
    # creates and returns a new object of type UnreadMailCount
    unread_mail = UnreadMailCount()
    unread_mail.unread_contact_count = 0
    unread_mail.put()
    return unread_mail.key
    
def create_contact_counter_object():
    contact_counter = CountInitiateContact()
    # no need to set defaults to 0, as this is already done in the model definition.
    contact_counter.put()
    return contact_counter.key

def get_vip_online_status_string(userobject_key):
    online_status = online_presence_support.get_online_status(userobject_key)
    
    icon = '<span class="cl-dot cl-%s_dot"></span>' % constants.OnlinePresence.presence_color_dict[online_status]
    
    status_string = u"%s %s" % (icon, constants.OnlinePresence.presence_text_dict[online_status])
    return status_string
    
    

def get_photo_message(userobject):

    # generate the message to be shown in the profile photo space if a photos is not available,
    # and when viewed by non-owners of the account.

    unique_last_login_object = userobject.unique_last_login_offset_ref.get()
    
    try:
        if unique_last_login_object.has_public_photo_offset and unique_last_login_object.has_private_photo_offset:
            photo_message = u"%s" % (text_fields.has_private_and_public_photos)
        elif unique_last_login_object.has_public_photo_offset:
            photo_message = u"%s" % (text_fields.has_public_photos)
        elif unique_last_login_object.has_private_photo_offset:
            photo_message = u"%s" %  (text_fields.has_private_photos)
        else:
            photo_message = u"%s" %  (text_fields.has_no_photos)
    except:
        photo_message = u''
        error_reporting.log_exception(logging.critical)       

            
    return photo_message
           
def break_time_difference_into_sub_units(time_difference):
    
    weeks, days = divmod(time_difference.days, 7)
    minutes, seconds = divmod(time_difference.seconds, 60)
    hours, minutes = divmod(minutes, 60)    
    return (weeks, days, hours, minutes, seconds)

def return_time_difference_in_friendly_format(time_to_display, capitalize = True, data_precision = 2, time_is_in_past = True, show_in_or_ago = True):
    
    #  time_to_display is a datetime object.
    # This function will return a more user-friendly (timezone neutral) display of 
    # the "time_to_display" value. If time_to_display is sufficiently far in the past/future, then
    # we just print the GMT date, as timezone differences will not be significant.
    # data_precision is the number of data points related to time that we will show. Eg. if the value is 2, then we will show
    # hours and minutes, or days and hours, or weeks and days .. but only 2 values.
    
    newer_time = datetime.datetime.now()
    
    if time_is_in_past:
        time_difference = newer_time - time_to_display
    else:
        time_difference = time_to_display - newer_time
    
    (weeks, days, hours, minutes, seconds) = break_time_difference_into_sub_units(time_difference)
    
    precision_count = 0

    generated_html = ''
    
    if weeks>0:
        generated_html = u'%s' % time_to_display.strftime("%d-%b-%Y")
        precision_count += 1
    
    else: 

          
        
        if days > 0:
            days_text = ungettext(
                    '%(days)s day',
                    '%(days)s days',
                    days
            ) % {
                'days': days,
            }     
            precision_count += 1
        else:
            days_text = ''
        
        
        if hours>0 and precision_count < data_precision:
            hours_text = ungettext(
                    '%(hours)s hour',
                    '%(hours)s hours',
                    hours
            ) % {
                'hours': hours,
            }     
            precision_count += 1    
            if days_text:
                hours_text = ", %s" % hours_text             
        else:
            hours_text = ''
            
            
        if  minutes >0 and precision_count < data_precision:
            minutes_text = ungettext(
                    '%(minutes)s minute',
                    '%(minutes)s minutes',
                    minutes
            ) % {
                'minutes': minutes,
            }     
            precision_count += 1    
            if hours_text or days_text:
                minutes_text = ", %s" % minutes_text            
        else:
            minutes_text = ''
 
            
        if  seconds >=0 and precision_count < data_precision:
            seconds_text = ungettext(
                    '%(seconds)s second',
                    '%(seconds)s seconds',
                    seconds
            ) % {
                'seconds': seconds,
            }     
            precision_count += 1    
            if minutes_text or hours_text or days_text:
                seconds_text = ", %s" % seconds_text
        else:
            seconds_text = ''      
            
        joined_time = "%s%s%s%s" % (days_text, hours_text, minutes_text, seconds_text)
        
        if time_is_in_past:
            if show_in_or_ago:
                if capitalize:
                    ago_text = ugettext("ago (capitalize if first word)")
                else:                  
                    ago_text = ugettext("ago")
            else:
                ago_text = ''
                
            generated_html = ugettext("%(joined_time)s %(ago_text)s") % {'joined_time' : joined_time, 'ago_text' : ago_text}
        else:
            # time is in the future
            if show_in_or_ago:
                if capitalize:
                    in_text = ugettext("In")
                else:                  
                    in_text = ugettext("in")
            else:
                in_text = ''
            generated_html = "%(in_text)s %(joined_time)s" % {'joined_time' : joined_time, 'in_text' : in_text}

             
    return generated_html

def compute_captcha_bypass_string(sender_uid, receiver_uid):
    # this is a function that provides some level of security for the captcha, since this key
    # must be known if the captcha is to be bypassed when sending a message between two users.
    
    # only compute it based on the last few characters
    return old_passhash(sender_uid[-5:]  + receiver_uid[-5:])


def left_pad_with_nbsp(desired_length, input_string):
    
    string_length = len(input_string)
    
    if string_length > desired_length:
        return input_string
    else:
        num_nbsp = desired_length - string_length
        nbsp_string = ''.join(['&nbsp;' for num in xrange(num_nbsp)])
        return ''.join([nbsp_string, input_string])

        
def right_pad_with_nbsp(desired_length, input_string):
    
    string_length = len(input_string)
    
    if string_length > desired_length:
        return input_string
    else:
        num_nbsp = desired_length - string_length
        nbsp_string = ''.join(['&nbsp;' for num in xrange(num_nbsp)])
        return ''.join([input_string, nbsp_string])
    

def break_long_words(original_string, word_length):
    
    str_list = []
    lines = original_string.splitlines()
    
    for line in lines:
        words = line.split(" ")
        for word in words:
            if word: # don't do anything if empty string or None
                if len(word) > word_length:
                    for i in xrange(0,len(word),word_length):
                        new_word = word[i:i+word_length]   
                        str_list.append(new_word)  
                        str_list.append(" ")
                else:
                    str_list.append(word)
                    str_list.append(" ")
        
        if line != lines[-1]:
            # only add in the return if it is not the last line
            str_list.append("\n")

    return_string = "".join(str_list)
    return return_string


def clone_entity(e, **extra_args):
    """Clones an entity, adding or overriding constructor attributes.
  
    The cloned entity will have exactly the same property values as the original
    entity, except where overridden. By default it will have no parent entity or
    key name, unless supplied.
  
    Args:
      e: The entity to clone
      extra_args: Keyword arguments to override from the cloned entity and pass
        to the constructor.
    Returns:
      A cloned, possibly modified, copy of entity e.
      
      
    Example usage:
      
      b = clone_entity(a)
      c = clone_entity(a, key_name='foo')
      d = clone_entity(a, parent=a.key().parent())   
    """
    
    klass = e.__class__
    props = dict((k, v.__get__(e, klass)) for k, v in klass._properties.iteritems())
    props.update(extra_args)
    return klass(**props)


NUM_PASSWORD_CHARS = 5

def gen_passwd():
    newpasswd = ''
    chars = string.digits
    for i in range(NUM_PASSWORD_CHARS):
        newpasswd = newpasswd + random.choice(chars)
    return newpasswd


def compute_secret_verification_code(username, email_address):
    # computes a secret code that is used for verifying a particular username and email_address.

    # generate a 7 digit random number (stored as a string)
    secret_verification_code = "%d" % random.randint(1000000, 9999999)
    return secret_verification_code


def check_if_user_has_denounced_profile(owner_uid, display_uid):
    # checks if the owner userobject has reported the displayed profile as unacceptable.
    
    displayed_uid_key = ndb.Key(urlsafe = display_uid)
    owner_uid_key = ndb.Key(urlsafe = owner_uid)
    
    q = models.MarkUnacceptableProfile.query()
    q = q.filter(models.MarkUnacceptableProfile.displayed_profile == displayed_uid_key)
    q = q.filter(models.MarkUnacceptableProfile.reporter_profile ==  owner_uid_key)
         
    mark_unacceptable_profile = q.get()
    return mark_unacceptable_profile



def check_if_authorized_for_private_photos(primary_userobject_key, displayed_userobject_key):

    # NOTE: There is some twisted logic in the naming scheme here -- I would fix it, but didn't realize until
    # The system was already live.
    # Basically, inside the query, the "displayed_profile" refers to the profile that was displayed when a kiss/wink/key was sent.
    # This means that the sender of the contact (kiss/key), was the viewer at the time that the contact was sent.
    # The receiver of the contact is the "displayed_profile"... However, when we are checking to see if a person
    # has the key to see private photos, then we need to query the userobject as if it were the "displayed_profile"
    # because it was the "displayed_profile" when the key was received. 
    #
    # In other words user Alex is viewing user Julie. We want to see if Alex has the key of Julie to see her private photos. 
    # We need to query the initiate_contact_object with the displayed_user_object set to Alex, and the viewer_userobject
    # set to Julie (even though *now* alex is the one viewing the profile of Julie)
    
    has_key_to_private_photos = False
    
    
    # make sure that the primary userobject exists. If it doesn't exist, then this is a non-logged in
    # user (someone checking out the site, or a web crawler)
    if primary_userobject_key:
        
        # Note the reversal of primary and displayed userobjects in the following query, as per the
        # explanation given above.
        initiate_contact_object = get_initiate_contact_object(
            viewer_userobject_key = displayed_userobject_key, 
            display_userobject_key = primary_userobject_key)
        
        if initiate_contact_object:
            if initiate_contact_object.key_stored:
                has_key_to_private_photos = True
                
                
    return has_key_to_private_photos


def delete_sub_object(parent_object, sub_object_key_name):
    
    # accepts a string representing the name of a sub-object of userobject, and deletes it from the database.
    # This is used in the case of a failed registration attempt, and will be used later on when we write code to
    # clean-up and remove deleted profiles.
    

    
    try:
        
        key_to_delete = getattr(parent_object, sub_object_key_name)

        error_message = """
        ***
        Deleting key %s: %s referenced from %s
        """ %(key_to_delete, sub_object_key_name, parent_object.__class__.__name__)
        
        error_reporting.log_exception(logging.warning, error_message = error_message ) 
        key_to_delete.delete()

    except: 
        error_message = """
        ***
        Unable to delete key %s referenced from %s
        """ % (sub_object_key_name, repr(parent_object))
        
        error_reporting.log_exception(logging.error, error_message = error_message ) 
        
        

def set_sub_object(parent_object, sub_object_name, func, args):
    
    # accepts a string representing the name of a sub-object of an object, and checks if it has been set.
    # If it has not been set, then it will be set to the "new_value" and an error will be reported
    

    try:
        # make sure that the value that we are about to overwrite really is not assigned
        assert(not getattr(parent_object, sub_object_name))
        
        new_value = func(*args)
        status_message = """
        ***
        Setting %s to %s
        """ %( sub_object_name, repr(new_value))
        
        logging.warning(status_message) 
        setattr(parent_object, sub_object_name, new_value)
    except: 
        import inspect

        error_message = """
        ***
        Unable to set %s to function: %s args %s
        """ %( sub_object_name, func.__name__, inspect.getargspec(func))
        
        error_reporting.log_exception(logging.error, error_message = error_message ) 
        
        
def get_first_position_of_value_in_list(search_value, list_to_check):
    # searches through the given list to see if the "search_value" is contained in the list. If found,
    # end the search and return the first location of the value. Otherwise, return None.
    
    for i, val in enumerate(list_to_check):
        if search_value == val:
            return i
    
    # if no match is found, return None.
    return None
   

            
def create_and_return_usertracker():
    
    # creates a user_tracker object
        
    user_tracker = models.UserTracker()
    user_tracker.put()

    return user_tracker.key

def create_and_return_user_photos_tracker():
    # creates a user_photo_tracker object
    user_photos_tracker = models.UserPhotosTracker()
    user_photos_tracker.put()
    return user_photos_tracker.key
            

def update_ip_address_on_user_tracker(user_tracker_ref):
    
    # store tracking information related to the IP address that the current user is entering from
    
    try:
        
        user_tracker = user_tracker_ref.get()
        assert(user_tracker)
        
        remoteip  = environ['REMOTE_ADDR'] 
        
        position_of_ip_in_user_tracker_list = get_first_position_of_value_in_list(remoteip, user_tracker.track_ip_list)
        if position_of_ip_in_user_tracker_list != None:
            # the current IP address has previously accessed this user profile
            user_tracker.num_times_ip_used_list[position_of_ip_in_user_tracker_list] += 1
            user_tracker.last_time_ip_used_list[position_of_ip_in_user_tracker_list] = datetime.datetime.now()
    
        else:
            # This is a unique IP address that is entering into the user profile
            user_tracker.track_ip_list.append(remoteip)
            user_tracker.num_times_ip_used_list.append(1)
            user_tracker.first_time_ip_used_list.append(datetime.datetime.now())
            user_tracker.last_time_ip_used_list.append(datetime.datetime.now())
        
        user_tracker.put()
        
    except:
        error_reporting.log_exception(logging.critical)
        

            
        

def update_email_address_on_user_tracker(userobject, email_address):
    
    # store tracking information related to the email_address which the user has currently verified.
    # Note: we consider a verification to be any time that a user has clicked on a link in an email that
    # we have provided to them.
    #
    # Note: In some cases to be accurate, it will be necessary to pass in an email_address from the email that was sent out,
    # since the user can change his email_address between the time he has received an email and the time that he clicks on
    # a link within the email. (but for new/registering users this is not an issue) -- 
    # We currently only should use this function for user registrations until we have a more accuate form of linking the
    # email sent out to the email address that will be stored for the given user (eg. by including it directly in the link)
    
    
    # We have currently only designed this code to be called a single time (on user registration) -- if it is called more than that
    # this would be an error. 
    try:
        user_tracker_obj = userobject.user_tracker.get()
        
        assert(user_tracker_obj)
        
        position_of_email_address_in_user_tracker_list = get_first_position_of_value_in_list(email_address, user_tracker_obj.verified_email_addresses_list)
        
        assert position_of_email_address_in_user_tracker_list == None
        
        user_tracker_obj.verified_email_addresses_list.append(email_address)
        user_tracker_obj.first_time_email_address_verified_list.append(datetime.datetime.now())
        user_tracker_obj.last_time_email_address_verified_list.append(datetime.datetime.now())
        
        user_tracker_obj.put()
        
    except:
        error_reporting.log_exception(logging.critical)       

        
        
def when_to_send_next_notification_txn(new_contact_key, hours_between_notifications):
    # Intended to run in a transaction. 
    # this code should work for both the unread_mail_count object (mail counter), 
    # and the new_contact_counter object (winks, etc. counter)
    new_contact_obj = new_contact_key.get()
    
    if hours_between_notifications != None and new_contact_obj.num_new_since_last_notification > 0:
        new_contact_obj.when_to_send_next_notification = new_contact_obj.date_of_last_notification + \
                         datetime.timedelta(hours = hours_between_notifications)
    else:
        new_contact_obj.when_to_send_next_notification = datetime.datetime.max
        
    new_contact_obj.when_to_send_next_notification_string = str(new_contact_obj.when_to_send_next_notification)    
    new_contact_obj.put()
    
    
def  get_hours_between_notifications(userobject, translation_dictionary):
    
    # translation_dictionary should be either of
    # a) constants.hours_between_message_notifications OR
    # b) constants.hours_between_new_contacts_notifications

    if userobject.email_address_is_valid:
        hours_between_notifications = translation_dictionary[userobject.email_options[0]]
    else:
        hours_between_notifications = None
        
    return hours_between_notifications
        
def get_location_dropdown_options_and_details(country_code, region_code):
    # Fills in location information that is required on the client side for filling in location menu and 
    # sub-region dropdown menus.
    
    response_dict = {}
    
    try:

        region_options_html = ''
        sub_region_options_html = ''
        
        # get the actual dropdown menu contents for the selected region and sub-region
        if country_code and country_code in localizations.region_options_html: 
            region_options_html = localizations.region_options_html[country_code]
            if region_code and region_code in localizations.sub_region_options_html[country_code]: # return the sub-regions
                sub_region_options_html = localizations.sub_region_options_html[country_code][region_code]
    
        response_dict['region_options_html'] = region_options_html
        response_dict['sub_region_options_html'] = sub_region_options_html
        
        return response_dict
    except:
        error_reporting.log_exception(logging.critical)   
        return 'Error'
    


    

    
def get_field_in_current_language(field_name, field_val, lang_code):
    # returns the field value in the current language
    lang_idx = localizations.input_field_lang_idx[lang_code]
    field_dictionary_by_field_name = getattr(user_profile_main_data.UserSpec, "signup_fields_options_dict")
    return field_dictionary_by_field_name[field_name][lang_idx][field_val]
    
    
def get_friend_bazaar_specific_interests_in_current_language(userobject, lang_idx):
    # returns an abbreviated string (comma seperated list) of the activities that the user being viewed 
    # (indicated by userobject) has indicated they are interested in.
    
    MAX_NUM_ACTIVITIES = 10
    current_num_activities_displayed = 0
    
    activity_list = []
    generated_html = ''
    
    try:
    
        
        for current_field in user_profile_main_data.UserSpec.list_of_activity_categories:
            # Side note: If we update the python version, the order of these elements might change - this will make old URLs obsolete. 
            list_for_current_field = getattr(userobject, current_field)
            
            for (idx, field_val) in enumerate(list_for_current_field):
                
                if field_val == "prefer_no_say":
                    continue
                
                option_in_current_language = user_profile_details.UserProfileDetails.checkbox_options_dict[current_field][lang_idx][field_val]
                    
                if current_num_activities_displayed < MAX_NUM_ACTIVITIES:
                    activity_list.append(u'%s' % option_in_current_language)
                    current_num_activities_displayed += 1
                else:
                    # break out early, we are finished
                    break
                
            # end inner for loop
            
            if current_num_activities_displayed >= MAX_NUM_ACTIVITIES:
                # break out of outer loop if we have already retrieved tha max number of activities
                break;
            
        if len(activity_list) > 0:
            generated_html += u" %s " % ugettext("Interested in:")
            generated_html += ", ".join(activity_list[:-1])
            if len(activity_list) > 1:
                generated_html += "%s %s" % (ugettext(", and"), activity_list[-1])
            else:
                generated_html += "%s" % activity_list[-1]
                

        return generated_html
    except:
        error_reporting.log_exception(logging.critical)       
        return ''    
    
    
    
def get_fields_in_current_language(field_vals_dict, lang_idx, pluralize_sex = True, search_or_profile_fields = "profile"):
        
    # returns the passed-in values in the current language. This code was initially written for generating titles
    # for profile pages.

    # field_vals_dict: contains a dictionary indexed by field (sex, age, preference, etc.), and containing the current value
    # of the field that must be translated into the current language.
    
    location = ''
    return_dict  = {
        'age': '----',
        'sex': '----',
        'sub_region': '----',
        'region': '----',
        'country': '----',
        'location': '----',
    }
    
    if settings.BUILD_NAME == "language_build":
        
        return_dict.update({# the following entries are only used in language_build
                            'languages': '----', # list of languages spoken
                            'languages_to_learn': '----', # list of languages to learn
                            'language_to_teach': '----',
                            'language_to_learn': '----',        
                            })
        
    elif settings.BUILD_NAME == "friend_build":
        return_dict.update({# following is only for friend_build
                            'for_sale' : '----',
                            'for_sale_sub_menu' : '----',
                            })
        #return_dict.update(user_profile_details.UserSpec.activity_categories_unset_dict)
    else:
        return_dict.update({# following is only for dating websites
                            'relationship_status': '----',
                            'preference': '----',                            
                            })
    
    try:
        # we need the options dict for the reverse lookup to get the appropriate value for a given field/value
        if search_or_profile_fields == "profile":
            field_dictionary_by_field_name = getattr(user_profile_main_data.UserSpec, "signup_fields_options_dict")
        elif search_or_profile_fields == "search":
            field_dictionary_by_field_name = getattr(user_profile_main_data.UserSpec, "search_fields_options_dict")
        else:
            assert(0)
        

        for (field_name, field_val) in field_vals_dict.iteritems():
            if field_name == 'for_sale_sub_menu':
                # the "for_sale_sub_menu" data field is only a place holder in the search box that is over-written by ajax calls 
                # depending on the value selected in the "for_sale" menu -- therefore, it does not contain valid data.
                # So, we need to look up the current value selected in the 'for_sale_menu', and lookup the value in the 
                # appropriate sub_menu
                lookup_field_name = field_vals_dict['for_sale']
            else:
                lookup_field_name = field_name
            
            try:
                if not isinstance(field_val, list):
                    if field_val and field_val != "----" and field_name != 'username' and field_name != 'bookmark':
                        return_dict[field_name] = field_dictionary_by_field_name[lookup_field_name][lang_idx][field_val]
                        
                        if settings.BUILD_NAME == "discrete_build" or settings.BUILD_NAME == "gay_build" or settings.BUILD_NAME == "swinger_build":
                            if field_name == "relationship_status" and lang_idx == localizations.input_field_lang_idx['es']:
                                if settings.BUILD_NAME == "gay_build":
                                    # all profiles in gay_build site are male - give Spanish masculine ending "o"
                                    return_dict[field_name] = re.sub('@', 'o', return_dict[field_name])                                    
                                elif field_vals_dict['sex'] == 'male' or field_vals_dict['sex'] == 'other' or field_vals_dict['sex'] == 'tstvtg':
                                    return_dict[field_name] = re.sub('@', 'o', return_dict[field_name])
                                elif field_vals_dict['sex'] == 'female' or field_vals_dict['sex'] == 'couple':
                                    return_dict[field_name] = re.sub('@', 'a', return_dict[field_name])
                                else:
                                    pass # no substitution necessary
                                
                            
                else:
                    field_vals_list_dict = field_val
                    return_dict[field_name] = generic_html_generator_for_list(lang_idx, lookup_field_name, field_vals_list_dict, 
                                                                              constants.NUM_LANGUAGES_IN_PROFILE_SUMMARY)
            except:
                error_message = "*Error* get_fields_in_current_language - %s value: %s" % (field_name, field_val)
                return_dict[field_name] = ''
                error_reporting.log_exception(logging.warning, error_message = error_message)
        
        try:
            if pluralize_sex:
    
                if settings.BUILD_NAME != "language_build" and settings.BUILD_NAME != "friend_build":
                    # if pluralized, lookup the field name in the "preference" setting (since it is pluralized),
                    # otherwise use the "sex" setting.
                    if field_vals_dict['preference'] != "----":
                        return_dict["preference"] = field_dictionary_by_field_name["preference"][lang_idx][field_vals_dict['preference']]
                    if field_vals_dict['sex'] != "----":
                        return_dict["sex"] = field_dictionary_by_field_name["preference"][lang_idx][field_vals_dict['sex']]
                else:
                    # preference fields do not exist for language_build or friend_build, so lookup in the "sex" field
                    if field_vals_dict['sex'] != "----":
                        return_dict["sex"] = field_dictionary_by_field_name["sex"][lang_idx][field_vals_dict['sex']]
            else:
                if settings.BUILD_NAME != "language_build" and settings.BUILD_NAME != "friend_build":
                    if field_vals_dict['preference'] != "----":
                        return_dict["preference"] = field_dictionary_by_field_name["sex"][lang_idx][field_vals_dict['preference'] ]
                if field_vals_dict['sex'] != "----":
                    return_dict["sex"] = field_dictionary_by_field_name["sex"][lang_idx][field_vals_dict['sex']]
                
        except:
            # This can be triggered if someone passes in bad parameters on the URL
            error_reporting.log_exception(logging.warning)    
            
        try:
            # in order to get better google keyword coverage, override sex and preference for certian age ranges
            # depending on the language.
            if settings.SEO_OVERRIDES_ENABLED:
                if field_vals_dict['age'] != "----":
                    lang_code = localizations.lang_code_by_idx[lang_idx]
                    return_dict["sex"] = search_engine_overrides.override_sex(lang_code, int(field_vals_dict['age']), return_dict["sex"])
                    
                    if settings.BUILD_NAME != "friend_build" and settings.BUILD_NAME != "language_build":
                        return_dict["preference"] = search_engine_overrides.override_sex(lang_code, int(field_vals_dict['age']), return_dict["preference"])
                
            if field_vals_dict['sub_region'] and field_vals_dict['sub_region'] != "----":
                return_dict['sub_region'] = field_dictionary_by_field_name['sub_region'][lang_idx][field_vals_dict['sub_region']]  
            if field_vals_dict['region'] and field_vals_dict['region'] != "----":
                return_dict['region'] = field_dictionary_by_field_name['region'][lang_idx][field_vals_dict['region']]   
            if field_vals_dict['country'] != "----":
                return_dict['country'] = field_dictionary_by_field_name['country'][lang_idx][field_vals_dict['country']]
            
            if return_dict['sub_region'] != "----" : 
                return_dict['location'] = "%s, %s, %s" % (return_dict['sub_region'], return_dict['region'], return_dict['country'])
            elif return_dict['region'] != "----":
                return_dict['location'] = "%s, %s" % (return_dict['region'], return_dict['country'])
            elif return_dict['country'] != "----": 
                return_dict['location'] = return_dict['country']
            else:
                return_dict['location'] = '----'
        except:
            # This can be triggered if someone passes in bad parameters on the URL, that result in
            # the sub_region, region, or country containing invalid values that are not defined. 
            error_reporting.log_exception(logging.warning)
        
    except:
        error_reporting.log_exception(logging.critical) 
        
    return (return_dict)


def add_session_id_to_user_tracker(user_tracker_ref, session_id):
    # adds the current session identifier to the user_tracker so that if necessary we can clear the sessions from the
    # database, thereby forcing a logout of a user.
    
    try:
        user_tracker = user_tracker_ref.get()
        # the following code allocates memory for the list up until the maximum number of sessions is stored,
        # at which point we start to wrap around the list. 
        list_length = len(user_tracker.list_of_session_ids)
        if list_length < constants.MAX_STORED_SESSIONS:
            user_tracker.list_of_session_ids.append(session_id)
            user_tracker.list_of_session_ids_last_index = list_length
        else:
            list_idx = (user_tracker.list_of_session_ids_last_index + 1) % constants.MAX_STORED_SESSIONS 
            user_tracker.list_of_session_ids[list_idx] = session_id
            user_tracker.list_of_session_ids_last_index = list_idx
            
        user_tracker.put()

    except:
        error_reporting.log_exception(logging.critical)
        

        

def get_for_sale_to_buy(for_sale_to_buy_current_selection, lang_idx):
    
    if for_sale_to_buy_current_selection and for_sale_to_buy_current_selection in user_profile_main_data.UserSpec.search_fields:
        return user_profile_main_data.UserSpec.search_fields[for_sale_to_buy_current_selection]['options'][lang_idx]
    else:
        return "Unknown get_for_sale_to_buy_options value %s requested" % for_sale_to_buy_current_selection
    
    
# the following code is intentionally oustside of a function, so that it will only be executed a single time upon
# initialization of the program. 
# This dictionary will cache the generated html for the for_sale/to_buy sub-menus. This is necessary because these sub menus
# are stored as arrays, but must be converted to a string of html to be passed to the template.
for_sale_to_buy_dropdown_options_dict_cache = []
for lang_idx, language_tuple in enumerate(settings.LANGUAGES):
    for_sale_to_buy_dropdown_options_dict_cache.append({})
    
def get_child_dropdown_options_and_details(parent_val, lang_idx):
    # Fills in location information that is required on the client side for filling in location menu and 
    # sub-region dropdown menus.
    
    response_dict = {}
    
    try:
        
        # for efficiency, 
        if parent_val == "----":
            return "----"
        if not for_sale_to_buy_dropdown_options_dict_cache[lang_idx].has_key(parent_val):    
            if parent_val in user_profile_main_data.UserSpec.search_fields:
                generated_options_html = ''
                for option_line in user_profile_main_data.UserSpec.search_fields[parent_val]['options'][lang_idx]:
                    generated_options_html += option_line
                for_sale_to_buy_dropdown_options_dict_cache[lang_idx][parent_val] = generated_options_html
        else:
            pass
        
        return for_sale_to_buy_dropdown_options_dict_cache[lang_idx][parent_val]
    except:
        error_reporting.log_exception(logging.critical)   
        return 'Error in get_child_dropdown_options_and_details'
    
    
def get_fake_mail_parent_entity_key(uid1, uid2):
    # in order to ensure that all messages between two users are in the same entity group, we create a "fake"
    # entity key, which will be assigned as a parent to all messages between this pair of users. To ensure that
    # there is only one unique key for each pair of users, we *always* use a key name which contains
    # the lower key followed by the higher key
    
    # Note: Using "uid's" instead of "nid's" is a mistake - if we ever need to restore mail messages to a different
    # application id, the parent will not be consistent, and the maill messages will not be found. 
    
    # must ensure that keys are compared using *string* or *integer* representations, *not* key representations - because the 
    # order can change - see (my comment) on StackOverflow
    # http://stackoverflow.com/questions/7572386/why-are-appengine-database-keys-sorted-differently-than-strings
    uid1 = str(uid1)
    uid2 = str(uid2)
    
    if uid1 < uid2:
        parent_key_name = "%s_and_%s" % (uid1, uid2)
    else:
        parent_key_name = "%s_and_%s" % (uid2, uid1)
    mail_parent_key = ndb.Key('FakeMailMessageParent', parent_key_name)
    return mail_parent_key


def get_have_sent_messages_key_name(owner_key, other_key):
    key_name = "%s_and_%s" % (owner_key.urlsafe(), other_key.urlsafe())
    return key_name

    
def get_have_sent_messages_key(owner_key, other_key):
    key_name = get_have_sent_messages_key_name(owner_key, other_key)
    have_sent_messages_key = ndb.Key('UsersHaveSentMessages', key_name)
    return have_sent_messages_key

def get_have_sent_messages_object(owner_key, other_key, create_if_does_not_exist = False):
    
    try:
        have_sent_messages_key = get_have_sent_messages_key(owner_key, other_key)
        have_sent_messages_object = have_sent_messages_key.get()
        if not have_sent_messages_object and create_if_does_not_exist:
            have_sent_messages_object = models.UsersHaveSentMessages(id = get_have_sent_messages_key_name(owner_key, other_key))
            have_sent_messages_object.datetime_first_message_to_other_today = datetime.datetime.now()
            have_sent_messages_object.put()
        return have_sent_messages_object
    except:
        error_reporting.log_exception(logging.critical)   
        return None
    
def get_initiate_contact_object(viewer_userobject_key, display_userobject_key, create_if_does_not_exist = False ):
    # This function returns the object corresponding to previous contact beween the owner and the displayed
    # profile. This object contains favorites, kisses, etc. 
    
    # NOTE: There is some twisted logic in the naming scheme here .
    # Basically, the "displayed_profile" refers to the profile that was/is displayed when a kiss/wink/key was sent.
    # This means that the sender of the contact (kiss/key), was the viewer at the time that the contact was sent.
    # The receiver of the contact is the "displayed_profile"... However, when we are checking to see if a person
    # has the key to see private photos, then we need to query the userobject as if it were the "displayed_profile"
    # because it was the "displayed_profile" when the key was received. 
    #
    # In other words user Alex is viewing user Julie. We want to see if Alex has the key of Julie to see her private photos. 
    # We need to query the initiate_contact_object with the displayed_user_object set to Alex, and the viewer_userobject
    # set to Julie (even though *now* alex is the one viewing the profile of Julie)
    
    # check if the client has had previous contact with the profile being viewed
    
    
        
    try:
        memcache_key_str = constants.INITIATE_CONTACT_MEMCACHE_PREFIX + viewer_userobject_key.urlsafe() + display_userobject_key.urlsafe()
        memcache_entity = memcache.get(memcache_key_str)
        
        if memcache_entity == 0 and not create_if_does_not_exist:
            # we stored a zero if we have already checked the database and there is no object for this pair of 
            # users. As long as we are not creating a new entity (if not create_if_does_not_exist), then we can return
            # a None value for this query.
            return None
            
        elif memcache_entity is not None and memcache_entity != 0:
            # Entity found in memcache - just return it.
            initiate_contact_object = deserialize_entity(memcache_entity) 
            return initiate_contact_object
            
        
        else: 
            # Two possibilities to get here:
            # 1) memcache is None - We need to check the database to see what the current initiate_contact_object is 
            #   and store to memcache
            # 2) memcache_entity == 0 (we have queried the database previously, but it was empty) *and* 
            # create_if_does_not_exist is True (we need to create a new entity)
             
            object_key_name = viewer_userobject_key.urlsafe() + display_userobject_key.urlsafe() 
            initiate_contact_key = ndb.Key('InitiateContactModel', object_key_name)
            initiate_contact_object = initiate_contact_key.get()
            
            if initiate_contact_object is None:
                # database does not contain an object for this pair of users.
                if create_if_does_not_exist:
                    # only create a new object if the database has not already stored one for the viewer and the display user.
                    initiate_contact_object = models.InitiateContactModel(id = object_key_name, 
                        displayed_profile = display_userobject_key, viewer_profile = viewer_userobject_key)
                    
                    # write the object to memcache and database.
                    put_initiate_contact_object(initiate_contact_object, viewer_userobject_key, display_userobject_key)
                else:
                    # if the database has returned a "None" value, then there is currently no object stored for these
                    # two users. However, in order to allow memcache return a value and prevent the database from
                    # being queried repeatedly for an object that is not in the database, we set the memcache to
                    # zero instead of None.
                    memcache_entity = 0
                    memcache.set(memcache_key_str, memcache_entity, constants.SECONDS_PER_MONTH)
                    
            elif initiate_contact_object:
                # initiate_contact_object exists - write it into memcache for future gets
                memcache.set(memcache_key_str, serialize_entity(initiate_contact_object), constants.SECONDS_PER_MONTH) 
                
        return initiate_contact_object

    except:
        error_reporting.log_exception(logging.critical)
        return None       
    
    
def put_initiate_contact_object(initiate_contact_object, viewer_userobject_key, display_userobject_key):
    
    initiate_contact_object.put()
    memcache_key_str = constants.INITIATE_CONTACT_MEMCACHE_PREFIX + viewer_userobject_key.urlsafe() + display_userobject_key.urlsafe()
    memcache.set(memcache_key_str, serialize_entity(initiate_contact_object), constants.SECONDS_PER_MONTH)
    
    
def convert_string_key_from_old_app_to_current_app(old_key_string):
    
    try:
        old_key = ndb.Key(urlsafe = old_key_string)
        kind = old_key.kind()
        id_or_name = old_key.id()
        old_app_name = old_key.app()
    
        new_key = ndb.Key(kind, id_or_name)
        new_key_string = new_key.urlsafe()
        new_app_name = new_key.app()
        
        # We should never be re-directing a key that is the same app name as the current app
        logging.info("old_app_name %s new_app_name %s" % (old_app_name, new_app_name))
        assert(old_app_name != new_app_name)
        return new_key_string
    
    except:
        error_reporting.log_exception(logging.critical)
        return None
    
    
def get_username_combinations_list(username):
    
    # return a list that is made up of the username[:], username[1:], username[2:], etc.
    # This is necessary for partial username matching.
    
    username_combinations_list = []
    
    for start_idx in range(len(username)):
        for end_idx in range(start_idx + 1, len(username) + 1):
            username_combinations_list.append(username[start_idx:end_idx])
        
    return username_combinations_list
        
        
def check_if_reset_num_messages_to_other_sent_today(have_sent_messages_object):
    # checks if enough time has passed since the last "time window" in which the current user is allowed to send new
    # messages to the other user.
    try:
        if have_sent_messages_object.datetime_first_message_to_other_today + datetime.timedelta(
            hours = constants.NUM_HOURS_WINDOW_TO_RESET_MESSAGE_COUNT_TO_OTHER_USER - constants.RESET_MAIL_LEEWAY) <  datetime.datetime.now():
            return True
        else:
            return False
    except:
        error_reporting.log_exception(logging.error, error_message = "have_sent_messages_object = %s" % repr(have_sent_messages_object))   
        # We screwed up - so we give the user the benefit of the doubt and return True (ie. reset the counter to allow more messages
        # to be sent today)
        return True
    
        
def check_if_allowed_to_send_more_messages_to_other_user(have_sent_messages_object, initiate_contact_object):
    # checks if the current user has exceeded the number of messages that he is allowed to send to the other
    # user in the current "time window"
    # returns True if allowed to send messages, False if not

    if have_sent_messages_object:
        userobject = have_sent_messages_object.owner_ref.get()
        other_userobject = have_sent_messages_object.other_ref.get()

        user_paid_status = userobject.client_paid_status
        other_paid_status = other_userobject.client_paid_status
    else:
        user_paid_status = None
        other_paid_status = None
     
    txt_for_when_quota_resets = ''
    if not have_sent_messages_object :
        is_allowed = True
    
    elif have_sent_messages_object and have_sent_messages_object.num_messages_to_other_sent_today < \
         constants.STANDARD_NUM_MESSAGES_TO_OTHER_USER_IN_TIME_WINDOW:
        is_allowed = True

    # If either the current sender, or the person that they are sending the message to is a VIP member
    # (has client_paid_status), then the message quota is increased.
    elif (user_paid_status or other_paid_status) and have_sent_messages_object.num_messages_to_other_sent_today < \
         constants.VIP_AND_CHAT_FRIEND_NUM_MESSAGES_TO_OTHER_USER_IN_TIME_WINDOW:
        # VIP members can send more messages to other users
        is_allowed = True
    
    elif have_sent_messages_object and \
         initiate_contact_object and \
         initiate_contact_object.chat_friend_stored == "connected" and \
         have_sent_messages_object.num_messages_to_other_sent_today < \
         constants.VIP_AND_CHAT_FRIEND_NUM_MESSAGES_TO_OTHER_USER_IN_TIME_WINDOW:
        # These users are "chat friends" so they have a higher limit.
        is_allowed = True
    
    else:
        time_when_it_will_reset = have_sent_messages_object.datetime_first_message_to_other_today + datetime.timedelta(
                   hours = constants.NUM_HOURS_WINDOW_TO_RESET_MESSAGE_COUNT_TO_OTHER_USER)      
        txt_for_when_quota_resets = return_time_difference_in_friendly_format(time_when_it_will_reset, capitalize = False, 
                                                          data_precision = 2, time_is_in_past = False, show_in_or_ago = True)
        is_allowed = False
    
    return (is_allowed, txt_for_when_quota_resets)

def get_removed_user_reason_html(removed_userobject):
    
    # Generates text that explains why a given userobject was eliminated. 
    
    generated_html = ''
    notify_text = ''
    
    # include special text to warn users about scammer profiles and tell them why profiles have been eliminated
    notify_us_of_similar_profiles_text = u"<br><br>%s" % ugettext("If you see any other profiles like this, please send an email to %(support_email_address)s to notify us of the user name.") % {
        'app_name' : settings.APP_NAME,
        'support_email_address' : constants.support_email_address}
    
    if removed_userobject.reason_for_profile_removal == "terms":
        # if we didn't specify why this profile was eliminated, show the "terms" message
        removed_text = u"%s" % ugettext("This user has been eliminated by the administrator for violating the terms of service agreement.")

        class_def = 'class = "cl-warning-text"'
        
    elif removed_userobject.reason_for_profile_removal == "scammer":
        removed_text = u"%s" % ugettext("This user has been eliminated by the administrator for running a scam. \
Please do not send emails or contact them in any manner, because it is likely that their objective is to ask you for money.")

        notify_text =  u"%s" % notify_us_of_similar_profiles_text
        class_def = 'class = "cl-warning-text"'

    elif removed_userobject.reason_for_profile_removal == "fake":
        removed_text =  u"%s" % ugettext("This user has been eliminated by the administrator for being a fake profile. \
Please do not send emails or contact them in any manner, since their goal is to get you to sign up for a paid service.")  

        notify_text =  u"%s" % notify_us_of_similar_profiles_text
        class_def = 'class = "cl-warning-text"'
                
    else:
        removed_text =  u"%s" % ugettext("This user profile has been eliminated")

        class_def = ''

    if removed_text:
        generated_html += u'<span %s>%s%s</span><br><br>\n' % (class_def, removed_text, notify_text) 

    return generated_html

def get_client_paid_status(userobject):
    
    vip_status = None
    if userobject.client_paid_status and userobject.client_paid_status_expiry > datetime.datetime.now():
        # This is a VIP member - return their current status.
        vip_status = userobject.client_paid_status

    return(vip_status)


def get_nid_from_uid(uid):
    # function that looks up the nid [ie. key().id()] based on the uid. 

    userobject = ndb.Key(urlsafe = uid).get()
    nid = userobject.key.integer_id()
    return nid
    
def get_uid_from_nid(nid):
    
    user_key = ndb.Key('UserModel', long(nid))
    user_uid = user_key.urlsafe()   
    return user_uid

def return_and_report_internal_error(request):
    
    error_reporting.log_exception(logging.critical)
    txt = ugettext('Internal error - this error has been logged, and will be investigated immediately')
    return http.HttpResponseServerError(txt)



def user_is_admin(userobject):
    if userobject and userobject.username == constants.ADMIN_USERNAME and users.is_current_user_admin():
        return True
    else:
        return False
    
def get_country_name_from_code(country_code):
    
    if country_code:
        if country_code + ',,' in localizations.location_dict[0]:
            return localizations.location_dict[0][country_code +",," ]
        else:
            # we can't get the name for the country_code, so just return the raw code
            return country_code
    else:
        return None


def generate_profile_information_for_administrator(display_userobject, is_admin):
    
    generated_html = ''
    
    try:
        if is_admin:
            # show information about this user to the administrator.
            generated_html += u'<br><br><div>'            
            if display_userobject.client_paid_status:
                generated_html += "<b>Is VIP</b><br><br>"
                
                
            generated_html += "Email: %s<br>" % display_userobject.email_address
            generated_html += "Login IP: %s<br>" % display_userobject.last_login_ip_address
            
            generated_html += "Login Country: %s<br>" % get_country_name_from_code(display_userobject.last_login_country_code)
    
            generated_html += "Login Region: %s<br>" % display_userobject.last_login_region_code
            generated_html += "Login City: %s<br>" % display_userobject.last_login_city
            generated_html += "Registration IP: %s<br>" % display_userobject.registration_ip_address
            generated_html += "Registration Country: %s<br>" % get_country_name_from_code(display_userobject.registration_country_code)            
            generated_html += "Registration City: %s<br>" % display_userobject.registration_city
            generated_html += "Registration Date: %s<br>" % display_userobject.creation_date
            
            generated_html += '<br></div>'    
            
    except:
        error_reporting.log_exception(logging.error)
            
    return generated_html


def store_login_ip_information(request, userobject):
    userobject.last_login_ip_address = os.environ['REMOTE_ADDR'] 
    userobject.last_login_country_code = request.META.get('HTTP_X_APPENGINE_COUNTRY', None)
    userobject.last_login_region_code = request.META.get('HTTP_X_APPENGINE_REGION', None)
    userobject.last_login_city = request.META.get('HTTP_X_APPENGINE_CITY', None)    
    



    
def render_internal_ad(ad_name):
    
    template = loader.get_template('proprietary_ads/%s.html/' % ad_name)  
    context = Context (dict({
        }, **constants.template_common_fields))      
    http_response = template.render(context) 
    return http_response


def render_google_ad(ad_format):
    # ad_format currently is GOOGLE_AD_160x600 or GOOGLE_AD_728x90
    if not site_configuration.DEVELOPMENT_SERVER:
        return getattr(constants, ad_format)
    else:
        return "Google Ads are not shown in the DEBUG build"
        
    
    
def do_display_online_status(owner_uid):
    # Determines if this user should be shown information that is reserved for our VIP clients.
    # An example of this is showing the online status of all users in the page.

    try:    
    
        if constants.SHOW_VIP_UPGRADE_OPTION:
            # This build has the option of upgrading to VIP - therefore we just give them a taste of the VIP benefits
            
            userobject = utils_top_level.get_object_from_string(owner_uid)
            client_paid_status = userobject.client_paid_status
            
            if client_paid_status:
                # This is a VIP (paid) member - always show online status 
                show_online_status = True 
            else:
                # This is a non-VIP (free) member.
                # check if they are currently in a trial period. I
                show_online_status_memcache_key = constants.SHOW_ONLINE_STATUS_TRIAL_TIMEOUT_MEMCACHE_PREFIX + owner_uid
                show_online_status= memcache.get(show_online_status_memcache_key)   
                if show_online_status is not None:
                    show_online_status = True
                else:
                    show_online_status = False
        else:
            # For this build, upgrading to VIP is not an option - all users are treated as VIP.
            show_online_status = True
                
        return show_online_status
    
    except:
        error_reporting.log_exception(logging.error) 
        return False

def show_online_status(owner_uid):
    
    if constants.SHOW_VIP_UPGRADE_OPTION:
        userobject = utils_top_level.get_object_from_string(owner_uid)
        client_paid_status = userobject.client_paid_status
        
        if client_paid_status:
            # This is a VIP (paid) member - always show online status 
            return True     
        else :
            return False
    else:
        # The current build does not allow upgrades - treat all users as VIP
        return True

def set_show_online_status_timeout(owner_uid):
    
    # keep track of how long this user will be allowed to view other users online status, 
    # and also how long before they will be allowed to start another trial.
    try:
        block_online_status_memcache_key = constants.BLOCK_ONLINE_STATUS_TRIAL_TIMEOUT_MEMCACHE_PREFIX + owner_uid
        is_blocked_start_time = memcache.get(block_online_status_memcache_key)
        
        if is_blocked_start_time is None:
            start_trial_time = datetime.datetime.now()
            show_online_status_memcache_key = constants.SHOW_ONLINE_STATUS_TRIAL_TIMEOUT_MEMCACHE_PREFIX + owner_uid
            memcache.set(show_online_status_memcache_key, start_trial_time, constants.SHOW_ONLINE_STATUS_TRIAL_TIMEOUT_SECONDS)
            memcache.set(block_online_status_memcache_key, start_trial_time, constants.BLOCK_ONLINE_STATUS_TRIAL_RESET_SECONDS)
            return "OK"
        
        else:
            # return how much longer until the trial will be un-blocked
            return return_time_difference_in_friendly_format(is_blocked_start_time + \
                    datetime.timedelta(seconds = constants.BLOCK_ONLINE_STATUS_TRIAL_RESET_SECONDS),
                    time_is_in_past=False, show_in_or_ago=False)
        
        
    except:
        error_reporting.log_exception(logging.error) 
        return "Error"        
    
    
def get_date_in_current_language(datetime_date):
    # returns date in language appropriate format, which includes month, day, and year. Does not include
    # hours. 
    
    datetime_date_day = datetime_date.day
    datetime_date_month = datetime_date.month
    datetime_date_year = datetime_date.year

    month_in_current_language = constants.MONTH_NAMES[datetime_date_month]
    date_in_current_language = ugettext("%(month)s %(day)s, %(year)s") % {'month': month_in_current_language, 
                                                                          'day' : datetime_date_day,
                                                                          'year' : datetime_date_year}
    return date_in_current_language

def get_date_or_time_in_current_language(datetime_date):
    
    # if more than 24 hours have passed, returns date in month, day, and year format. Otherwise,
    # returns it in the format of "5 hours ago" (because we don't handle timezones properly yet)
    
    if datetime.datetime.now() - datetime_date >= datetime.timedelta(hours = 24):
        time_str = get_date_in_current_language(datetime_date)
    else:
        time_str = return_time_difference_in_friendly_format(datetime_date, capitalize = False)
        
    return time_str


def get_why_to_register():
    # following text is replaced even in english
    if constants.SITE_IS_TOTALLY_FREE:
        is_free_text = "%s %s %s. %s" % (settings.APP_NAME, ugettext("is"), ugettext("100 percent free"), ugettext("We never ask for your credit card or any other form of payment"))
    else:
        is_free_text = '%s %s %s - %s' % (settings.APP_NAME, ugettext("is"), ugettext("free"),  ugettext("chat and messages included"))
        
    why_to_register = u"<ul>"
    why_to_register += ugettext("List of benefits for registering with %(app_name)s.  %(is_free_text)s") % {
        'app_name': settings.APP_NAME, 'is_free_text' : is_free_text,}
    why_to_register += u"</ul>"
        
        
    return why_to_register


def is_exempt_user():
    
    # We have a list of users that have extra privileges for setting up accounts and other things.
    # If the user is logged into a google account, and their google email address matches an email in
    # this list, then they are "exempt" from  certain restrictions such as inputting password, 
    # email address, etc.
    
    is_privileged = False
    try:
        if users.User().email() in constants.REGISTRATION_EXEMPT_EMAIL_ADDRESSES_SET:
            is_privileged = True
    except:
        pass
    
    return is_privileged
    