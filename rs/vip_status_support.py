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

from django.utils import translation

import os 
import logging
import error_reporting, email_utils, profile_utils
import settings, constants, models, login_utils, utils_top_level, utils, store_data, messages
import datetime, re
from models import UserModel
import hashlib


from django.http import HttpResponse
from django import http


  
FORTUMO_VALID_IP_LIST = ['79.125.125.1', '79.125.5.205', '79.125.5.95'] # These were the original IP addresses before 28.04.2014.
# The following are the new IP addresses that are used starting 28.04.2014
FORTUMO_VALID_IP_LIST = FORTUMO_VALID_IP_LIST + ['54.72.6.126', '54.72.6.27', '54.72.6.17', '54.72.6.23', '79.125.125.1', '79.125.5.95', '79.125.5.205']




def fortumo_webapp_ipn(request):
  # Fortumo is an SMS payment provider that will call this function when a payment is received. 
  # Information about how to process the payment can be found at http://developers.fortumo.com/receipt-verification/
  # The code here is based on the PHP code in the example on the fortumo website.
  try:
    remoteip = os.environ['REMOTE_ADDR']
    if not remoteip in FORTUMO_VALID_IP_LIST:
      error_reporting.log_exception(logging.error, request=request, 
                                    error_message = "unauthorized remoteip %s is trying to access fortumo ipn" % remoteip)    
      return HttpResponse("Error - invalid IP")
      
    if not check_signature(request):
      error_reporting.log_exception(logging.error, request=request, error_message = "invalid fortumo signature")    
      return HttpResponse("Error - invalid Signature")
    
    txn_id = "fortumo-" + request.GET['payment_id']
    currency = request.GET['currency']
    amount_paid = request.GET['price']
    num_days_awarded = int(request.GET['amount'])
    payer_phone_number = request.GET['sender']
    payment_status = request.GET['status']
    nid = request.GET['cuid']
    uid = utils.get_uid_from_nid(nid)
    userobject = utils_top_level.get_object_from_string(uid)
    
    # only grant virtual credits to account, if payment has been successful.
    if (payment_status == 'completed' or payment_status == 'pending'):
      if check_payment_and_update_structures(userobject, currency, amount_paid, num_days_awarded, txn_id, "paypal", payer_phone_number, "NA"):
        logging.info("Successfully processed payment status: %s from user nid %s" % (payment_status, nid))
        update_userobject_vip_status("fortumo", userobject,  num_days_awarded, payer_phone_number)      
        
    elif (payment_status == 'failed'):
      status_message = '"failed" payment status for user nid %s %s' % (nid, userobject.username)
      logging.error(status_message)
      message_content = status_message      
      email_utils.send_admin_alert_email(message_content, subject="%s fortumo VIP failed payment status received" % settings.APP_NAME)
      
    else:
      raise Exception("Failed to award credits during fortumo IPN notification - check logs") 
    
    return HttpResponse("OK")
    
  except:
    message_content = "Failed to award VIP status for fortumo ipn call "
    email_utils.send_admin_alert_email(message_content, subject="%s Fortumo Error VIP" % settings.APP_NAME)
    error_reporting.log_exception(logging.critical, request=request, error_message = "Fortumo credits not awarded ")
        
    # Return "OK" even though we had a server error - this should stop fortumo from re-sending notifications of the
    # payment.
    return HttpResponse("OK")
    
    
    
def check_signature(request):
  secret = settings.fortumo_web_apps_secret
  keys_of_get = request.GET.keys()
  keys_of_get.sort()
  calculation_string = u''
  for key in keys_of_get:
    if key != "sig":
      calculation_string += "%s=%s" % (key, request.GET[key])
      
  calculation_string += secret
  #logging.info("calculation_string: %s" % calculation_string)
  sig = hashlib.md5(calculation_string.encode("utf-8")).hexdigest()
  return (request.GET['sig'] == sig)  

def check_payment_and_update_structures(userobject, currency, amount_paid, num_days_awarded, txn_id, payment_source, payer_account_info, last_name):
  
  # This stores information about the user that has made the payment. This is stored for informational purposes 
  # and to detect duplicate payment submissions with the same txn_id 
  # If the current txn_id is detected in the database, then we will return False otherwise return True
  # to indicate that this is a new/unique payment.
  
  # DO NOT wrap this in a try/except - we will let the outer blocks exception handlers deal with any exceptions
  # since they send notification email to the administrator.
  transaction_is_ok = False
      
  # make sure that the txn_id is not already stored in the database in order to prevent duplicate submissions
  query = models.PaymentInfo.gql("WHERE txn_id = :txn_id", txn_id = txn_id)
  if not query.get():
    logging.info("Storing IPN transaction ID %s" % txn_id)

    payment_object = models.PaymentInfo()
    payment_object.username = userobject.username
    payment_object.owner_userobject = userobject.key
    payment_object.amount_paid = float(amount_paid)
    payment_object.currency = currency
    payment_object.date_paid = datetime.datetime.now()
    payment_object.num_days_awarded = num_days_awarded
    payment_object.txn_id = txn_id
    payment_object.payment_source = payment_source
    payment_object.payer_account_info = payer_account_info
    payment_object.last_name = last_name
    transaction_is_ok = True

    payment_object.put()
  else:
    logging.error("Not processing IPN transaction ID %s since it is already stored" % txn_id)
  
  return transaction_is_ok


def get_new_vip_status_and_expiry(previous_expiry, num_days_awarded):

  # Compares the previous_paid_status, and the just_paid_status, and sets the new_paid_status to the higher of the two.
  # Also, either adds just_paid_extra_days to the previous_expiry, or just computes a new expiry_date if not available.
  # returns (new_paid_status, new_expiry_date)
  
  # initialize in case of error
  (just_paid_status, new_expiry_date) = (None, previous_expiry)
  
  try:
    assert(num_days_awarded > 0)
    
    just_paid_status = "%d days of VIP status added on %s" % (num_days_awarded, datetime.datetime.now())
    logging.info(just_paid_status)

    # store payment related information on the userobject.
  
    if previous_expiry <= datetime.datetime.now():
      # previous_paid_status has expired - so just assign the new values
      new_expiry_date = datetime.datetime.now() + datetime.timedelta(days = num_days_awarded) 
      
    else:
      # Need to take into account previously purchased credits, and add them to the newly acquired credits.
      new_expiry_date = previous_expiry + datetime.timedelta(days = num_days_awarded)  
        
  except:
    error_reporting.log_exception(logging.critical)
    
  return (just_paid_status, new_expiry_date)
  
  
def update_userobject_vip_status(payment_provider, userobject,  num_days_awarded, payer_account_info):

  # updates VIP status on the userobject to reflect the new num_days_awarded that have either
  # been purchased or awarded to the userobject profile. 
    
  # payer_account_info: in the case of paypal, this is the paypal-associated email address. 
  #                     for fortumo, this is the phone number that has made the payment. 
  message_content = ''
  try:
    
    previous_language = translation.get_language()# remember the original language, so we can set it back when we finish 
    lang_code = 'en'
    try:
      # Set translation language so that the generated profile description (title) is in english
      translation.activate(lang_code)      
   
      (userobject.client_paid_status, userobject.client_paid_status_expiry) = \
        get_new_vip_status_and_expiry(userobject.client_paid_status_expiry, num_days_awarded)
        
      utils.put_userobject(userobject)
      
      profile_href = "http://www.%(domain_name)s%(profile_href)s" % {
        'domain_name': settings.DOMAIN_NAME, 
        'profile_href' :  profile_utils.get_userprofile_href(lang_code, userobject),
      }      
        
      message_content = """<strong>VIP status awarded</strong><br><br>
      User: <a href="%(href)s">%(username)s</a><br>    
      App name: %(app_name)s<br>
      Payment provider: %(payment_provider)s<br>
      Payer account: %(payer_account_info)s<br>
      Description: %(description)s<br>
      Days awarded: %(num_days_awarded)s<br>
      Expiry date: %(expiry)s<br>
      Status: %(status)s<br>
      <br>
      ==========================================<br>
      <strong>Admin Stuff:</strong>
      %(admin_info)s<br>
      """ % {'app_name' : settings.APP_NAME, 
             'payment_provider' : payment_provider, 
             'payer_account_info' : payer_account_info,
             'username':  userobject.username, 
             'href' :  profile_href,
             'description' : profile_utils.get_base_userobject_title(lang_code, userobject.key.urlsafe()),
             'num_days_awarded' : num_days_awarded, 
             'expiry' : userobject.client_paid_status_expiry,
             'status' : userobject.client_paid_status,
             'admin_info' : utils.generate_profile_information_for_administrator(userobject, True),
             }
        
      email_utils.send_admin_alert_email(message_content, subject="%s %s VIP Awarded - Service: %s" % (settings.APP_NAME, userobject.username, payment_provider))
      messages.send_vip_congratulations_message(userobject)
        
    finally:
      translation.activate(previous_language)
        
    
  except:
    # This is a very serious error - someone has been awarded VIP status, but it was not stored correctly. 
    # This requires immediate investigation. Send an email to administrator. 
    error_reporting.log_exception(logging.critical)
    try: 
      # In case there is a problem with sending the error alert
      message_content = "Failed to award VIP status. See logs for error"
      email_utils.send_admin_alert_email(message_content, subject="%s VIP error - %s" % (settings.APP_NAME, payment_provider))
    except:
      error_reporting.log_exception(logging.critical)
      
  return message_content
    
    

def manually_give_paid_status(request, username, num_days_awarded, txn_id = None):
  
  try:
    num_days_awarded = int(num_days_awarded)
    
    q = UserModel.query()
    q = q.filter(UserModel.username == username.upper())
    userobject = q.get()

    if txn_id:
      # manually add in the txn_id if it is inclded
      currency = "NA - Manually Assigned"
      check_payment_and_update_structures(userobject, currency, num_days_awarded, 
                                          num_days_awarded, txn_id, "manually assigned", "NA - manually awarded", "NA - manually awarded")
    
    message_content = update_userobject_vip_status("manually awarded", userobject,  num_days_awarded, payer_account_info = "NA - manually awarded") 
    return http.HttpResponse(message_content)
  
  except:
    error_reporting.log_exception(logging.critical)
    return http.HttpResponseServerError("Error")
  
  
def manually_remove_paid_status(request, username):
  
  try:
    username = username.upper()
    q = UserModel.query()
    q = q.filter(UserModel.username == username)
    userobject = q.get()
    
    if userobject:
      
      userobject.client_paid_status_expiry = datetime.datetime.now()
      userobject.client_paid_status = None
      utils.put_userobject(userobject)
          
      return http.HttpResponse("Removed paid status from user: %s" % username)
    else:
      return http.HttpResponse("User %s does not exist - cannot remove paid status" % username)
  
  except:
    error_reporting.log_exception(logging.critical)
    return http.HttpResponseServerError("Error")
  

