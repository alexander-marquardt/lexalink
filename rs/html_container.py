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


""" This module contains the python functions and classes that are used for
generating HTML code, but focused on those that are composed of mostly HTML, 
with some code-generated
aspects. Functionality is similar to the html template system, but here, some of the HTML
is generated with code """

from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext
from forms import FormUtils
from user_profile_details import UserProfileDetails
import utils



import settings, text_fields, error_reporting, logging

class UserMainHTML():
    
    
    @classmethod
    def javascript_for_buttons_and_link_click(cls, section_name, uid, input_type):
        
        if input_type == "about_user":
            disable_submit_on_enter = ", true";
        else:
            disable_submit_on_enter = '';
            
        generated_html = smart_unicode("""
            <script type="text/javascript" language="javascript">
            
            $(document).ready(function(){
                // handle the button submission, and re-direct to the correct pages
                handle_submit_button("%(section_name)s", "%(uid)s"%(disable_submit_on_enter)s);
                handle_cancel_button("%(section_name)s", "%(uid)s");
                // load the edit fields after "edit" link has been clicked.
                handle_link_for_edit("%(section_name)s", "%(input_type)s", "%(uid)s", "%(live_static_dir)s");
            });
            
            </script>""" % {
                             "section_name": section_name,
                             "uid": uid, "input_type": input_type,
                             'disable_submit_on_enter' : disable_submit_on_enter,
                             "live_static_dir": settings.LIVE_STATIC_DIR})
        return generated_html
    
    @classmethod        
    def text_for_buttons_and_form(cls, section_name):
        generated_html = smart_unicode("""
        <div id="id-edit-%(section_name)s-section">
        <form id="id-%(section_name)s-form" method="POST">
        
        <!-- following div will be replaced by js with drop-downs for editing the data -->
        <div id="id-edit-%(section_name)s-place-holder"></div>
      
        <table> <tr> 
          <td><input type=button class="cl-submit" id="id-submit-%(section_name)s" value="%(save_button)s"></td>
          <td><input type=button class="cl-cancel" id="id-cancel-%(section_name)s" value="%(cancel_button)s"></td>
        </tr> </table>
        </form>
        </div> <!-- end id-%(section_name)s-section -->
        """% {"section_name": section_name, 'save_button' : ugettext("Save"), 'cancel_button': ugettext("Cancel")})
        
        return generated_html
    
    
    @classmethod
    def get_text_about_user(cls, userobject, is_primary_user, for_edit = False):
        # the "about me" section that is stored in the database will be displayed if available, and
        # if not available, an html template with instructions for the user will be displayed.
        if userobject.about_user != '----' :
            # If the user has information stored (even if it is not considered long enough to be "valid")
            # Display stored value, except when value stored is the default "----" value.
            text_about_user = userobject.about_user
        elif for_edit:
            # The user has clicked on the "edit" button for their own "about me" section, and they have not yet
            # entered any text - therefore we show an empty box.
            text_about_user = ''
        else: # the default "----" value is still stored
            # we are only displaying the user profile (to the owner of the profile)
            # fall-through case -- tell the user what to write about.
            if is_primary_user: 
                
                if settings.BUILD_NAME != "Language" and settings.BUILD_NAME != "Friend":
                    what_to_write_about = ugettext("""Write a description about yourself and what you are looking for %(no_publicity_text)s %(customized_text)s %(no_sex_no_dating)s.""") % \
                        {'no_publicity_text': "%s\n\n" % ugettext("No publicity text"),
                         'customized_text' : ugettext("Dating specific text"),
                         'no_sex_no_dating' :''}
                else:
                    if settings.BUILD_NAME == "Language":
                        what_to_write_about = ugettext("""Write a description about yourself and what you are looking for %(no_publicity_text)s %(customized_text)s %(no_sex_no_dating)s.""") % \
                            {'no_publicity_text': "%s\n\n" % ugettext("No publicity text"),
                             'customized_text': ugettext("Language-exchange specific text"),
                             'no_sex_no_dating' :'',}
                    if settings.BUILD_NAME == "Friend":
                        what_to_write_about = ugettext("""Write a description about yourself and what you are looking for %(no_publicity_text)s %(customized_text)s %(no_sex_no_dating)s.""") % \
                            {'no_publicity_text': '',
                             'customized_text': ugettext("Friend specific text"),
                             'no_sex_no_dating' : "%s\n\n" % ugettext("Please keep in mind that %(app_name)s is *not* a dating \
site and is *not* an escort agency, and all meetings are for friendly activities only. Members that violate the spirit \
of %(app_name)s will be eliminated and banned.") % {'app_name': settings.APP_NAME}
                             }
                             
                
                text_about_user = u"%s\n\n\n\n" % what_to_write_about        
            else:
                # viewing another users profile, and they do not have a description written
                text_about_user = u"%s\n" % ugettext("Has not written a description")
        
        # replace newlines with <br> so that html will be displayed as the user intended.
        #
        # THIS IS IN-EFFICIENT - should be re-written with the <br> already stored in a parallel 
        # data structure so that we don't have to do this operation on every single profile that is 
        # viewed.
        text_about_user = text_about_user.replace('\n', '<br>') 
        
        return text_about_user
        
    @classmethod
    def define_html_for_main_body_input_section(
        cls, lang_idx, userobject, section_name, section_label, model_class, uid, input_type, is_primary_user):
        # - section_name - name of current section such as "signup_fields", "checkbox_fields", etc.
        # - input_type - either "dropdown" or "checkbox"
        
        try:
            generated_html = ''
            if is_primary_user:
                generated_html += cls.javascript_for_buttons_and_link_click(section_name, uid, input_type)
            
            generated_html += """<div class="cl-clear"></div>
            <div class="grid_2 alpha">   
            <div id="id-edit-%(section_name)s-link">
            <p>
            <strong>%(section_label)s:</strong><br>"""% {
                                 "section_name": section_name, "section_label": section_label}
            if is_primary_user and (input_type != "email_address" or userobject.client_paid_status):
                # only show the "edit" link if the account is being viewed by the owner of the account.
                # Email addresses can only be modified by VIP members.
                generated_html += """<a href = "#display-%(section_name)s-section">(%(edit_text)s)</a>""" % {
                    "edit_text": ugettext("edit"), "section_name": section_name}
                
            generated_html += """</p>
            </div> <!-- end id-edit-%(section_name)s-link -->
            </div> <!-- end grid_2 -->
            
            <div class="grid_7 omega" >
            <div id="id-display-%(section_name)s-section">
            <a name = "display-%(section_name)s-section"></a>
            """ % {"section_name": section_name}
            
            
            # TODO: The following code should be re-organized - instead of a series of if/else, we should pull these
            # into individual functions that are called directly.
            
            if input_type == "dropdown":
                # get the HTML that specifies the settings for the current section -- no dropdown menus are
                # generated by this call.
                generated_html += FormUtils.generate_dropdown_form_for_current_section(lang_idx, 
                    userobject, section_name,  model_class, edit=False)
                
            elif input_type == "checkbox" or input_type == "radio":
                generated_html += "<p>%s</p>" % utils.generic_html_generator_for_list(lang_idx, section_name, 
                getattr(userobject, section_name))
                
            elif input_type == "email_address":
                if not userobject.email_address_is_valid:
                    generated_html += u"<p>%s</p>" %  text_fields.email_encouragement_text
                else:
                    generated_html +=  getattr(userobject, section_name)
                    
            elif input_type == "current_status":
                if userobject.current_status != "----":
                    generated_html += userobject.current_status
                else:
                    # Note, lazy translated object below need to be converted into string before copying
                    generated_html += u"%s" % text_fields.share_thinking                    
                    
            elif input_type == "change_password":
                generated_html += u"<p>%s</p>" % text_fields.change_password_text
                
            elif input_type == "about_user":
                generated_html += cls.get_text_about_user(userobject, is_primary_user)
                
             
            generated_html += """
                  </div> <!-- end id="id-display-%(section_name)s-section" -->""" % {
                    "section_name": section_name}
                  
            if is_primary_user:
                
                generated_html += cls.text_for_buttons_and_form(section_name)
                
    
                
            generated_html += """</div> <!-- end grid7 omega -->"""
            return generated_html
 
        except:
            error_reporting.log_exception(logging.critical)   
            return ""   
        
        
 
        