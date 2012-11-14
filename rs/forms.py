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


# This code generates the drop down menus and text boxes that are used for input forms throughout the code.

from django.http import HttpResponse

import logging, re, urllib

import settings

from rs.models import *
from user_profile_details import *
from django.utils.safestring import mark_safe
from django.utils.html import conditional_escape
from constants import MAX_NUM_PHOTOS, PHOTOS_PER_ROW
from constants import field_formats , MAIL_TEXTAREA_ROWS
from localizations import input_field_lang_idx
import queries
import captcha
import constants, utils_top_level
import utils, error_reporting, text_fields

try:
    from proprietary import search_engine_overrides
except:
    pass

# keep this at the bottom to ensure that it is not overwritten by a lambda imported from 
# another module
from django.utils.translation import ugettext


# note/TODO: This entire module is pretty ugly and could be greatly simplified (both for code efficiency and 
# for understandibility). -- it was one of the first pieces of python/web code I wrote ..
# Instead of trying to combine a bunch of functionality into generic multi-use functions, split the 
# functions into more specific units that do one thing, and only one thing.

#############################################

class FormUtils():
    # container for the classes that help to generate the forms for input.
    fields_for_title_generation   = []
    
    # define which fields can be used in generating titles for profiles and search results. 
    if settings.BUILD_NAME != "Language" and settings.BUILD_NAME != "Friend":
        fields_for_title_generation = UserSpec.principal_user_data + ['region', 'sub_region']
    elif settings.BUILD_NAME == "Language":
        fields_for_title_generation = UserSpec.principal_user_data + ['region', 'sub_region', 'languages', 'languages_to_learn']    
    elif settings.BUILD_NAME == "Friend":
        fields_for_title_generation = UserSpec.principal_user_data + ['region', 'sub_region',]
    else:
        assert(0)

   
    
    @classmethod
    def contact_table(cls, display_uid):
        
        generated_html = ''
        
        if settings.BUILD_NAME != "Language" and settings.BUILD_NAME != "Friend":
            list_of_contact_icons = [ 'favorite', 'wink', 'kiss',  'key', 'chat_friend','blocked']
        else:
            # Notes: 1) we remove "kisses" completely. 2) we overload "wink" to mean greeting (but the code refers to it as a wink)
            list_of_contact_icons = [ 'favorite', 'wink', 'key', 'chat_friend', 'blocked']


        generated_html += """<script type="text/javascript" language="javascript">
        $(document).ready(function(){
            handle_click_on_contact_icon("favorite", "%(display_uid)s");
            handle_click_on_contact_icon("wink", "%(display_uid)s");
            handle_click_on_contact_icon("kiss", "%(display_uid)s");
            handle_click_on_contact_icon("key", "%(display_uid)s");
            handle_click_on_contact_icon("chat_friend", "%(display_uid)s");
            handle_click_on_contact_icon("blocked", "%(display_uid)s");
            getJSON_initiate_contact_settings("%(display_uid)s", '');
        });
        </script>""" % {'display_uid' : display_uid}
        
        generated_html += u"""
        <table id="id-contact-table">
        <tr>"""
        
        # add div necessary for the dialog box which will tell the user if there is an error related to their 
        # contact_icon click
        warning_text = ugettext("Warning")
        generated_html += '<div id="id-contact_icon" title = "%s" style="display: none;"></div>' % warning_text
        for icon in list_of_contact_icons:
            
            generated_html += u"""<td class="cl-contact-td">
            <a id="id-submit-%(section_name)s" href="#id-submit-%(section_name)s">
            <img src="/%(static_dir)s/img/%(build_name)s/%(image_name)s" align=middle alt="">
            </a>
            </td>""" % {'section_name': icon, 'image_name': constants.ContactIconText.icon_images[icon],
                        'build_name' : settings.BUILD_NAME, "static_dir" : settings.LIVE_STATIC_DIR}
        
        generated_html += u"<tr>"
        for icon in list_of_contact_icons:
            generated_html += u"""
            <td id="id-%(section_name)s-status" class="cl-contact-td">
            <span id="id-%(section_name)s_stored"></span>
            <span id="id-%(section_name)s_stored_date"></span>
            </td>""" % {'section_name': icon}
        generated_html += """
        </tr></table> """
                
        return generated_html
    
    @classmethod
    def generate_input_text_field(cls, intype, section_name, name, max_field_length, class_def): 
        # generates a text input field
        # intype - "text" or "password"
        # section_name - name of the section in the html form that this box appears in (useful for making ids unique)
        # name - name of the input box
            
        generated_html = '<input type="%s" class="%s" id="id-%s-%s" name="%s" maxlength=%s>' % (
            intype, class_def,  section_name, name, name, 
            max_field_length)
        return generated_html

    # We cache some of the generated HTML into local "static" variables (tied to the class)
    # to save CPU resources. 
    cache_generated_text_input_table_row = {}
    @classmethod
    def generate_text_input_table_row(cls, label, name, intype, login_type, left_col_td_format, right_col_td_format, 
                                      myinputmaxlength = constants.MAX_TEXT_INPUT_LEN):
        # - cls: this is a class method, and so operations are done on the "class object", not on instances
        #        of the object. Therefore pass in cls as first parameter.
        # - label: the text which will be displayed to the user
        # - name: the variable name that will be used for identifying the input in the form
        # - intype: eg: text, password, dropdown ...
        # - login_type: either left_side_fields or signup_fields. 
        #       Used for displaying feedback in a relevant location when
        #       the user has errors in their login or singup.
        # - left_col_td_format: the class that will be applied to td cells in the left column
        # - right_col_td_format: the class that is applied to td cells in the right column
        
        try:
            cache_key = "%s_%s_%s_%s" % (label, name, intype, login_type)
            if not cls.cache_generated_text_input_table_row.has_key(cache_key):
                generated_html = ''
                generated_html += u'<tr>\n'
                generated_html += u'<td class="%s" > %s </td>\n' % (left_col_td_format, label)
                text_field_html = cls.generate_input_text_field(intype,  login_type, name, myinputmaxlength, 'cl-standard-textinput-width-px')
                generated_html += u'<td class="%s" > %s </td>\n' % (
                    right_col_td_format, text_field_html)
                generated_html += u'</td></tr>\n'
                cls.cache_generated_text_input_table_row[cache_key] = generated_html
        
            return cls.cache_generated_text_input_table_row[cache_key]
        except:
            error_reporting.log_exception(logging.critical)
            return ""   
    #############################################
    cache_generate_select_and_options = {}
    @classmethod
    def generate_select_and_options(cls, lang_idx, field_name, class_name, css_id, options_list, add_dashes_option=False):
        # this is a code snippet that just loops over the values passed in options_list
        # and places them inside select tags. Therefore, generates a self-contained 
        # dropdown. Note that the options_list has already been "pre-processed" to 
        # contain some html code, including the <option> tags, and names and values to display.
        
        # cache the generated value, since it is likely to be the same many times
        
        try:
            cache_key = u"%s_%s_%s_%s_%s" % (field_name, class_name, css_id, id(options_list), lang_idx)
            if not cls.cache_generate_select_and_options.has_key(cache_key):
    
                generated_html = u''
                generated_html += u'<select id="%s" name="%s" class="%s">\n' % (css_id, field_name, class_name)
                # This data structure must be populated, or we cannot loop over it
                assert(options_list != None)
                
                # this is an option that is specially set for login verification (but can be used for other
                # purposes if necessary). The value returned is '' unless an option is selected, which 
                # allows us to verify that the user has entered in a valid value.
                if add_dashes_option:
                    generated_html += u'<option value="">----\n'
                if options_list: # make sure it is not empty
                    for opt in options_list[lang_idx]:
                        generated_html += opt
  
                generated_html += u'</select>\n'
                cls.cache_generate_select_and_options[cache_key] = generated_html
                
            return cls.cache_generate_select_and_options[cache_key]
            
        except:
            error_reporting.log_exception(logging.critical)
            return ""        
        
    #############################################
    cache_generate_dd_input_table_row = {}
    @classmethod
    def generate_dd_input_table_row(cls, lang_idx, label, field_name, options, login_type):
        
        # cache the generated value, since it is likely to be the same many times
        #
        # The following use of id might be incorrect -- "id" can be re-issued to another object after 
        # the current object is de-allocated - look into this. TODO
        try:
            cache_key = "%s_%s_%s_%s_%s" % (label, field_name, id(options), login_type, lang_idx)
            if not cls.cache_generate_dd_input_table_row.has_key(cache_key):
                generated_html = ''
                generated_html += u'<tr>\n'
                generated_html += u'<td class="%s" > %s </td>\n' % (field_formats['right_align_login'], label)
                
                td_id = "%s_%s" % (field_name, login_type)
                generated_html += u'<td class="%s" id="%s" >' % (field_formats['left_align_login'], td_id)
                
                
                css_id = "id-%s-%s" % (login_type, field_name)
                generated_html += FormUtils.generate_select_and_options(
                    lang_idx,
                    field_name = field_name,
                    class_name = 'cl-standard-dropdown-width-px',
                    css_id = css_id,
                    options_list = options,
                    add_dashes_option = True)
                
              
                if field_name == 'country':
                    # The following two selects are place-holders that will be replaced by the javascrip once country has been selected.
                    generated_html += '\n<select name="region" id="id-signup_fields-region" class="cl-standard-dropdown-width-px"></select>\n'
                    generated_html += '<select name="sub_region" id="id-signup_fields-sub_region" class="cl-standard-dropdown-width-px"></select>\n'
                    
                    
                generated_html += u'</td></tr>'
                
                cls.cache_generate_dd_input_table_row[cache_key] = generated_html
                
            return cls.cache_generate_dd_input_table_row[cache_key] 
        except:
            error_reporting.log_exception(logging.critical)
            return ""   
    
    @classmethod
    def get_profile_photo_and_key(cls, userobject):
        
        try:
            
            photo_object_key = \
                PhotoModel.all(keys_only = True).filter('is_profile =', True).filter('parent_object =', userobject).get()
            if photo_object_key:
                photo_object_key_str = str(photo_object_key)
            else:
                photo_object_key_str = None
    
            photo_object = utils_top_level.get_object_from_string(photo_object_key_str);
            
            return (photo_object_key_str, photo_object)
        except:
            error_reporting.log_exception(logging.error)       
            return ('', None)
        
        
    ####
    @classmethod
    def generate_profile_photo_html(cls, userobject_ref, profile_no_photo_text, photo_href = "", photo_size = "medium",
                                    checkbox_html = '', icon_html = '', is_primary_user = False):

        generated_html = ''
        
        try:
            userobject = userobject_ref
            
            (photo_object_key_str, photo_object) = cls.get_profile_photo_and_key(userobject)
    
           
            
            if photo_size == "medium":
                td_class = u"cl-profile-photo-td-img"
            else:
                td_class = u"cl-photo-td-img"
                
            # checkbox (if applicable) and the background image (frame) for the photo    
            generated_html += u'<table class = "cl-profile-photo-table"><tr>%s\
            <td class= "%s">\n' % (checkbox_html, td_class)  
                
            # if the user has been marked for elimination, then don't show their photo.
            if photo_object and ((not userobject_ref.user_is_marked_for_elimination and photo_object.is_approved) or is_primary_user):
                
                if photo_href:
                    fancybox_title = u"<a class='fancybox-text-link' href='%s'>%s %s</a>" % (photo_href, ugettext("See profile of:"), userobject.username)
                else:
                    fancybox_title = userobject.username                
                
                url_for_photo = u'/rs/ajax/get_%s_photo/%s.png' % (photo_size, photo_object_key_str)
                url_for_large_photo = u'/rs/ajax/get_%s_photo/%s.png' % ('large', photo_object_key_str)
                                            

                    
                generated_html += u'<a class="%s" rel=%s href="%s" title="%s"><img class = "%s" src = "%s"><br>\n' % (
                "cl-fancybox-profile-gallery", "cl-profile-gallery", 
                url_for_large_photo, fancybox_title, 'cl-photo-img', url_for_photo) 
                    
            else:
                if userobject_ref.user_is_marked_for_elimination:
                    generated_html += u'%s\n' % ugettext("Eliminated")
                elif photo_object and not photo_object.is_approved:
                    generated_html += u'%s\n' % ugettext("Approving photo")
                else:
                    generated_html += u'%s\n' % (profile_no_photo_text)
                    
            generated_html += u'</td>%s</tr>\n</table>\n' % icon_html
    
        except:
            error_reporting.log_exception(logging.error)   
            
        return generated_html

    ####
    @classmethod
    def generate_photos_html(cls, display_userobject, primary_userobject, edit=False, table_id = "id-photo-table",
                             is_primary_user = False):
        # Generates the HTML code that contains references to the photos that are stored
        # in the database for the current user. 
        # If edit is True, then it also generates associated user inputs for selecting which
        # photos are visible to public, private, and which will be the profile picture.
        
        # Think carefully before caching the generated html, because it is generated differently for each user
        # depending on the number of photos they have.
        
        try:
            #photo_objects = display_userobject.photomodel_set.order('creation_date').fetch(MAX_NUM_PHOTOS)
            photo_objects_keys = PhotoModel.all(keys_only=True).filter('parent_object =', display_userobject).fetch(MAX_NUM_PHOTOS)
            num_photos = len(photo_objects_keys)
            
            num_photos_in_current_row = 0
            
            html_for_photo_row = [] # Contains the generated html corresponding to each row that contains actual photos.
                                    # Each row of photos is containned in a seperate index of the array.
                                    
            # Check if the primary use has the key to view private photos of the display_user. \
            # However, if the primary user is viewing, then show them their own profile. (note, if the primary
            # user is viewing their profile as others see it, then is_primary_user will be set to False)
            if primary_userobject and primary_userobject.username == constants.ADMIN_USERNAME:
                is_admin = True
            else:
                is_admin = False
            
            if is_primary_user or is_admin:
                has_key_to_private_photos = True
            else:
                primary_userobject_key = display_userobject_key = None
                
                if primary_userobject:
                    primary_userobject_key = primary_userobject.key()
                if display_userobject:
                    display_userobject_key = display_userobject.key()
                has_key_to_private_photos = utils.check_if_authorized_for_private_photos(primary_userobject_key, display_userobject_key)
            
            # the following fields allow the user to specify details of how their photos are displayed
            html_for_delete_photo_checkbox_row = []
            html_for_is_private_checkbox_row = []
            html_for_is_profile_radiobutton_row = []
    
            html_for_photo_designation_row = [] # private/public/etc.
            
            current_photo_row = 0
            has_profile_photo = False
            for current_photo_num in range(MAX_NUM_PHOTOS):
                
                if current_photo_num < num_photos:
                    photo_object_key = photo_objects_keys[current_photo_num]
                else:
                    photo_object_key = None
                
                # check if we need to introduce another row for photos.
                if (num_photos_in_current_row == PHOTOS_PER_ROW):
                    num_photos_in_current_row = 0
                    
                if num_photos_in_current_row == 0: #new row
                    html_for_photo_row.append(u'<tr>\n')
                    
                    if edit == True:
                        html_for_photo_row[current_photo_row] += u'<td class="cl-photo-options-label-td"></td>' #empty cell     
                        if photo_object_key != None: 
                            # only print out labels is is at least one photo
                            erase_photo_text = ugettext("Erase photo") 
                            photo_is_private_text = ugettext("Photo is private")
                            principal_photo_text = ugettext("Principal photo (public)")
                                     
                            html_for_delete_photo_checkbox_row.append(\
                                u'<tr><td class="cl-photo-options-label-td">%s</td>' % erase_photo_text)
                            html_for_is_private_checkbox_row.append(\
                                u'<tr><td class="cl-photo-options-label-td">%s</td>' % photo_is_private_text)
                            html_for_is_profile_radiobutton_row.append(\
                                u'<tr><td class="cl-photo-options-label-td">%s</td>' % principal_photo_text)
                        else:
                            # add empty list values so that later on we can just loop through the lists without 
                            # any special case code
                            html_for_delete_photo_checkbox_row.append('')
                            html_for_is_private_checkbox_row.append('')
                            html_for_is_profile_radiobutton_row.append('')
                            
                    elif is_primary_user:
                        # insert a new row, that will be placed into the photo table, and immediately below the photos.
                        html_for_photo_designation_row.append(u'<tr>')
                        
                if photo_object_key != None:
                    photo_object_key_str = str(photo_object_key)
                    photo_object = utils_top_level.get_object_from_string(photo_object_key_str)
                                    
                    # this URL will ensure that ajax call to get the photo are able to locate
                    # the correct database keys for finding each photo.
                    if not is_admin:
                        url_for_photo = '/rs/ajax/get_small_photo/%s.png' % (photo_object_key_str)
                        url_for_large_photo = '/rs/ajax/get_large_photo/%s.png' % (photo_object_key_str)
                    else:
                        # Show ADMIN the private photos when viewing other acccounts.
                        # Note: the following code ensure that ADMIN will be shown all private photos - however
                        # for added security, we use the "admin" URL, which requires that an admin account is logged
                        # into google (in addition to ADMIN being logged into the website).
                        if photo_object.is_private:
                            url_for_photo = '/rs/admin/ajax/get_small_photo/%s.png' % (photo_object_key_str)
                            url_for_large_photo = '/rs/admin/ajax/get_large_photo/%s.png' % (photo_object_key_str)   
                        else:
                            url_for_photo = '/rs/ajax/get_small_photo/%s.png' % (photo_object_key_str)
                            url_for_large_photo = '/rs/ajax/get_large_photo/%s.png' % (photo_object_key_str)  
                            
                    # if it is not private (is public), and it is approved, then show it with unrestricted access..
                    if not photo_object.is_private and photo_object.is_approved:
                        title = ""
                        html_for_photo_row[current_photo_row] += u'<td class="%s" >\
                            <a class="%s" rel=%s href="%s" title="%s"><img  class = "%s" src="%s" alt=""></a></td>\n'  % \
                            ('cl-photo-td-img', "cl-fancybox-profile-gallery", "cl-user-photo-gallery", 
                             url_for_large_photo, title, 'cl-photo-img', url_for_photo)
                        
                        if is_primary_user and not edit:
                            html_for_photo_designation_row[current_photo_row] += u'<td class="cl-center-align">%s</td>' %\
                                                          ugettext("Public (feminine)")
                        
                    else:
                        # otherwise, it is a private photo, change the background
                        title = text_fields.photo_is_private_text
                        if has_key_to_private_photos:
                            html_for_photo_row[current_photo_row] += u'<td class="%s" >\
                                <a class="%s" rel=%s href="%s" title="%s"><img  class = "%s" src="%s" alt=""></a></td>\n'  % \
                                ('cl-photo-td-private-img', "cl-fancybox-profile-gallery", "cl-user-photo-gallery", 
                                 url_for_large_photo, title, 'cl-photo-img', url_for_photo)
                        else:
                            html_for_photo_row[current_photo_row] += u'<td class="%s" >%s</td>\n' % \
                                ('cl-photo-td-private-img', ugettext("Private photo"))
                        
                        if is_primary_user and not edit:
                            if photo_object.is_private:
                                html_for_photo_designation_row[current_photo_row] += u'<td class="cl-center-align cl-color-text">%s</td>\n' % \
                                                              ugettext("They need your key")
                            else:
                                # we are still waiting for approval for this photo.
                                html_for_photo_designation_row[current_photo_row] += u'<td class="cl-center-align">%s</td>\n' %\
                                                              ugettext("Approving photo")
                    
                    
                    if edit:
                        object_key_string = str(photo_object.key())
                        is_private = is_profile = ''
                        if photo_object.is_private:
                            is_private = "checked"
                        if photo_object.is_profile:
                            is_profile = "checked"
                            has_profile_photo = True
                            
                        html_for_delete_photo_checkbox_row[current_photo_row] += \
                            u'<td class = "cl-photo-options-select-td"><input type = "checkbox" name="%s" \
                            id="id-%s-checkbox-%s" value="%s"> %s\n </td>' % \
                            ("delete_photo", "delete_photo", object_key_string, object_key_string, "")
                        html_for_is_private_checkbox_row[current_photo_row] += \
                            u'<td class = "cl-photo-options-select-td"><input type = "checkbox" %s name="%s" \
                            id="id-%s-checkbox-%s" value="%s"> %s\n </td>' % \
                            (is_private, "is_private", "is_private", object_key_string, object_key_string, "")
                        html_for_is_profile_radiobutton_row[current_photo_row] += \
                            u'<td class = "cl-photo-options-select-td"><input type = "radio" %s name="%s" \
                                id="id-%s-checkbox-%s" value="%s"> %s\n </td>' % \
                            (is_profile, "is_profile", "is_profile", object_key_string, object_key_string, "")
                        
                       
                else:
                    #empty photo, background image class
                    html_for_photo_row[current_photo_row] += u'<td class="%s" >%s</td>\n' % ('cl-photo-td-img', ugettext("Photo"))  
                    
                num_photos_in_current_row += 1
                
                if edit and photo_object_key != None:
                    if num_photos_in_current_row == PHOTOS_PER_ROW or current_photo_num == num_photos:
                        html_for_delete_photo_checkbox_row[current_photo_row] += u'</tr>'
                        html_for_is_private_checkbox_row[current_photo_row] += u'</tr>'
                        html_for_is_profile_radiobutton_row[current_photo_row] += u'</tr>'
                    
                if num_photos_in_current_row == PHOTOS_PER_ROW:
                    html_for_photo_row[current_photo_row] += u'</tr>\n'
                    if is_primary_user and not edit:
                        html_for_photo_designation_row[current_photo_row] += u'</tr>\n'
                    current_photo_row += 1
                    
            # Detect if loop exited early (without filling out an entire row), and do some clean-up if necessary
            if (num_photos_in_current_row != PHOTOS_PER_ROW):
                html_for_photo_row[current_photo_row] += u'</tr>\n'
                html_for_photo_designation_row[current_photo_row] += u'</tr>\n'
                current_photo_row += 1 #if loop exited early, needs to be incremented
            
                
            # now loop over all the generated html by row, and write it into the generated_html variable.
            num_photo_rows = current_photo_row
            generated_html = ''
            
            # bump the table down a little, just to make it better aligned
            if not edit:
                generated_html += "<br>"
                
            generated_html += '<table id="%s">\n' % table_id
            
            for current_photo_row in range(num_photo_rows):
                generated_html += html_for_photo_row[current_photo_row]
                if edit:
                    generated_html += html_for_is_profile_radiobutton_row[current_photo_row]
                    generated_html += html_for_is_private_checkbox_row[current_photo_row]
                    generated_html += html_for_delete_photo_checkbox_row[current_photo_row]
                    
                elif is_primary_user:
                    generated_html += html_for_photo_designation_row[current_photo_row]
    
    
             
            if edit:
                
                # if there is no principal photo, then check the "no profile photo" button.
                if has_profile_photo:
                    is_checked = ""
                else:
                    is_checked = "checked"
                #insert a row which allows the user to specify that they do not wish to have a profile picture displayed
                generated_html += u'<tr><td>&nbsp;</td></tr><tr><td class="cl-photo-options-label-td">%s</td>\
                <td class = "cl-photo-options-select-td"><input type = "radio" %s name="%s"></td></tr>' %\
                (ugettext("No primary photo"), is_checked, "is_profile")
                generated_html += u'<tr><td>&nbsp;</td></tr>'
                
            generated_html += u'</table>\n'
            
        
        except:
            generated_html = ''
            error_reporting.log_exception(logging.error)       

        
        return generated_html
    
    

    ####
    cache_generic_html_generator_for_checkboxes = {}
    @classmethod
    def generic_html_generator_for_checkboxes(cls, checkbox_options_list, fields_per_row):
        # Generates the HTML code for displaying the checkbox options available for different
        # parameters. 
        # - checkbox_options_list: contains a list of html formatted options corresponding to the 
        #       various options available in the checkboxes. 
        
        try:
            cache_key = "%s" % (id(checkbox_options_list))
            if not cls.cache_generic_html_generator_for_checkboxes.has_key(cache_key):
                
                generated_html = '<table>'
                
                field_count = fields_per_row
                
                for option in checkbox_options_list:
                    
                    if field_count == fields_per_row:
                        field_count = 0
                        generated_html += '<tr>\n'
                        
                    field_count += 1
                                            
                    if fields_per_row == 1:
                        # if we only have 1 field per row, then we don't want to compress the td widths -- eliminate the class
                        generated_html += u'<td class="%s" >\n' % ""
                    else:
                        generated_html += u'<td class="%s" >\n' % (field_formats['left_align_user_main'])
                    generated_html += option
                    generated_html += u'</td>'
                    
                    if field_count == fields_per_row:
                        generated_html += u'</tr>\n'
             
                # if the for loop exists, and a closing /tr was not printed, print it now
                if field_count != fields_per_row:
                    generated_html += u'</tr>\n'
                    
                generated_html += '</table>'
                
                cls.cache_generic_html_generator_for_checkboxes[cache_key] = generated_html
                    
            return cls.cache_generic_html_generator_for_checkboxes[cache_key]
        except:
            error_reporting.log_exception(logging.critical)       
            return ''       


        
    ####


    
    ####
    @classmethod
    def generic_html_generator_for_fields(cls, lang_idx, model_class, 
                                          field_list_name, 
                                          section_name,
                                          field_dictionary_by_field_name,
                                          field_container_object_ref, edit = False):
        # Generates the HTML code for displaying the options for fields that are passed in
        # This is written generically, so it should work for fields on different objects,
        # as long as they follow the same format as our existing objects.
        # For example could be used to output client details including
        # height, body_type, etc. They are specified in profile_details.
        # If edit_details = True, then drop-down menus are generated, otherwise
        # the current user options are displayed.
        #
        # - model_class - specifies which model was used as the prototype for the object that we 
        #      are displaying/editing. This is necessary because the model has additional information
        #      that is not stored in the object, such as allowable values, labels, etc.
        # - section_name - name of the data structure that contains all of the input
        #      fields data-structures for the current form. 
        # - field_list -  specifies the name of the array that contains "keys" that will be looped 
        #      over and have fields generated for each
        # - field_dictionary_by_field_name - a dictionary for doing lookups of the field label for the given
        #      key in the current language.
        # - field_container_object_ref - the object that contains the fields that we are looping over. Used
        #      in display (non-edit) mode for showing current values that the user has. -- might consider 
        #      replacing this with javascript call to make code more consistent. TODO - look into this.
        # - edit_details -  if true, dropdown menus will be displayed, and POST will be generated
        #      if false, then the currently stored values will be displayed.
        
        
        
        # DO NOT cache this function (for now). Most of the dropdown menu caching is already done in
        # generate_select_and_options, and the other stuff shouldn't be cached, unless done on a per
        # user basis, since it involves displaying current settings for each user.  If we change the
        # code to use javascript to retrieve the current settings, then this could be cached.
        
        try:
            generated_html = ''
            
            fields_per_row = 2
            field_count = fields_per_row
    
            generated_html += '<table>\n'
            
            field_list = getattr(model_class, field_list_name)
            age = int(getattr(field_container_object_ref, "age"))
            
            for field_name in field_list:
                
                try:
                    if field_count == fields_per_row:
                        field_count = 0
                        generated_html += u'<tr>\n'
             
                    model_signup_fields = getattr(model_class, section_name)
                    field_name_in_current_language = model_signup_fields[field_name]['label'][lang_idx]
                    
                    if settings.BUILD_NAME == "Language":
                        # do not print the langage_to_learn, since this is already incorporated into
                        # the checkbox fields for language_to_learn, and can be out-of-date, since 
                        # it was only updated on registration.
                        if field_name == "language_to_learn":
                            continue
            
                    # temporarily, we only print out the fields that are drop-down. 
                    # password edit will be added seperately later.
                    if model_signup_fields[field_name]['input_type'] == u'select':
                        
                        field_count += 1
                        
                        generated_html += u'<td class="%s" >\n' % (field_formats['left_align_user_main'])
                        generated_html += u'<strong>&nbsp;%s:&nbsp;</strong></td>\n' % (field_name_in_current_language)
                        generated_html += u'<td class="%s" >\n' % (field_formats['left_align_user_main'])
        
                        # if we are in "edit" mode, then drop-down menus will be generated
                        if edit:
                            
                            css_id = "id-edit-%s-%s" % (section_name, field_name)
                            generated_html += FormUtils.generate_select_and_options(
                                lang_idx = lang_idx, 
                                field_name = field_name, 
                                class_name = 'cl-standard-dropdown-width-px', 
                                css_id = css_id,
                                options_list = model_signup_fields[field_name]['options'])
                            
                            if field_name == 'country':
                                logging.debug("generating region and sub_region html")
                                # since the location field needs additional sub-regions, add them in here. These place-holders will be 
                                # replaced using jquery/ajax calls.                       
                                generated_html += u'\n<select name="region" id="id-edit-signup_fields-region" class="cl-standard-dropdown-width-px"></select>\n'
                                generated_html += u'<select name="sub_region" id="id-edit-signup_fields-sub_region" class="cl-standard-dropdown-width-px"></select>\n'
                            
                        else: # we are in display mode just get the current value for the field 
        
                            field_key_val = getattr(field_container_object_ref, field_name)
                            
                            # This condition should not occur -- but, just in-case 
                            # if key is empty, no data will be displayed
                            if field_key_val:
                                
                                # Hackey: print the region and sub-region into the same table cell as the country
                                if field_name == 'country':
                                    for sub_field_name in ['sub_region', 'region']:
                                        sub_field_key_val = getattr(field_container_object_ref, sub_field_name, None)
                                                    
                                        # if key is empty, no data will be displayed. Also, if it is set to our
                                        # undefined value of "----" it will not be displayed. 
                                        if sub_field_key_val and sub_field_key_val != "----":
                                            field_value_in_current_language = field_dictionary_by_field_name[sub_field_name][lang_idx][sub_field_key_val]
                                            generated_html += u'%s, ' % field_value_in_current_language
                                            
                                field_value_in_current_language = field_dictionary_by_field_name[field_name][lang_idx][field_key_val]
                                
                                if settings.SEO_OVERRIDES_ENABLED:
                                    if field_name == "sex" or field_name == "preference":
                                        field_value_in_current_language = search_engine_overrides.override_sex(localizations.lang_code_by_idx[lang_idx], age, field_value_in_current_language)
                                
                                generated_html += u'%s' % field_value_in_current_language
                                
                        generated_html += u'</td>\n'
                    
                    if field_count == fields_per_row:
                        generated_html += u'</tr>\n'
                except:
                    # catch indivual errors, so that remaining fields can be displayed
                    error_reporting.log_exception(logging.critical) 
            # for loop ends
            
            # if the for loop exists, and a closing /tr was not printed, print it now
            if field_count != fields_per_row:
                generated_html += u'</tr>\n'
                               
            generated_html += u'</table>\n'

            return generated_html
        
        except:
            error_reporting.log_exception(logging.critical)       
            return ''
    
    ####   
    
    @classmethod
    def get_base_userobject_title(cls, lang_code, userobject):
        # Gets the main part of the user profile title -- before adding in SEO optimizations
        # and anything else.
        
        
        lang_idx = localizations.input_field_lang_idx[lang_code]        
        field_vals_dict = {}

        for field_name in cls.fields_for_title_generation:
            field_vals_dict[field_name] = getattr(userobject, field_name)
                             
        vals_in_curr_language_dict = utils.get_fields_in_current_language(field_vals_dict, lang_idx, pluralize_sex = False, search_or_profile_fields = "profile")
                         
        if settings.BUILD_NAME == "Discrete" or settings.BUILD_NAME == "Gay" or settings.BUILD_NAME == "Swinger":
            base_title = u"%s" % (ugettext("%(relationship_status)s %(sex)s Seeking %(preference)s In %(location)s") % {
                'relationship_status' : vals_in_curr_language_dict['relationship_status'],
                'sex': vals_in_curr_language_dict['sex'], 
                'location': vals_in_curr_language_dict['location'], 
                'preference' : vals_in_curr_language_dict['preference']})
            
        elif settings.BUILD_NAME == "Single" or settings.BUILD_NAME == "Lesbian":
            base_title = u"%s" % (ugettext("%(sex)s Seeking %(preference)s For %(relationship_status)s In %(location)s") % {
                'relationship_status' : vals_in_curr_language_dict['relationship_status'],                
                'sex': vals_in_curr_language_dict['sex'], 
                'location': vals_in_curr_language_dict['location'], 
                'preference' : vals_in_curr_language_dict['preference']})
            
        elif settings.BUILD_NAME == "Language":
            base_title = u"%s" % ugettext("Speaker Of %(languages)s Seeking Speakers Of %(languages_to_learn)s In %(location)s") % {
            'languages': vals_in_curr_language_dict['languages'], 'location': vals_in_curr_language_dict['location'], 
            'languages_to_learn' : vals_in_curr_language_dict['languages_to_learn']} 
        elif settings.BUILD_NAME == 'Friend':
            activity_summary = utils.get_friend_bazaar_specific_interests_in_current_language(userobject, lang_idx)
            base_title = u"%s" % (ugettext("%(sex)s In %(location)s") % {
                'sex': vals_in_curr_language_dict['sex'],
                'location' : vals_in_curr_language_dict['location'],
            })
            base_title += u"%s" % activity_summary
        else:
            assert(0)        
    
        return base_title
    
    @classmethod
    def get_profile_url_description(cls, lang_code, userobject):
        # returns a description of the current profile that is suitable for display in a URL
        profile_url_description = cls.get_base_userobject_title(lang_code, userobject)
        profile_url_description = re.sub('[,;()/]', '', profile_url_description)
        profile_url_description = re.sub(r'\s+' , '-', profile_url_description)        
        profile_url_description = urllib.quote(profile_url_description.encode('utf8')) # escape unicode chars for URL    
        return profile_url_description
    
    
    @classmethod
    def generate_title_and_meta_description_for_current_profile(cls, lang_code, userobject):
        # given the userobject that is passed in, generate a text string that is appropriate for display
        # in the title of the webpage. 
        generated_title = meta_description = ''
        lang_idx = localizations.input_field_lang_idx[lang_code]
        
        try:
                
            if settings.SEO_OVERRIDES_ENABLED:
                meta_description_tag = search_engine_overrides.get_main_page_meta_description_common_part()
            else:
                meta_description_tag = ''
                
            base_title = cls.get_base_userobject_title(lang_code, userobject)
            generated_title = u"%s." % (base_title)
            meta_description = u"%s. %s" %(meta_description_tag, base_title)

        except:
            error_reporting.log_exception(logging.critical)       
            return ('', '') 
        
        return (generated_title, meta_description)
    
    @classmethod
    def generate_dropdown_form_for_current_section(cls, lang_idx, userobject, section_name, model_class, edit = False):
        # generate the html for displaying the basic user information -- age
        # gender, preferences, relationship status.
        # TODO: This function is now basically useless, and should just be integrated
        # into the generic_html_generator_for_fields 
        
        try: 
            field_list_name = section_name + '_to_display_in_order'
            field_container_object_ref = userobject
            options_dict_name = section_name + '_options_dict'
            field_dictionary_by_field_name = getattr(model_class, options_dict_name)
            
            generated_html = cls.generic_html_generator_for_fields(
                lang_idx,
                model_class,
                field_list_name, 
                section_name, 
                field_dictionary_by_field_name,
                field_container_object_ref, 
                edit)
            
            return generated_html  
        except:
            error_reporting.log_exception(logging.critical)       
            return ''
        
        
    ###########
    @classmethod
    def process_rows(cls, lang_idx, current_section, current_section_fields_spec, spec_class):

        try:
            generated_html = '';
            
            if current_section_fields_spec == 'left_side_fields' or current_section_fields_spec == 'signup_fields' or\
               current_section_fields_spec == 'change_password_fields':      
                fields_to_display_in_order = current_section_fields_spec + "_to_display_in_order"
                for field_name in getattr(spec_class, fields_to_display_in_order):
                            
                    current_section_fields = getattr(spec_class, current_section)
                    current_section_fields_names = current_section_fields[field_name]
                    mylabel = current_section_fields_names['label'][lang_idx]
                    
                    #input_type refers to 'text', 'select', 'password', etc.
                    myinputtype = current_section_fields_names['input_type']
                    
                    if current_section_fields_names.has_key('max_length'):
                        myinputmaxlength = current_section_fields_names['max_length']
                    else: myinputmaxlength = constants.MAX_TEXT_INPUT_LEN
                    
                    if myinputtype == 'text' or myinputtype == 'password':
                        generated_html += FormUtils.generate_text_input_table_row(mylabel,
                        field_name, myinputtype, current_section_fields_spec, 
                        field_formats['right_align_login'], field_formats['left_align_login'],
                        myinputmaxlength)
                    elif myinputtype == 'select':
                        choices = current_section_fields_names['options']
                        generated_html += FormUtils.generate_dd_input_table_row(lang_idx, mylabel, 
                            field_name, choices, current_section_fields_spec)
                    else:
                        raise Exception("Unknown input type")
            else:
                raise Exception("Unknown section type\n")
            
            return generated_html
        except:
            error_reporting.log_exception(logging.critical)       
            return ''    
    
    @classmethod 
    def generate_html_for_captcha(cls, section_name):
        # generates the html for displaying the captcha.
        
        generated_html = ''
        
        generated_html += u"""<div>%(instruction)s
            <img src="/%(static_dir)s/img/captcha_reload.png" alt=''>%(inside)s.<br>
            </div>""" % {'instruction' : ugettext('If you cannot read the words in the "captcha", you can select \
other words by clicking on the symbol'), 'static_dir': settings.LIVE_STATIC_DIR, 'inside' : ugettext('inside the "captcha"')}
        
        # CAPTCHA ##########################
      
        generated_html += u'<div id="id-%(section_name)s-captcha">' % {"section_name": section_name} 

        
        generated_html += captcha.displayhtml(
            use_ssl = False,
            error = None)
        generated_html += '</div>'
        # END CAPTCHA ########################
        
        return generated_html
        
   
    @classmethod 
    def html_for_submit_button(cls, section_name, value):
        submit_button_html =  u"""
        <input type=button class = "cl-submit" id="id-submit-%(section_name)s" value="%(value)s">
        """ % {"section_name": section_name, "value": value}
        return submit_button_html
    
    
    
    
    @classmethod
    def html_for_report_unacceptable_profile(cls, section_name, owner_uid, display_uid):
        
        generated_html = ''
        
        try:
            marked_as_unacceptable = utils.check_if_user_has_denounced_profile(owner_uid, display_uid)
    
            if marked_as_unacceptable:
                generated_html += """
                <div class="cl-clear"></div>
                <div id="id-%s-status" class="cl-color-text">%s</div>
                <div class="cl-clear"></div>""" % (section_name, text_fields.profile_reported)
                
            generated_html += u"""
            <script type="text/javascript" language="javascript">
                $(document).ready(function(){
                // handle the button submission
                handle_post_button_with_confirmation_of_result("%(section_name)s", "%(display_uid)s");            
             });
             </script>
             """ % {"section_name": section_name, 'display_uid': display_uid}
    
            generated_html += u"""
    
            <form id="id-%(section_name)s-form" method="POST">
            """ % {"section_name": section_name}
                        
            # the actual button for the sumbission
            if marked_as_unacceptable:
                generated_html += cls.html_for_submit_button(section_name, ugettext("Remove report"))   
            else:
                generated_html += cls.html_for_submit_button(section_name, ugettext("Report this profile"))
            
            # place holder for feedback about the status of the submission
            generated_html += """<div class="cl-clear"></div><div id="id-%s-status" class="cl-color-text"></div>""" % (section_name)
            
            generated_html += u"""
            <p><p>
            </form>
            <div class="cl-clear"></div>
            """ % {"section_name": section_name}
                               
                
        except:
            error_reporting.log_exception(logging.critical)
            
        return generated_html
        
        
    @classmethod
    def get_standard_textarea_html(cls, section_name, num_rows, add_edit_to_id = False):
        
        # Note the "strange" naming convention for the textarea -- this is done to keep it consistent with
        # previously existing javascript code. In other cases, a submit button can post multiple fields, but
        # in this case, only a single field is submitted, and therfore the same name is used 2x 
        # (this isn't currently necessary for this code to function, but is consistent with other code, and will
        # make future transitions easier -- especially if JSON data is requested from the server)        

        if add_edit_to_id:
            edit = "edit-"
        else:
            edit = ''
            
        generated_html = u"""
        <!--[if lt IE  7]>
        <textarea id="id-%(edit)s%(section_name)s-%(section_name)s" class="cl-standard-textarea-ie6" 
        name = %(section_name)s rows = %(text_area_rows)s tabindex=1></textarea>
        <![endif]-->
        <!--[if !lt IE 7]><!-->
        <textarea id="id-%(edit)s%(section_name)s-%(section_name)s" class="cl-standard-textarea" 
        name = %(section_name)s rows = %(text_area_rows)s tabindex=1></textarea>
        <!--<![endif]-->
        <div class="cl-clear"></div>
        """  % { "section_name": section_name, 'text_area_rows': num_rows, 'edit' : edit}      
        return generated_html
        
    @classmethod
    def define_html_for_mail_textarea(cls, section_name, to_uid, captcha_bypass_string, 
                                      have_sent_messages_object, spam_statistics_string = '', ):
        
        # Text and associated javascript for displaying the textarea, and for handling the click on
        # the send button. To date, section_name will be either "send_mail", or 
        # "send_mail_from_profile_checkbox_[yes|no]"
        # "send_mail" will reload entire message history, while "send_mail_from_profile" will only request a small
        # summary of the conversation history.
        # the "to_uid" is the destination (receiver) UID of the message.
        #
        # captcha_bypass_string - in the case that the captcha is to be bypassed, the captcha_bypass_string 
        #                  contans a hash of the sender_key and the receiver_key combined. This is a form
        #                  of security through obscurity. If the value does not contain the correct hash,
        #                  to authorize a bypass, then it is assumed that the captcha was loaded and must
        #                  be verified.
        #
        # num_xxxx - these values are only passed in in the case that this function is called from callbacks_from_html
        #            module. Otherwise, the default is left as None. This is because, by construction we do not use
        #            captchas for any cases other than when this module is called from callbacks_from_html.
        #
        # have_sent_messages_object: if these users have previously had contact, then do NOT count
        #            this message in their daily quota. 
        
        try:
        
            generated_html = ''
    
            if captcha_bypass_string == "no_bypass":
                show_captcha = True
            else:
                # doesn't have a captcha, but it will be verified that the captcha_bypass_string is correct .. this
                # will prevent an attacker from re-using a single bypass string to bypass the captcha on all the pages.
                show_captcha = False 
            
            
            if have_sent_messages_object:
                have_sent_messages_string = "have_sent_messages"
            else:
                have_sent_messages_string = "have_not_had_contact"
                
            generated_html += u"""
            <script type="text/javascript" language="javascript">
                $(document).ready(function(){
                
                // handle the button submission
                handle_submit_send_mail_button("%(section_name)s", "%(to_uid)s", "%(captcha_bypass_string)s", \
                "%(have_sent_messages_string)s", "%(success_status_string)s", "%(error_status_string)s");
    
                $("#id-show-ajax-spinner-captcha").hide();
            });
            </script> """ % {"section_name": section_name, "to_uid": to_uid, 
                             "captcha_bypass_string": captcha_bypass_string, 
                             "have_sent_messages_string": have_sent_messages_string,
                             "success_status_string": ugettext("Sent correctly"),
                             "error_status_string": ugettext("Not sent, try again")}
    
    
    
            # The "edit" section will be shown when the appropriate link is clicked. 
            generated_html += u"""
            <div id="id-edit-%(section_name)s-section" class="grid_7 alpha omega">
            <form id="id-%(section_name)s-form" method="POST">
            """ % { "section_name": section_name}

            generated_html += cls.get_standard_textarea_html(section_name, MAIL_TEXTAREA_ROWS)
    
            # Tell user to think before sending the message!
            if not have_sent_messages_object:
                generated_html += u"""
                    <div>
                    <strong>%(before_sending)s</strong> %(have_you_read)s<br><br>
                    </div>
                    """ %{'before_sending' : ugettext("Before sending it!"),
                          'have_you_read' : ugettext('Are you what they have specified that they are looking for? \
Have you written something intelligent and related to their profile ... something more than "Hey babe, what\'s up". \
If not, your profile may be marked as sending spam.')}
                
    
            
            generated_html += spam_statistics_string
            
            if show_captcha == True:
    
                # generate the CAPTCHA here
                generated_html += cls.generate_html_for_captcha(section_name)
    
    
            generated_html += cls.html_for_submit_button(section_name, ugettext("Send message"))
                  
            
            generated_html += u"""
            </form>
            
            <div id="id-show-ajax-spinner-captcha">
            <img src="/%(static_dir)s/img/small-ajax-loader.gif" align=middle alt=''><br><br>
            </div>       
            
            </div> <!-- id="id-edit-%(section_name)s-section" -->
            <div class="cl-clear"></div>
            """ % {"static_dir" : settings.LIVE_STATIC_DIR, "section_name": section_name}
            
            return generated_html

        except:
            error_reporting.log_exception(logging.critical)
            return ugettext("Internal error - this error has been logged, and will be investigated immediately")        
        
###############################################
    @classmethod
    def define_html_for_verify_new_captcha(cls, section_name, additional_form_data):
        # generates the html to show a captcha to new users.
        
        # additional_form_data contains the input (hidden) input fields that will be posted if captcha is 
        # answered correctly.
        
        # url_get_string contains data entered, but in a format that will be used for re-populating the login
        # form if the user decides to return to the login page.
        
        # NOTE: there is a lot of duplicate code here when compared to the define_html_for_mail_textarea function
        # consider combining (TODO)

        generated_html = ''
        
        generated_html += u"""
        <script type="text/javascript" language="javascript">
            $(document).ready(function(){
            
            // handle the button submission
            handle_verify_captcha("%(section_name)s");
            
            $("#id-show-ajax-spinner-captcha").hide();
         });
         </script>
         """ % {"section_name": section_name}


        # The fact that this is an "edit" section is necessary in order for the javascript to interpret 
        # the "Enter" keypress as a submit. Therefore do not remove this or change the name.
        
        
        generated_html += u"""
        <br>
        <div id="id-edit-%(section_name)s-section">        
        <form id="id-%(section_name)s-form" method="POST">
        """ % { "section_name": section_name}

        generated_html += additional_form_data
        generated_html += cls.generate_html_for_captcha(section_name) 
        # place holder for feedback about the status of the captcha
        generated_html += """<div class="cl-clear"></div><div id="id-%s-status" class="cl-color-text"></div>""" % (section_name)
        generated_html += cls.html_for_submit_button(section_name, u"%s" % ugettext("Verify"))
        
        generated_html += u"""
        </form>
        
        <div id="id-show-ajax-spinner-captcha">
        <img src="/%(static_dir)s/img/small-ajax-loader.gif" align=middle alt=''><br><br>
        </div>  
        
        </div> <!-- id="id-edit-%(section_name)s-section" -->
        <div class="cl-clear"></div>
        """ % {"static_dir" : settings.LIVE_STATIC_DIR, "section_name": section_name}
        
        return generated_html
   
        
    
###############################################
class MyHTMLLoginGenerator():
# This class generates the HTML code for the forms in the login screen
        
    ###########
    @classmethod
    def as_table_rows(cls, lang_idx, current_section_fields_spec):
        # Prints out the forms corresponding to models defined in UserSpec class.

        generated_html = FormUtils.process_rows(lang_idx, 'signup_fields', current_section_fields_spec, UserSpec)
        return generated_html
    
                          
class MyHTMLSearchBarGenerator():
    
    
    # Define the format of the search bar here, so that if it needs to be modified, only this 
    # data structure needs to be touched.
    
    
    def __init__(self, lang_idx):
        self.lang_idx = lang_idx
        assert(lang_idx >= 0)
    
    search_tbl_first_col = u"""<td class="cl-search-td-first">&nbsp;</td>"""
    search_tbl_last_col = u"""<td class="cl-search-td-last">&nbsp;</td>"""
    
    cache_simple_search_inputs_as_td_items = {}
    

    def search_as_table_of_td_items(self):
        # Generates the HTML code for displaying inside the search box at the top of each page. 
        
        NUM_COLUMNS_IN_SEARCH_BOX = 3
        
        try:
            # the only thing that should currently change the output of this function is the "current_language"
            # definition. Therefore, key on this to ensure that this data is only generated once for each language.
            cache_key = self.lang_idx

            num_colums = NUM_COLUMNS_IN_SEARCH_BOX * 2 + 2
            column_count = 0

            if not MyHTMLSearchBarGenerator.cache_simple_search_inputs_as_td_items.has_key(cache_key):
                search_box_txt = ugettext("Search Box")
                search_box_additional_txt = ugettext("Specify the profiles that you would like to see")
                generated_html = u"""<tr><td>&nbsp;</td></tr>
                <tr><th colspan=%s class="cl-search-box-header">%s 
                <span class = "cl-nobold">(%s)</span></th></tr>
                <tr><td>&nbsp;</td></tr>""" % (num_colums, search_box_txt, search_box_additional_txt,)
                
                generated_html += '<tr>%s' % MyHTMLSearchBarGenerator.search_tbl_first_col; column_count += 1
                
                for field_name in UserSpec.simple_search_fields:
    
                    
                    label =  UserSpec.search_fields[field_name]['label'][self.lang_idx]
                    label_num =  UserSpec.search_fields[field_name]['label_num']
                    
                    generated_html += u'<td class="cl-search-td-left-align"><strong>&nbsp;%s&nbsp;%s:&nbsp;</strong></td>\n' % (label_num, label); column_count += 1       
                    generated_html += u'<td class="cl-search-td-left-align" >\n'; column_count += 1
                    
                    css_id = "id-search-%s" % field_name
                    
                    generated_html += FormUtils.generate_select_and_options(
                        lang_idx = self.lang_idx,
                        field_name = field_name,
                        class_name = 'cl-standard-dropdown-width-px ',
                        css_id = css_id, 
                        options_list = UserSpec.search_fields[field_name]['options'],
                    )
                 
                    generated_html += u'</td>\n'
                    
                    if column_count == num_colums -1:
                        # add in the last column, which has a smaller width - and then terminate the current row and start a new row
                        generated_html += u'%s</tr><tr>%s\n' % \
                                       (MyHTMLSearchBarGenerator.search_tbl_last_col,
                                        MyHTMLSearchBarGenerator.search_tbl_first_col); 
                        column_count = 1 # start at 1 because we just added in the first column on the new row
                    
                            
                if settings.BUILD_NAME == "Friend":
                    extra_cols_before_search_button = "<td></td><td></td><td></td>"
                else:
                    extra_cols_before_search_button = "<td></td>"
                    
                # Loop ended, now add in the "search button"
                generated_html += u"""
        %s
        <td class="cl-search-td-left-align">
            <input type=submit value="%s" class="cl-search-button" id="id-submit-search"></td>
        %s
        </tr>
        """ % (extra_cols_before_search_button, ugettext("Search"), MyHTMLSearchBarGenerator.search_tbl_last_col)
                

                
                MyHTMLSearchBarGenerator.cache_simple_search_inputs_as_td_items[cache_key] = generated_html
                

            return MyHTMLSearchBarGenerator.cache_simple_search_inputs_as_td_items[cache_key]
    
        except:
            error_reporting.log_exception(logging.critical)       
            return ''
        
    cache_search_by_name_as_td_items = {}
    
    
    def search_by_name_td_items(self):
    # Define the portion of the search menu that will allow users to search for other profiles by name.
        
        cache_key = self.lang_idx
        num_columns = 0
        section_name = "search_by_name"
        
        
        if not MyHTMLSearchBarGenerator.cache_search_by_name_as_td_items.has_key(cache_key):
            generated_html = ''
            generated_html += '<tr>%s' % MyHTMLSearchBarGenerator.search_tbl_first_col; num_columns += 1
            label = ugettext("Username to search for")
            generated_html += u'<td class="cl-search-td-left-align"><strong>&nbsp;%s:&nbsp;</strong></td>\n' % (label); num_columns += 1 
            text_input = '<input type="text" class="cl-standard-textinput-width-px" id="id-%s" name="%s" maxlength=%s>' % (
                section_name, section_name, constants.MAX_USERNAME_LEN)
            generated_html += u'<td class="cl-search-td-left-align" >%s</td>\n' % text_input; num_columns += 1            
            generated_html += u'<td>&nbsp;&nbsp;&nbsp;<input type=submit value="%s" class="cl-search-button" id="id-submit-search"></td>' % (ugettext("Search"))
            generated_html += u'%s</tr>\n' % (MyHTMLSearchBarGenerator.search_tbl_last_col); num_columns += 1
                                                
            search_box_txt = ugettext("Search Box")
            search_box_additional_txt = ugettext("Specify the username that you would like to see")
            table_heading_html = u"""<tr><td>&nbsp;</td></tr>
            <tr><th colspan=%s class="cl-search-box-header">%s 
            <span class = "cl-nobold">(%s)</span></th></tr>
            <tr><td>&nbsp;</td></tr>""" % (num_columns, search_box_txt, search_box_additional_txt,)
            generated_html = table_heading_html + generated_html
            MyHTMLSearchBarGenerator.cache_search_by_name_as_td_items[cache_key] = generated_html
        
        return MyHTMLSearchBarGenerator.cache_search_by_name_as_td_items[cache_key]
    
    
def print_current_search_settings(search_vals_dict, lang_idx):
    
    try:
        NUM_COLUMS = 3
        
        curr_column = 0
        generated_html = '<table><tr>'
    
        for field_name in UserSpec.simple_search_fields:
            curr_column += 1
            
            label =  UserSpec.search_fields[field_name]['label'][lang_idx]
                         
            field_val = 'Undefined' #initialze this so the exception handler doesn't fail
            try:
                printed_value_already_computed = False
                if  search_vals_dict[field_name] == "----" and \
                    (field_name == 'country' or field_name == 'region' or field_name == 'sub_region'):
                    # This is a hack that will require fundamental changes to fix. Since locations do not
                    # contain the "----" value, we need to hard-code a lookup here.
                    printed_value = UserSpec.dont_care_tuple[lang_idx + 1] 
                    printed_value_already_computed = True
                    
                elif settings.BUILD_NAME == "Friend":
                    if field_name == "for_sale" or field_name == "to_buy":
                        printed_value = friend_bazaar_specific_code.all_activities_tuple[lang_idx + 1] 
                        printed_value_already_computed = True
                    if field_name == "for_sale_sub_menu" or field_name == "to_buy_sub_menu":
                        printed_value = UserSpec.show_all_tuple[lang_idx + 1] 
                        printed_value_already_computed = True
                        
                if not printed_value_already_computed:
                    field_dict_by_field_name = getattr(UserSpec, 'search_fields_options_dict')
                    field_val = search_vals_dict[field_name]
                    printed_value = field_dict_by_field_name[field_name][lang_idx][field_val]     
            except: 
                error_message = "field_name = %s lang_idx = %s field_val = %s" % (field_name, lang_idx, field_val)
                error_reporting.log_exception(logging.error, error_message = error_message)
                        
            generated_html += u'<td class="cl-search-td-left-align"><strong>&nbsp;%s:&nbsp;</strong></td>\n' % label        
            generated_html += u'<td class="cl-search-td-left-align" >%s</td>\n' % printed_value                             
            
            # the following code moves us down to the next row
            if curr_column == NUM_COLUMS:
                generated_html += u'</tr><tr>\n'
                curr_column = 0
                    
        generated_html += '</tr></table>'
    except:
        error_reporting.log_exception(logging.critical)
        generated_html = ''
        
    return generated_html



