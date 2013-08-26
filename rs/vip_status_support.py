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


import os 
import urllib, urllib2
import logging
import error_reporting, email_utils
import settings, constants, models, login_utils, utils_top_level, utils, store_data, messages, vip_paypal_structures
import datetime, re
from models import UserModel
from localization_files import currency_by_country
import views, http_utils, hashlib


from django.http import HttpResponse, HttpResponseServerError, HttpResponseRedirect

if settings.TESTING_PAYPAL_SANDBOX:
  PP_URL = "https://www.sandbox.paypal.com/cgi-bin/webscr"
else:
  PP_URL = "https://www.paypal.com/cgi-bin/webscr"
  
FORTUMO_VALID_IP_LIST = ['79.125.125.1', '79.125.5.205', '79.125.5.95']

custom_info_pattern = re.compile(r'site:(.*); username:(.*); nid:(.*);')  
  
def instant_payment_notification(request):
  parameters = None
  payment_status = None

  try:
    logging.info("Received payment notification from paypal")

    # Note: apparently PayPal can send a Pending status while waiting for authorization, and then later a Completed
    # payment_status -- but I believe that in both cases, it expects a confirmation of the message to be send
    # back
    payment_status = request.REQUEST.get('payment_status', None) # Completed or Pending are the most interesting .. but there are others as well
    status = None
    
    if request.POST:
      parameters = request.POST.copy()
    else:
      parameters = request.GET.copy()

    logging.info("parameters %s" % repr(parameters))

    if parameters:
      
      parameters['cmd']='_notify-validate'
      
      # parameters['charset'] tells us the type of encoding that was used for the characters. We
      # must encode the response to use the same encoding as the request.
      charset = parameters['charset']
      logging.info("charset = %s" % charset)
      #params_decoded = dict([k, v.decode(charset)] for k, v in parameters.items())
      params_urlencoded = urllib.urlencode(dict([k, v.encode('utf-8')] for k, v in parameters.items()))     

      #params_urlencoded = urllib.urlencode(parameters)
      req = urllib2.Request(PP_URL, params_urlencoded)
      req.add_header("Content-type", "application/x-www-form-urlencoded")
      logging.info("request response: %s" % repr(req))
      response = urllib2.urlopen(req)
      status = response.read()
      if not status == "VERIFIED":
        logging.error("The request could not be verified, check for fraud. Status:" + str(status))
        parameters = None
      else:
        logging.info("Payment status: %s" % status)

    if status == "VERIFIED":
      custom = parameters['custom']
      match_custom = custom_info_pattern.match(custom)
      if match_custom:
        nid = match_custom.group(3)
      else:
        raise Exception("Paypal custom value does not match expected format: %s" % custom)
      
      #logging.info("Paypal parameters: %s" % parameters)
      
      donation_type = parameters['item_number']
      txn_id = "paypal-" + parameters['txn_id']
      currency = parameters['mc_currency']
      amount_paid = parameters['mc_gross']
      payer_email = parameters['payer_email']
      
      # os0 is represented as option_selection1
      # We are not presently using this varible, but can use this in the future instead of looking up the membership
      # category based on the price.
      option_selected = parameters['option_selection1'] # this is language specific (ie. "1 year" in english "1 año" in spanish)

            
      uid = utils.get_uid_from_nid(nid)
      userobject = utils_top_level.get_object_from_string(uid)

      if currency in vip_paypal_structures.paypal_valid_currencies:
        membership_category = vip_paypal_structures.vip_price_to_membership_category_lookup[currency][amount_paid]
        num_days_awarded = vip_paypal_structures.num_days_in_vip_membership_category[membership_category]
      else:
        raise Exception("Paypal currency %s not handled by code" % currency)
        
      if check_payment_and_update_structures(userobject, currency, amount_paid, num_days_awarded, txn_id, "paypal"):
        # only process the payment if this is the first time we have seen this txn_id.
        update_userobject_vip_status("paypal", userobject,  num_days_awarded, payer_email)         
        
      return HttpResponse("OK")
    else:
      raise Exception("Paypal transaction status is %s" % (status))


  except:
    error_reporting.log_exception(logging.critical, request=request)
    
    try:
      # This is serious enough, that it warrants sending an email to the administrator. We don't include any extra
      # information such as username, or email address, since these values might not be available, and could cause the 
      # message to trigger an exception
      message_content = """Paypal error - User not awarded VIP status - check paypal to see who has sent funds and
      check if status is correctly set"""
      email_utils.send_admin_alert_email(message_content, subject = "%s Paypal Error" % settings.APP_NAME)
    except:
      error_reporting.log_exception(logging.critical)

    # Return "OK" even though we had a server error - this will stop paypal from re-sending notifications of the
    # payment.
    return HttpResponse("OK")

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
      if check_payment_and_update_structures(userobject, currency, amount_paid, num_days_awarded, txn_id, "paypal"):
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
    error_reporting.log_exception(logging.critical, request=request, error_message = "Fortumo credits not awarted ")
        
    # Return "OK" even though we had a server error - this should stop fortumo from re-sending notifications of the
    # payment.
    return HttpResponse("OK")
    
    
    
def check_signature(request):
  secret = settings.fortumo_web_apps_secret
  keys_of_get = request.GET.keys()
  keys_of_get.sort()
  calculation_string = ''
  for key in keys_of_get:
    if key != "sig":
      calculation_string += "%s=%s" % (key, request.GET[key])
      
  calculation_string += secret
  #logging.info("calculation_string: %s" % calculation_string)
  sig = hashlib.md5(calculation_string).hexdigest()
  return (request.GET['sig'] == sig)  

def check_payment_and_update_structures(userobject, currency, amount_paid, num_days_awarded, txn_id, payment_source):
  
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
  try:
    

    (userobject.client_paid_status, userobject.client_paid_status_expiry) = \
      get_new_vip_status_and_expiry(userobject.client_paid_status_expiry, num_days_awarded)
    
    utils.put_userobject(userobject)
    
    message_content = """VIP status awarded:<br>
    App name: %(app_name)s<br>
    Payment Provider: %(payment_provider)s<br>
    Payer Account: %(payer_account_info)s<br>
    User: %(username)s (%(email_address)s)<br>
    Days purchased: %(num_days_awarded)s<br>
    Expiry date: %(expiry)s<br>
    Status: %(status)s<br>
    """ % {'app_name' : settings.APP_NAME, 
           'payment_provider' : payment_provider, 
           'payer_account_info' : payer_account_info,
           'username':  userobject.username, 
           'email_address' : userobject.email_address,
           'num_days_awarded' : num_days_awarded, 
           'expiry' : userobject.client_paid_status_expiry,
           'status' : userobject.client_paid_status}
    
    email_utils.send_admin_alert_email(message_content, subject="%s %s VIP Awarded - %s" % (settings.APP_NAME, userobject.username, payment_provider))
    messages.send_vip_congratulations_message(userobject)
    
  except:
    # This is a very serious error - someone has been awarded VIP status, but it was not stored correctly. 
    # This requires immediate investigation. Send an email to administrator. 
    error_reporting.log_exception(logging.critical)
    try: 
      # In case there is a problem with sending the error alert
      message_content = "Failed to award VIP status. See logs for error"
      email_utils.send_admin_alert_email(message_content, subject="%s Paypal Error VIP" % settings.APP_NAME)
    except:
      error_reporting.log_exception(logging.critical)
      
    
    

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
                                          num_days_awarded, txn_id, "manually assigned")
    
    update_userobject_vip_status("manually awarded", userobject,  num_days_awarded, payer_account_info = "N/A - manually awarded") 
    return http_utils.ajax_compatible_http_response(request, "Done")
  
  except:
    error_reporting.log_exception(logging.critical)
    return http_utils.ajax_compatible_http_response(request, "Error", HttpResponseServerError)
  
  
def manually_remove_paid_status(request, username):
  
  try:
    q = UserModel.query()
    q = q.filter(UserModel.username == username.upper())
    userobject = q.get()
    
    userobject.client_paid_status_expiry = datetime.datetime.now()
    userobject.client_paid_status = None
    utils.put_userobject(userobject)
        
    return http_utils.ajax_compatible_http_response(request, "Done")
  
  except:
    error_reporting.log_exception(logging.critical)
    return http_utils.ajax_compatible_http_response(request, "Error", HttpResponseServerError)
  

