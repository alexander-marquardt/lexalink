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

import settings
import logging
from rs import utils, localizations, login_utils, forms, admin, constants, views, common_data_structs, user_profile_main_data
from rs import models, error_reporting
from django import template, shortcuts, http
from django.utils import simplejson

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

def login(request, is_admin_login = False):
    # displays the information for allowing the user to log in. Also, processes the post information
    # from login attempts.
    # 
    # if referring_code is passed in, this means that this user has been referred by a friend. We therefore write
    # a cookie to their computer (with the refferers ID) so that we can detect if they register at some point in the future. 
    # This is then used for crediting the referrings account. 
    
    try:
                
        error_list = [] # used for containing error messages to be presented to user in a friendly format
        login_type = '' # default value required for first pass, since no request has yet taken place
        login_dict = None
        html_for_posted_values = ''
        
        # hashed_password is used for storing a hashed version of the password that was previously entered,
        # so that if the login page is called back with previously entered data, we can check if the password
        # has already been encrypted, or if it is still cleartext.
        hashed_password = ''
        
        lang_idx = localizations.input_field_lang_idx[request.LANGUAGE_CODE]
                            
                
        # Note that this function can be called from a POST or a GET (URL-passing in login parameters), 
        # or on initial loading without POST information.
        # If it is called without POST information, then the default login page is simply displayed. Otherwise
        # the POST data is analyzed to see if the login/signup is successful.
        # GET is used for sending an incorrect login back to the original login page along with parameters
        # that have previously been entered (such as a username)
        # 
        if request.method == 'POST' or request.method == 'GET':
               
            (login_allowed, message_for_client) = check_if_login_country_allowed(request)
            
            if not login_allowed:
                logging.critical("Must handle countries that are not allowed")
                assert(0)
            
            login_type = request.REQUEST.get('login_type', '') # use REQUEST, because this applies to either GET or POST
            login_dict = login_utils.get_login_dict_from_post(request, login_type)            
                
            ##### existing user is logging in ##################################
            if (login_type == 'left_side_fields'):
                
                #clear_old_session(request)
                username = ''
                
                # remove spaces in the username/email field
                login_dict['username_email'] = login_dict['username_email'].replace(' ', '')
                
                # this is a callback from the routines that store the user profile when an email authorization link is clicked on.
                user_already_registered = request.REQUEST.get('already_registered', '') 
                if (user_already_registered):
                    username = login_dict['username_email'] 
                    message_for_client = ugettext("""
                    The account for %(username)s has been correctlly registered. You can enter using your "Nick" %(username)s
                    and password""") % {'username' : username}
      
                    error_list.append(message_for_client)   
                    
                else:
                    
                    # Ensure that the most recently
                    # accessed object will be returned in case of a conflict (which might occur if a person uses the same email
                    # address for multiple accounts)       
                    q_last_login = models.UserModel.query().order(-models.UserModel.last_login_string)
                    
                    email_or_username_login = None
                    if email_re.match(login_dict['username_email']):                       
                        email_or_username_login = "email"
                        q_username_email = q_last_login.filter(models.UserModel.email_address == login_dict['username_email'].lower())
                    else:
                        email_or_username_login = "username"
                        username = login_dict['username_email'].upper()
                        q_username_email = q_last_login.filter(models.UserModel.username == username)
                        if (rematch_non_alpha.search(username) != None or len(username) < 3):
                            error_list.append(ErrorMessages.username_alphabetic)
                                            
                    
                    
                    # Verify that the password only contains acceptable characters  - 
                    # this is necessary for the password hashing algorithm which only works with ascii chars, 
                    # and make sure that it is not empty.
                    if not login_dict['password'] or rematch_non_alpha.search(login_dict['password']) != None :
                        error_list.append(ErrorMessages.password_alphabetic)
                    else:
                        if not is_admin_login:
                            # make sure that the password is not empty -- should never even get into here
                            # if it is not set (earlier error checking should catch this). 
                            assert(login_dict['password'])
                                   
                            # All "normal" (non admin) logins MUST check the password!!
                            q_with_password = q_username_email.filter(models.UserModel.password == utils.passhash(login_dict['password']))
                            
                            # make sure that profile has not been marked for elimination (if we are an administrator, we can
                            # still log into deleted accounts, so we don't add this value into the search query)
                            q_not_eliminated = q_with_password.filter(models.UserModel.user_is_marked_for_elimination == False)                          
                            

                        else:
                            # for administrator, we don't filter on the password. We also allow the administrator to log into 
                            # deleted accounts (so q_not_eliminated does not mean tht the profile has necessarily
                            # not been marked for elmination when the admin is logging in, but this allows us to use
                            # the same variable in the following code)
                            q_not_eliminated = q_username_email


    
                if not error_list:
                    # No errors so far. Continue validation.
                    
                    # Note: if the password has been reset, then the 'password_reset' value will contain
                    # the new password (as opposed to directly overwriting the 'password' field). This is done  to prevent
                    # random people from resetting other peoples passwords. -- Once the user has 
                    # logged in using the new 'reset_password', then we copy this field over to the 'password'
                    # field. If the user never logs in with this 'reset_password', then the original password
                    # is not over-written -- and we instead erase the 'reset_password' value
                    
                    password_has_been_reset = False
                    userobject = q_not_eliminated.get()
    
                    if not userobject and not is_admin_login:
                        # if the original query failed, do a query using the 'password_reset' value --
                        # this will contain a new password, if the user has requested a new password be 
                        # sent to their email account.
                        # set up the query to check the 'password_reset' value
                        q_password_reset = q_username_email.filter(models.UserModel.password_reset == utils.passhash(login_dict['password']))
                        q_not_eliminated = q_password_reset.filter(models.UserModel.user_is_marked_for_elimination == False)  

                        userobject = q_not_eliminated.get()    
                        if userobject:
                            password_has_been_reset = True
                    
                    
                    if not userobject and not is_admin_login:
                        # The user was unable to login -- 
                        # check to see if the username/email+password was registered at some point, and has been eliminated
    
                        q_is_eliminated = q_with_password.filter(models.UserModel.user_is_marked_for_elimination == True)
                        eliminated_userobject = q_is_eliminated.get()
                        
                        # if no eliminated object was found, try again, but this time only if the user has entered a username (not an email)
                        # and we will remove the password from the query. This will allow better reporting for people who may have forgotten
                        # their password. (we do not query without password for an email address login to prevent people from probing our system
                        # to see if an email address was registered)
                        if not eliminated_userobject:
                            
                            if email_or_username_login == 'username':
                                # we know that a username as opposed to an email address was entered
                                q_is_eliminated = q_username_email.filter(models.UserModel.user_is_marked_for_elimination == True)
                                eliminated_userobject = q_is_eliminated.get()                            
                        
                        if eliminated_userobject:
                            # Let user know that the profile was eliminated. 
                            message_for_client = utils.get_removed_user_reason_html(eliminated_userobject)
                            error_list.append(message_for_client)
                            
                        else: # the profile (email + password OR username) did not appear in the list of eliminated userobjects
                            
                            error_list.append(ErrorMessages.incorrect_username_password)
                                             
                        
                    if userobject:
                        # success, user is in database and has entered correct data
                        owner_uid = userobject.key.urlsafe()
                        owner_nid = utils.get_nid_from_uid(owner_uid)
                        
                        # make sure that the userobject has all the parts that the code expects it to have.
                        store_data.check_and_fix_userobject(userobject, request.LANGUAGE_CODE)
    
                        # if administrator is logging in, do not update anything. 
                        if not is_admin_login:
                            
                            if password_has_been_reset:
                                # The user has logged in using the new password - so eliminate the 
                                # original password.
                                userobject.password = userobject.password_reset
                                userobject.password_reset = None
                            else: # entering with the original password
                                
                                # if the user has entered with the original password, then remove the reset_password
                                # so that they don't have two valid passwords floating around
                                if userobject.password_reset != None:
                                    userobject.password_reset = None
                                
    
                            userobject.previous_last_login = userobject.last_login
                            userobject.last_login =  datetime.datetime.now()   
                            userobject.last_login_string = str(userobject.last_login)
                                                    
                            if not utils.get_client_paid_status(userobject):
                                # client has lost their VIP status - clear from both the userobject and and the 
                                # unique_last_login_offset structures.
                                userobject.client_paid_status = None
                                
                                # this user up until now has not had to solve any captchas since he was a VIP member - therefore, it is possible
                                # that his spam_tracker has accumulated a number of times being reported as spammer. We don't want to punish people
                                # after they lose their vip status, and so we set the number of captchas solved to be equal to the number of times
                                # reported as a spammer (this means that any previous spam messages will not require that a new captcha be solved). 
                                spam_tracker =  userobject.spam_tracker.get()                           
                                spam_tracker.number_of_captchass_solved_total = spam_tracker.num_times_reported_as_spammer_total
                                spam_tracker.put()
                                
                                
                                
                            (userobject.unique_last_login, userobject.unique_last_login_offset_ref) = \
                             get_or_create_unique_last_login(userobject, userobject.username)
                            
                            
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
                        store_session(request, userobject)
                    
    
                        logging.info("Logging in User: %s IP: %s country code: %s -re-directing to edit_profile_url" % (userobject.username, os.environ['REMOTE_ADDR'], http_country_code))
    
                        # Set language to whatever the user used the last time they were logged in. 
                        search_preferences = userobject.search_preferences2.get()
                        lang_code = search_preferences.lang_code
                        assert(lang_settings.set_language_in_session(request, lang_code))
                        # Note: we "manually" set the language in the URL on purpose, because we need to guarantee that the language
                        # stored in the profile, session and URL are consistent (so that the user can change it if it is not correct)
                        redirect_url = "/%(lang_code)s/edit_profile/%(owner_nid)s/" % {
                                'lang_code': lang_code, 'owner_nid':owner_nid}                        
                        return http_utils.redirect_to_url(request, redirect_url)                        

                        
                

            else:
                assert(login_type == '') 
                
    
                
            # the following information is used for telling the user that the emailed link that they have clicked on was unable to be
            # authorized. 
            # unable_to_verify_user GET value contains the username that we were unable to find in the authorization info data struct.
            unable_to_verify_username = request.REQUEST.get('unable_to_verify_user', '') 
            if (unable_to_verify_username):
                message_for_client = ugettext("""We are unable verify/authorize the account for %(unable_to_verify_username)s. 
                This can happen if you have already verified your acount. If the account %(unable_to_verify_username)s is 
                yours, then you can directly enter with your "Nick" and your password in the boxes above.""") % {
                'unable_to_verify_username' : unable_to_verify_username}
            
                error_list.append(message_for_client)
                
        # The following two calls generate the table rows required for displaying the login
        # note that this is a reference to the class, *not* to an instance (object) of the class. This is because
        # we do not want to re-generate a new object for each unique login (this would make caching
        # difficult).
        html_for_signup = forms.MyHTMLLoginGenerator.as_table_rows(localizations.input_field_lang_idx[request.LANGUAGE_CODE], 'signup_fields')
        
        # This code is used for generating maintenance warning messages. 
        (maintenance_soon_warning, maintenance_shutdown_warning) = admin.generate_code_for_maintenance_warning()
            
        # login_type is passed in to ensure that error-messages occur in the correct part of the
        # display.    
        if error_list:
            error_reporting.log_exception(logging.info, error_message=repr(error_list))
            
        meta_info = {}
        if settings.SEO_OVERRIDES_ENABLED:
            meta_info['page_title'] = search_engine_overrides.get_main_page_title()
        else:
            meta_info['page_title'] = ''
            
        meta_info['content_description'] =  meta_info['page_title']
        meta_info['keywords_description'] =  meta_info['page_title']
        
        my_template = template.loader.get_template('login.html')
        context = template.Context (dict({   
            'LANGUAGES' : settings.LANGUAGES,                
            'html_for_signup': html_for_signup,
            'login_type' : login_type, 
            'html_for_previously_posted_values' : html_for_posted_values,
            'is_admin_login': is_admin_login,
            'maintenance_soon_warning': maintenance_soon_warning,
            'maintenance_shutdown_warning': maintenance_shutdown_warning,
            'link_to_hide': 'login',
            'errors': error_list,
            'minimum_registration_age' : constants.minimum_registration_age,
            'request' : request,
            'javascript_version_id': settings.JAVASCRIPT_VERSION_ID,
            'welcome_html': views.welcome_html(),
            }, **constants.template_common_fields))
        body_main_html = my_template.render(context)
        

        http_response = shortcuts.render_to_response("common_wrapper.html", dict({   
            'meta_info': meta_info,
            'wrapper_data_fields' : common_data_structs.wrapper_data_fields,
            'body_main_html' : body_main_html,
        }, **constants.template_common_fields))

        return http_response
    
    except: 
        return utils.return_and_report_internal_error(request)


        
def process_registration(request):
    # new user is signing up 
    lang_idx = localizations.input_field_lang_idx[request.LANGUAGE_CODE]
    response_dict = {}
       
    if request.method == 'POST' or request.method == 'GET':
           
        (login_allowed, message_for_client) = check_if_login_country_allowed(request)
        
        if not login_allowed:
            logging.critical("Must handle countries that are not allowed")  
            assert(0)
        
        login_dict = login_utils.get_login_dict_from_post(request, "signup_fields")
                
        login_dict['country'] = request.REQUEST.get('country', '----')
        login_dict['sub_region'] = request.REQUEST.get('sub_region', '----')
        login_dict['region'] = request.REQUEST.get('region', '----')
        
        # re-write all user names to upper-case to prevent confusion
        # and amateur users from not being able to log in.
        login_dict['username'] = login_dict['username'].upper()
                    
        # if email address is given, make sure that it is valid
        if login_dict['email_address'] and login_dict['email_address'] != "----":
            # remove blank spaces from the email address -- to make it more likely to be acceptable
            login_dict['email_address'] = login_dict['email_address'].replace(' ', '')
            login_dict['email_address'] = login_dict['email_address'].lower()
        
        (error_dict) = login_utils.error_check_signup_parameters(login_dict, lang_idx)
        
        # Now check if username is already taken
        query = models.UserModel.query().filter(models.UserModel.username == login_dict['username'])
        query_result = query.fetch(limit=1)
        if len(query_result) > 0:
            error_dict['username'] = ErrorMessages.username_taken
        else:
            # now check if the username is in the process of being registered (in EmailAuthorization model)
            query = models.EmailAutorizationModel.query().filter(models.EmailAutorizationModel.username == login_dict['username'])
            query_result = query.fetch(limit=1)
            if len(query_result) > 0:
                error_dict['username'] = ErrorMessages.username_taken 
                
        # if there are no errors, then store the signup information.
        if not error_dict:
    
            # we keep a copy of the hashed password so that if we are re-directed back to the login page
            # with a hashed password (as opposed to cleartext), we can check to see if the password matches
            # the previously hashed password. If there is a match, then DO NOT hash it again -- just leave it
            # as it is, because we know that it is already hashed.  
            login_dict['password_hashed'] = request.REQUEST.get('password_hashed', '')
            
            if login_dict['password'] != login_dict['password_hashed']:
                # encrypt the password -- but only if it is a new password or if the password
                # has been changed by the user if it does not match the password stored in password_hashed
                password_hashed = utils.passhash(login_dict['password'])
                login_dict['password'] = password_hashed
                login_dict['password_hashed'] = password_hashed
            else:
                # it is already hashed -- don't has it again.
                login_dict['password_hashed'] = login_dict['password']
            
            # we should totally remove 'password_verify' from the UserModel eventually -- but for 
            # now just set it to the password (since we have just replaced the password with the hash).
            login_dict['password_verify'] = login_dict['password']
                           
            response =  login_utils.verify_user_login(request, login_dict)
            response_dict['Registration_OK'] = response
        else:
            response_dict['Registration_Error'] = error_dict
            
        json_response = simplejson.dumps(response_dict)
        return http.HttpResponse(json_response, mimetype='text/javascript')        