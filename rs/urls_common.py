
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


from django.conf.urls.defaults import *

from rs import views, ajax, store_data, search_results, mailbox, contacts, \
     reset_password, blobstore_handlers, batch_jobs, email_utils, admin, login_utils,\
     models, lang_settings, channel_support, vip_status_support, \
     videochat, rendering, sitemaps, mail_handlers, track_viewers, messages
from rs.user_profile_main_data import *
from rs.user_profile_details import *
import gaesessions
import logging

urlpatterns = patterns('',
    url(r'^$', views.login, name="views.login"),
    (r'^/$', views.login),     
    
    #(r'^ajax/$', rendering.render_main_html, {'generated_html': '', 'render_wrapper_only' : True}), 
        
    (r'^setlang/(?P<lang_code>[\w]{2})/$', lang_settings.set_language_and_redirect_back),    
    
    url(r'^rs/welcome/$', views.welcome, name="views.welcome"),
    url(r'^rs/logout/$', views.logout, name="views.logout"),
    url(r'^rs/terms/$', views.terms, name="views.terms"),    
    url(r'^rs/press/$', views.press, name="views.press"),
    (r'^rs/auth/crawler_login/$', views.crawler_login),
    (r'^rs/crawler_auth/$', views.crawler_auth),
    
    
    
    (r'^rs/resubmit_email/$', login_utils.resubmit_email),
    (r'^rs/auth/clear_session/$', login_utils.clear_session),
    
    # NOTE: we pass the UID into functions that retrieve or modify user information, so that
    # we can verify that the request and the UID come from the same user. This is as much
    # for internal code consistency verification, as it is to reduce attacks.
    
    # The user_main views are user-dependent. Each URL is different so that 
    # URL-based caching will work. We use the uid to ensure uniqueness.
    url(r'^rs/delete_account/(?P<owner_uid>[\w|-]+)/$', login_utils.delete_or_enable_account, {'delete_or_enable': 'delete'}, name="delete_account"),
    url(r'^rs/enable_account/(?P<owner_uid>[\w|-]+)/$', login_utils.delete_or_enable_account, {'delete_or_enable': 'enable'}, name="enable_account"),
    
    url(r'^edit_profile/(?P<display_nid>\d+)/$', views.user_main, {'is_primary_user': True}, name="edit_profile_url"),    
    url(r'^profile/(?P<display_nid>\d+)/(?P<profile_url_description>.+)/$', views.user_main, {'is_primary_user': False}, name="user_profile_url"),
    
    # The following URLs are what we used to use for displaying user profiles, and should redirect to the 
    # new URL so that search engines and others will update and use the correct value
    url(r'^rs/other/(?P<display_uid>[\w|-]+)/$', views.redirect_to_user_main, {'is_primary_user': False}, name="rs/other"),
    url(r'^rs/user_home/(?P<display_uid>[\w|-]+)/$', views.redirect_to_user_main, {'is_primary_user': True}, name="rs/user_home"),    
    
    
    url(r'^search/$', search_results.generate_search_results, name="search_gen"),
    url(r'^search_by_name/$', search_results.generate_search_results, {'type_of_search' : 'by_name'}, name="search_by_name_gen"),
    # The following is a old version of the above URL - eventually we should depreciate it entirely.
    # url(r'^rs/generate_search_results/$', search_results.generate_search_results, name="generate_search_results"),
    url(r'^rs/generate_search_results/$', search_results.permanent_search_query_redirect, name="generate_search_results"),
    
    url(r'^show_profile_views/$', track_viewers.generate_html_for_profile_views, name = 'show_profile_views'),
    url(r'^show_contacts/(?P<contact_type>\w+)/(?P<sent_or_received>\w+)/$', 
        contacts.show_contacts, name = 'show_contacts'),
    
    url(r'^rs/auth/generate_mailbox/(?P<mailbox_name>[\w|-]+)/(?P<owner_uid>[\w|-]+)/$', 
        mailbox.generate_mailbox, name = "generate_mailbox"),
    url(r'^rs/auth/generate_mailbox_with_bookmark/(?P<bookmark>[\w|-]+)/(?P<mailbox_name>[\w|-]+)/(?P<owner_uid>[\w|-]+)/$',
        mailbox.generate_mailbox, name = "generate_mailbox_with_bookmark"),
    url(r'^rs/auth/mail_message_display/(?P<owner_uid>[\w|-]+)/(?P<other_uid>[\w|-]+)/$', 
        mailbox.mail_message_display, name='mail_message_display'),

    
    url(r'^rs/reset_password/$', reset_password.reset_password, name="reset_password"),    
    url(r'^rs/reset_password/(?P<email_address>.+)/$', reset_password.reset_password, name="reset_password.username"),    
    url(r'^rs/submit_email_for_reset_password/$', reset_password.submit_email_for_reset_password, name="submit_email_for_reset_password"),    
    
    (r'^rs/blobstore_photo_upload/$', blobstore_handlers.blobstore_photo_upload),
    (r'^rs/store_photo_options/(?P<owner_uid>[\w|-]+)/[\w|-]+/$', store_data.store_photo_options),
    (r'^rs/store_about_user[_dialog_popup]*/(?P<owner_uid>[\w|-]+)/$', store_data.store_about_user),
    (r'^rs/store_signup_fields/(?P<owner_uid>[\w|-]+)/$', store_data.store_data, {
        'fields_to_store': UserSpec.principal_user_data + ['region', 'sub_region',], 'update_title':True, 'is_signup_fields':True}),
    (r'^rs/store_details_fields/(?P<owner_uid>[\w|-]+)/$', store_data.store_data,{
        'fields_to_store': UserProfileDetails.details_fields_to_display_in_order}),
    (r'^rs/store_current_status/(?P<owner_uid>[\w|-]+)/$', store_data.store_current_status),  
    (r'^rs/store_email_address/(?P<owner_uid>[\w|-]+)/$', store_data.store_email_address),
    (r'^rs/store_email_options/(?P<owner_uid>[\w|-]+)/$', store_data.store_email_options),
    (r'^rs/store_change_password_fields/(?P<owner_uid>[\w|-]+)/$', store_data.store_change_password_fields),
    (r'^rs/store_send_mail/(?P<to_uid>[\w|-]+)/(?P<captcha_bypass_string>[\w|-]+)/(?P<have_sent_messages_string>[\w|-]+)/$', messages.store_send_mail, {
        'text_post_identifier_string': 'send_mail'}),  
    (r'^rs/store_report_unacceptable_profile/(?P<display_uid>[\w|-]+)/', store_data.store_report_unacceptable_profile),
    #(r'^rs/store_new_user_after_verify_email_code/dummy/$', store_data.store_new_user_after_verify_email_code),
    (r'^rs/store_new_user_after_verify_email_url/$', store_data.store_new_user_after_verify_email_url),
    # Note, we break from the naming convention for the following url to keep it shorter for inclusion in emails.
    (r'^rs/authenticate/(?P<username>[\w|-]+)/(?P<secret_verification_code>[\w|-]+)/$',
     store_data.store_new_user_after_verify_email_url),
    (r'^rs/store_send_mail_from_profile_checkbox_no/(?P<to_uid>[\w|-]+)/(?P<captcha_bypass_string>[\w|-]+)/(?P<have_sent_messages_string>[\w|-]+)/$', 
     messages.store_send_mail, {'text_post_identifier_string': 'send_mail_from_profile_checkbox_no'}),    
    (r'^rs/store_send_mail_from_profile_checkbox_yes/(?P<to_uid>[\w|-]+)/(?P<captcha_bypass_string>[\w|-]+)/(?P<have_sent_messages_string>[\w|-]+)/$', 
     messages.store_send_mail, {'text_post_identifier_string': 'send_mail_from_profile_checkbox_yes'}),
    (r'^rs/store_initiate_contact/(?P<to_uid>[\w|-]+)/$', store_data.store_initiate_contact),
    (r'^rs/store_create_new_group/$', channel_support.store_create_new_group),
    # the following will store the checkbox fields such as languages, athletics, entertainmnet, turn_ons, etc.
    # Keep after all other "store_..." URL handlers since this is generic and would catch/block most of them
    (r'^rs/store_(?P<option_name>[\w|-|_]+)/(?P<owner_uid>[\w|-]+)/$', store_data.store_generic_checkbox_option_list),
        
    url(r'^rs/manage_mailbox/(?P<owner_uid>[\w|-]+)/$', mailbox.manage_mailbox, name="manage_mailbox"),     
        
    # cns - is change_notification_settings -- but keep it small because it a URL for sending in an email
    (r'^rs/cns/(?P<subscription_option>[\w|-]+)/(?P<username>[\w|-]+)/(?P<hash_of_creation_date>[\w|-]+)/$', 
     email_utils.change_notification_settings),
    
    # del - delete user profile by clicking on link in email message.
    # first page is a confirmation that they actually wish to delete their account
    (r'^rs/confirm_delete/(?P<username>[\w|-]+)/(?P<hash_of_creation_date>[\w|-]+)/$', 
     email_utils.delete_userobject_confirmation),
    
    # first page is a confirmation that they actually wish to delete their account
    (r'^rs/do_delete/(?P<username>[\w|-]+)/(?P<hash_of_creation_date>[\w|-]+)/$', 
     login_utils.delete_userobject_with_name_and_security_hash),    
    
    # NOTE: for "get" operations, we pass in the UID. This is done so that the information is not 
    # incorrectly cached by external devices, which may wrongly interpret a single address as having
    # the same value -- which would be the case if no UID were included.
    
    # Note that the regular expression accepts a random value as the rightmost value so that
    # IE will not cache the page.
    (r'^rs/ajax/get_current_status_settings/(?P<uid>[\w|-]+)/[\w|-]+/$', ajax.get_current_status_settings),
    (r'^rs/ajax/get_simple_search_settings/[\w|-]+/$', ajax.get_simple_search_settings),    
    (r'^rs/ajax/get_email_address_settings/(?P<uid>[\w|-]+)/[\w|-]+/$', ajax.get_email_address_settings),
    (r'^rs/ajax/get_about_user[_dialog_popup]*_settings/(?P<uid>[\w|-]+)/[\w|-]+/$', ajax.get_about_user_settings),
    (r'^rs/ajax/get_details_fields_settings/(?P<uid>[\w|-]+)/[\w|-]+/$', ajax.get_details_fields_settings),    
    (r'^rs/ajax/get_signup_fields_settings/(?P<uid>[\w|-]+)/[\w|-]+/$', ajax.get_signup_fields_settings),
    (r'^rs/ajax/get_change_password_fields_settings/(?P<uid>[\w|-]+)/[\w|-]+/$', ajax.get_change_password_fields_settings),  
    (r'^rs/ajax/get_initiate_contact_settings/(?P<display_uid>[\w|-]+)/[\w|-]+/$', ajax.get_initiate_contact_settings),    
    (r'^rs/ajax/get_location_options/(?P<location_code>[\w|,|-]+)/$', ajax.get_location_options),
    (r'^rs/ajax/get_(?P<photo_size>[\w]+)_photo/(?P<photo_object_key_str>[\w|-]+).png$', ajax.get_photo), 
    (r'^rs/ajax/get_for_sale_to_buy_options/(?P<current_selection>[\w|-|_]+)/', ajax.get_for_sale_to_buy_options),
    # following line will catch calls to get_entertainment_settings, get_athletics_settings, etc.
    (r'^rs/ajax/get_(?P<option_name>[\w|-|_]+)_settings/(?P<uid>[\w|-]+)/[\w|-]+/$', ajax.get_generic_options_settings),
    
    
    
    # The following "load" functions generate the HTML required for displaying the given section, as opposed to
    # passing back user-specific data for the given section.
    (r'^rs/ajax/load_profile_photo/[\w|-]+/$', ajax.load_profile_photo), 
    (r'^rs/ajax/load_photos/[\w|-]+/$', ajax.load_photos), 
    (r'^rs/ajax/load_photos_for_edit/[\w|-]+/$', ajax.load_photos_for_edit), 
    (r'^rs/ajax/load_photos_for_edit/$', ajax.load_photos_for_edit), 
    (r'^rs/ajax/load_photo_upload_form_url/[\w|-]+/$', ajax.load_photo_upload_form_url), 
    (r'^rs/ajax/load_current_status/[\w|-]+/$', ajax.load_current_status), 
    (r'^rs/ajax/load_current_status_for_edit/$', ajax.load_current_status_for_edit),     
    (r'^rs/ajax/load_email_address/[\w|-]+/$', ajax.load_email_address), 
    (r'^rs/ajax/load_email_address_for_edit/$', ajax.load_email_address_for_edit), 
    (r'^rs/ajax/load_signup_fields/[\w|-]+/$', ajax.load_signup_fields), 
    (r'^rs/ajax/load_signup_fields_for_edit/$', ajax.load_signup_fields_for_edit), 
    (r'^rs/ajax/load_details_fields/[\w|-]+/$', ajax.load_details_fields), 
    (r'^rs/ajax/load_details_fields_for_edit/$', ajax.load_details_fields_for_edit), 
    (r'^rs/ajax/load_email_options_for_edit/$', ajax.load_checkbox_section_for_edit, {'section_name': 'email_options', 
                                                                                      'fields_per_row': 1}), 
    (r'^rs/ajax/load_change_password_fields/[\w|-]+/$', ajax.load_change_password_fields), 
    (r'^rs/ajax/load_change_password_fields_for_edit/$', ajax.load_change_password_fields_for_edit),   
    (r'^rs/ajax/load_send_mail/(?P<other_uid>[\w|-]+)/[\w|-]+/$', ajax.load_send_mail),
    (r'^rs/ajax/load_send_mail_from_profile_checkbox_no/(?P<other_uid>[\w|-]+)/[\w|-]+/$', 
     ajax.load_send_mail_from_profile, {
        'show_checkbox_beside_summary': False}),      
    (r'^rs/ajax/load_send_mail_from_profile_checkbox_yes/(?P<other_uid>[\w|-]+)/[\w|-]+/$', 
     ajax.load_send_mail_from_profile, {
         'show_checkbox_beside_summary': True}),  
    (r'^rs/ajax/load_about_user[_dialog_popup]*/[\w|-]+/$', ajax.load_about_user),       
    (r'^rs/ajax/load_about_user(?P<for_dialog_popup_string>[_dialog_popup]*)_for_edit/$', ajax.load_about_user_for_edit),       
    (r'^rs/ajax/load_mail_history/(?P<bookmark_key_str>[\w|-]+)/(?P<other_uid>[\w|-]+)/$', ajax.load_mail_history),
    (r'^rs/ajax/favorite_message/(?P<have_sent_messages_id>[\w|-]+)/$', ajax.favorite_message),  
    (r'^rs/ajax/read_message/(?P<have_sent_messages_id>[\w|-]+)/$', ajax.move_message, {'mailbox_to_move_message_to' : 'inbox'}),  
    (r'^rs/ajax/inbox_message/(?P<have_sent_messages_id>[\w|-]+)/$', ajax.move_message, {'mailbox_to_move_message_to' : 'inbox'}),  
    (r'^rs/ajax/spam_message/(?P<have_sent_messages_id>[\w|-]+)/$', ajax.move_message, {'mailbox_to_move_message_to' : 'spam'}), 
    (r'^rs/ajax/trash_message/(?P<have_sent_messages_id>[\w|-]+)/$', ajax.move_message, {'mailbox_to_move_message_to' : 'trash'}),  
    (r'^rs/ajax/load_mail_textarea/(?P<other_uid>[\w|-]+)/(?P<section_name>[\w|-]+)/$', ajax.load_mail_textarea),   
    
    # keep the following "load_checkbox_..." *below* all other "load_checkbox_..." declarations so that 
    # they do not in-advertantly catch a more specific function call.
    (r'^rs/ajax/load_(?P<section_name>[\w|-|_]+)_for_edit/$', ajax.load_checkbox_section_for_edit), # keep this above the next line   
    (r'^rs/ajax/load_(?P<section_name>[\w|-|_]+)/[\w|-]+/$', ajax.load_checkbox_section), # keep below previous call, since it is more specific
    
    (r'^rs/ajax/set_show_online_status_trial/[\w|-]+/$', ajax.set_show_online_status_trial), # keep below previous call, since it is more specific
    
    # temporarily reduced the following error message to a warning, until we can come back and cleanup all possible
    # instances in which this URL might be called - it is currently generating too many errors in the log, and masking 
    # other, more serious, error messages.
    (r'^rs/ajax/report_javascript_error/$', ajax.report_javascript_status, {'logging_function': logging.warning}), 
    (r'^rs/ajax/report_javascript_debugging_info/$', ajax.report_javascript_status, {'logging_function': logging.info}),        
    
    # calls for chat functionality
    (r'^rs/channel_support/post_message/[\w|-]+/$', channel_support.post_message),
    #(r'^rs/channel_support/get_group_members/(?P<group_id>[\w|-]+)/[\w|-]+/$', channel_support.get_group_members),
    (r'^rs/channel_support/poll_server_for_status_and_new_messages/[\w|-]+/$', channel_support.poll_server_for_status_and_new_messages),
    (r'^rs/channel_support/close_chat_box/[\w|-]+/$', channel_support.close_chat_box),
    (r'^rs/channel_support/open_new_chatbox/[\w|-]+/$', channel_support.open_new_chatbox),
    (r'^rs/channel_support/close_all_chatboxes_on_server/[\w|-]+/$', channel_support.close_all_chatboxes_on_server),
    (r'^rs/channel_support/update_user_presence_on_server/[\w|-]+/$', channel_support.update_user_presence_on_server),
    (r'^rs/channel_support/update_chatbox_status_on_server/[\w|-]+/$', channel_support.update_chatbox_status_on_server),
    (r'^rs/channel_support/set_minimize_chat_box_status/[\w|-]+/$', channel_support.set_minimize_chat_box_status),
    (r'^rs/channel_support/initialize_main_and_group_boxes_on_server/[\w|-]+/$', channel_support.initialize_main_and_group_boxes_on_server),
        
    # Paypal feedback URLs
    (r'^paypal/ipn/$', vip_status_support.instant_payment_notification),
    (r'^paypal/ipn/must_overwrite_this_url_dynamically/$', vip_status_support.instant_payment_notification_default),
    
    # Videochat URLs
    (r'^videochat_server/$', videochat.videochat_server),
    (r'^videochat_window/video_phone.html$', videochat.videochat_window),
    
    ###############################################
    # Sitemap generation and sitemap display links
    (r'^rs/admin/generate_sitemaps/$', sitemaps.generate_sitemaps),
    
    (r'^sitemap_index-(?P<sitemap_index_number>[\d]+).xml$', sitemaps.get_sitemap_index),    
    (r'^sitemap-(?P<sitemap_number>[\d]+).xml$', sitemaps.get_sitemap),
    
    ########################################################################################3
    # Administrative/Batch stuff
    
    # add an extra logout so that you don't have to be logged in as an admin in order to log out.
    (r'^rs/admin_logout', admin.admin_logout),
    (r'^rs/admin/logout', admin.admin_logout),
    (r'^rs/admin/review_public_photos_bookmark/(?P<what_to_show>[\w|-]+)/(?P<bookmark>[\w|-]+)/$',admin.review_photos),
    (r'^rs/admin/review_public_photos/(?P<what_to_show>[\w|-]+)/$',admin.review_photos),
    (r'^rs/admin/review_public_photos/$',admin.review_photos, {'what_to_show':'show_all'}),
    
    (r'^rs/admin/review_private_photos_bookmark/(?P<what_to_show>[\w|-]+)/(?P<bookmark>[\w|-]+)/$',admin.review_photos,
     {'is_private': True}),
    (r'^rs/admin/review_private_photos/(?P<what_to_show>[\w|-]+)/$',admin.review_photos,
     {'is_private': True}),
    (r'^rs/admin/review_private_photos/$',admin.review_photos,
     {'what_to_show': 'show_all', 'is_private': True}),
    (r'^rs/admin/ajax/get_(?P<photo_size>[\w]+)_photo/(?P<photo_object_key_str>[\w|-]+).png$', ajax.get_photo, {
        'is_admin_login': True}),   
    
    # The following call is responsible for calling the code to send out email notifications, and re-queues itself 
    # to periodically send out notifications to all users who have received new messages/contacts.
    (r'^rs/admin/batch_email_notification_launcher/$', email_utils.batch_email_notification_launcher),
    # The followin functions will be called by the above function. Each of these will loop over the users and 
    # submit each user individually to the batch system for sending a notification.
    (r'^rs/admin/email_new_message/$', email_utils.send_batch_email_notifications, {
        'object_type': models.UnreadMailCount, 'key_type_on_usermodel' : models.UserModel.unread_mail_count_ref}),
    (r'^rs/admin/email_new_contacts/$', email_utils.send_batch_email_notifications, {
        'object_type': models.CountInitiateContact,
        'key_type_on_usermodel' : models.UserModel.new_contact_counter_ref}),
    
    
    # The following sends a single notification to a single user. Will be called by the task manager, and re-queued
    # if there is a problem sending.
    (r'^rs/admin/send_new_message_notification_email/$', email_utils.send_new_message_notification_email),    
    
    (r'^rs/admin/send_generic_email_message/$', email_utils.send_generic_email_message,{}),    
    (r'^rs/admin/send_confirmation_email/$', email_utils.send_confirmation_email,{}), 
        
    #(r'^rs/admin/deferred_copy_mailbox_model/$', batch_jobs.deferred_copy_mailbox_model),
    #(r'^rs/admin/deferred_copy_have_had_contact/$', batch_jobs.deferred_copy_have_had_contact),
    #(r'^rs/admin/deferred_fix_initiate_contact_model/$', batch_jobs.deferred_fix_initiate_contact_model),
    
    #(r'^rs/admin/batch_send_email/$', batch_jobs.batch_send_email),
    #(r'^rs/admin/batch_send_uncompleted_registration_email/$', batch_jobs.batch_send_uncompleted_registration_email),
    
    (r'^rs/admin/view_message/$', batch_jobs.view_message),
    
    #(r'^rs/admin/batch_create_username_combinations_list/$', batch_jobs.batch_create_username_combinations_list),
    
    
    
    (r'^rs/admin/remove_ip/(?P<ip_to_remove>[\w|\.]+)/$', admin.batch_remove_profiles),
    (r'^rs/admin/remove_ip/(?P<ip_to_remove>[\w|\.]+)/(?P<reason_for_removal>[\w]+)/$', admin.batch_remove_profiles),
    (r'^rs/admin/remove_name/(?P<name_to_remove>[\w|\.]+)/$', admin.batch_remove_profiles),
    (r'^rs/admin/remove_name/(?P<name_to_remove>[\w|\.]+)/(?P<reason_for_removal>[\w]+)/$', admin.batch_remove_profiles),
    (r'^rs/admin/remove_email/(?P<email_to_remove>[^#?]+?)/$', admin.batch_remove_profiles),
    (r'^rs/admin/remove_email/(?P<email_to_remove>[^#?]+?)/(?P<reason_for_removal>[\w]+)/$', admin.batch_remove_profiles), 
    
    (r'^rs/admin/enable_name/(?P<name_to_enable>[\w|\.]+)/$', admin.enable_username),
    
    
    (r'^rs/admin/cleanup_sessions/$', gaesessions.cleanup_sessions),
    
    (r'^rs/admin/manually_give_paid_status/(?P<username>[\w]+)/(?P<num_credits>[\w]+)/$', vip_status_support.manually_give_paid_status),
    (r'^rs/admin/manually_give_paid_status/(?P<username>[\w]+)/(?P<num_credits>[\w]+)/(?P<txn_id>[\w]+)/$', vip_status_support.manually_give_paid_status),
    (r'^rs/admin/manually_remove_paid_status/(?P<username>[\w]+)/$', vip_status_support.manually_remove_paid_status),
    
    #(r'^rs/admin/test_store_payment_and_update_structures/(?P<username>[\w]+)/(?P<txn_id>[\w]+)/$', vip_status_support.test_store_payment_and_update_structures),
    #(r'^rs/admin/approve_public_photos_bookmark/(?P<bookmark>[\w|-]+)/$',admin.mark_photos_as_approved),
    #(r'^rs/admin/approve_public_photos/$',admin.mark_photos_as_approved),

    #(r'^rs/admin/batch_fix_viewed_profile_counter/$', batch_jobs.batch_fix_viewed_profile_counter), 
    (r'^rs/admin/batch_fix_object/$', batch_jobs.batch_fix_object), 
    
    (r'^rs/admin/fix_items_sub_batch/$', batch_jobs.fix_items_sub_batch),
    
    
    (r'^rs/admin/login/$', views.login, {'is_admin_login': True}),
      
    (r'^rs/admin/count_clients/$', admin.count_clients),
    
    (r'^_ah/bounce$', mail_handlers.handle_bounced_email),
        
    # Test stuff
    (r'^rs/test/render_notification_control/$', email_utils.render_notification_control_html),
    
    # robots.txt
    (r'^robots.txt$', views.robots_txt),
)