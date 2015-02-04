import logging
import binascii
import urllib
import hashlib
import string
import hmac
import math
from random import randint

from django.shortcuts import render_to_response
from django.utils.translation import ugettext
from django.utils import simplejson
from django import http

from google.appengine.ext import ndb

import site_configuration
import settings

from rs import email_utils
from rs import error_reporting
from rs import models
from rs import utils
from rs import utils_top_level
from rs import vip_payments_common
from rs import vip_status_support
from rs import vip_paysafe_soap_messages


# Leave the following value set to None if we are not trying to force a particular country's options to be displayed
TESTING_COUNTRY = 'ES'

vip_paysafecard_valid_currencies = ['EUR', 'USD', 'MXN', 'USD_NON_US']
vip_paysafecard_valid_currencies = ['EUR']

# The following are used for storing ints as a string, which will make them shorter. These correspond to paysafecard
# documentation, which states that only  A-Z, a-z, 0-9, -(hyphen) and _ (underline) are allowed. We use
# the hyphen for separating the different parts of the identifier, and so we do not put it into this string of
# allowed characters.
# We don't use "_" only for aesthetic reasons (I don't like the look of it in the transaction identifiers)
encode_allowed_chars = string.digits + string.letters
encode_dict = dict((c, i) for i, c in enumerate(encode_allowed_chars))


# The following definitions ensure that if we want for example a maximum of 6 characters to be returned from
# our random id postfix generator, then the 'largest' string generated will be 'ZZZZZZ'
number_of_encoded_chars_to_generate = 8
max_number_for_random_id_postfix = int(math.pow(len(encode_allowed_chars), number_of_encoded_chars_to_generate)) - 1
# Find the minimum number that will result in the specified number of digits (this is only for aesthetics, and
# is not really necessary, but it will result in each random number being the same number of digits in length)
min_number_for_random_id_postfix = utils.base_decode('1' + '0'*(number_of_encoded_chars_to_generate-1), encode_dict)

# we only send a portion of the hmac encoded digest as determined by hmac_num_chars
hmac_num_chars = 6

# During development, we are running from localhost which cannot recieve communications from the internet,
# therefore, just send the notifications to the server that we are using for debugging paysafecard transactions.
development_payment_notification_server = 'http://paysafecard.romancesapp.appspot.com/'

vip_paysafecard_prices_with_currency_units = vip_payments_common.generate_prices_with_currency_units(
    vip_payments_common.vip_standard_membership_prices, vip_paysafecard_valid_currencies)

if site_configuration.TESTING_PAYSAFECARD:
    username = site_configuration.PAYSAFE_SOAP_TEST_USERNAME
    password = site_configuration.PAYSAFE_SOAP_TEST_PASSWORD
    merchant_id = site_configuration.PAYSAFE_TEST_MID

else:
    username = site_configuration.PAYSAFE_SOAP_USERNAME
    password = site_configuration.PAYSAFE_SOAP_PASSWORD
    merchant_id = site_configuration.PAYSAFE_MID


def generate_paysafe_radio_options(currency):
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

        generated_html += u"""<input type="radio" name="amount" value="%(price)s" %(selected)s>
        <strong>%(duration)s %(duration_units)s</strong>: %(display_price)s<br>\n""" % {
            'duration': duration, 'duration_units' : duration_units,
            'selected' : selected,
            'price' : vip_payments_common.vip_standard_membership_prices[currency][member_category],
            'display_price' : vip_paysafecard_prices_with_currency_units[currency][member_category]}

    return generated_html

def generate_paysafecard_data(request, owner_nid):

    try:
        # Get the ISO 3155-1 alpha-2 (2 Letter) country code, which we then use for a lookup of the
        # appropriate currency to display. If country code is missing, then we will display
        # prices for the value defined in vip_paypal_structures.DEFAULT_CURRENCY
        if not TESTING_COUNTRY:
            http_country_code = request.META.get('HTTP_X_APPENGINE_COUNTRY', None)
        else:
            error_reporting.log_exception(logging.error, error_message = "TESTING_COUNTRY is over-riding HTTP_X_APPENGINE_COUNTRY")
            http_country_code = TESTING_COUNTRY


        if site_configuration.TESTING_PAYSAFECARD:
            paysafecard_customer_panel_url = settings.PAYSAFE_CUSTOMER_PANEL_TEST_URL
        else:
            paysafecard_customer_panel_url = settings.PAYSAFE_CUSTOMER_PANEL_URL

        internal_currency_code = vip_payments_common.get_internal_currency_code(http_country_code, vip_paysafecard_valid_currencies)

        paysafecard_data = {}
        paysafecard_data['owner_nid'] = owner_nid
        paysafecard_data['currency_code'] = vip_payments_common.real_currency_codes[internal_currency_code]
        paysafecard_data['country_override'] = TESTING_COUNTRY
        paysafecard_data['testing_paysafecard'] = site_configuration.TESTING_PAYSAFECARD
        paysafecard_data['radio_options'] = generate_paysafe_radio_options(internal_currency_code)
        paysafecard_data['paysafecard_customer_panel_url'] = paysafecard_customer_panel_url

        return paysafecard_data
    except:
        error_reporting.log_exception(logging.critical)
        return http.HttpResponseServerError('Error generating paysafecard data')

def generate_hmac(unique_id):
    hmac_digest = hmac.new(site_configuration.PAYSAFE_HMAC_KEY, unique_id, hashlib.sha256).digest()
    int_hash = int(binascii.b2a_hex(hmac_digest), 16)
    string_hash = utils.base_encode(int_hash, base=encode_allowed_chars)
    # We need to shorten the hash because paysafecard doesn't accept more than 60 characters, and recommends
    # no more than 20 (which we will be over)
    short_hash = string_hash[:hmac_num_chars]
    return short_hash

def get_random_number_string_for_transaction_id():
    rand = randint(min_number_for_random_id_postfix, max_number_for_random_id_postfix)
    encoded_rand = utils.base_encode(rand, base=encode_allowed_chars)
    return encoded_rand

def create_disposition(request):

    try:

        # Note: do not pull the nid from the request, since this page may be shown on the logout when then user has
        # already closed their session. Doing this gives us one last chance to get them to signup for a VIP membership.
        owner_nid = request.POST.get('owner_nid', None); assert(owner_nid)
        user_key = ndb.Key('UserModel', long(owner_nid))

        if request.method != 'POST':
            error_message = "create_disposition was not called with POST data"
            error_reporting.log_exception(logging.critical, error_message = error_message)
            return http.HttpResponseBadRequest(error_message)


        amount = request.POST.get('amount', None); assert(amount)
        currency_code = request.POST.get('currency_code', None); assert(currency_code)

        if currency_code in vip_paysafecard_valid_currencies:
            membership_category = vip_payments_common.vip_price_to_membership_category_lookup[currency_code][amount]
            num_days_to_be_awarded = vip_payments_common.num_days_in_vip_membership_category[membership_category]
        else:
            raise Exception("Paysafecard currency %s not handled by code" % currency_code)

        if site_configuration.DEVELOPMENT_SERVER:
            # Give "real" URLs so that we can check if payment notifications are being received.
            pn_url = urllib.quote(development_payment_notification_server + '/paysafecard/payment_notification/', '')
        else:
            pn_url = urllib.quote('http://%s/paysafecard/payment_notification/' % request.META['HTTP_HOST'], '')

        ok_url = urllib.quote('http://%s/paysafecard/ok_url/' % request.META['HTTP_HOST'], '')
        nok_url = urllib.quote('http://%s/paysafecard/nok_url/' % request.META['HTTP_HOST'], '')

        random_postfix = get_random_number_string_for_transaction_id()
        unique_id = str(owner_nid) + '-' + random_postfix
        hmac_signature = generate_hmac(unique_id)
        merchant_transaction_id = unique_id + '-' + hmac_signature

        paysafecard_disposition_response = vip_paysafe_soap_messages.create_disposition(
            username,
            password,
            merchant_transaction_id,
            amount,
            currency_code,
            ok_url,
            nok_url,
            owner_nid,
            pn_url)

        logging.info('paysafecard_disposition_response: %s'  % repr(paysafecard_disposition_response))

        assert(int(paysafecard_disposition_response['errorCode']) == 0)
        assert(int(paysafecard_disposition_response['resultCode']) == 0)
        assert(paysafecard_disposition_response['mid'] == merchant_id)
        assert(paysafecard_disposition_response['mtid'] == merchant_transaction_id)

        # It appears that the disposition was created without any issues - therefore write it to the database
        paysafecard_disposition = models.PaysafecardDisposition(
            id=merchant_transaction_id,
            transaction_amount = amount,
            transaction_currency = currency_code,
            membership_category = membership_category,
            num_days_to_be_awarded = num_days_to_be_awarded,
            owner_userobject = user_key)

        paysafecard_disposition.put()

        response_dict = {
            'merchant_id' : merchant_id,
            'merchant_transaction_id': merchant_transaction_id,
            'currency_code': currency_code,
            'amount': amount
        }

        json_response = simplejson.dumps(response_dict)
        return http.HttpResponse(json_response, mimetype='text/javascript')

    except:
        try:
            # This is serious enough, that it warrants sending an email to the administrator.
            message_content = """Paysafecard error - unable to create disposition"""
            email_utils.send_admin_alert_email(message_content, subject = "%s Paysafe Error" % settings.APP_NAME)

        finally:
            error_reporting.log_exception(logging.critical, request=request)
            return http.HttpResponseServerError('Error in create_disposition')



def payment_notification(request):

    # After the client eneters their paysafecard information and transmits it toe paysafecard's servers, we will
    # receive a notification indicating the transaction ID, the amount received, and other information. If the client
    # pays in a currency other than the billing currency, then currency conversions are done by paysafecard, and we
    # therefore cannot look at the payment amount to figure out exactly which VIP status to award to the user.
    # For this reason, we must look up the transaction using the merchant_transaction_id to determine what
    # to award to the user. If the merchant_transaction_id is not found in our database, then this may be
    # a fraudulent attempt to get free VIP status.
    try:

        error_message = ''
        if request.method != 'POST':
            error_message = "payment_notification was not called with POST data"
            error_reporting.log_exception(logging.critical, error_message = error_message)
            return http.HttpResponseBadRequest(error_message)

        logging.info('request = %s ' % repr(request))
        merchant_transaction_id = request.POST.get('mtid', None); assert(merchant_transaction_id)
        event_type = request.POST.get('eventType', None); assert(event_type == 'ASSIGN_CARDS')

        # Make sure that the merchant transaction is signed correctly so that we know that it was initiated from
        # our servers. This will prevent someone from sending fraudulent payment notifications to our server, as they
        # would need our hmac key to generate the correct signature
        (nid_str, random_postfix, original_hmac_signature) = merchant_transaction_id.split('-')
        unique_id = nid_str + '-' + random_postfix
        verify_hmac_signature = generate_hmac(unique_id)
        assert(verify_hmac_signature == original_hmac_signature)

        nid = long(nid_str)

        # Note: serial_numbers is actually made up of 4 values seperated by ';' that may be repeated multiple times
        # in the case that more than one card was used to make the payment. eg. a payment from a single card would
        # be SerialNumber;CurrencyCode;Amount;CardTypeId - a payment from two cards would be
        # SerialNumber1;CurrencyCode1;Amount1;CardTypeId1;SerialNumber2;CurrencyCode2;Amount2;CardTypeId2 etc.
        serial_numbers = request.POST.get('serialNumbers', None); assert(serial_numbers)

        uid = utils.get_uid_from_nid(nid)
        userobject = utils_top_level.get_object_from_string(uid)


        paysafe_disposition = models.PaysafecardDisposition.get_by_id(merchant_transaction_id)
        if paysafe_disposition:
            if not paysafe_disposition.transaction_completed:


                paysafecard_debit_response = vip_paysafe_soap_messages.execute_debit(
                    username,
                    password,
                    merchant_transaction_id,
                    paysafe_disposition.transaction_amount,
                    paysafe_disposition.transaction_currency,
                    1  # Close transaction
                )

                logging.info('paysafecard_debit_response: %s' % repr(paysafecard_debit_response))

                assert(int(paysafecard_debit_response['errorCode']) == 0)
                assert(int(paysafecard_debit_response['resultCode']) == 0)

                paysafe_disposition.transaction_completed = True
                paysafe_disposition.serial_numbers = serial_numbers
                paysafe_disposition.put()

                # The following check for a transaction_id is redundant since we have already checked, however this
                # function call also sets up the common structure that keeps track of what payments have been made
                # and from which payment provider (eg. common for both paypal and paysafecard)
                if vip_status_support.check_payment_and_update_structures(
                        userobject,
                        paysafe_disposition.transaction_currency,
                        paysafe_disposition.transaction_amount,
                        paysafe_disposition.num_days_to_be_awarded,
                        merchant_transaction_id,
                        "paysafecard",
                        serial_numbers,
                        "Last name not available"):

                    vip_status_support.update_userobject_vip_status("paysafecard", userobject,  paysafe_disposition.num_days_to_be_awarded, serial_numbers)

            else:
                error_message = 'Paysafecard merchant_transaction_id: %s is already complete - why is it executing again?' % merchant_transaction_id
        else:
            # if someone calls this URL without us having first created an associated disposition.
            error_message = 'Paysafecard - could not find disposition for merchant_transaction_id: %s' % merchant_transaction_id

        transaction_info = 'merchant_transaction_id: %s serial_numbers: %s event_type: %s' % (merchant_transaction_id, serial_numbers, event_type)
        if error_message:
            # Note that for these errors, we will still fall through to the HttpResponse("OK"), since we don't want
            # paysafecard to send them multiple times.
            error_message = error_message + '\n' + transaction_info
            error_reporting.log_exception(logging.critical, error_message=error_message)
            email_utils.send_admin_alert_email(error_message, subject = "%s Paysafe Error" % settings.APP_NAME)

        logging.info(transaction_info)
        return http.HttpResponse("OK")

    except:
        try:
            # This is serious enough, that it warrants sending an email to the administrator.
            message_content = """Paysafecard error - unable to process payment notification"""
            email_utils.send_admin_alert_email(message_content, subject = "%s Paysafe Error" % settings.APP_NAME)

        finally:
            error_reporting.log_exception(logging.critical, request=request)
            return http.HttpResponseServerError('Error in payment_notification')



def transaction_ok(request):

    message_to_display = ugettext("Congratulations. Your payment has been assigned.  We will now debit your card, "
                                  "and you will receive a message in a few moments confirming your VIP status.")

    http_response = render_to_response('user_main_helpers/paysafecard_transaction_status.html', {
        'message_to_display': message_to_display,
        })
    return http_response

def transaction_nok(request):
    message_to_display = ugettext("Sorry, we were unable to process your payment. "
                                  "You card will not be charged, and VIP status has not been awarded.")
    http_response = render_to_response('user_main_helpers/paysafecard_transaction_status.html', {
        'message_to_display': message_to_display,
        })
    return http_response