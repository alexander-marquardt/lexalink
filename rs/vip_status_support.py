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
import error_reporting
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
      email = parameters['payer_email']
            
      userobject = utils_top_level.get_object_from_string(uid)

      if currency == 'EUR':
        num_credits_awarded = constants.client_paid_status_num_credits_awarded_for_euros[int(float(amount))]
      else:
        assert(0)
        
      update_userobject_vip_status(userobject,  num_credits_awarded, captcha_exempt = True)         
      store_payment_and_update_structures(userobject, currency, amount, num_credits_awarded, txn_id)
      return HttpResponse("OK")

  except:
    error_reporting.log_exception(logging.critical, request=request)

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
      
      #payment_object.client_paid_status = client_paid_status
      #payment_object.date_of_expiry = datetime.datetime.now() + datetime.timedelta(days = days_to_expiry)
      payment_object.put()
    else:
      logging.warning("Not processing IPN transaction ID %s since it is already stored" % txn_id)
    
  except:
    error_reporting.log_exception(logging.critical)
  
  return num_credits_awarded


def get_new_vip_status_and_expiry(previous_paid_status, previous_expiry, num_credits_to_apply):
  # this function relates to when we used to differentiate between differnt VIP status-levels. It can probably
  # be greatly simplified given that (now) the only difference is in the number of days that they have VIP status.
  
  # Compares the previous_paid_status, and the just_paid_status, and sets the new_paid_status to the higher of the two.
  # Also, either adds just_paid_extra_days to the previous_expiry, or just computes a new expiry_date if not available.
  # returns (new_paid_status, new_expiry_date)
  
  # initialize in case of error
  (new_paid_status, new_expiry_date) = (previous_paid_status, previous_expiry)
  
  try:
    if num_credits_to_apply > 0:
      
      # need to handle the case that the number of credits that are being cashed in exceed the number of status
      # levels that we have available. In this case, we give maximum status level, and just increase the number of
      # days until expiry.
      if num_credits_to_apply <= constants.reverse_lookup_client_paid_status_credit_amounts[constants.max_status_allowed]:
        just_paid_status = constants.client_paid_status_credit_amounts[num_credits_to_apply]
        just_paid_extra_days = constants.client_paid_status_number_of_days[just_paid_status]  
        logging.debug("1 just_paid_extra_days %s" % just_paid_extra_days)

      else:
        just_paid_status = constants.max_status_allowed
        credits_beyond_max = num_credits_to_apply - constants.reverse_lookup_client_paid_status_credit_amounts[constants.max_status_allowed]
        logging.debug("credits_beyond_max %s" % credits_beyond_max)
        days_beyond_max = (credits_beyond_max / constants.credits_required_for_each_level_beyond_max) * constants.days_awarded_for_each_level_beyond_max
        logging.debug("days_beyond_max %s" % days_beyond_max)
        just_paid_extra_days = constants.client_paid_status_number_of_days[just_paid_status]  + days_beyond_max
        logging.debug("2 just_paid_extra_days %s" % just_paid_extra_days)

    
      # store payment related information on the userobject.
      
      if previous_expiry <= datetime.datetime.now():
        # previous_paid_status has expired - so just assign the new values
        new_paid_status = just_paid_status
        new_expiry_date = datetime.datetime.now() + datetime.timedelta(days = just_paid_extra_days) 
        
      else:
        # If the just_paid_status is higher than the previous_paid_status
        # then set the new status to the just_paid_status, otherwise, the user keeps their old status and it's expiry is just extended. 
        # This provides an incentive for users to continue paying monthly quotas before their previous status expires.
                
        new_expiry_date = previous_expiry + datetime.timedelta(days = just_paid_extra_days)  
      
        if previous_paid_status:
          # make sure that previous_paid_status is not None, so that the following if statement can execute
          if constants.reverse_lookup_client_paid_status_credit_amounts[just_paid_status] > \
             constants.reverse_lookup_client_paid_status_credit_amounts[previous_paid_status]:
            # only if the new status is higher than the previous status should we update. 
            new_paid_status = just_paid_status
          else:
            # the just_paid_status is the same or lower than as the existing (previous) paid_status, and therefore we 
            # allow the user to keep their previous_paid_status value (which is better for the user)
            new_paid_status = previous_paid_status
            
        else: # this user did not have a previous paid_status, therefore we assign it the new value.
          new_paid_status = just_paid_status

  except:
    error_reporting.log_exception(logging.critical)
    
  return (new_paid_status, new_expiry_date)
  
  
def update_userobject_vip_status(userobject,  num_credits_to_apply, captcha_exempt = False):

  # updates VIP status on the userobject to reflect the new num_credits_to_apply that have either
  # been purchased or awarded to the userobject profile. 
    
  try:
    
    if userobject.client_is_exempt_from_spam_captchas == False:
      # if the client is already exempt (True) we don't want to overwrite it here - he will keep this status as long
      # as he maintains VIP status. After his status expires, this value will be cleared on his next login (in views.py).
      # This is principally designed to prevent people that were awarded VIP status just for signing up from being exempt
      # from having to solve captchas.
      userobject.client_is_exempt_from_spam_captchas = captcha_exempt

    (userobject.client_paid_status, userobject.client_paid_status_expiry) = \
      get_new_vip_status_and_expiry(userobject.client_paid_status, userobject.client_paid_status_expiry, 
                                    num_credits_to_apply)
    
    # clear and update the offsets for showing this user higher up in the search results.
    for k, v in constants.client_paid_status_number_of_days.iteritems():
        setattr(userobject.unique_last_login_offset_ref, "has_" + k + "_offset", False)
    setattr(userobject.unique_last_login_offset_ref, "has_" + userobject.client_paid_status + "_offset", True)
    userobject.unique_last_login_offset_ref.put()
    
    (userobject.unique_last_login, userobject.unique_last_login_offset_ref) = \
      login_utils.get_or_create_unique_last_login(userobject, userobject.username)
    
    utils.put_userobject(userobject)    
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

    update_userobject_vip_status(userobject,  num_credits) 
    
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
    
    login_utils.clear_diamond_status_from_unique_last_login_offset_ref(userobject.unique_last_login_offset_ref)
    
    return http_utils.ajax_compatible_http_response(request, "Done")
  
  except:
    error_reporting.log_exception(logging.critical)
    return http_utils.ajax_compatible_http_response(request, "Error", HttpResponseServerError)
  

