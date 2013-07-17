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

import datetime, inspect

from google.appengine.ext import ndb 
from google.appengine.api import users
from google.appengine.api import taskqueue

from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django import http
from django.utils.translation import ugettext

import settings 

import error_reporting, logging
import models, utils, sharding, constants, store_data, login_utils
from rs import profile_utils

from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth import login as django_login, logout as django_logout, authenticate as django_authenticate
from google.appengine.api import users
from django.template import loader, Context


def admin_logout(request):
    
    user = users.get_current_user()
    
    if user:
        generated_html = '<a href=\"%s\">sign out</a><br>' % (users.create_logout_url("/"))
    else:
        generated_html = "Must be logged in to logout<br>\n"
        
    return HttpResponse(generated_html) 
    

def review_photos(request, is_private=False, what_to_show = "show_new", bookmark = ''):
    # this is a maintenance program, that will run through all uploaded photos in the system for
    # easy viewing and maintenance.
    # what_to_show is a string that can either be "only_show_new" or "show_all"
    #
    try:
        PhotoModel = models.PhotoModel
            
        PAGESIZE = 16 # total number of photos per page (how many to fetch in the query)
        PAGEWIDTH = 8 # number of photos per row
        
        continue_html =  generated_html = post_footer_html = post_header_html = ''
           
        q = PhotoModel.query().order(-PhotoModel.creation_date)    
        q = q.filter(PhotoModel.is_private == is_private)   
        
        if what_to_show == "show_new" and is_private:
            # show the private photos that have not been reviewed
            q = q.filter(PhotoModel.has_been_reviewed == False)  
            
        if what_to_show == "show_new" and not is_private:
            # show the public photos that have not been approved
            q = q.filter(PhotoModel.is_approved == False)
        
        num_photos_deleted = 0
        num_photos_marked_private = 0
        num_photos_approved = 0
        num_photos_reviewed = 0
        num_photos_unapproved = 0
    
        if request.method == 'POST': 
            
            def store_options_for_photo_key(photo_key_str, review_action_dict):
                photo_object = ndb.Key(urlsafe = photo_key_str).get()
                parent_uid = photo_object.parent_object.urlsafe()
                # if we deleted a photo, we need to recompute the photo-based offsets
                store_data.store_photo_options(request, parent_uid, is_admin_photo_review = True, review_action_dict = review_action_dict)            
            
            delete_photo_list_of_keys_strs = request.POST.getlist('delete_photo')
            for photo_key_str in delete_photo_list_of_keys_strs:
                # delete the photo and recompute the photo-based offsets            
                store_options_for_photo_key(photo_key_str, review_action_dict = {'delete' : photo_key_str})
                num_photos_deleted += 1
                
            mark_private_photo_list_of_keys_strs = request.POST.getlist('mark_private_photo')
            for photo_key_str in mark_private_photo_list_of_keys_strs:
                try:
                    # if we mark a photo private, we need to recompute the photo-based offsets                
                    # this could fail if we just deleted the photo - but then wy would we be marking it private .. 
                    store_options_for_photo_key(photo_key_str, review_action_dict = {'is_private' : photo_key_str})
                    num_photos_marked_private += 1     
                except:
                    # if it fails because it was just deleted, then ignore it - need to get the error type and write a seperate except
                    error_reporting.log_exception(logging.error)            
                
                
            def approve_or_unapprove_photo(photo_key_str, is_approved):
                
                modify_num_photos = 0
                try:
                    photo_object = ndb.Key(urlsafe = photo_key_str).get()
                    
                    # object may have been deleted - so make sure it exists
                    if photo_object:
                        photo_object.is_approved = is_approved
                        utils.put_object(photo_object)    
                        modify_num_photos = 1 if is_approved else -1
    
                    else:
                        error_reporting.log_exception(logging.warning, error_message = "photo_object not found")                  
                except:
                    error_reporting.log_exception(logging.error) 
                    return 0
    
                return modify_num_photos
                                
            approve_photo_list_of_keys_strs = request.POST.getlist('approve_photo')
            # Photo has been approved as a public photo
            for photo_key_str in approve_photo_list_of_keys_strs:
                num_photos_approved += approve_or_unapprove_photo(photo_key_str, True)  
            
            unapprove_photo_list_of_keys_strs = request.POST.getlist('mark_private_photo')
            for photo_key_str in unapprove_photo_list_of_keys_strs:
                num_photos_approved += approve_or_unapprove_photo(photo_key_str, False)      
                
            reviewed_photo_list_of_keys = request.POST.getlist('reviewed_photo')
            # Photo has been reviewed - means that we have looked at it and determined that it doesn't need to be deleted
            # from the datastore. Remove the non-watermarked copies of the photos and mark the photo as reviewed.
            for photo_key_str in reviewed_photo_list_of_keys:
                try:
                    
                    photo_object = ndb.Key(urlsafe = photo_key_str).get()
                    # we may have just deleted the photo_object, so make sure that it exists.
                    if photo_object:
                        photo_object.has_been_reviewed = True
                        # remove the "original" (without watermark) photos - these were only necessary for verification
                        # of non-reviewed photos. 
                        photo_object.medium_before_watermark = None
                        photo_object.large_before_watermark = None
                        utils.put_object(photo_object)
                        num_photos_reviewed += 1     
                except:
                    error_reporting.log_exception(logging.error)         
                
        generated_html += 'Deleted %d photos<br>\n' % num_photos_deleted
        generated_html += 'Marked private %d photos<br>\n' % num_photos_marked_private
        generated_html += 'Approved %d photos<br>\n' % num_photos_approved
        generated_html += 'Reviewed %d photos<br><br><br>\n' % num_photos_reviewed
        generated_html += 'Un-Approved %d photos<br>\n' % num_photos_unapproved
        
        # since we use this function for both deleting/approving, as well as displaying the photos -- we need a "final" pass
        # to process prviously marked photos -- this is indicated by the "final_pass" bookmark.
        
        if bookmark != 'final_pass':
            if bookmark :
                bookmark_key = ndb.Key(urlsafe = bookmark)
                photo_bookmark_object =bookmark_key.get()
                q = q.filter(PhotoModel.creation_date <=  photo_bookmark_object.creation_date) # only get the photos that are older than the bookmark.
           
            # note: creation_date refers to last time photo was updated
                      
            
        
            batch = q.fetch(PAGESIZE + 1)
        
            generated_html += """
            <table>
            <tr>""" 
    
            num_in_current_row = 0
            
            for photo_object in batch[:PAGESIZE]:  
            
                photo_object_key_str = photo_object.key.urlsafe()
                photo_parentobject = photo_object.parent_object.get()
                
                profile_href = profile_utils.get_userprofile_href(request.LANGUAGE_CODE, photo_parentobject, is_primary_user=False)
                
                if photo_object.has_been_reviewed:
                    url_for_photo = '/rs/admin/ajax/get_%s_photo/%s.png' % ("medium", photo_object_key_str)
                    url_for_large_photo = '/rs/admin/ajax/get_%s_photo/%s.png' % ("large", photo_object_key_str)
                else:
                    url_for_photo = '/rs/admin/ajax/get_%s_photo/%s.png' % ("medium_before_watermark", photo_object_key_str)
                    url_for_large_photo = '/rs/admin/ajax/get_%s_photo/%s.png' % ("large_before_watermark", photo_object_key_str)
                    
                           
                creation_datetime_formatted = utils.return_time_difference_in_friendly_format(photo_object.creation_date)
                
                status_html = ''
                if photo_object.is_approved:
                    status_html += '<span style="color:green"> Approved for public</span><br>'
                else:
                    status_html += '<span style="color:red"> Not approved public</span><br>'
                    
                if photo_object.has_been_reviewed:
                    fancybox_title = "Has been previously reviewed"
                    status_html += '<span style="color:green">Reviewed</span><br>'
                else:
                    fancybox_title = "Admin view - these un-reviewed photos should *not* have watermarks"
                    status_html += '<span style="color:red">Not Reviewed</span><br>'
                
                generated_html += '<td>%s<br><a href="%s">%s</a><br>%s<br>' % (status_html, profile_href, photo_parentobject.username, 
                                                                         creation_datetime_formatted)
                
                generated_html += """<table><tr><td class = "img_min_height"><a class="%s" rel=%s href="%s" title="%s"><img class = "%s" src = "%s"><br></td></tr></table>\n""" % (
                    "cl-fancybox-profile-gallery", "cl-gallery1", 
                    url_for_large_photo, fancybox_title, 'cl-photo-img', url_for_photo)        
                
                
                generated_html += '<input type = "checkbox" name=delete_photo value="%s"> Delete <br>\n' %( photo_object_key_str)
                
                if not is_private:
                    # it is marked as "public"
                    generated_html += '<input type = "checkbox" name=mark_private_photo value="%s"> Mark Private <br>\n' % (photo_object_key_str)
                    
                    # if the photo is new, we want to give the user at least X minutes to mark it as "private".
                    # Therefore, we don't mark it as "approved" which has the same effect as leaving it as "private" 
                    # which is desired because the user needs a window of time between uploding the photo and showing 
                    # it publicly so that they can mark private photos as "private" without risking public display.
                    if photo_object.creation_date > datetime.datetime.now() - datetime.timedelta(minutes = 5):
                        checked_val = ''
                    else:
                        if photo_object.is_approved:
                            # if already approved, don't check it since that would be redundant
                            checked_val = ''
                        else:
                            checked_val = "checked"
                        
                    generated_html += '<input type = "checkbox" name=approve_photo value="%s" %s> Approve for public<br>\n' % (photo_object_key_str, checked_val)
                                
                
                if photo_object.has_been_reviewed:
                    checked_val = "" # we have already reviewed it, don't mark it again  as reviewed
                else:
                    checked_val = "checked"
                generated_html += '<input type = "checkbox" name=reviewed_photo value="%s" %s> Mark Reviewed <br>\n' % (photo_object_key_str, checked_val)
    
    
                    
                generated_html += "</td>"
          
                num_in_current_row += 1
                
                if num_in_current_row == PAGEWIDTH:
                    generated_html += "</tr><tr>\n"
                    num_in_current_row = 0
                
            href = ''
            if len(batch) == PAGESIZE + 1:
                bookmark = batch[-1].key.urlsafe()
                
        
                if not is_private:
                    href = "/rs/admin/review_public_photos_bookmark/%s/%s/" % (what_to_show, bookmark)
                    continue_html += '<a href=%s>Show next page</a><br>\n' % href
                else:
                    href = "/rs/admin/review_private_photos_bookmark/%s/%s/" % (what_to_show, bookmark)
                    continue_html += '<a href=%s>Show next page</a><br>\n' % href
        
            generated_html += """
            </tr>\n
            </table>
            
            """
            
            if href == '':
                # note, since this is a final call, and it is only for processing the photos that we have marked for
                # deletion, this call can be to either the private or the public photos code.
                href = "/rs/admin/review_private_photos_bookmark/%s/final_pass/" % (what_to_show)
                
                
            post_header_html = """
            <head>
            <style type="text/css">
            .img_min_height {
            height: %(image_height)spx;
            }
            </style>
            <link rel="stylesheet" href="/%(live_static_dir)s/css/jquery.fancybox-1.3.4.css" type="text/css" media="screen">
            <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.4.4/jquery.min.js"></script>
            <script type="text/javascript" src="/%(live_static_dir)s/js/rometo-utils.js"></script>
    
            <script type="text/javascript" src="/%(live_static_dir)s/js/jquery.fancybox-1.3.4.js"></script>
    
            <script type="text/javascript">
            $(document).ready(function() {
            fancybox_setup($("a.cl-fancybox-profile-gallery"));
            });
            </script>
            </head>
            """ % {'live_static_dir': settings.LIVE_STATIC_DIR, 'image_height' : constants.MEDIUM_IMAGE_Y}
    
            post_header_html += '<form method = "POST" action = "%s">' % href
            post_footer_html = """
            <input type=submit  alt="" value="Process Marked Photos">
            </form><br>\n"""
          
            
        html_to_render = continue_html + post_header_html + generated_html + post_footer_html
    
        user = users.get_current_user()
        
        if user:
            html_to_render += '<a href=/rs/admin/review_public_photos/show_all/>Review all public photos</a><br>\n'    
            html_to_render += '<a href=/rs/admin/review_public_photos/show_new/>Review new public photos</a><br><br>\n'    
            html_to_render += '<a href=/rs/admin/review_private_photos/show_all/>Review all private photos</a><br>\n'       
            html_to_render += '<a href=/rs/admin/review_private_photos/show_new/>Review new private photos</a><br>\n'       
            html_to_render += '<br>Welcome %s: <a href=\"%s\">sign out</a><br><br><br>' % (user.nickname(), users.create_logout_url("/"))
            
            for build_name in constants.app_name_dict.keys():
                domain_name = constants.domain_name_dict[build_name]
                app_name = constants.app_name_dict[build_name]
                html_to_render += '<a href=http://www.%s/rs/admin/review_public_photos/show_new/>%s public photos</a><br>\n'  % (domain_name, app_name)
    
    
        else:
            html_to_render = "Error: user not logged in!!!!"
            
        # show the photo rules for the current site to the administrator, so they don't forget    
        template = loader.get_template("user_main_helpers/photo_rules.html")
        context = Context(constants.template_common_fields)
        photo_rules_html = "<br><br>%s" % template.render(context)
        
        html_to_render += photo_rules_html
    except:
        error_reporting.log_exception(logging.critical)  
        html_to_render = "Critical error - check logs"
        
    return HttpResponse(html_to_render)



def generate_code_for_maintenance_warning():
    # code for printing out warnings if google is doing database maintenance and we are shut
    # down.
    
    if settings.shutdown_time == False or settings.SHUTDOWN_DURATION == 0:
        return ('', '')
    
    shutdown_time = settings.shutdown_time
    SHUTDOWN_DURATION = settings.SHUTDOWN_DURATION # minutes

    maintenance_soon_warning_html = ''
    maintenance_shutdown_warning_html = ''   
    
    current_time = datetime.datetime.now()
    
    time_to_shutdown = shutdown_time - current_time
    minutes_to_shutdown, seconds = divmod(time_to_shutdown.seconds, 60)
    
    warning_message_text = ugettext("In %(minutes_to_shutdown)s minutes, we are closing %(app_name)s.com for \
approximately %(shutdown_time)s minutes for maintenance") % {'minutes_to_shutdown':minutes_to_shutdown, 
                                                             'app_name':settings.APP_NAME, 
                                                             'shutdown_time':SHUTDOWN_DURATION}
    
    if time_to_shutdown < datetime.timedelta(minutes = 5) and time_to_shutdown > datetime.timedelta(minutes = 0):
        maintenance_soon_warning_html += u"""<script type="text/javascript">alert("%s")</script>""" % warning_message_text
    
    # if time_to_shutdown is negative, then we are already in shutdown mode -- but only 
    # print this warning for SHUTDOWN_DURATION minutes. 
    elif time_to_shutdown < datetime.timedelta(minutes = 0) and\
         time_to_shutdown > datetime.timedelta(minutes = -SHUTDOWN_DURATION):
        
        # time_to_shutdown is a negative number
        time_remaining = time_to_shutdown + datetime.timedelta(minutes = SHUTDOWN_DURATION)
        minutes_remaining, seconds = divmod(time_remaining.seconds, 60)       
        
        already_shutdown_text = ugettext("We have closed %(app_name)s.com for approximately %(shutdown_time)s minutes for maintenance.\
We hope to re-open in %(minutes_remaining)s minutes.") % {'shutdown_time': SHUTDOWN_DURATION, 
                                                          'minutes_remaining': minutes_remaining,
                                                          'app_name': settings.APP_NAME  }
                
        
        maintenance_shutdown_warning_html = u"""
       <script type="text/javascript">alert(%(already_shutdown_text)s)</script>
       
       <br><br><br><br><br><br> 
       <span class="cl-text-24pt-format cl-warning-text" >%(already_shutdown_text)s</span>
       <br><br><br><br><br><br> 
       """ % {'already_shutdown_text' : already_shutdown_text}
        
    return (maintenance_soon_warning_html, maintenance_shutdown_warning_html)
        


        


def count_clients(request):
    
    count = sharding.get_count("number_of_new_users_shard_counter")
    generated_html = 'Number of registered users is: %d' % int(count)
    
    return HttpResponse(generated_html)

         
def run_query_to_take_action_on_profiles(request, action_to_take, query_key, query_value, reason_for_profile_removal, new_password, new_email_address):

    PAGESIZE = 100 # don't make this much more than 100 or we start overusing memory and get errors   
    generated_html = ''
    
    q= models.UserModel.query().filter(models.UserModel._properties[query_key] == query_value).filter(models.UserModel.is_real_user == True)
    userobject_batch = q.fetch(PAGESIZE)
            
    if not userobject_batch:
        # there are no more objects - break out of this function.
        info_message = u"No more objects found - Exiting function<br>\n"
        logging.info(info_message)
        return info_message

    for userobject in userobject_batch:  
        try:
            info_message = u"** %s %s userobject<br>\n" % (action_to_take, userobject.username)
            info_message += u"%s" % login_utils.take_action_on_account_and_generate_response(
                request, userobject, action_to_take, reason_for_profile_removal, new_password, new_email_address, return_html_or_text = "text")
            
            generated_html += info_message
            logging.info(info_message)                    
                
        except:
            error_reporting.log_exception(logging.critical)  
        
    return generated_html
        
        
def batch_take_action_on_profiles(request, action_to_take, field_for_action, val_for_query, reason_for_profile_removal = None, new_password = None,
                                  new_email_address = None):

    
    """ This function scans the database for profiles that need to be fixed
    
    action_to_take: "delete", "undelete", "set_password" , "reset"
        delete: means that the profile will have its "user_is_marked_for_elimination" set to True - this will prevent it from showing up in queries, and
                will eventually be removed from the database
        undelete: un-does a delete by marking user_is_marked_for_elimination to False
        disable: sets the user password to a secret value, and clears the email address
        enable: sets the user password to a new value, and sets the email_address to a passed-in value.
        
    field_for_action: "name", "ip", "email"
    val_for_query: if field_for_acion is "email", this is the email address, if field_for_action is "name" this is the name, etc.
    
    """
    
    valid_field_for_action_vals = ["name", "ip", "email"] # currently just used for error reporting
    
    try:
                    
        generated_html = 'Updating userobjects:<br><br>'
            
        val_for_query = val_for_query.replace(' ', '')
        
        if field_for_action == "ip":
            generated_html += run_query_to_take_action_on_profiles(request, action_to_take, 'registration_ip_address', val_for_query, 
                                                                   reason_for_profile_removal, new_password, new_email_address)
            generated_html += run_query_to_take_action_on_profiles(request, action_to_take, 'last_login_ip_address', val_for_query, 
                                                                   reason_for_profile_removal, new_password, new_email_address)
        elif field_for_action == "name":
            val_for_query = val_for_query.upper()
            generated_html += run_query_to_take_action_on_profiles(request, action_to_take, 'username', val_for_query, 
                                                                   reason_for_profile_removal, new_password, new_email_address)
        elif field_for_action == "email":
            val_for_query = val_for_query.lower()
            generated_html += run_query_to_take_action_on_profiles(request, action_to_take, 'email_address', val_for_query, 
                                                                   reason_for_profile_removal, new_password, new_email_address)            
        else:
            return http.HttpResponse("Called with incorrect URL - invalid field_for_action value of %s. Valid values are: %s" % (
                field_for_action, valid_field_for_action_vals))
            
        return http.HttpResponse(generated_html)
    except:
        error_reporting.log_exception(logging.critical)
        return http.HttpResponseServerError()
    
    
def backup_database(request):
    # Backup the important elements from the database into Google Cloud Storage
    
    try:
        
        app_id = constants.app_id_dict[settings.BUILD_NAME]
        bucket_name = "lexabit-common" 

        today = datetime.date.today()
        curr_day = today.strftime('%d')
        curr_month = today.strftime('%B')
        curr_year = today.strftime('%Y')
        sub_dir = "/%s/%s/%s/%s/" % (curr_year, curr_month, curr_day, app_id)

        # get all object types from models.py
        object_name_list = []
        for name, obj in inspect.getmembers(models):
            if inspect.isclass(obj):
                object_name_list.append(obj.__name__)
             
        gs_bucket_name = bucket_name + sub_dir
        logging.info("Backing up %s to bucket: %s" % (app_id, gs_bucket_name))
        taskqueue.add(queue_name = 'backup-entities-queue',
                      url    = '/_ah/datastore_admin/backup.create', 
                      method = 'GET',
                      target = 'ah-builtin-python-bundle', 
                      params ={ 'kind' : object_name_list,
                                'name' : 'cron-backup-', 
                                'filesystem' : "gs",
                                'gs_bucket_name' : gs_bucket_name,
                                }
                      )
        
        return HttpResponse("OK")
    
    except:
        error_reporting.log_exception(logging.critical)
        return http.HttpResponseServerError()