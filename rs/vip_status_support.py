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


import urllib
import urllib2
import logging
import error_reporting, email_utils
import settings, constants, models, login_utils, utils_top_level, utils, store_data
import datetime
from models import UserModel
import views, http_utils


from django.http import HttpResponse, HttpResponseServerError, HttpResponseRedirect

if settings.TESTING_PAYPAL_SANDBOX:
  PP_URL = "https://www.sandbox.paypal.com/cgi-bin/webscr"
else:
  PP_URL = "https://www.paypal.com/cgi-bin/webscr"



def instant_payment_notification_default(request):
  # since the default IPN URL that we entered into PayPal only allowed us to enter in a single domain
  # we must dynamically set the IPN URL for all transactions. If this default URL is ever hit, then
  # this is an error.
  logging.critical("The default IPN URL should never be called - check what is happening with PayPal")
  return HttpResponseServerError("Error")
  
def instant_payment_notification(request):
  parameters = None
  payment_status = None

  try:
    logging.info("Received payment notification from paypal")

    # Note: apparently PayPal can send a Pending status while waiting for authorization, and then later a Completed
    # payment_status -- but I believe that in both cases, it expects a confirmation of the message to be send
    # back
    payment_status = request.REQUEST.get('payment_status', None) # Completed or Pending are the most interesting .. but there are others as well
    
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
      uid = parameters['custom']
      donation_type = parameters['item_number']
      txn_id = parameters['txn_id']
      currency = parameters['mc_currency']
      amount = parameters['mc_gross']
      payer_email = parameters['payer_email']
            
      userobject = utils_top_level.get_object_from_string(uid)

      if currency == 'EUR':
        num_credits_awarded = constants.client_paid_status_num_credits_awarded_for_euros[int(float(amount))]
      else:
        assert(0)
        
      update_userobject_vip_status(userobject,  num_credits_awarded, payer_email)         
      store_payment_and_update_structures(userobject, currency, amount, num_credits_awarded, txn_id)
      return HttpResponse("OK")

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

  return HttpResponseServerError("Error")


#def test_store_payment_and_update_structures(request, username, txn_id):
  ## just a temporary function for verifying that store_payment_and_update_structures works.
  
  #query_filter_dict = {}    
  #query_filter_dict['username'] = username.upper()

  #query = UserModel.all()
  #for (query_filter_key, query_filter_value) in query_filter_dict.iteritems():
      #query = query.filter(query_filter_key, query_filter_value)
  #userobject = query.get()
  
  #if userobject:
    #store_payment_and_update_structures(userobject, 'EUR', 10, txn_id)
  #else:
    #logging.error("userobject for %s not found"  % username)
    
  #return HttpResponse("OK")

def store_payment_and_update_structures(userobject, currency, amount, num_credits_awarded, txn_id):
  
  # This stores information about the user that has made the payment. This is stored for informational purposes.
  
  try:
   
    amount_paid_times_100 = int(float(amount) * 100)
     
    # make sure that the txn_id is not already stored in the database in order to prevent duplicate submissions
    query = models.PaymentInfo.gql("WHERE txn_id = :txn_id", txn_id = txn_id)
    if not query.get():
      logging.info("Storing IPN transaction ID %s" % txn_id)

      payment_object = models.PaymentInfo()
      payment_object.username = userobject.username
      payment_object.owner_userobject = userobject
      payment_object.amount_paid_times_100 = amount_paid_times_100
      payment_object.date_paid = datetime.datetime.now()
      payment_object.num_credits_awarded = num_credits_awarded
      payment_object.txn_id = txn_id

      payment_object.put()
    else:
      logging.warning("Not processing IPN transaction ID %s since it is already stored" % txn_id)
    
  except:
    error_reporting.log_exception(logging.critical)
  
  return num_credits_awarded


def get_new_vip_status_and_expiry(previous_expiry, num_credits_to_apply):

  # Compares the previous_paid_status, and the just_paid_status, and sets the new_paid_status to the higher of the two.
  # Also, either adds just_paid_extra_days to the previous_expiry, or just computes a new expiry_date if not available.
  # returns (new_paid_status, new_expiry_date)
  
  # initialize in case of error
  (just_paid_status, new_expiry_date) = (None, previous_expiry)
  
  try:
    if num_credits_to_apply > 0:
      
      just_paid_extra_days = constants.client_paid_status_credit_amounts[num_credits_to_apply]  
      just_paid_status = "%d credits (%d days) applied on %s" % (num_credits_to_apply, just_paid_extra_days, datetime.datetime.now())
      logging.info(just_paid_status)

      # store payment related information on the userobject.
    
      if previous_expiry <= datetime.datetime.now():
        # previous_paid_status has expired - so just assign the new values
        new_expiry_date = datetime.datetime.now() + datetime.timedelta(days = just_paid_extra_days) 
        
      else:
        # Need to take into account previously purchased credits, and add them to the newly acquired credits.
        new_expiry_date = previous_expiry + datetime.timedelta(days = just_paid_extra_days)  
        
  except:
    error_reporting.log_exception(logging.critical)
    
  return (just_paid_status, new_expiry_date)
  
  
def update_userobject_vip_status(userobject,  num_credits_to_apply, payer_email):

  # updates VIP status on the userobject to reflect the new num_credits_to_apply that have either
  # been purchased or awarded to the userobject profile. 
    
  try:
    
    userobject.client_is_exempt_from_spam_captchas = True

    (userobject.client_paid_status, userobject.client_paid_status_expiry) = \
      get_new_vip_status_and_expiry(userobject.client_paid_status_expiry, num_credits_to_apply)
    
    utils.put_userobject(userobject)
    
    message_content = """VIP status awarded:<br>
    App name: %(app_name)s<br>
    Payer email: %(payer_email)s<br>
    User: %(username)s (%(email_address)s)<br>
    Credits applied: %(num_credits)s<br>
    Expiry date: %(expiry)s<br>
    Status: %(status)s<br>
    """ % {'app_name' : settings.APP_NAME, 
           'payer_email' : payer_email,
           'username':  userobject.username, 
           'email_address' : userobject.email_address,
           'num_credits' : num_credits_to_apply, 
           'expiry' : userobject.client_paid_status_expiry,
           'status' : userobject.client_paid_status}
    
    email_utils.send_admin_alert_email(message_content, subject="%s VIP Awarded" % settings.APP_NAME)
    
  except:
    error_reporting.log_exception(logging.critical) 
    

def manually_give_paid_status(request, username, num_credits):
  
  try:
    num_credits = int(num_credits)
    
    query_filter_dict = {}    
    query_filter_dict['username'] = username.upper()
    query_filter_dict['is_real_user'] = True

    query = UserModel.all()
    for (query_filter_key, query_filter_value) in query_filter_dict.iteritems():
        query = query.filter(query_filter_key, query_filter_value)
    userobject = query.get()

    update_userobject_vip_status(userobject,  num_credits, payer_email = "N/A - manually awarded") 
    
    return http_utils.ajax_compatible_http_response(request, "Done")
  
  except:
    error_reporting.log_exception(logging.critical)
    return http_utils.ajax_compatible_http_response(request, "Error", HttpResponseServerError)
  
  
def manually_remove_paid_status(request, username):
  
  try:
    query_filter_dict = {}    
    query_filter_dict['username'] = username.upper()
    query_filter_dict['is_real_user'] = True
  
    query = UserModel.all()
    for (query_filter_key, query_filter_value) in query_filter_dict.iteritems():
        query = query.filter(query_filter_key, query_filter_value)
    userobject = query.get()
    
    userobject.client_paid_status_expiry = datetime.datetime.now()
    userobject.client_paid_status = None
    utils.put_userobject(userobject)
        
    return http_utils.ajax_compatible_http_response(request, "Done")
  
  except:
    error_reporting.log_exception(logging.critical)
    return http_utils.ajax_compatible_http_response(request, "Error", HttpResponseServerError)
  

