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

import uuid
import logging, StringIO, pickle, datetime, os
import json

from google.appengine.api import users

from rs import utils, localizations, login_utils, forms, admin, constants, views, common_data_structs, user_profile_main_data
from rs import store_data, channel_support, lang_settings
from rs import models, error_reporting, messages, utils_top_level
from django import template, shortcuts, http
from django.utils import simplejson
from django.core.validators import email_re
from django.utils.translation import ugettext
from django.core.urlresolvers import reverse
from localeurl import utils as localeurl_utils

try:
    from rs.proprietary import search_engine_overrides
except:
    pass

#############################################
# to prevent possible problems with multiple sessions being active at once, make sure that the 
# user is logged out before letting them log in. Also, this should make it more difficult for
# jealous spouse to accidently discover that their partner has been logged in, since previous session
# will be automatically logged out if the user goes to the home page.

def check_if_login_country_allowed(request):

    login_allowed = True
    message_for_client = ''
    country_encoded = None
    region_encoded = None
    
    http_country_code = request.META.get('HTTP_X_APPENGINE_COUNTRY', None)
    if http_country_code:
        # check if country is valid and is allowed to register profiles on our website
        if http_country_code in localizations.forbidden_countries:
    
            # user will not be allowed to register or login from un-supported countries.
            forbidden_country_name = localizations.forbidden_countries[http_country_code] 
            message_for_client = u"We do not currently allow users from %s" % forbidden_country_name
            logging.warning(message_for_client)
            login_allowed = False
        else:
            tmp_country_encoded = "%s,," % http_country_code
            if tmp_country_encoded in localizations.location_dict[0]:
                # make sure that it is a country that we support.
                country_encoded = tmp_country_encoded
            else:
                logging.info("Logging in user in unknown country: %s" % http_country_code)  
                
        http_region_code = request.META.get('HTTP_X_APPENGINE_REGION', None)
        if country_encoded and http_region_code:
            http_region_code = http_region_code.upper()
            
            # check if the region code matches a region key 
            tmp_region_encoded = "%s,%s," % (http_country_code, http_region_code)
            if tmp_region_encoded in localizations.location_dict[0]:
                region_encoded = tmp_region_encoded
            else:
                logging.warning("Region code %s not found in location_dict" % http_region_code)
        
    return (login_allowed, message_for_client)




def landing_page(request):
    # Redirects to search results, and adds a get parameter to indicate that  the registration/enter 
    # dialog should be shown to the user. 
    
    try:
        redirect_to_search_results = reverse('search_gen')   + "?query_order=unique_last_login"   
        for key in request.GET:
            value = request.GET[key]
            redirect_to_search_results += "&%s=%s" % (key, value)
            
        return http.HttpResponseRedirect(redirect_to_search_results)  
        
    
    except: 
        return utils.return_and_report_internal_error(request)        
        

def get_registration_html(request):
    
    try:
        http_country_code = request.META.get('HTTP_X_APPENGINE_COUNTRY', None)
        signup_template = template.loader.get_template('login_helpers/registration.html')
        html_for_signup = forms.MyHTMLLoginGenerator.as_table_rows(localizations.input_field_lang_idx[request.LANGUAGE_CODE], 'signup_fields')
        context = template.Context (dict({
            'html_for_signup': html_for_signup, 
            'minimum_registration_age' : constants.minimum_registration_age,
            'is_popup_login_registration' : True,
            'http_country_code' : http_country_code,
            }, **constants.template_common_fields))
        signup_html = signup_template.render(context)
        
        login_template = template.loader.get_template('login_helpers/login.html')
        context =  template.Context (dict({
            'is_popup_login_registration' : True
            }, **constants.template_common_fields))
        login_html = login_template.render(context)
                

        response_dict = { 'signup_html' : signup_html,
                        'login_html' : login_html}
    
        json_response = simplejson.dumps(response_dict)
        return http.HttpResponse(json_response, mimetype='text/javascript')      
    except:
        return utils.return_and_report_internal_error(request)
                

def store_authorization_info_and_send_email_wrapper(request, login_dict, encrypted_password, password_salt, currently_displayed_url):

    # Receives the user_login values and forces user to verify a registration code sent to their email address before
    # registration data is stored in the permanent data structures. 

    try:
        generated_html = ''
        
        (username, email_address) = login_utils.extract_data_from_login_dict(login_dict)        
        assert(username); assert(email_address)
                   
           
        # if someone calls the associated URL without using our website (i.e hacking us), it is possible that they could pass in
        # bad values, and register invalid emails and usernames -- catch this.
        if (not email_re.match(email_address) or constants.rematch_non_alpha.search(username) != None or len(username) < 3):
            error_message="Invalid data passed in: username: %s email_address: %s" % (username, email_address)
            error_reporting.log_exception(logging.error, error_message=error_message)
            raise Exception(error_message)
            
                    
        # pickle the GET string for re-insertion into the request object when the user clicks on the email link to
        # validate their account. 
        # We create a StringIO object because the pickle module expectes files to pickle the objects into. This is like a 
        # fake file.  
        pickled_login_get_dict_fake_file = StringIO.StringIO()
        
        
        dump_login_dict = login_dict.copy()
        # remove the password from the login_dict before pickling it so that we don't have un-encrypted passwords stored in the database.
        dump_login_dict['password'] = "Unencrypted password is not stored - you should be using the encrypted_password field"
        pickle.dump(dump_login_dict, pickled_login_get_dict_fake_file)        
        pickled_login_get_dict = pickled_login_get_dict_fake_file.getvalue()
        authorization_info_status = login_utils.store_authorization_info_and_send_email(
            currently_displayed_url, username, email_address, encrypted_password, password_salt, 
            pickled_login_get_dict, request.LANGUAGE_CODE)   
        
        pickled_login_get_dict_fake_file.close()
             
        if authorization_info_status != "OK":    
            error_reporting.log_exception(logging.error, error_message = authorization_info_status)  

        return authorization_info_status

    except:
        error_reporting.log_exception(logging.critical)   
        return "Critical error in verify_user_email"
    


def process_login(request):
    
    # Note that this function can be called from a POST or a GET (URL-passing in login parameters), 
    # or on initial loading without POST information.
    # If it is called without POST information, then the default login page is simply displayed. Otherwise
    # the POST data is analyzed to see if the login/signup is successful.
    # GET is used for sending an incorrect login back to the original login page along with parameters
    # that have previously been entered (such as a username)
    # 
    try:
        # If this is an administrator (as defined by the admins in the Google App Engine console), then the user
        # will have extra privelidges such as not having to enter a password to enter into an account. 
        is_admin_login = users.is_current_user_admin()
        
        response_dict = {}
        error_dict = {}
        lang_idx = localizations.input_field_lang_idx[request.LANGUAGE_CODE]
        
        if request.method != 'POST':
            error_message = "process_login was not called with POST data"
            error_reporting.log_exception(logging.error, error_message = error_message)  
            return http.HttpResponseBadRequest(error_message)
        
               
        (login_allowed, message_for_client) = check_if_login_country_allowed(request)
        
        if not login_allowed:
            logging.critical("Must handle countries that are not allowed")
            assert(0)
        
        
        login_dict = {'username_email' : request.POST.get('username_email', '----'),
                      'password' : request.POST.get('password', '----'),
                      }
        

                    
        
        for key in login_dict.keys():
            if not login_dict[key]: login_dict[key] = "----" 
            
        #clear_old_session(request)
        userobject = None
        username = ''
        
        # remove spaces in the username/email field
        login_dict['username_email'] = login_dict['username_email'].replace(' ', '')
        
        # Ensure that the most recently
        # accessed object will be returned in case of a conflict (which might occur if a person uses the same email
        # address for multiple accounts)       
        q_order_by_last_login = models.UserModel.query().order(-models.UserModel.last_login_string)
        
        email_or_username_login = None
        if email_re.match(login_dict['username_email']):                       
            email_or_username_login = "email"
            q_username_email = q_order_by_last_login.filter(models.UserModel.email_address == login_dict['username_email'].lower())
        else:
            email_or_username_login = "username"
            username = login_dict['username_email'].upper()
            q_username_email = q_order_by_last_login.filter(models.UserModel.username == username)
            if (len(username) < 3 or username == "----"): 
                error_dict['username_email'] = u"%s" % constants.ErrorMessages.username_too_short            
            elif (constants.rematch_non_alpha.search(username) != None ):
                error_dict['username_email'] = u"%s" % constants.ErrorMessages.username_alphabetic
                   
                              
        if is_admin_login and login_dict['password'] == "----":
            # If administrator has entered in a password, then we assume that they are testing the "normal" login
            # flow. Only if the password is not entered (as indicated by "----") will we login as admin.

            # There should only be a single "active" (not eliminated) user for each username/email.
            userobject = q_username_email.get()            
        else:
            q_not_eliminated = q_username_email.filter(models.UserModel.user_is_marked_for_elimination == False)  
            userobject = q_not_eliminated.get()
            
            if userobject:
                # Verify that the password is not empty.
                if login_dict['password'] == "----":
                    error_dict['password'] = u"%s" % constants.ErrorMessages.password_required
            else:
                # userobject no found, just for informational purposes, we check to see if the user profile has been
                # eliminated, and if so we provide some feedback to the user about the reason for elimination of their 
                # profile.
                q_is_eliminated = q_username_email.filter(models.UserModel.user_is_marked_for_elimination == True)
                eliminated_userobject = q_is_eliminated.get()  
                show_reason_for_elimination = False
                
                if eliminated_userobject and email_or_username_login == 'username':
                    # if the user has entered a username for an eliminated account, show them the reason for elimination, even
                    # if the password was incorrect - this does not violate anyones privacy
                    show_reason_for_elimination = True
                
                elif eliminated_userobject and (eliminated_userobject.password == utils.old_passhash(login_dict['password']) or \
                     eliminated_userobject.password == utils.new_passhash(login_dict['password'], eliminated_userobject.password_salt)):
                    # The username_login is an email address, this needs more privacy protection.
                    # Let user know that the profile was eliminated (but only if they have entered in the correct password). 
                    # To protect users privacy, we don't want to confirm that an email address was registered unless the 
                    # correct password was entered. 
                    show_reason_for_elimination = True
                    
                if show_reason_for_elimination:
                    message_for_client = utils.get_removed_user_reason_html(eliminated_userobject)
                    error_dict['reason_for_removal_message'] = message_for_client                
            
        correct_username_password = False
        if userobject:
                
            if is_admin_login and login_dict['password'] == "----":
                correct_username_password = True
                
            elif userobject.password == utils.old_passhash(login_dict['password']):
                # All "normal" (non admin) logins MUST check the password!!                
                correct_username_password = True
                # Now we have to resest the users password to the new_passhash algorithm to make it more secure. 
                # This requires that we generate a salt in addition to hashing with the new algorithm.
                userobject.password_salt = uuid.uuid4().hex
                userobject.password = utils.new_passhash(login_dict['password'], userobject.password_salt)
                
            elif userobject.password == utils.new_passhash(login_dict['password'], userobject.password_salt):
                # All "normal" (non admin) logins MUST check the password!!                
                correct_username_password = True                     
                
            elif userobject.password_reset and userobject.password_reset == utils.new_passhash(login_dict['password'], userobject.password_salt):
                # Note: if the password has been reset, then the 'password_reset' value will contain
                # the new password (as opposed to directly overwriting the 'password' field). This is done  to prevent
                # random people from resetting other peoples passwords. -- Once the user has 
                # logged in using the new 'reset_password', then we copy this field over to the 'password'
                # field. If the user never logs in with this 'reset_password', then the original password
                # is not over-written -- and we instead erase the 'reset_password' value (lower down in this function)             
                correct_username_password = True
                userobject.password = userobject.password_reset
                
            else:
                correct_username_password = False

        if not correct_username_password:
            error_dict['incorrect_username_password_message'] = u"%s" % constants.ErrorMessages.incorrect_username_password            
            if not 'username_email' in error_dict:
                error_dict['username_email'] = ''
            if not 'password' in error_dict:
                error_dict['password'] = ''
           

        if not error_dict:
            assert(userobject)
            # success, user is in database and has entered correct data
            owner_uid = userobject.key.urlsafe()
            owner_nid = utils.get_nid_from_uid(owner_uid)
            
            # make sure that the userobject has all the parts that the code expects it to have.
            store_data.check_and_fix_userobject(userobject, request.LANGUAGE_CODE)

            # if administrator is logging in, do not update any of the user login times, or other data that should only be updated
            # if the real user logs in. However, if the administrator is logging in, and has entered a password, then they
            # would like to be recognized as a standard login, and therefore we should update the login times.
            if not is_admin_login or (is_admin_login and login_dict['password'] != "----"):
                
                userobject.password_reset = None # if the user has sucessfully logged in, then we know that the "reset_password" is no longer needed
                userobject.previous_last_login = userobject.last_login
                userobject.last_login =  datetime.datetime.now()   
                userobject.last_login_string = str(userobject.last_login)
                                        
                if not utils.get_client_vip_status(userobject):
                    # client has lost their VIP status - clear from both the userobject
                    userobject.client_paid_status = None
                    
                    # this user up until now has not had to solve any captchas since he was a VIP member - therefore, it is possible
                    # that his spam_tracker has accumulated a number of times being reported as spammer. We don't want to punish people
                    # after they lose their vip status, and so we set the number of captchas solved to be equal to the number of times
                    # reported as a spammer (this means that any previous spam messages will not require that a new captcha be solved). 
                    spam_tracker =  userobject.spam_tracker.get()                           
                    spam_tracker.number_of_captchass_solved_total = spam_tracker.num_times_reported_as_spammer_total
                    spam_tracker.put()
                    
                userobject.unique_last_login = login_utils.compute_unique_last_login(userobject)
                
                # remove chat boxes from previous sessions.
                channel_support.close_all_chatboxes_internal(owner_uid)
                 
                # reset the new_messages_since_last_notification data strutures since the user 
                # is logging in, and is obviously aware of new messages etc. 
                store_data.reset_new_contact_or_mail_counter_notification_settings(userobject.unread_mail_count_ref)
                store_data.reset_new_contact_or_mail_counter_notification_settings(userobject.new_contact_counter_ref) 
                
                # log information about this users login time, and IP address
                utils.update_ip_address_on_user_tracker(userobject.user_tracker)
                
                utils.store_login_ip_information(request, userobject)

                utils.put_userobject(userobject)

            # update session to point to the current userobject
            login_utils.store_session(request, userobject)

            http_country_code = request.META.get('HTTP_X_APPENGINE_COUNTRY', None)
            logging.info("Logging in User: %s IP: %s country code: %s -re-directing to edit_profile_url" % (userobject.username, os.environ['REMOTE_ADDR'], http_country_code))

            # Set language to whatever the user used the last time they were logged in. 
            search_preferences = userobject.search_preferences2.get()
            lang_code = search_preferences.lang_code
            assert(lang_settings.set_language_in_session(request, lang_code))
            
            current_path = request.POST.get('current_path', None)
            if current_path:
                locale, path = localeurl_utils.strip_path(current_path)  
                if path in constants.URLS_THAT_NEED_REDIRECT_AFTER_ENTRY:
                    # Note: we "manually" set the language in the URL on purpose, because we need to guarantee that the language
                    # stored in the profile, session and URL are consistent (so that the user can change it if it is not correct)
                    destination_url = "/%(lang_code)s/edit_profile/%(owner_nid)s/" % {
                        'lang_code': lang_code, 'owner_nid':owner_nid}  
                else:
                    destination_url = current_path
            else:
                #  This is an error condition that should not occur if the client-side javascript is behaving properly
                error_reporting.log_exception(logging.critical, error_message = "process_login did not receive a current_path value")  
                # Send them to the search results page so that they have something interesting to look at (since they may or may not 
                # now be logged in, we don't want to leave them sitting on the landing page)
                destination_url = reverse('search_gen')           
                                  
            response_dict['Login_OK_Redirect_URL'] = destination_url
        else:
            assert(error_dict)
            # there were errors - report them
            response_dict['Login_Error'] = error_dict
            


        json_response = simplejson.dumps(response_dict)
        return http.HttpResponse(json_response, mimetype='text/javascript')  
        

    except:
        error_message = "process_login unknown error"
        error_reporting.log_exception(logging.critical, error_message = error_message)          
        return http.HttpResponseBadRequest(error_message)
                
                
def process_registration(request):
    # new user is signing up 
    # We pass in the currently_displayed_url so that when the user registers, they will be directed back to
    # the exact same page they were on when they initially signed up -- this could be almost any page
    # since we now have pop-up dialogs that are shown overtop of the various pages.
    lang_idx = localizations.input_field_lang_idx[request.LANGUAGE_CODE]
    response_dict = {}
       
    try:
        if request.method != 'POST':
            error_message = "process_registration was not called with POST data"
            error_reporting.log_exception(logging.critical, error_message = error_message)  
            return http.HttpResponseBadRequest(error_message)
        
        currently_displayed_url = request.POST.get('currently_displayed_url', None)
        
        (login_allowed, message_for_client) = check_if_login_country_allowed(request)
        
        if not login_allowed:
            logging.critical("Must handle countries that are not allowed")  
            assert(0)
        
        login_dict = login_utils.get_registration_dict_from_post(request)
                
        login_dict['country'] = request.POST.get('country', '----')
        login_dict['sub_region'] = request.POST.get('sub_region', '----')
        login_dict['region'] = request.POST.get('region', '----')
        
        # re-write all user names to upper-case to prevent confusion
        # and amateur users from not being able to log in.
        login_dict['username'] = login_dict['username'].upper().replace(' ', '')
        username = login_dict['username']
                    
        # setup default email_address for developer testing
        if login_dict['email_address'] == "----" and utils.is_exempt_user():
            # for testing and debugging, we allow developers to bypass the check on the email address, and
            # we just assign their google email address to this field automatically (if it is empty)
            login_dict['email_address'] = users.User().email()
            logging.warning("\n**** Warning: Setting registration email address to %s\n" % login_dict['email_address'])
            
        if login_dict['password'] == "----" and utils.is_exempt_user():
            # setup default password for developer testing
            login_dict['password'] = constants.DEFAULT_PROFILE_PASSWORD
            logging.warning("\n**** Warning: Setting registration password to %s\n" % login_dict['password'])

                    
        # if email address is given, make sure that it is valid
        # remove blank spaces from the email address -- to make it more likely to be acceptable
        login_dict['email_address'] = login_dict['email_address'].replace(' ', '')
        login_dict['email_address'] = login_dict['email_address'].lower()
        email_address =  login_dict['email_address']
            

        (error_dict) = login_utils.error_check_signup_parameters(login_dict, lang_idx)
        
        # Now check if username is already taken
        query = models.UserModel.query().filter(models.UserModel.username == username)
        query_result = query.fetch(limit=1)
        if len(query_result) > 0:
            error_dict['username'] = u"%s" % constants.ErrorMessages.username_taken
        else:
            # now check if the username is in the process of being registered (in EmailAuthorization model)
            query = models.EmailAutorizationModel.query().filter(models.EmailAutorizationModel.username == username)
            query_result = query.fetch(limit=1)
            if len(query_result) > 0:
                error_dict['username'] = u"%s" % constants.ErrorMessages.username_taken 
                
        # if there are no errors, then store the signup information.
        if not error_dict:
    
            password_salt = uuid.uuid4().hex              
            # encrypt the password 
            encrypted_password = utils.new_passhash(login_dict['password'], password_salt)
            authorization_info_status =  store_authorization_info_and_send_email_wrapper(request, login_dict, encrypted_password, password_salt, currently_displayed_url)
            if authorization_info_status == 'OK':
                response_dict['Registration_OK'] = {'username': username,
                                                    'verification_email' :  email_address}
                if utils.is_exempt_user():
                    response_dict['Registration_OK']['allow_empty_code'] = "true"
            else:
                response_dict['Registration_Error'] = {'message': authorization_info_status}
        else:
            response_dict['Registration_Error'] = error_dict
            
        json_response = simplejson.dumps(response_dict)
        return http.HttpResponse(json_response, mimetype='text/javascript')  
        

    except:
        error_message = "Unknown error"
        error_reporting.log_exception(logging.critical, error_message = error_message)          
        return http.HttpResponseBadRequest(error_message)
    
    
  
    

def store_new_user_after_verify(request, lang_idx, login_dict, encrypted_password, password_salt):
    # Store the user information passed in the request into a userobject.
    # Does some validation to prevent attacks 
    
    try:
        
        # The following error-checking should never fail unless the user has modified their login parameters 
        # after signing up - this is here just for peace of mind.
        error_dict = login_utils.error_check_signup_parameters(login_dict, lang_idx)
 
        if error_dict:
            # if there is an error, make them re-do login process (this should never happen though)
            error_message = repr(error_dict)
            error_reporting.log_exception(logging.error, error_message=error_message)
            return ("Error", None)
        
        login_dict['username'] = login_dict['username'].upper()
        username = login_dict['username']
        password = encrypted_password
        # if the username is already registered, then do not add another user into the database. 
        # Re-direct the user to to the login screen and indicate that they must enter in their 
        # username and password to login.
        q = models.UserModel.query().order(-models.UserModel.last_login_string)
        q = q.filter(models.UserModel.username == username)
        q = q.filter(models.UserModel.user_is_marked_for_elimination == False)
        userobject = q.get()
        if userobject:
            # user is already authorized -- send back to login
            return ("username_already_registered", None)       
        
        q = models.UserModel.query().order(-models.UserModel.last_login_string)
        q = q.filter(models.UserModel.username == username)
        q = q.filter(models.UserModel.user_is_marked_for_elimination == True)
        userobject = q.get()
        if userobject:
            # user has been deleted - return the userobject so that we can later provide 
            # additional information about why this userobject was deleted
            return ("username_deleted", userobject)  
        
        # make sure that the user name is not already registered. (this should not happen
        # under normal circumstances, but could possibly happen if someone is hacking our system or if two users have gone through
        # the registration process and attempted to register the same username at the same moment)
        query = models.UserModel.gql("WHERE username = :username", username = username)
        if query.get():
            error_reporting.log_exception(logging.warning, error_message = 'Registered username encountered in storing user - sending back to main login')       
            return ("Error", None)
    
    except:
        error_reporting.log_exception(logging.critical)   
        return ("Error", None)

    # do not change the order of the following calls. Userobject is written twice because this
    # is necessary to get a database key value. Also, since this is only on signup, efficiency is
    # not an issue.
    
    try:
        
        # Cleanup the login_dict before passing it in to the UserModel
        if 'login_type' in login_dict:
            del login_dict['login_type']
        
        # passing in the login_dict to the following declaration will copy the values into the user object.
        userobject = models.UserModel(**login_dict)
        userobject.password = encrypted_password
        userobject.password_salt = password_salt
        
        userobject.username_combinations_list = utils.get_username_combinations_list(username)
        
        utils.put_userobject(userobject)
               
        userobject.search_preferences2 = login_utils.create_search_preferences2_object(userobject, request.LANGUAGE_CODE) 
        userobject = login_utils.setup_new_user_defaults_and_structures(userobject, login_dict['username'], request.LANGUAGE_CODE)
        userobject.viewed_profile_counter_ref = login_utils.create_viewed_profile_counter_object(userobject.key)
        userobject.accept_terms_and_rules_key = login_utils.create_terms_and_rules_object()
        
        # store indication of email address validity (syntactically valid )
        if login_dict['email_address'] == '----':
            userobject.email_address_is_valid = False
        else:
            userobject.email_address_is_valid = True
            
            # We can update the user_tracker object with the
            # email address, since we have now confirmed that it is truly verified.
            utils.update_email_address_on_user_tracker(userobject, login_dict['email_address'])
            try:
                # make sure that the email address is a valid email address.
                assert(email_re.match(login_dict['email_address']))
            except:
                error_reporting.log_exception(logging.warning, error_message = 'Email address %s is invalid' % login_dict['email_address'])       
        
                
        userobject.registration_ip_address = os.environ['REMOTE_ADDR']   
        userobject.registration_city = userobject.last_login_city = request.META.get('HTTP_X_APPENGINE_CITY', None)    
        userobject.registration_country_code = userobject.last_login_city = request.META.get('HTTP_X_APPENGINE_COUNTRY', None)    
        utils.store_login_ip_information(request, userobject)
        
        utils.put_userobject(userobject)
        logging.info("New userobject stored: Username: %s Email: %s" %  (userobject.username, userobject.email_address))

        login_utils.store_session(request, userobject)

        lang_set_in_session = lang_settings.set_language_in_session(request, request.LANGUAGE_CODE)
        assert(lang_set_in_session)    
                   
        # send the user a welcome email and key and wink from Alex
        messages.welcome_new_user(request)
    
    except:
        # if there is any failure in the signup process, clean up all the data stored, and send the user back to the login page with the data that they
        # previously entered.
        try:
            error_message = "Error storing user -- cleaning up and sending back to login screen"
            error_reporting.log_exception(logging.critical, request = request, error_message = error_message )   

            utils.delete_sub_object(userobject, 'search_preferences2')
            utils.delete_sub_object(userobject, 'spam_tracker')
            utils.delete_sub_object(userobject, 'unread_mail_count_ref')
            utils.delete_sub_object(userobject, 'new_contact_counter_ref')
            utils.delete_sub_object(userobject, 'user_tracker')
            utils.delete_sub_object(userobject, 'viewed_profile_counter_ref')
            utils.delete_sub_object(userobject, 'user_photos_tracker_key')

            try: 
                error_message = "Deleting userobject: %s : %s" % (userobject.username, repr(userobject))                
                userobject.key.delete() # (Finally - remove the userobject)
                error_reporting.log_exception(logging.critical,  error_message = error_message)  

            except: 
                error_message = "Unable to delete userobject: %s : %s" % (userobject.username, repr(userobject))
                error_reporting.log_exception(logging.critical, request = request, error_message = error_message)
        except:
            error_reporting.log_exception(logging.critical, error_message = "Unable to clean up after failed sign-up attempt" ) 
            
        return ("Error", None)

    # log information about this users login time, and IP address
    utils.update_ip_address_on_user_tracker(userobject.user_tracker)

    logging.info("Registered/Logging in User: %s IP: %s country code: %s " % (
        userobject.username, os.environ['REMOTE_ADDR'], request.META.get('HTTP_X_APPENGINE_COUNTRY', None)))
    return ("OK", userobject)


def check_verification_and_authorize_user(request):
    # Note, this function is called directly as a URL from a user clicking on an email link OR
    # it is called from the user entering the verification_code in a popup dialog. 
    # We direct them to a web page after verification.
    #
    # We return a json object containing the URL that the client-side javascript will then redirect to.
    
    
    
    try:
        if request.method != 'POST':
            error_message = "check_verification_and_authorize_user was not called with POST data"
            raise Exception(error_message)
        
        username = request.POST.get("username", None)
        secret_verification_code = request.POST.get("secret_verification_code", None)
        current_path = request.POST.get("current_path", None)
        
        logging.info("username: %s entered code: %s" % (username, secret_verification_code))
        
        # remove spaces from verificaiton code - if use copies and pastes it incorrectly
        # it might have a space before or after.
        secret_verification_code = secret_verification_code.replace(' ' , '')
        
        if current_path:
            locale, path = localeurl_utils.strip_path(current_path)  
            if path in constants.URLS_THAT_NEED_REDIRECT_AFTER_ENTRY:
                destination_url = "/"
            else:
                destination_url = current_path
        else:
            destination_url = "/"
            
        authorization_info = login_utils.query_authorization_info_for_username(username)
        if authorization_info:
            if authorization_info.secret_verification_code != secret_verification_code:
                authorization_status = "Incorrect code" 
                if utils.is_exempt_user() and not secret_verification_code:
                    # If this is an exempt (admin) user and he has left the input empty, then for testing
                    # purposes, we continue with the registration process. Note: that in order to submit an "empty"
                    # string from the client side, the user must actually press the Enter key inside the text box -
                    # otherwise if the user presses the submit button, then the text box will contain the text 
                    # "Verification code" which will not work.
                    authorization_status = "Authorization OK"
            else:
                # secret codes match
                authorization_status = "Authorization OK" # User has sucessfully authorized their account
        else:
            authorization_status = "No authorization_info"
            
        if authorization_status == "Authorization OK":
            
            
            login_get_dict = pickle.load(StringIO.StringIO(authorization_info.pickled_login_get_dict))
            encrypted_password = authorization_info.encrypted_password
            password_salt = authorization_info.password_salt
            lang_idx = localizations.input_field_lang_idx[request.LANGUAGE_CODE]
            (store_user_status, userobject) = store_new_user_after_verify(request, lang_idx, login_get_dict, encrypted_password, password_salt)
            if store_user_status == "OK":
                if destination_url == "/":
                    # if destination_url is not defined (ie. = "/"), then we will direct the user to edit their profile
                    # otherwise, we just send the user to whatever destination_url we have already assigned.
                    destination_url = reverse("edit_profile_url", kwargs={'display_nid' : userobject.key.id()})  
            elif store_user_status == "Error":
                destination_url = "/"
            elif store_user_status == "username_already_registered":
                destination_url = '/?already_registered_username=%s&show_registration_login_popup=true' % username
            elif store_user_status == "username_deleted":
                response_dict = {"username_deleted" : utils.get_removed_user_reason_html(userobject)}
                json_response = json.dumps(response_dict)
                return http.HttpResponse(json_response, mimetype='text/javascript')                                     
            else:
                destination_url = "/"                
                error_reporting.log_exception(logging.critical, error_message = "unknown status %s returned from store_new_user_after_verify" % store_user_status)
                

        else:
            # The verification code does not match the username that is being verified.
            
            # could happen if the user clicks on the link to authorize their account at some point after
            # we have erased the authorization info, or if the code really doesn't match

            # We want to let the user know that the code they have entered is incorrect, without redirecting to 
            # another page.
            if authorization_status == "Incorrect code" :
                warning_message= ugettext("Incorrect code")
                                 
            elif authorization_status == "No authorization_info":
                warning_message =  ugettext("Verification code is invalid or expired")
                                 
            else :
                error_reporting.log_exception(logging.critical)  
                warning_message = ugettext("Internal error - this error has been logged, and will be investigated immediately")
            
            response_dict = {"warning_html" : u'<strong><span class="cl-warning-text">%(warning_message)s</span></strong>' % {
                'warning_message' : warning_message}
                             }
            json_response = json.dumps(response_dict)
            return http.HttpResponse(json_response, mimetype='text/javascript')    
        
    except: 
        destination_url = "/"
        error_reporting.log_exception(logging.critical)      
        
    logging.info('Username:"%s". Will be redirected by javascript client to to %s' % (username, destination_url))
    response_dict = {"User_Stored_Redirect_URL" : destination_url}
    json_response = simplejson.dumps(response_dict)
    return http.HttpResponse(json_response, mimetype='text/javascript')          
