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


import logging
import settings
import urllib, urllib2
import re

from django.http import HttpResponse

import site_configuration

from rs import email_utils
from rs import error_reporting
from rs import vip_payments_common
from rs import utils, utils_top_level
from rs import vip_status_support

from rs.localization_files import currency_by_country


# keep track of which currencies we currently support.
vip_paypal_valid_currencies = ['EUR', 'USD', 'MXN', 'USD_NON_US']


if settings.TESTING_PAYPAL_SANDBOX:
  PP_URL = "https://www.sandbox.paypal.com/cgi-bin/webscr"
else:
  PP_URL = "https://www.paypal.com/cgi-bin/webscr"


custom_info_pattern = re.compile(r'site:(.*); username:(.*); nid:(.*);')

# generate the dictionary that will allow us to do a reverse lookup when we receive a payment amount
# to the corresponding membership category
vip_prices_with_currency_units = vip_payments_common.generate_prices_with_currency_units(
    vip_payments_common.vip_standard_membership_prices, vip_paypal_valid_currencies)
vip_price_to_membership_category_lookup  = vip_payments_common.generate_vip_price_to_membership_category_lookup(vip_payments_common.vip_standard_membership_prices)

def generate_paypal_radio_options(currency):
    # for efficiency don't call this from outside this module, instead perform a lookup in
    # paypal_radio_options
    generated_html = u''
    for member_category in vip_payments_common.vip_membership_categories:
        duration = u"%s" % vip_payments_common.vip_option_values[member_category]['duration']
        duration_units = u"%s" % vip_payments_common.vip_option_values[member_category]['duration_units']
        
        if member_category == vip_payments_common.SELECTED_VIP_DROPDOWN:
            selected = "checked"
        else:
            selected = ''

        generated_html += u"""<input type="radio" name="os0" value="%(duration)s %(duration_units)s" %(selected)s>
        <strong>%(duration)s %(duration_units)s</strong>: %(total_price)s<br>\n""" % {
            'duration': duration, 'duration_units' : duration_units, 
            'selected' : selected,                
            'total_price' : vip_prices_with_currency_units[currency][member_category]}
            
    return generated_html

def generate_paypal_options_hidden_fields(currency):
    
    # Paypal has a pretty obfuscated manner of passing values to their checkout page. 
    # First, an option_select[0-9] must be linked to a "value" that the user has selected
    # Then, the option_select[0-9] is intrinsically linked to an option_amount[0-9] (price), which allows  the 
    # selected value to pass a price to the paypal checkout page. 
    # Eg. In order to process a payment for 1 week (in spanish "1 semana"), we would have the following entries
    # <input type="radio" name="os0" value="1 semana">1 semana : $5.95   <-- defines the value "1 semana", and shows appropriate text to the user
    # <input type="hidden" name="option_select0" value="1 semana"> <-- link from "1 semana" to selector 0
    # <input type="hidden" name="option_amount0" value="5.95">     <-- link from selector 0 to the price of 5.95
    
    generated_html = ''
    counter = 0
    for member_category in vip_payments_common.vip_membership_categories:
        generated_html += u'<input type="hidden" name="option_select%d" value="%s %s">' % (
            counter, vip_payments_common.vip_option_values[member_category]['duration'], vip_payments_common.vip_option_values[member_category]['duration_units'])
        generated_html += u'<input type="hidden" name="option_amount%d" value="%s">' % (counter, vip_payments_common.vip_standard_membership_prices[currency][member_category])
        counter += 1
        
    return generated_html



def generate_paypal_data(request, username, owner_nid):

    # Get the ISO 3155-1 alpha-2 (2 Letter) country code, which we then use for a lookup of the
    # appropriate currency to display. If country code is missing, then we will display
    # prices for the value defined in vip_paypal_structures.DEFAULT_CURRENCY
    if not vip_payments_common.TESTING_COUNTRY:
        http_country_code = request.META.get('HTTP_X_APPENGINE_COUNTRY', None)
    else:
        error_reporting.log_exception(logging.error, error_message = "TESTING_COUNTRY is over-riding HTTP_X_APPENGINE_COUNTRY")
        http_country_code = vip_payments_common.TESTING_COUNTRY

    internal_currency_code = vip_payments_common.get_internal_currency_code(http_country_code, vip_paypal_valid_currencies)

    paypal_data = {}
    paypal_data['country_override'] = vip_payments_common.TESTING_COUNTRY
    paypal_data['country_code'] = http_country_code
    paypal_data['language'] = request.LANGUAGE_CODE
    paypal_data['testing_paypal_sandbox'] = site_configuration.TESTING_PAYPAL_SANDBOX
    paypal_data['owner_nid'] = owner_nid
    paypal_data['username'] = username
    paypal_data['currency_code'] = vip_payments_common.real_currency_codes[internal_currency_code]

    if not site_configuration.TESTING_PAYPAL_SANDBOX:
        paypal_data['paypal_account'] = site_configuration.PAYPAL_ACCOUNT
    else:
        paypal_data['paypal_account'] = site_configuration.PAYPAL_SANDBOX_ACCOUNT

    paypal_data['radio_options'] = generate_paypal_radio_options(internal_currency_code)
    paypal_data['options_hidden_fields'] = generate_paypal_options_hidden_fields(internal_currency_code)

    return paypal_data


def paypal_instant_payment_notification(request):
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
      last_name = parameters['last_name']

      # os0 is represented as option_selection1
      # We are not presently using this varible, but can use this in the future instead of looking up the membership
      # category based on the price.
      option_selected = parameters['option_selection1'] # this is language specific (ie. "1 year" in english "1 año" in spanish)


      uid = utils.get_uid_from_nid(nid)
      userobject = utils_top_level.get_object_from_string(uid)

      if currency in vip_paypal_valid_currencies:
        membership_category = vip_price_to_membership_category_lookup[currency][amount_paid]
        num_days_awarded = vip_payments_common.num_days_in_vip_membership_category[membership_category]
      else:
        raise Exception("Paypal currency %s not handled by code" % currency)

      if vip_status_support.check_payment_and_update_structures(userobject, currency, amount_paid, num_days_awarded, txn_id, "paypal", payer_email, last_name):
        # only process the payment if this is the first time we have seen this txn_id.
        vip_status_support.update_userobject_vip_status("paypal", userobject,  num_days_awarded, payer_email)

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