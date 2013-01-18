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


import logging, datetime, os, re

from google.appengine.ext import db 
from google.appengine.ext import blobstore


from django.http import HttpResponse, HttpResponseNotFound
from django.utils import simplejson
from django.utils.translation import ugettext

from email.Utils import formatdate
from calendar import timegm


from utils import ajax_call_requires_login
from user_profile_details import UserProfileDetails
from user_profile_main_data import UserSpec
from forms import FormUtils
from html_container import UserMainHTML
from utils import return_time_difference_in_friendly_format, compute_captcha_bypass_string
from constants import ContactIconText
import mailbox
import constants
import utils, utils_top_level
import store_data, settings
import localizations, text_fields
import error_reporting

# This module contains functions that respond to ajax requests from the client.
# There are two main types of files here, get_xxx and load_xxx. The load_xxx
# functions are generally used for generating HTML that is non-user specific. Ie.
# a checkbox with various options available (but none selected). On the other hand
# the get_xxx functions are used for getting the user-specific settings for a particular
# field, and the client javascript will configure the loaded html to correspond to the the 
# values returned by the get_xxx.

def get_location_options(request, location_code):
    # returns html that represents the region options for a select dropdown menu for a given country
    
    try:
        (country_code, region_code, sub_region_code) = location_code.split(",")
        
        # TODO: clean this up, and make consistent with the rest of the code
        if region_code: #don't move country_code before region_code
            region_code = "%s,%s," % (country_code, region_code)        
        if country_code:
            country_code = "%s,," % country_code

        
        if country_code and not region_code: # return the regions
            if country_code in localizations.region_options_html:
                return HttpResponse(localizations.region_options_html[country_code])
            
        elif country_code and region_code: # return the sub-regions
            if country_code in localizations.region_options_html and region_code in localizations.sub_region_options_html[country_code]: 
                return HttpResponse(localizations.sub_region_options_html[country_code][region_code])
    except:
        error_message = "Serious error in get_location_options: location_code: %s" % location_code
        error_reporting.log_exception(logging.critical, request=request, error_message=error_message)


    return HttpResponse("----")

def get_for_sale_to_buy_options(request, current_selection):
    """
    get the options for either the for_sale or to_buy sub-menu
    for_sale_or_to_buy: either "for_sale" or "to_buy" - just tells us which dropdown we are filling in
    current_selection: tells the current value of the for_sale or to_buy menu, which is necessary to get the appropriate child menus
    """
    try:
        lang_idx = localizations.input_field_lang_idx[request.LANGUAGE_CODE]
        http_response = utils.get_for_sale_to_buy(current_selection, lang_idx)
        return HttpResponse(http_response)
    except:
        error_reporting.log_exception(logging.critical, request=request, error_message="Error in get_for_sale_to_buy_options")
        return HttpResponse("Error")

def get_settings(request, list_of_fields, data_structure_to_extract_values):
    # This is a generic handler for looking up settings, given a list of fields to loop over, and 
    # given the data structure which the values should be extracted from
    response_dict = {}
    try:
        if request.method == 'GET':
            for field in list_of_fields:
                response_dict[field] = getattr(data_structure_to_extract_values ,field)
            
            return response_dict
        
        else:
            # this should only be called with a GET, and otherwise something strange has happened
            raise Exception("ajax.get_settings has been called in an unexpected way")
        
    except:
        error_reporting.log_exception(logging.critical, request=request)
        
    # return an empty dictionary
    return response_dict
    
# the following code is intentionally called *outside* of any function so that it will only execute 
# once on initialization. We place it here because it is only used in get_simple_search_settings()
default_response_dict = {'query_order': 'unique_last_login',  'region_options_html': '', 'sub_region_options_html': ''}
for field in UserSpec.simple_search_fields:   
    default_response_dict[field] = "----"
if settings.BUILD_NAME == "Friend":
    default_response_dict["for_sale_sub_menu_options_html"] = ''
    default_response_dict["to_buy_sub_menu_options_html"] = ''

def get_simple_search_settings(request):
    # this function returns the default simple search settings, based on the values that were previously
    # stored for the given user (by default, set to whatever their last search was).
    
    response_dict = default_response_dict.copy()  
    try:
                         
        if request.session.__contains__('userobject_str'):
            userobject =  utils_top_level.get_userobject_from_request(request)
            
            for field in UserSpec.simple_search_fields:
                response_val = getattr(userobject.search_preferences2 ,field)
                # The following is a temporary fix related to the fact that we changed 'dont_care'
                # to "----" but some profiles will still have the old value. This can be removed once
                # a database cleanup has been done.
                response_dict[field] = response_val
        else:
            # not sure if this should be a warning or not .. why are non-logged in users calling this function - if this happens
            # then we should re-write some of the javascript to prevent it.
            error_reporting.log_exception(logging.warning, error_message = "non-logged in user attempting to get search_settings")

        # Now we generate the dynamically allocated sub-menus, depending on the currently selected values.
        response_dict.update(utils.get_location_dropdown_options_and_details(response_dict['country'], response_dict['region']))
        
        if settings.BUILD_NAME == "Friend":
            response_dict['for_sale_sub_menu_options_html'] = utils.get_child_dropdown_options_and_details(response_dict['for_sale'], 
                                localizations.input_field_lang_idx[request.LANGUAGE_CODE])
            
            #response_dict['to_buy_sub_menu_options_html'] = utils.get_child_dropdown_options_and_details(response_dict['to_buy'], 
                                #localizations.input_field_lang_idx[request.LANGUAGE_CODE])
                
    except:
        error_reporting.log_exception(logging.critical)

    json_response = simplejson.dumps(response_dict) 
    return HttpResponse(json_response,  mimetype='text/javascript')

@ajax_call_requires_login
def get_signup_fields_settings(request, uid):
    # this function returns the current user info settings, for display in the drop-down
    # menus when users want to edit the values.. 
    
    response_dict = {}
    
    try:
        userobject = utils_top_level.get_userobject_from_request(request)
        assert(uid == str(userobject.key()))
        response_dict = get_settings(request, UserSpec.signup_fields_to_display_in_order + ['region', 'sub_region'], userobject)
        
        # add additional location data to the response_dict 
        response_dict.update(
            utils.get_location_dropdown_options_and_details(response_dict['country'], response_dict['region']))
        
    except:
        error_reporting.log_exception(logging.critical, request=request)

    json_response = simplejson.dumps(response_dict) 
    return HttpResponse(json_response,  mimetype='text/javascript')

@ajax_call_requires_login
def get_details_fields_settings(request, uid):
    # this function returns the current user details settings, for display in the drop-down
    # menus when users want to edit the values.. 
    response_dict = {}
    try:
        userobject = utils_top_level.get_userobject_from_request(request)
        assert(uid == str(userobject.key()))
        response_dict =  get_settings(request, UserProfileDetails.details_fields_to_display_in_order, userobject)
    except:
        error_reporting.log_exception(logging.critical, request=request)

    json_response = simplejson.dumps(response_dict) 
    return HttpResponse(json_response,  mimetype='text/javascript')

@ajax_call_requires_login
def get_json_list(request, list_of_options):
    # generic function that takes in a list, and returns a json-encapsulated object.
    
    if request.method == 'GET':
        json_response = simplejson.dumps(list_of_options) 
        return HttpResponse(json_response,  mimetype='text/javascript')
    else:
        # this should only be called with a GET, and otherwise something strange has happened
        raise Exception("ajax.get_json_list has been called in an unexpected way")
    
@ajax_call_requires_login    
def get_generic_options_settings(request, uid, option_name):  
    
    try:
        userobject = utils_top_level.get_userobject_from_request(request)
        assert(uid == str(userobject.key()))
        list_of_selected_options  = getattr(userobject, option_name)
        return get_json_list(request, list_of_selected_options)
    except:
        error_reporting.log_exception(logging.critical)
        return get_json_list(request, "")


@ajax_call_requires_login
def get_email_address_settings(request, uid):
    
    try:
        userobject = utils_top_level.get_userobject_from_request(request)
        assert(uid == str(userobject.key()))
        if userobject.email_address != "----":
            json_response = simplejson.dumps(userobject.email_address) 
        else: 
            # if email address is set to ----, don't show that to the user,
            # send them an empty string instead.
            json_response = simplejson.dumps("")
    except:
        error_reporting.log_exception(logging.critical)
        json_response = simplejson.dumps("Error")

    return HttpResponse(json_response,  mimetype='text/javascript')



@ajax_call_requires_login
def get_about_user_settings(request, uid):
    
    try:
        userobject = utils_top_level.get_userobject_from_request(request)
        assert(uid == str(userobject.key()))
        
        # is_primary_user is true, since this function can only be called after the user has edited his about_user value
        about_user = UserMainHTML.get_text_about_user(userobject, is_primary_user = True, for_edit = True)
        json_response = simplejson.dumps(about_user) 
    
    except:
        error_reporting.log_exception(logging.critical)
        json_response = simplejson.dumps("Error")

    return HttpResponse(json_response,  mimetype='text/javascript')



@ajax_call_requires_login
def get_current_status_settings(request, uid):
    
    try:
        userobject = utils_top_level.get_userobject_from_request(request)
        assert(uid == str(userobject.key()))
        current_status = ""
        if userobject.current_status != "----":
            current_status = userobject.current_status
        json_response = simplejson.dumps(current_status) 
        
    except:
        error_reporting.log_exception(logging.critical)
        json_response = simplejson.dumps("Error")
    
    return HttpResponse(json_response,  mimetype='text/javascript')


@ajax_call_requires_login
def get_change_password_fields_settings(request, uid):
    # don't do anything, because all of these fields should be returned as blank
    # This stub is required so that the javascript calls are consistent and don't
    # require special case code for the passwords.
    userobject = utils_top_level.get_userobject_from_request(request)
    assert(uid == str(userobject.key()))
    return HttpResponse("")



def get_photo(request, photo_object_key_str, photo_size = 'small', is_admin_login = False):
    # Gets photos indicated in the request. 
    # DO NOT mark this a requiring a login, because it is necessasry for people browsing the website.

    if request.method == 'GET':
        
        
        try:
            photo_object = utils_top_level.get_object_from_string(photo_object_key_str)
            assert(photo_object)    
           
            has_key_to_private_photos = False
            
            if (photo_object.is_private or not photo_object.is_approved) and 'userobject_str' in request.session:
                primary_userobject_key = db.Key(request.session['userobject_str'])
                display_userobject_key = photo_object.parent_object.key()
                
                if primary_userobject_key == display_userobject_key:
                    has_key_to_private_photos = True
                else:
                    has_key_to_private_photos = utils.check_if_authorized_for_private_photos(primary_userobject_key, display_userobject_key) 
            
            if is_admin_login:
                has_key_to_private_photos = True
                
            if (not photo_object.is_private and photo_object.is_approved) or has_key_to_private_photos:
                #build the response
                photo_img = getattr(photo_object, photo_size, None)
                response = HttpResponse(photo_img)

                # set the content type to png because that's what the Google images api 
                # stores modified images as by default
                response['Content-Type'] = 'image/png'
                # the following "last-modified" is based on the way it is done in django.views.decorators.http
                response['Last-Modified'] = formatdate(timegm(photo_object.creation_date.utctimetuple()))[:26] + 'GMT'

                if photo_object.is_private:
                    response['Cache-Control']  = 'private, max-age=%s' % constants.SECONDS_PER_MONTH
                else:
                    response['Cache-Control']  = 'public, max-age=%s' % constants.SECONDS_PER_MONTH
            else:
                error_reporting.log_exception(logging.warning, request=request, \
                                              error_message = 'User: "%s" Unauthorized photo access to profile: "%s:' % \
                                              (utils.get_username_from_request(request), utils.get_username_from_userobject(photo_object.parent_object)))
                response = HttpResponse("Error: Unauthorized access")

            return response
        except:
            error_reporting.log_exception(logging.error, request=request, error_message = 'User: "%s" get_photo error' % utils.get_username_from_request(request))
            return HttpResponse('Fail')
    else:
        error_reporting.log_exception(logging.warning, request=request, error_message = 'User: "%s" get_photo called with method other than GET' %\
                                      utils.get_username_from_request(request))
        return HttpResponse('Fail')
    
    
# The following "load" functions generate the HTML required for displaying the given section.
@ajax_call_requires_login
def load_profile_photo(request):
    # This should only be called on the profile of the "owner" when they are editing/uploading photos
    userobject = utils_top_level.get_userobject_from_request(request)
    return HttpResponse(FormUtils.generate_profile_photo_html(request.LANGUAGE_CODE, userobject, text_fields.photo_encouragement_text, 
                                                              is_primary_user = True))

@ajax_call_requires_login
def load_photos(request):
    userobject = utils_top_level.get_userobject_from_request(request)
    # Note: currently this function is only called by the owner of the profile (for non-owner profiles
    # currently photos are loaded when the page loads -- not ajax), while they are uploading 
    # or editing photos. If this is ever called by other users, then the values that we are currently
    # passing into the function below will have to be changed to include the other profile userobject,
    # and to disallow "is_primary_user" access.
    return HttpResponse(FormUtils.generate_photos_html(request.LANGUAGE_CODE, userobject, userobject, is_primary_user = True))

@ajax_call_requires_login
def load_photos_for_edit(request):
    userobject = utils_top_level.get_userobject_from_request(request)
    return HttpResponse(FormUtils.generate_photos_html(request.LANGUAGE_CODE, userobject, userobject,
                            edit=True, table_id = 'id-photo-table-for-edit', is_primary_user = True))
@ajax_call_requires_login
def load_photo_upload_form_url(request):
    try:
        blobstore_submit_url = blobstore.create_upload_url('/rs/blobstore_photo_upload/')
        json_response = simplejson.dumps({'blobstore_submit_url': blobstore_submit_url}) 
        return HttpResponse(json_response,  mimetype='text/javascript')
    except:
        error_reporting.log_exception(logging.error, error_message = 'blobstore_photo_upload exception')
        return HttpResponse("Fail")
            
@ajax_call_requires_login
def load_signup_fields(request):
    userobject = utils_top_level.get_userobject_from_request(request)
    generated_html =  HttpResponse(FormUtils.generate_dropdown_form_for_current_section(localizations.input_field_lang_idx[request.LANGUAGE_CODE],\
        userobject, "signup_fields", UserSpec))
    return generated_html

@ajax_call_requires_login
def load_signup_fields_for_edit(request):
    userobject = utils_top_level.get_userobject_from_request(request)
    generated_html =  HttpResponse(FormUtils.generate_dropdown_form_for_current_section(localizations.input_field_lang_idx[request.LANGUAGE_CODE],
        userobject, "signup_fields", UserSpec,  edit = True)) 
    return generated_html

@ajax_call_requires_login
def load_details_fields(request):
    userobject = utils_top_level.get_userobject_from_request(request)
    generated_html =  HttpResponse(FormUtils.generate_dropdown_form_for_current_section(localizations.input_field_lang_idx[request.LANGUAGE_CODE],
        userobject, "details_fields", UserProfileDetails)) 
    return generated_html

@ajax_call_requires_login
def load_details_fields_for_edit(request):
    userobject = utils_top_level.get_userobject_from_request(request)
    generated_html =  HttpResponse(FormUtils.generate_dropdown_form_for_current_section(localizations.input_field_lang_idx[request.LANGUAGE_CODE],
        userobject, "details_fields", UserProfileDetails, edit = True)) 
    return generated_html

@ajax_call_requires_login
def load_checkbox_section(request, section_name):
    try:
        lang_idx = localizations.input_field_lang_idx[request.LANGUAGE_CODE]
        userobject = utils_top_level.get_userobject_from_request(request)
        generated_html =  HttpResponse(
            utils.generic_html_generator_for_list(lang_idx, section_name, 
                getattr(userobject, section_name)))
        return generated_html
    except:
        error_reporting.log_exception(logging.critical)       
        return '' 

@ajax_call_requires_login
def load_checkbox_section_for_edit(request, section_name, fields_per_row = constants.CHECKBOX_INPUT_COLS_PER_ROW):
    try:
        lang_idx = localizations.input_field_lang_idx[request.LANGUAGE_CODE]
        generated_html =  HttpResponse(
            FormUtils.generic_html_generator_for_checkboxes(
                UserProfileDetails.checkbox_fields[section_name]['options'][lang_idx], fields_per_row))
        return generated_html
    except:
        error_reporting.log_exception(logging.critical)       
        return ''



@ajax_call_requires_login
def load_email_address(request):
    
    try:
        userobject = utils_top_level.get_userobject_from_request(request)
        if userobject.email_address_is_valid:
            generated_html =  userobject.email_address
        else:
            if userobject.email_address != "----":
                generated_html = '<div class="cl-color-text"> Email <strong>"%s"</strong> no es una \
                direccion valida.</div>' % userobject.email_address
            else:
                generated_html = "Eliminado"
    except:
        error_reporting.log_exception(logging.critical)
        generated_html = "Error"
                
    return HttpResponse(generated_html)


@ajax_call_requires_login
def load_mail_textarea(request, other_uid, section_name):
    
    try:
        userobject = utils_top_level.get_userobject_from_request(request)
        assert(userobject)
        owner_uid = str(userobject.key())
        have_sent_messages_object = utils.get_have_sent_messages_object(owner_uid, other_uid)
        generated_html = mailbox.generate_mail_textarea(section_name, owner_uid, other_uid, have_sent_messages_object)
        return HttpResponse(generated_html)
    except:
        error_reporting.log_exception(logging.error, error_message = 'load_mail_textarea error')
        return HttpResponse('Fail')

@ajax_call_requires_login
def load_about_user_for_edit(request):
    try:
        userobject = utils_top_level.get_userobject_from_request(request)
        assert(userobject)        
        generated_html = FormUtils.get_standard_textarea_html("about_user", constants.ABOUT_USER_MAX_ROWS, add_edit_to_id=True)
        return HttpResponse(generated_html)
    except:
        error_reporting.log_exception(logging.error, error_message = 'load_mail_textarea error')
        return HttpResponse('Fail')        

@ajax_call_requires_login
def load_about_user(request):
    try:
        userobject = utils_top_level.get_userobject_from_request(request)        
        generated_html = UserMainHTML.get_text_about_user(userobject, is_primary_user = True)
        return HttpResponse(generated_html)
    except:
        error_reporting.log_exception(logging.error, error_message = 'load_mail_textarea error')
        return HttpResponse('Fail')     

@ajax_call_requires_login
def load_email_address_for_edit(request):
    # the following is kind of a dirty hack. Set section name to "edit-email_address", and field_name to "email_address". 
    # This is necessary to make the code work with previously existing javascript functions. Additionally, this is a unique
    # section, in which the only input is in-fact the email address.
    
    # set the text field to be as wide as the "length" (number of characters allowed) -- since in this case the width is not
    # under any space restrictions.
    
    try:
        generated_html =  FormUtils.generate_input_text_field("email_address", "edit-email_address", "email_address", 
                                                              constants.field_formats['text_field_length'], 
                                                              'cl-wide-textinput-width-px')
        generated_html += "<p>%s</p>" % ugettext("""
    When you click on "Save", you will receive an email from <em>%(sender_email)s</em> that will confirm
    that your email address has been correctly stored.""") % {'sender_email': constants.sender_address_html}
    
    except:
        error_reporting.log_exception(logging.critical)
        generated_html = "Error"
         
    return HttpResponse(generated_html)


@ajax_call_requires_login
def load_current_status(request):
    
    try:
        userobject = utils_top_level.get_userobject_from_request(request)
        
        if userobject.current_status != "----":
            generated_html = u'<div>%s</div>' % userobject.current_status
        else:
            generated_html = u"%s" % text_fields.share_thinking
            
            
    except:
        error_reporting.log_exception(logging.critical)
        generated_html = "Error"
        
    return HttpResponse(generated_html)


@ajax_call_requires_login
def load_current_status_for_edit(request):
    # set the text field to be as wide as the "length" (number of characters allowed) -- since in this case the width is not
    # under any space restrictions.
    try:
        generated_html =  FormUtils.generate_input_text_field("current_status", "edit-current_status", "current_status",
                                                          constants.field_formats['status_field_length'], 
                                                          'cl-very-wide-textinput-width-px')
    except:
        error_reporting.log_exception(logging.critical)
        generated_html = "Error"
        
    return HttpResponse(generated_html)

@ajax_call_requires_login
def load_change_password_fields(request):
    
    try:
        userobject = utils_top_level.get_userobject_from_request(request)
        time_since_password_change =  datetime.datetime.now() - userobject.password_attempted_change_date
        
        # if password was updated in the previous minute, then we show the user a success message
        # This is hackey -- should look at another way of achieveing this functionality, possibly
        # by passing additional data with the POST.
        if time_since_password_change < datetime.timedelta(minutes = 1):
            if userobject.change_password_is_valid:
                generated_html = u"%s" % text_fields.success_change_password_text
            else:
                generated_html = u'<p class="cl-color-text"><strong>%s</strong></p>' % text_fields.failed_change_password_text
        else:
            generated_html = u"%s" % text_fields.change_password_text
            
    except:
        error_reporting.log_exception(logging.critical)
        generated_html = "Error" 
        
    return HttpResponse(generated_html)

@ajax_call_requires_login
def load_change_password_fields_for_edit(request):
    try:
        generated_html = "<table>"
        lang_idx = localizations.input_field_lang_idx[request.LANGUAGE_CODE]
        generated_html += FormUtils.process_rows(lang_idx, 'change_password_fields', 'change_password_fields', UserProfileDetails)
        generated_html += "</table>"
        
    except:
        error_reporting.log_exception(logging.critical)
        generated_html = "Error"
        
    return HttpResponse(generated_html)

@ajax_call_requires_login
def load_send_mail_from_profile(request, other_uid, show_checkbox_beside_summary):
    # TODO - rename this function - it is now being called for updating conversation summary
    # under various circuumnstances. 
    #
    # This function is responsible for returning the correct data after a "send_mail" event.
    # In the case of sending mal from a user profile, the message summary will be re-written 
    # to include the most recent message that has just been sent. This function therefore
    # returns this history/summary. 
    try:
        userobject = utils_top_level.get_userobject_from_request(request)
        (generated_html, have_sent_messages_object) = \
         mailbox.get_mail_history_summary(request, userobject, utils_top_level.get_object_from_string(other_uid),  show_checkbox_beside_summary)
    except:
        error_reporting.log_exception(logging.critical)
        generated_html = "Error"
        
    return HttpResponse(generated_html)


@ajax_call_requires_login
def load_send_mail(request, other_uid):
    # This function is responsible for returning the correct data after a "send_mail" event.
    # In the case of sending mal from a user profile, the message summary will be re-written 
    # to include the most recent message that has just been sent. This function therefore
    # returns this history/summary. 
    try:
        userobject = utils_top_level.get_userobject_from_request(request)
        other_userobject = db.get(db.Key(other_uid))
        generated_html = mailbox.generate_mail_message_display_html(userobject, other_userobject, request.LANGUAGE_CODE)
    except:
        error_reporting.log_exception(logging.critical)
        generated_html = "Error"
        
    return HttpResponse(generated_html)
    

@ajax_call_requires_login
def get_initiate_contact_settings(request, display_uid):
    # Gets the status for contact settings that have already been applied, and also returns
    # the date that the contact was last made.

    try:

        if settings.BUILD_NAME == "Language":
            wink_action = ugettext("Greeting sent")
        else:
            wink_action = ugettext("Wink sent")
            
        possible_actions = ('wink', 'favorite', 'kiss', 'key', 'chat_friend', 'blocked')
        action_verb_dict = {
            'wink': wink_action, 
            'favorite': ugettext("Is favorite"), 
            'kiss': ugettext("Kiss sent"),
            'key': ugettext("Has accsess to your private profile"),
            'blocked': ugettext("Is blocked (new messages automatically deleted)"),
        }
        
        chat_friend_verb_dict = {
             'request_sent': ugettext('You are waiting for a confirmation of your chat request'),
             'request_received': ugettext('You have received a chat request'),
             'connected': ugettext('You are connected, and will see this person in your chat list when they are online'),
        } 
        
        userobject = utils_top_level.get_userobject_from_request(request) 
        response_dict = {}
        
        userobject_key = userobject.key()
        display_userobject_key = db.Key(display_uid)
        initiate_contact_object = utils.get_initiate_contact_object(userobject_key, display_userobject_key)
        
        for action in possible_actions:
            action_stored  = action + "_stored"
            action_stored_date = action + "_stored_date"
            action_remove = "remove_" + action
            action_value = getattr(initiate_contact_object, action_stored, '')
            if action_value:
                if action != "chat_friend":
                    response_dict[action_stored] = '<span class="cl-icon-active-color-text">%s</span><br>' % action_verb_dict[action]
                    sent_date = getattr(initiate_contact_object, action_stored_date, '')
                    response_dict[action_stored_date] = '<span class="cl-icon-active-color-text">%s</span>' % (return_time_difference_in_friendly_format(sent_date))

                else: 
                    if action_value == 'request_sent' or action_value == 'request_received':
                        color_class = 'cl-secondary-icon-active-color-text'
                    if action_value == 'connected':
                        color_class = 'cl-icon-active-color-text'
                        
                    action_description = chat_friend_verb_dict[action_value]
                    response_dict[action_stored] = '<span class="%s">%s</span><br>' % (color_class, action_description)
            else:
                # if it is not set, then set the fields back to default values
                response_dict[action_stored] =  u"%s" % ContactIconText.icon_message[action]
                response_dict[action_stored_date] = u''
                
        json_response = simplejson.dumps(response_dict) 
        return HttpResponse(json_response,  mimetype='text/javascript')
    
    except:
        from django.http import HttpResponseServerError
        error_reporting.log_exception(logging.critical)
        HttpResponseServerError(ugettext("Internal error - this error has been logged, and will be investigated immediately"))


@ajax_call_requires_login    
def move_message(request, have_sent_messages_id, mailbox_to_move_message_to):        
    # marks the current message as read, and leaves it in the "inbox"
    mailbox.modify_message(db.Key(have_sent_messages_id), mailbox_to_move_message_to)
    # the HttpResponse is ignored .. so, shouldn't matter what the return value is.
    return HttpResponse("OK")    
        
@ajax_call_requires_login    
def favorite_message(request, have_sent_messages_id):
    # Allow user to mark a message as being a "favorite". This also has the side effect
    # of adding the favorited person to the initiate_contact_model favorites structure.
    # This duplication of the same data is necessary for being able to efficiently query
                 
    
    try:
        have_sent_messages_object = db.get(db.Key(have_sent_messages_id)) 
        
        # just toggle the value
        have_sent_messages_object.other_is_favorite = not have_sent_messages_object.other_is_favorite
        have_sent_messages_object.put()
        
        userobject_key = have_sent_messages_object.owner_ref.key()
        other_userobject_key = have_sent_messages_object.other_ref.key()
                
        initiate_contact_object = utils.get_initiate_contact_object(userobject_key, other_userobject_key, create_if_does_not_exist=True)
        
        # note: initiate_contact_object is for winks, kisses, keys -- have_sent_messages_object is
        # for messages -- however, the "favorites" is duplicated on both.
        initiate_contact_object.favorite_stored = have_sent_messages_object.other_is_favorite
        initiate_contact_object.favorite_stored_date = datetime.datetime.now()
        utils.put_initiate_contact_object(initiate_contact_object, userobject_key, other_userobject_key)
        
    
        # the HttpResponse is ignored .. so, shouldn't matter what the return value is.
        return HttpResponse("OK")
    except:
        error_reporting.log_exception(logging.critical)
        return HttpResponse("Error")
        


@ajax_call_requires_login
def load_mail_history(request, bookmark_key_str, other_uid):
    # loads mail history between two users, starting at messages that pointed to by the bookmark and older.
    
    try:
        owner_uid = request.session['userobject_str']
        userobject =  utils_top_level.get_userobject_from_request(request)
        other_userobject = utils_top_level.get_object_from_string(other_uid)
            
        # get messages that are older or equal to the bookmark -- get an additional message that will be
        # used as the next bookmark (hence the SINGLE_CONVERSATION_PAGESIZE +1)
        query_for_message = mailbox.setup_and_run_conversation_mailbox_query(bookmark_key_str, userobject, other_userobject, 
                                                                     mailbox.SINGLE_CONVERSATION_PAGESIZE+1)

            
        is_first_message = False
        generated_html = mailbox.generate_messages_html(query_for_message, is_first_message, userobject, other_uid, request.LANGUAGE_CODE)
        
    except:
        error_reporting.log_exception(logging.critical)
        generated_html = "Error"       
        
    return HttpResponse(generated_html)


def report_javascript_status(request, logging_function = logging.error):
    # Function that will write javascript errors to the log so that we can see when things are going wrong
    # on the client/javascript. 
    
    status_text = request.REQUEST.get('status_text', None)
    
    if status_text: 
        logging_function("Javascript status_text: %s\n" % status_text)
    else:
        logging_function("report_javascript_error called without an status_text included in the post/get\n")
        
    return HttpResponse("OK")



def set_show_online_status_trial(request):
    
    owner_uid = utils_top_level.get_uid_from_request(request)
    status = utils.set_show_online_status_timeout(owner_uid)
    if status == "OK":
        return HttpResponse(status)
    else:
        # it has returned the amount of time remaining before it will be un-blocked
        return HttpResponse(status)