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


from os import environ

from google.appengine.ext import db 
from google.appengine.api import memcache, users

import hashlib, re
import datetime, time, logging
import string, random, sys
import gaesessions
import http_utils


from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotAllowed, HttpResponseServerError
from django.shortcuts import render_to_response
from django.utils.translation import ugettext, ungettext

import settings
from models import UserModel

import constants, queries, text_fields, models, online_presence_support

from models import UnreadMailCount, CountInitiateContact
from utils_top_level import serialize_entities, deserialize_entities

import user_profile_main_data, localizations, models, error_reporting, utils_top_level, user_profile_details
from rs.import_search_engine_overrides import *

import base64


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
                return HttpResponseForbidden()
        else: 
            
            # check the IP address to see if it is the google web-crawler .
            remoteip  = environ['REMOTE_ADDR']
            
            if constants.GOOGLE_CRAWLER_IP_PATTERN.match(remoteip):
                # if it is the web-crawler - let then know that they need authorization to view the page.
                error_reporting.log_exception(logging.warning, error_message = 'Google crawler unauthorized access (No session)')
                return HttpResponseForbidden()
                
            else:
                error_reporting.log_exception(logging.warning, error_message = 'Error: Non-logged in user unauthorized access - redirect to /') 
                return http_utils.redirect_to_url(request, "/%s/" % request.LANGUAGE_CODE)

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
            return HttpResponse(error_message)

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
                    if settings.BUILD_NAME == 'Language':
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

def generate_profile_summary_table(request, profile):

    current_language = request.LANGUAGE_CODE
    lang_idx = localizations.input_field_lang_idx[current_language]
    
    generated_html = ''
    
    try:
        if settings.BUILD_NAME != "Language" and settings.BUILD_NAME != "Friend":        
            relationship_status_def = "%s"\
                % user_profile_main_data.UserSpec.signup_fields_options_dict['relationship_status'][lang_idx][profile.relationship_status]
            preference_def =  u"%s" % user_profile_main_data.UserSpec.signup_fields_options_dict['preference'][lang_idx][profile.preference]

        else:
            if settings.BUILD_NAME == "Language":
            
                languages_spoken_list = generic_html_generator_for_list(lang_idx, 'languages', profile.languages, max_num_entries = constants.NUM_LANGUAGES_IN_PROFILE_SUMMARY)
                languages_to_learn_list = generic_html_generator_for_list(lang_idx, 'languages_to_learn', profile.languages_to_learn, max_num_entries = constants.NUM_LANGUAGES_IN_PROFILE_SUMMARY)
                
                native_language_def = "%s"\
                    % user_profile_main_data.UserSpec.signup_fields_options_dict['native_language'][lang_idx][profile.native_language]
                #language_to_learn_def = "%s"\
                 #   % user_profile_main_data.UserSpec.signup_fields_options_dict['language_to_learn'][lang_idx][profile.language_to_learn]
            if settings.BUILD_NAME == "Friend":
                price_def = "%s" % user_profile_main_data.UserSpec.signup_fields_options_dict['friend_price'][lang_idx][profile.friend_price]
                currency_def = "%s" % user_profile_main_data.UserSpec.signup_fields_options_dict['friend_currency'][lang_idx][profile.friend_currency]
        
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
            error_message = "While displaying summary of: %s - Unable to decipher location: location: %s country: %s region: %s sub_region: %s" % (
                profile.username, location, country, region, sub_region)
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
        currency_text = u"%s:" % ugettext("Currency")

        if settings.BUILD_NAME != "Language" and settings.BUILD_NAME != "Friend":
            location_text = u"%s:" % ugettext("In location") # override this for english (and obviously for others as well)
        else:
            location_text = u"%s:" % ugettext("I am currently in")
        

        first_row_html = second_row_html = ''
        if settings.BUILD_NAME != "Language" and settings.BUILD_NAME != "Friend":
            first_row_html += '<td class = "cl-left-align-user-summary-text-normal"><strong>%s</strong></td>' % sex_text
            second_row_html += '<td class = "cl-summary-info">%s</td>' % sex_def
            
            first_row_html += '<td class = "cl-left-align-user-summary-text-normal"><strong>%s</strong>' % preference_text
            second_row_html += '<td class = "cl-summary-info">%s</td>' % preference_def

            if settings.BUILD_NAME == 'Discrete' or settings.BUILD_NAME == 'Swinger' or settings.BUILD_NAME == 'Gay':
                first_row_html += '<td class = "cl-left-align-user-summary-text-normal"><strong>%s</strong></td>' % relationship_status_text
            elif settings.BUILD_NAME == 'Single' or settings.BUILD_NAME == 'Lesbian': 
                first_row_html += '<td class = "cl-left-align-user-summary-text-normal"><strong>%s</strong></td>' % looking_for_text
            else: assert(0)
            second_row_html += '<td class = "cl-summary-info">%s</td>' % relationship_status_def
                
            first_row_html += '<td class = "cl-left-align-user-summary-text-narrower"><strong>%s</strong></td>' % age_text
            second_row_html += '<td class = "cl-summary-info">%s</td>' % age_def
            
            first_row_html += '<td class = "cl-left-align-user-summary-text-230px"><strong>%s</strong></td>' % location_text
            second_row_html += '<td class = "cl-summary-info">%s</td>' % location_def
            
        else:
            if settings.BUILD_NAME == "Language":
                first_row_html += '<td class = "cl-left-align-user-summary-text-for-languages"><strong>%s</strong></td>' % languages_spoken_text
                second_row_html += '<td class = "cl-summary-info">%s</td>' % languages_spoken_list
    
                first_row_html += '<td class = "cl-left-align-user-summary-text-for-languages"><strong>%s</strong></td>' % languages_to_learn_text
                second_row_html += '<td class = "cl-summary-info">%s</td>' % languages_to_learn_list

            first_row_html += '<td class = "cl-left-align-user-summary-text-normal"><strong>%s</strong></td>' % sex_text
            second_row_html += '<td class = "cl-summary-info">%s</td>' % sex_def
                        
            first_row_html += '<td class = "cl-left-align-user-summary-text-narrower"><strong>%s</strong></td>' % age_text
            second_row_html += '<td class = "cl-summary-info">%s</td>' % age_def
    
            if settings.BUILD_NAME == "Friend":
                first_row_html += '<td class = "cl-left-align-user-summary-text-normal"><strong>%s</strong></td>' % price_text
                second_row_html += '<td class = "cl-summary-info">%s</td>' % price_def 
                
                first_row_html += '<td class = "cl-left-align-user-summary-text-normal"><strong>%s</strong></td>' % currency_text
                second_row_html += '<td class = "cl-summary-info">%s</td>' % currency_def                
            
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
    memcache_key_str = constants.BASE_OBJECT_MEMCACHE_PREFIX + str(object_to_put.key())
    memcache.set(memcache_key_str, serialize_entities(object_to_put), constants.SECONDS_PER_MONTH)
    

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
    uid = str(userobject.key())
    
    #invalidate_user_summary_memcache(uid)
    
    for lang_tuple in settings.LANGUAGES:
        lang_code = lang_tuple[0]
        url_description_memcache_key_str = lang_code + constants.PROFILE_URL_DESCRIPTION_MEMCACHE_PREFIX + uid
        memcache_status = memcache.delete(url_description_memcache_key_str)
        
        profile_title_memcache_key_str = lang_code + constants.PROFILE_TITLE_MEMCACHE_PREFIX + uid
        memcache_status = memcache.delete(profile_title_memcache_key_str)
        

#def invalidate_user_summary_memcache(uid):
    ## invalidates the profile summary that is stored in memcache - this should be done when 
    ## changes to the user profile are made, including any modifications to the photos that
    ## have been uploaded - also, when photos are approved this should be called. 
    #for lang_tuple in settings.LANGUAGES:
        #lang_code = lang_tuple[0]
        #summary_first_half_memcache_key_str = lang_code + constants.PROFILE_FIRST_HALF_SUMMARY_MEMCACHE_PREFIX + uid
        #memcache_status = memcache.delete(summary_first_half_memcache_key_str)
    
def do_query(model_to_query, query_filter_dict, order_by = None):
    # This is a helper function that takes care of querying the database.
    # model_to_query: the name of the db model class that we are querying
    # query_filter_dict: contains a dictionary of the name/value pairs which we will match in thequery
    # order_by: [optional] if we want to modify the query order
    #
    # Returns: a filtered query list that matches the specified criteria
    
    if order_by:
        query = model_to_query.all().order(order_by)
    else:
        query = model_to_query.all()
        
    for (query_filter_key, query_filter_value) in query_filter_dict.iteritems():
        query = query.filter(query_filter_key, query_filter_value)    
    
    return query

    
def get_active_userobject_from_username(username):
    
    try:
        query_filter_dict = {}
        # ensure that unique_last_login None values are removed -- these are backup objects
    #    query_filter_dict['last_login_string > '] = None 
        order_by = "-last_login_string"
        query_filter_dict['is_real_user ='] = True
        query_filter_dict['user_is_marked_for_elimination ='] = False
        query_filter_dict['username ='] = username
                
        query = do_query(UserModel, query_filter_dict, order_by)
            
        if query.count(2) > 1:
            logging.critical("User %s has more than one active userobject" % username)
    
        userobject = query.get()
        if userobject:
            # use memcache.add since we don't need to invalidate old data if the key is already valid
            memcache_key_str = str(userobject.key()) + settings.VERSION_ID
            memcache.add(memcache_key_str, serialize_entities(userobject), constants.SECONDS_PER_MONTH)
            return userobject
        else:
            return None
    except:
        error_reporting.log_exception(logging.critical, error_message = 'Error in get_active_userobject_from_username') 
        return None
    
def passhash(raw_password):
    
    # hash the password so that it is unreadable
    pwhash = hashlib.sha1()
    pwhash.update(raw_password)
    return pwhash.hexdigest()

def get_new_contact_count_sum(new_contact_counter):
    # simply counts up the total number of contact items received since the previous last time the user has logged in
    # This also adds in the values since the current login, so that the value will reflect the total count since 
    # previous last login, up to the current minute.
    sum = 0
    
    sum += new_contact_counter.num_received_kiss_since_last_login
    sum += new_contact_counter.previous_num_received_kiss

    sum += new_contact_counter.num_received_wink_since_last_login
    sum += new_contact_counter.previous_num_received_wink

    sum += new_contact_counter.num_received_key_since_last_login
    sum += new_contact_counter.previous_num_received_key
    
    sum += new_contact_counter.num_received_friend_request_since_last_login
    sum += new_contact_counter.previous_num_received_friend_request    
    
    sum += new_contact_counter.num_received_friend_confirmation_since_last_login
    sum += new_contact_counter.previous_num_received_friend_confirmation 
    
    
    return sum


def create_unread_mail_object():
    # creates and returns a new object of type UnreadMailCount
    unread_mail = UnreadMailCount()
    unread_mail.unread_contact_count = 0
    unread_mail.put()
    return unread_mail
    
def create_contact_counter_object():
    contact_counter = CountInitiateContact()
    # no need to set defaults to 0, as this is already done in the model definition.
    contact_counter.put()
    return contact_counter

def get_vip_online_status_string(userobject_key):
    online_status = online_presence_support.get_online_status(userobject_key)
    status_string = constants.OnlinePresence.presence_text_dict[online_status]
    return status_string
    
    

def get_photo_message(userobject):

    # generate the message to be shown in the profile photo space if a photos is not available,
    # and when viewed by non-owners of the account.
    try:
        if userobject.unique_last_login_offset_ref.has_public_photo_offset and userobject.unique_last_login_offset_ref.has_private_photo_offset:
            photo_message = u"%s" % (text_fields.has_private_and_public_photos)
        elif userobject.unique_last_login_offset_ref.has_public_photo_offset:
            photo_message = u"%s" % (text_fields.has_public_photos)
        elif userobject.unique_last_login_offset_ref.has_private_photo_offset:
            photo_message = u"%s" %  (text_fields.has_private_photos)
        else:
            photo_message = u"%s" %  (text_fields.has_no_photos)
    except:
        photo_message = u''
        error_reporting.log_exception(logging.critical)       

            
    return photo_message
            

def return_time_difference_in_friendly_format(time_to_display, capitalize = True, data_precision = 2, time_is_in_past = True):
    
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
    
    weeks, days = divmod(time_difference.days, 7)
    minutes, seconds = divmod(time_difference.seconds, 60)
    hours, minutes = divmod(minutes, 60)
    
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
            if capitalize:
                ago_text = ugettext("ago (capitalize if first word)")
            else:                  
                ago_text = ugettext("ago")
            generated_html = ugettext("%(joined_time)s %(ago_text)s") % {'joined_time' : joined_time, 'ago_text' : ago_text}
        else:
            # time is in the future
            if capitalize:
                in_text = ugettext("In")
            else:                  
                in_text = ugettext("in")
            generated_html = "%(in_text)s %(joined_time)s" % {'joined_time' : joined_time, 'in_text' : in_text}

             
    return generated_html

def compute_captcha_bypass_string(sender_uid, receiver_uid):
    # this is a function that provides some level of security for the captcha, since this key
    # must be known if the captcha is to be bypassed when sending a message between two users.
    
    # only compute it based on the last few characters
    return passhash(sender_uid[-5:]  + receiver_uid[-5:])


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
    props = dict((k, v.__get__(e, klass)) for k, v in klass.properties().iteritems())
    props.update(extra_args)
    return klass(**props)


NUM_PASSWORD_CHARS = 5

def gen_passwd():
    newpasswd = ''
    chars = string.digits
    for i in range(NUM_PASSWORD_CHARS):
        newpasswd = newpasswd + random.choice(chars)
    return newpasswd



EMAIL_VERIFICATION_CONFIRMATION_HASH_SIZE = 5

# we need to prevent any possible confusion with the secret verification code -- therefore, replace the following 
# characters: 1, i, I, l, L, 0, O with less confusing (easier to distinguish) chars. 
intab = "1iIlL0O"
outtab = "ABCDEFG"
trantab = string.maketrans(intab, outtab)

def compute_secret_verification_code(username, email_address):
    # computes a secret code that is used for verifying a particular username and email_address.
    # Note: we add "_random_string_" into the string before hashing to make it more difficult for someone 
    # to reverse engineer the code that we use for computing the hash. 
    string_to_hash = "%s_random_string_%s" % (username, email_address)
    secret_verification_code = passhash(string_to_hash)
    secret_verification_code = secret_verification_code[:EMAIL_VERIFICATION_CONFIRMATION_HASH_SIZE]
    secret_verification_code = secret_verification_code.translate(trantab)
    secret_verification_code = secret_verification_code.upper()
    return secret_verification_code


def check_if_user_has_denounced_profile(owner_uid, display_uid):
    # checks if the owner userobject has reported the displayed profile as unacceptable.
    query_filter_dict = {}   
    
    displayed_uid_key = db.Key(display_uid)
    owner_uid_key = db.Key(owner_uid)
    
    query_filter_dict['displayed_profile ='] = displayed_uid_key
    query_filter_dict['reporter_profile ='] =  owner_uid_key
 
    query = do_query(models.MarkUnacceptableProfile, query_filter_dict)
        
    mark_unacceptable_profile = query.get()
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


def delete_sub_object(parent_object, sub_object_name):
    
    # accepts a string representing the name of a sub-object of userobject, and deletes it from the database.
    # This is used in the case of a failed registration attempt, and will be used later on when we write code to
    # clean-up and remove deleted profiles.
    
    
    object_to_delete = getattr(parent_object, sub_object_name)
    
    try:
        error_message = """
        ***
        Deleting %s: %s
        """ %( sub_object_name, repr(object_to_delete))
        
        error_reporting.log_exception(logging.warning, error_message = error_message ) 
        object_to_delete.delete()

    except: 
        error_message = """
        ***
        Unable to delete %s: %s
        """ %( sub_object_name, repr(object_to_delete))
        
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

    return user_tracker
            

def update_ip_address_on_user_tracker(user_tracker):
    
    # store tracking information related to the IP address that the current user is entering from
    
    try:
        
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
        user_tracker = userobject.user_tracker
        assert(user_tracker)
        
        position_of_email_address_in_user_tracker_list = get_first_position_of_value_in_list(email_address, user_tracker.verified_email_addresses_list)
        
        assert position_of_email_address_in_user_tracker_list == None
        
        user_tracker.verified_email_addresses_list.append(email_address)
        user_tracker.first_time_email_address_verified_list.append(datetime.datetime.now())
        user_tracker.last_time_email_address_verified_list.append(datetime.datetime.now())
        
        user_tracker.put()
        
    except:
        error_reporting.log_exception(logging.critical)       

        
        
def when_to_send_next_notification_txn(new_contact_key, hours_between_notifications):
    # Intended to run in a transaction. 
    # this code should work for both the unread_mail_count object (mail counter), 
    # and the new_contact_counter object (winks, etc. counter)
    new_contact_obj = db.get(new_contact_key)
    
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
    
    if settings.BUILD_NAME == "Language":
        
        return_dict.update({# the following entries are only used in Language
                            'languages': '----', # list of languages spoken
                            'languages_to_learn': '----', # list of languages to learn
                            'language_to_teach': '----',
                            'language_to_learn': '----',        
                            })
        
    elif settings.BUILD_NAME == "Friend":
        return_dict.update({# following is only for Friend
                            'for_sale' : '----',
                            'for_sale_sub_menu' : '----',
                            'friend_price' : '----',
                            'friend_currency' : '----',
                            })
        #return_dict.update(user_profile_details.UserSpec.activity_categories_unset_dict)
    else:
        return_dict.update({# following is only for dating websites
                            'relationship_status': '----',
                            'preference': '----',                            
                            })
    
    try:
        #model_signup_fields = getattr(user_profile_main_data.UserSpec, "signup_fields")
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
                        
                        if settings.BUILD_NAME == "Discrete" or settings.BUILD_NAME == "Gay" or settings.BUILD_NAME == "Swinger":
                            if field_name == "relationship_status" and lang_idx == localizations.input_field_lang_idx['es']:
                                if settings.BUILD_NAME == "Gay":
                                    # all profiles in Gay site are male - give Spanish masculine ending "o"
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
                error_message = "*Error* get_fields_in_current_language - %s Undefined" % field_name
                return_dict[field_name] = ''
                error_reporting.log_exception(logging.critical, error_message = error_message)
        
        if pluralize_sex:

            if settings.BUILD_NAME != "Language" and settings.BUILD_NAME != "Friend":
                # if pluralized, lookup the field name in the "preference" setting (since it is pluralized),
                # otherwise use the "sex" setting.
                if field_vals_dict['preference'] != "----":
                    return_dict["preference"] = field_dictionary_by_field_name["preference"][lang_idx][field_vals_dict['preference']]
                if field_vals_dict['sex'] != "----":
                    return_dict["sex"] = field_dictionary_by_field_name["preference"][lang_idx][field_vals_dict['sex']]
            else:
                # preference fields do not exist for Language or Friend, so lookup in the "sex" field
                if field_vals_dict['sex'] != "----":
                    return_dict["sex"] = field_dictionary_by_field_name["sex"][lang_idx][field_vals_dict['sex']]
        else:
            if settings.BUILD_NAME != "Language" and settings.BUILD_NAME != "Friend":
                if field_vals_dict['preference'] != "----":
                    return_dict["preference"] = field_dictionary_by_field_name["sex"][lang_idx][field_vals_dict['preference'] ]
            if field_vals_dict['sex'] != "----":
                return_dict["sex"] = field_dictionary_by_field_name["sex"][lang_idx][field_vals_dict['sex']]
                    
        # in order to get better google keyword coverage, override sex and preference for certian age ranges
        # depending on the language.
        if settings.SEO_OVERRIDES_ENABLED:
            if field_vals_dict['age'] != "----":
                lang_code = localizations.lang_code_by_idx[lang_idx]
                return_dict["sex"] = search_engine_overrides.override_sex(lang_code, int(field_vals_dict['age']), return_dict["sex"])
                
                if settings.BUILD_NAME != "Friend" and settings.BUILD_NAME != "Language":
                    return_dict["preference"] = search_engine_overrides.override_sex(lang_code, int(field_vals_dict['age']), return_dict["preference"])
            
        try:    
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
            error_reporting.log_exception(logging.error)
        
    except:
        error_reporting.log_exception(logging.critical) 
        
    return (return_dict)


def add_session_id_to_user_tracker(user_tracker, session_id):
    # adds the current session identifier to the user_tracker so that if necessary we can clear the sessions from the
    # database, thereby forcing a logout of a user.
    
    try:
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
        
def kill_user_sessions(user_tracker):
    # loops over the sessions identified in the user_tracker.list_of_session_ids list, and removes them from the database
    # This has the effect of immediately logging out all of the sessions that we remove. This is necessary for 
    # users that are behaving badly and that need to be immediately removed.
    
    try:
        for session_id in user_tracker.list_of_session_ids:
            expiry_time = int(session_id[:-33])
            if time.time() <= expiry_time:
                # it has not yet expired (ie. is still valid) so we need to remove it from
                # the database in order to force a logout. On the other hand, if it has expired we don't 
                # need to remove it as it does not have an active session, and because it will be cleaned up
                # by the cron jobs.
                memcache.delete(session_id) 
                key = db.Key.from_path(gaesessions.SessionModel.kind(), session_id)
                db_entry_key = db.get(key)
                if db_entry_key:
                    db.delete(db_entry_key)    
                    logging.info("deleting database session key %s\n" % session_id)
                    
        user_tracker.list_of_session_ids = []
        user_tracker.list_of_session_ids_last_index = None
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
    
    # must ensure that keys are compared using *string* representations, *not* key representations - because the 
    # order can change - see (my comment) on StackOverflow
    # http://stackoverflow.com/questions/7572386/why-are-appengine-database-keys-sorted-differently-than-strings
    uid1 = str(uid1)
    uid2 = str(uid2)
    
    if uid1 < uid2:
        parent_key_name = "%s_and_%s" % (uid1, uid2)
    else:
        parent_key_name = "%s_and_%s" % (uid2, uid1)
    mail_parent_key = db.Key.from_path('FakeMailMessageParent', parent_key_name)
    return mail_parent_key


def get_have_sent_messages_key_name(owner_key, other_key):
    key_name = "%s_and_%s" % (str(owner_key), str(other_key))
    return key_name

    
def get_have_sent_messages_key(owner_key, other_key):
    key_name = get_have_sent_messages_key_name(owner_key, other_key)
    have_sent_messages_key = db.Key.from_path('UsersHaveSentMessages', key_name)
    return have_sent_messages_key

def get_have_sent_messages_object(owner_key, other_key, create_if_does_not_exist = False):
    
    try:
        have_sent_messages_key = get_have_sent_messages_key(owner_key, other_key)
        have_sent_messages_object = db.get(have_sent_messages_key)
        if not have_sent_messages_object and create_if_does_not_exist:
            have_sent_messages_object = models.UsersHaveSentMessages(key_name = get_have_sent_messages_key_name(owner_key, other_key))
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
    
    
    # since the HR datastore code is dependent on the keys for pulling the data from the DB, as opposed
    # to doing a query, we need to have the keys updated to the new HR datastore (which can't be done until
    # we have actually moved to the new HR datastore)
    
        
    object_key_name = str(viewer_userobject_key) + str(display_userobject_key) 
    initiate_contact_key = db.Key.from_path('InitiateContactModel', object_key_name)
    initiate_contact_object = db.get(initiate_contact_key)
    
    if create_if_does_not_exist and not initiate_contact_object:
        # only create a new object if the database has not already stored one for the viewer and the display user.
        initiate_contact_object = models.InitiateContactModel(key_name = object_key_name, 
            displayed_profile = display_userobject_key, viewer_profile = viewer_userobject_key)
        initiate_contact_object.put()
            
    return initiate_contact_object

def convert_string_key_from_old_app_to_current_app(old_key_string):
    
    old_key = db.Key(old_key_string)
    kind = old_key.kind()
    id_or_name = old_key.id_or_name()
    old_app_name = old_key.app()

    new_key = db.Key.from_path(kind, id_or_name)
    new_key_string = str(new_key)
    new_app_name = new_key.app()
    
    # We should never be re-directing a key that is the same app name as the current app
    logging.info("old_app_name %s new_app_name %s" % (old_app_name, new_app_name))
    assert(old_app_name != new_app_name)
    return new_key_string

    
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
    if have_sent_messages_object.datetime_first_message_to_other_today + datetime.timedelta(
        hours = constants.NUM_HOURS_WINDOW_TO_RESET_MESSAGE_COUNT_TO_OTHER_USER - constants.RESET_MAIL_LEEWAY) <  datetime.datetime.now():
        return True
    else:
        return False
        
def check_if_allowed_to_send_more_messages_to_other_user(have_sent_messages_object):
    # checks if the current user has exceeded the number of messages that he is allowed to send to the other
    # user in the current "time window"
    if not have_sent_messages_object or \
       have_sent_messages_object and have_sent_messages_object.num_messages_to_other_sent_today < \
       constants.NUM_MESSAGES_TO_OTHER_USER_IN_TIME_WINDOW:
        return True
    else:
        return False
    
    
def get_removed_user_reason_html(removed_userobject):
    
    # Generates text that explains why a given userobject was eliminated. 
    
    generated_html = ''
    notify_text = ''
    
    # include special text to warn users about scammer profiles and tell them why profiles have been eliminated
    notify_us_of_similar_profiles_text = u"<br><br>%s" % ugettext("If you see any other profiles like this, please send an email to support@%(app_name)s to notify us of the user name.") % {
                    'app_name' : settings.APP_NAME}
    
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

def get_vip_status(userobject):
    
    vip_status = None
    if userobject.client_paid_status and userobject.client_paid_status_expiry > datetime.datetime.now():
        # This is a VIP member - return their current status.
        vip_status = userobject.client_paid_status

    return(vip_status)


def get_nid_from_uid(uid):
    # function that looks up the nid [ie. key().id()] based on the uid. 
    memcache_key = constants.NID_MEMCACHE_PREFIX + uid
    nid = memcache.get(memcache_key)    
    
    if nid is None:
        userobject = utils_top_level.get_object_from_string(uid)
        nid = userobject.key().id()
        memcache.set(memcache_key, nid, constants.SECONDS_PER_DAY)
    
    return nid
    
    
def return_and_report_internal_error(request):
    
    error_reporting.log_exception(logging.critical)
    txt = ugettext('Internal error - this error has been logged, and will be investigated immediately')
    return http_utils.ajax_compatible_http_response(request, txt, HttpResponseServerError)


def user_is_admin(userobject):
    if userobject and userobject.username == constants.ADMIN_USERNAME and users.is_current_user_admin():
        return True
    else:
        return False
    

def generate_profile_information_for_administrator(viewer_userobject, display_userobject):
    
    generated_html = ''
    
    try:
        if user_is_admin(viewer_userobject):
            # show information about this user to the administrator.
            generated_html += u'<br><br><div class="grid_9 alpha omega">'            
            if display_userobject.client_paid_status:
                generated_html += "Is VIP<br><br>"
                
                
            generated_html += "Email: %s<br>" % display_userobject.email_address
            generated_html += "Login IP: %s<br>" % display_userobject.last_login_ip_address
            
            if display_userobject.last_login_country_code:
                generated_html += "Login Country: %s<br>" % localizations.location_dict[lang_idx][display_userobject.last_login_country_code]
            else:
                generated_html += u'Last Country: %s<br>' % display_userobject.last_login_country_code
    
            generated_html += "Login Region: %s<br>" % display_userobject.last_login_region_code
            generated_html += "Login City: %s<br>" % display_userobject.last_login_city
            generated_html += "Registration IP: %s<br>" % display_userobject.registration_ip_address
            generated_html += "Registration City: %s<br>" % display_userobject.registration_city
            
            generated_html += '<br></div>'    
            
    except:
        error_reporting.log_exception(logging.error)
            
            
    return generated_html


def store_login_ip_information(userobject):
    userobject.last_login_ip_address = os.environ['REMOTE_ADDR'] 
    userobject.last_login_country_code = request.META.get('HTTP_X_APPENGINE_COUNTRY', None)
    userobject.last_login_region_code = request.META.get('HTTP_X_APPENGINE_REGION', None)
    userobject.last_login_city = request.META.get('HTTP_X_APPENGINE_CITY', None)    