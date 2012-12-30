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


""" Handles requests for resetting password """
from django.core.urlresolvers import reverse

from django.http import HttpResponse, HttpResponseBadRequest
from django.core.validators import email_re
from django.utils.translation import ugettext

from os import environ

import settings, constants

from forms import FormUtils
from constants import rematch_non_alpha
from models import UserModel
from utils import passhash, gen_passwd

import email_utils, utils, rendering

import ajax, logging, error_reporting, text_fields


def reset_password(request, email_address=''):
    
    generated_html = u'<br><br><br>'
    
    generated_html += u"""
    <form method="POST" action="%(email_reset_url)s" rel="form-address:%(email_reset_url)s">

    <table>
    <tr>
    <td><strong>%(your_id)s:</strong></td>
    <td><input type=text name="email_address" value="%(email_address)s" size=30 maxlength=100></td>
    </tr>
    
    <tr>
    <td><input type=submit value="%(send)s"></td>
    </tr>
    </table>
    
    </form>""" % {'email_reset_url': reverse(submit_email_for_reset_password), 'your_id' : ugettext("Enter your email address"),
                  'email_address' : email_address , 'send': ugettext("Send") }
    
    generated_html += ugettext("""When you click on "Send", you will receive an email from \
<em>%(sender_email)s</em> with your new password.""") % {'sender_email': constants.sender_address_html}
    
    generated_html += "<br><br>%s" % ugettext("""
** This only works if you have previously registered your email address. If you did not register an
email address, then it is not possible to recover your account.<br><br>
If you have a problem or a suggestion, send us an email to <strong>%(sender_email)s.</strong>""") % {
    'sender_email': constants.sender_address_html}
    
    
    generated_html += u'<br><br><a href="/">%(app_name)s.com</a>' % {'app_name': settings.APP_NAME}
    
    navigation_text = "%s - %s" % (settings.APP_NAME, ugettext("New password"))
    return rendering.render_main_html(request, generated_html, text_override_for_navigation_bar = navigation_text, 
                                      hide_page_from_webcrawler = True,
                                      show_search_box = False, hide_why_to_register = True)



def generate_and_save_password(email_address):
    # resets the password for the user corresponding to the given email address.

    new_password =  ''
    userobject = None
    
    email_address = email_address.replace(' ', '')
    
    assert(email_re.match(email_address)) 
        
    email_address = email_address.lower()
    query = UserModel.gql("WHERE email_address = :email_address and \
    is_real_user = True and\
    user_is_marked_for_elimination = False \
    ORDER BY last_login_string DESC", 
    email_address = email_address)
    
    userobject = query.get()
    
    if not userobject:
        logging.info("Unable to set new password for email: %s - not registered: " % email_address)
        
        query = UserModel.gql("WHERE email_address = :email_address and \
        is_real_user = True and\
        user_is_marked_for_elimination = True \
        ORDER BY last_login_string DESC", 
        email_address = email_address)
        
        eliminated_userobject = query.get()
        if eliminated_userobject:
            logging.error("email_address: %s has been eliminated, but the user is trying to recuperate their password" % email_address)

    if userobject:
        # we have found a user matching the given email address
        username = userobject.username
        new_password = gen_passwd()
        info_message = "Setting %s email: %s password to: %s\nKey %s" % (
            username, email_address, new_password, userobject.key())
        logging.info(info_message)
        userobject.password_reset = passhash(new_password)
        utils.put_userobject(userobject)
    else:
        error_reporting.log_exception(logging.warning, error_message = "Unable to set new password for email: %s - No userobject found" % email_address)
        
    return (new_password, userobject)




def submit_email_for_reset_password(request):
    # accepts an email address or a "Nick" (which we use to pull an email address out of the database),
    # and reset the users password.
    
    try:
        remoteip  = environ['REMOTE_ADDR']

        generated_html = u'<br><br><br>'
        is_valid = False
        is_email = False
        

        email_address =  request.REQUEST.get('email_address', '')

        if email_re.match(email_address):
        
            (new_password, userobject) = generate_and_save_password(email_address)
        
            
            generated_html += u"<p><p>%s" % ugettext("""
            We have sent a new password to %(email_address)s, but <strong>only if this email_address is registered as a member</strong>.
            <em>In order to protect the privacy of our members, we do not confirm if the email address is registered or not.</em>""") \
                % {'email_address' : email_address}
        


            if new_password:
                email_utils.send_password_reset_email(userobject, new_password)

        else:
            generated_html += u"<p><p>%s" % ugettext("%(email_address)s is not a valid email address" % {'email_address' : email_address})

        generated_html += u"<p><p>%s" % ugettext("If you have a problem or suggestion, please send us a message at: <strong>support@%(app_name)s.com</strong>.") % {
            'app_name': settings.APP_NAME}
        
        navigation_text = ugettext("Finished") ;    
        return rendering.render_main_html(request, generated_html, text_override_for_navigation_bar = navigation_text,
                                          show_search_box = False,
                                          hide_page_from_webcrawler = True, 
                                          hide_why_to_register = True)
    
    except:
        error_reporting.log_exception(logging.critical, request = request)
        return HttpResponse("Error")
