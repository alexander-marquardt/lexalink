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


from google.appengine.ext import ndb 
from django import http 
from django.shortcuts import render_to_response
from models import VideoPhoneUserInfo

from django.utils.html import escape
import utils, datetime, logging, error_reporting, settings, utils_top_level


def videochat_server(request):
    # App-engine implementation of videophone code - Alexander Marquardt
    
    try:
	logging.info("Entering videochat_server function")
	
	# returns an HttpResponse with XML representation of the user and connectivity information
	generated_xml = 'Content-type: text/plain\n\n<?xml version="1.0" encoding="utf-8"?>\n<result>'
	
	window_name = request.GET.get('chatWindowName', None)
	identity = request.GET.get('identity', None)
	friends = request.GET.getlist('friends')
	
	query_filter_dict = {}
	if window_name:
	    logging.info("writing to database: window_name %s\nidentity%s\n" % (window_name, identity))
	    try:
		query_filter_dict['m_window_identifier ='] = window_name
		order_by = '-m_updatetime' # in case by accident we write more than one value for a window_name, get the most recent
		query = utils.do_query(VideoPhoneUserInfo, query_filter_dict, order_by)  
		
		chat_user_info = query.get()
		if not chat_user_info:
		    chat_user_info = VideoPhoneUserInfo()
		    
		
		chat_user_info.m_window_identifier = window_name
		chat_user_info.m_identity = identity
		chat_user_info.m_updatetime = datetime.datetime.now()
		chat_user_info.put()
		
		generated_xml += '\t<update>true</update>'
		
	    except:
		error_reporting.log_exception(logging.critical)		
		generated_xml += '\t<update>false</update>'
    
	    
	for f in friends:
	    logging.info("generating xml for friend lookup %s" % f)
	    
	    generated_xml += "\t<friend>\n\t\t<chatWindowName>%s</chatWindowName>" % escape(f)
	    
	    query_filter_dict['m_window_identifier ='] = f
	    query_filter_dict['m_updatetime >'] = datetime.datetime.now() - datetime.timedelta(hours = 1)
	    query = utils.do_query(VideoPhoneUserInfo, query_filter_dict)
	    
	    chat_friend_info = query.get()
	    if chat_friend_info:
		generated_xml += "\t\t<identity>%s</identity>" %escape(chat_friend_info.m_identity)
	    else:
		logging.critical("Did not find window_name: %s" % f)
		
	    generated_xml += "\t</friend>"
	    
	    
	generated_xml += "</result>"
    
	logging.info("generated_xml: %s" % generated_xml)	
	return http.HttpResponse(generated_xml)
    except:
	error_reporting.log_exception(logging.critical)
	return http.HttpResponseServerError("Error: " + generated_xml)
	
	
def videochat_window(request):
    
    html_flash_wrapper_file = 'video_phone_symlink1/%s/video_phone.html' % settings.FLASH_FILES_DIR
    
    try:
	uid = request.session['userobject_str']
	other_uid = request.GET.get('other_uid', None)
	
	initiate_call = request.GET.get('initiate_call', None) # either "yes" or "no"
	if not other_uid:
	    raise Exception("Error: other_uid not defined")
	else:
	    other_userobject = utils_top_level.get_object_from_string(other_uid)
	    other_username = other_userobject.username
	
	return render_to_response(html_flash_wrapper_file, 
	                          {'django_template_web_service_url': request.META['HTTP_HOST'] + "/videochat_server/",
	                           'django_template_uid' : uid,
	                           'django_template_other_uid' : other_uid,
	                           'django_template_initiate_call' : initiate_call,
	                           'django_template_other_username' : other_username,
	                           }
	                          )
    except:
	error_reporting.log_exception(logging.critical)
	return http.HttpResponse("Error in connecting to videochat_window function")
    