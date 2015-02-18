import logging
import urllib
import string
import math
import json
import time
from random import randint

from django.shortcuts import render_to_response
from django.utils.translation import ugettext
from django import http

from google.appengine.ext import ndb

import site_configuration
import settings

from rs import constants
from rs import email_utils
from rs import error_reporting
from rs import models
from rs import utils
from rs import utils_top_level
from rs import vip_payments_common
from rs import vip_status_support
from rs import vip_paysafe_soap_messages

if settings.ENABLE_PAYSAFECARD:
    # Declar all countries tha paysafecard is supported. Use a set literal for lookup efficiency
    vip_paysafe_card_valid_countries = {
        'AR', # Argentina
        'AU', # Australia
        'AT', # Austria
        'BE', # Belgium
        'BG', # Bulgaria
        'CA', # Canada
        'HR', # Croatia
        'CY', # Cyprus
        'CZ', # Czech Republic
        'DK', # Denmark
        'FI', # Finland
        'FR', # France
        'DE', # Germany
        'GR', # Greece
        'HU', # Hungary
        'IE', # Ireland
        'IT', # Italy
        'LV', # Latvia
        'LT', # Lithuania
        'LU', # Luxembourg
        'MT', # Malta
        'MX', # Mexico
        'NL', # Netherlands
        'NO', # Norway
        'PE', # Peru
        'PL', # Poland
        'PT', # Portugal
        'RO', # Romania
        'SK', # Slovakia
        'SI', # Slovenia
        'ES', # Spain
        'SE', # Sweeden
        'CH', # Switzerland
        'TR', # Turkey
        'GB', # United Kingdom
        'US', # United States
        'UY', # Uruguay
    }
else:
    # Temporariliy remove display of paysafecard payment, while we are waiting for authorization from them
    vip_paysafe_card_valid_countries = {}

vip_paysafecard_valid_currencies = ['EUR']#, 'USD', 'MXN', 'USD_NON_US']
VIP_DEFAULT_CURRENCY = 'EUR' # Temporarily, we only support Euros - we are waiting for authorization for USD and MXN

# The following are used for storing ints as a string, which will make them shorter. These correspond to paysafecard
# documentation, which states that only  A-Z, a-z, 0-9, -(hyphen) and _ (underline) are allowed. We use
# the hyphen for separating the different parts of the identifier, and so we do not put it into this string of
# allowed characters.
# We don't use "_" only for aesthetic reasons (I don't like the look of it in the transaction identifiers)
encode_allowed_chars = string.digits + string.letters
encode_dict = dict((c, i) for i, c in enumerate(encode_allowed_chars))


# The following definitions ensure that if we want for example a maximum of 6 characters to be returned from
# our random id postfix generator, then the 'largest' string generated will be 'ZZZZZZ'
number_of_encoded_chars_to_generate = 5
max_number_for_random_id_postfix = int(math.pow(len(encode_allowed_chars), number_of_encoded_chars_to_generate)) - 1
# Find the minimum number that will result in the specified number of digits (this is only for aesthetics, and
# is not really necessary, but it will result in each random number being the same number of digits in length)
min_number_for_random_id_postfix = utils.base_decode('1' + '0'*(number_of_encoded_chars_to_generate-1), encode_dict)

# During development, we are running from localhost which cannot recieve communications from the internet,
# therefore, just send the notifications to the server that we are using for debugging paysafecard transactions.
development_payment_notification_server = 'http://paysafecard.romancesapp.appspot.com/'

vip_standard_paysafecard_prices_with_currency_units = vip_payments_common.generate_prices_with_currency_units(
    vip_payments_common.vip_standard_membership_prices, vip_paysafecard_valid_currencies)

vip_discounted_paysafecard_prices_with_currency_units = vip_payments_common.generate_prices_with_currency_units(
    vip_payments_common.vip_discounted_membership_prices, vip_paysafecard_valid_currencies)

vip_discounted_paysafe_prices_percentage_savings = vip_payments_common.compute_savings_percentage_discount(
    vip_payments_common.vip_discounted_membership_prices, vip_payments_common.vip_standard_membership_prices, vip_paysafecard_valid_currencies)

if site_configuration.TESTING_PAYSAFECARD:
    username = site_configuration.PAYSAFE_SOAP_TEST_USERNAME
    password = site_configuration.PAYSAFE_SOAP_TEST_PASSWORD
    merchant_id = site_configuration.PAYSAFE_TEST_MID

else:
    username = site_configuration.PAYSAFE_SOAP_USERNAME
    password = site_configuration.PAYSAFE_SOAP_PASSWORD
    merchant_id = site_configuration.PAYSAFE_MID


def generate_paysafe_radio_options(currency, membership_prices, prices_with_currency_units, original_prices_with_currency_units = []):
    # for efficiency don't call this from outside this module, instead perform a lookup in
    # paypal_radio_options
    generated_html = u''
    for member_category in vip_payments_common.vip_membership_categories:
        duration = u"%s" % vip_payments_common.vip_option_values[member_category]['duration']
        duration_units = u"%s" % vip_payments_common.vip_option_values[member_category]['duration_units']

        if member_category == vip_payments_common.DEFAULT_SELECTED_VIP_OPTION:
            selected = "checked"
        else:
            selected = ''

        savings_html = vip_payments_common.get_html_showing_savings(currency, member_category, vip_discounted_paysafe_prices_percentage_savings, original_prices_with_currency_units)

        generated_html += u"""<input type="radio" name="amount" value="%(price)s" %(selected)s>
        <strong>%(duration)s %(duration_units)s</strong>: %(display_price)s  %(savings_html)s<br>\n""" % {
            'duration': duration, 'duration_units' : duration_units,
            'selected' : selected,
            'price' : membership_prices[currency][member_category],
            'savings_html': savings_html,
            'display_price' : prices_with_currency_units[currency][member_category]}

    return generated_html

def generate_paysafecard_data(http_country_code, user_has_discount):

    try:
        paysafecard_data = {}

        if http_country_code not in vip_paysafe_card_valid_countries:
            paysafecard_data['paysafecard_supported_country'] = False
        else:
            paysafecard_data['paysafecard_supported_country'] = True
            if site_configuration.TESTING_PAYSAFECARD:
                paysafecard_customer_panel_url = settings.PAYSAFE_CUSTOMER_PANEL_TEST_URL
            else:
                paysafecard_customer_panel_url = settings.PAYSAFE_CUSTOMER_PANEL_URL

            internal_currency_code = vip_payments_common.get_internal_currency_code(http_country_code, vip_paysafecard_valid_currencies, VIP_DEFAULT_CURRENCY)

            paysafecard_data['currency_code'] = vip_payments_common.real_currency_codes[internal_currency_code]
            paysafecard_data['testing_paysafecard'] = site_configuration.TESTING_PAYSAFECARD

            if user_has_discount:
                paysafecard_data['radio_options'] = generate_paysafe_radio_options(
                    internal_currency_code, vip_payments_common.vip_discounted_membership_prices,
                    vip_discounted_paysafecard_prices_with_currency_units, vip_standard_paysafecard_prices_with_currency_units, )
            else:
                paysafecard_data['radio_options'] = generate_paysafe_radio_options(
                    internal_currency_code, vip_payments_common.vip_standard_membership_prices,
                    vip_standard_paysafecard_prices_with_currency_units )

            paysafecard_data['paysafecard_customer_panel_url'] = paysafecard_customer_panel_url

        return paysafecard_data
    except:
        error_reporting.log_exception(logging.critical)
        return http.HttpResponseServerError('Error generating paysafecard data')

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

        userobject = utils_top_level.get_userobject_from_nid(owner_nid)
        user_has_discount = utils.get_client_vip_status(userobject)
        user_has_discount_flag = vip_payments_common.USER_HAS_DISCOUNT_STRING if user_has_discount else vip_payments_common.USER_NO_DISCOUNT_STRING

        if request.method != 'POST':
            error_message = "create_disposition was not called with POST data"
            error_reporting.log_exception(logging.critical, error_message = error_message)
            return http.HttpResponseBadRequest(error_message)


        amount = request.POST.get('amount', None); assert(amount)
        currency_code = request.POST.get('currency_code', None); assert(currency_code)

        if currency_code in vip_paysafecard_valid_currencies:
            if user_has_discount:
                membership_category = vip_payments_common.vip_discounted_price_to_membership_category_lookup[currency_code][amount]
            else:
                membership_category = vip_payments_common.vip_standard_price_to_membership_category_lookup[currency_code][amount]

            num_days_to_be_awarded = vip_payments_common.num_days_in_vip_membership_category[membership_category]
        else:
            raise Exception("Paysafecard currency %s not handled by code" % currency_code)

        if site_configuration.DEVELOPMENT_SERVER:
            # Give "real" URLs so that we can check if payment notifications are being received.
            pn_url = urllib.quote(development_payment_notification_server + '/paysafecard/pn_url/', '')
        else:
            pn_url = urllib.quote('http://%s/paysafecard/pn_url/' % request.META['HTTP_HOST'], '')


        time_in_millis = int(round(time.time() * 1000))
        encoded_time = utils.base_encode(time_in_millis, base=encode_allowed_chars)
        random_postfix = get_random_number_string_for_transaction_id()
        merchant_transaction_id = str(owner_nid) + '-' + random_postfix + '-' + encoded_time + '-' + user_has_discount_flag

        # make sure to pass a '' as the second parameter to urllib.quote -- otherwise, '/' will not be quoted.
        ok_url = urllib.quote('http://%s/paysafecard/ok_url/?mtid=%s&currency=%s' % (request.META['HTTP_HOST'], merchant_transaction_id, currency_code), '')
        nok_url = urllib.quote('http://%s/paysafecard/nok_url/' % request.META['HTTP_HOST'], '')

        paysafecard_disposition_response = vip_paysafe_soap_messages.create_disposition(
            username,
            password,
            merchant_transaction_id,
            amount,
            currency_code,
            ok_url,
            nok_url,
            owner_nid,
            pn_url,
            )

        log_disposition_resonse_msg = 'paysafecard_disposition_response: %s'  % repr(paysafecard_disposition_response)
        if (int(paysafecard_disposition_response['errorCode']) == 0) and \
                (int(paysafecard_disposition_response['resultCode']) == 0) and\
                (paysafecard_disposition_response['mid'] == merchant_id) and \
                (paysafecard_disposition_response['mtid'] == merchant_transaction_id):

            logging.info(log_disposition_resonse_msg)

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
                'create_disposition_success_flag': True,
                'merchant_id' : merchant_id,
                'merchant_transaction_id': merchant_transaction_id,
                'currency_code': currency_code,
                'amount': amount
            }
        else:
            # There was a problem with creating the disposition
            response_dict = {'create_disposition_success_flag': False}
            error_reporting.log_exception(logging.error, error_message = log_disposition_resonse_msg)
            email_utils.send_admin_alert_email(log_disposition_resonse_msg, subject = "%s Paysafe Error" % settings.APP_NAME)

    except:
        try:
            # This is serious enough, that it warrants sending an email to the administrator.
            message_content = """Paysafecard error - unable to create disposition"""
            email_utils.send_admin_alert_email(message_content, subject = "%s Paysafe Error" % settings.APP_NAME)

        finally:
            error_reporting.log_exception(logging.critical, request=request)
            response_dict = {'create_disposition_success_flag': False}

    json_response = json.dumps(response_dict)
    return http.HttpResponse(json_response, mimetype='text/javascript')


def do_debit_and_update_vip_structures(userobject, merchant_transaction_id, serial_numbers):

    error_message = ''

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

            if (int(paysafecard_debit_response['errorCode']) == 0) and (int(paysafecard_debit_response['resultCode']) == 0):

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

                    vip_status_support.update_userobject_vip_status("Paysafecard", userobject,
                        paysafe_disposition.num_days_to_be_awarded, serial_numbers,
                        paysafe_disposition.transaction_amount, paysafe_disposition.transaction_currency,
                        merchant_transaction_id, "No additional info")
                else:
                    # This branch should never be entered, since transaction should not be in the database since it has
                    # been confirmed to not already be complete in the paysafe_disposition struture - but check just in case
                    error_message = 'By construction, we should not be attempting to store transaction again'
            else:
                error_message = 'Paysafecard error in paysafecard_debit_response: %s ' % repr(paysafecard_debit_response)
        else:
            # This condition could happen if we process the payment directly from the okUrl (before pn_url is called),
            # and then receive a pnUrl notification of the message after we have already processed the payment, or vice versa.
            logging.warning('Paysafecard transaction %s is already complete - no action taken.')
            if not utils.get_client_vip_status(userobject):
                error_message = 'Paysafecard transaction is already complete - but user %s does not have VIP status' % (userobject.username)
    else:
        # if someone calls this URL without us having first created an associated disposition.
        error_message = 'Paysafecard - could not find disposition for transaction'

    transaction_info = 'merchant_transaction_id: %s serial_numbers: %s' % (merchant_transaction_id, serial_numbers)
    if error_message:
        error_message = error_message + '\n' + transaction_info
        error_reporting.log_exception(logging.critical, error_message=error_message)
        email_utils.send_admin_alert_email(error_message, subject = "%s Paysafe Error" % settings.APP_NAME)
        successful_debit = False
    else:
        logging.info(transaction_info)
        successful_debit = True

    return successful_debit


def pn_url(request):

    # After the client enters their paysafecard information and transmits it to paysafecard's servers, we will
    # receive a notification indicating the transaction ID, the amount received, and other information. If the client
    # pays in a currency other than the billing currency, then currency conversions are done by paysafecard, and we
    # therefore cannot look at the payment amount to figure out exactly which VIP status to award to the user.
    # For this reason, we must look up the transaction using the merchant_transaction_id to determine what
    # to award to the user. If the merchant_transaction_id is not found in our database, then this may be
    # a fraudulent attempt to get free VIP status.
    try:

        if request.method != 'POST':
            error_message = "pn_url was not called with POST data"
            error_reporting.log_exception(logging.critical, error_message = error_message)
            return http.HttpResponseBadRequest(error_message)

        logging.info('request = %s ' % repr(request))
        merchant_transaction_id = request.POST.get('mtid', None); assert(merchant_transaction_id)
        event_type = request.POST.get('eventType', None); assert(event_type == 'ASSIGN_CARDS')

        (nid_str, random_postfix, encoded_time, user_has_discount_flag) = merchant_transaction_id.split('-')
        nid = long(nid_str)

        # Note: serial_numbers is actually made up of 4 values seperated by ';' that may be repeated multiple times
        # in the case that more than one card was used to make the payment. eg. a payment from a single card would
        # be SerialNumber;CurrencyCode;Amount;CardTypeId - a payment from two cards would be
        # SerialNumber1;CurrencyCode1;Amount1;CardTypeId1;SerialNumber2;CurrencyCode2;Amount2;CardTypeId2 etc.
        serial_numbers = request.POST.get('serialNumbers', None); assert(serial_numbers)

        uid = utils.get_uid_from_nid(nid)
        userobject = utils_top_level.get_object_from_string(uid)

        successful_debit = do_debit_and_update_vip_structures(userobject, merchant_transaction_id, serial_numbers)
        if successful_debit:
             logging.info('pn_url - Paysafecard payment successfully debited')

        else:
            # debit failed - we don't generate an error message here, since a message was already generated
            # inside do_debit_and_update_vip_structures
            logging.info('pn_url - Error - Paysafecard payment not debited')

        return http.HttpResponse("OK")

    except:
        try:
            # This is serious enough, that it warrants sending an email to the administrator.
            message_content = """Paysafecard error - unable to process payment notification"""
            email_utils.send_admin_alert_email(message_content, subject = "%s Paysafe Error" % settings.APP_NAME)

        finally:
            error_reporting.log_exception(logging.critical, request=request)
            return http.HttpResponseServerError('Error in pn_url')



def ok_url(request):
    # Customer card has been sucessfully entered 'assigned' and the user has been redirected to the URL associated
    # with this function. Show the user the status of their payment.
    paysafe_username = site_configuration.PAYSAFE_SOAP_TEST_USERNAME
    paysafe_password = site_configuration.PAYSAFE_SOAP_TEST_PASSWORD
    merchant_transaction_id = request.GET.get('mtid')
    transaction_currency = request.GET.get('currency')

    userobject = utils_top_level.get_userobject_from_request(request)
    success_message = ugettext("Congratulations. You have been awarded VIP status! Check your messages for more details")
    user_error_message = ugettext("<p>There has been an error processing your payment."
                             "<p>Our automated systems have notified us of this problem and we "
                             "will investigate as soon as possible.")

    paysafe_get_serial_numbers_response = vip_paysafe_soap_messages.get_serial_numbers(paysafe_username,
                                                                                       paysafe_password,
                                                                                       merchant_transaction_id,
                                                                                       transaction_currency)

    logging.info('paysafe_get_serial_numbers_response: %s' % paysafe_get_serial_numbers_response)

    internal_error_message = ''

    if (int(paysafe_get_serial_numbers_response['errorCode']) != 0) or (int(paysafe_get_serial_numbers_response['resultCode']) != 0):
        message_to_display = user_error_message
        internal_error_message = 'errorCode or resultCode is not zero'

    elif paysafe_get_serial_numbers_response['dispositionState'] == 'O':
        # The payment has been Consumed (final debit has been called) - nothing else to do - show success message
        logging.info('ok_url - Paysafecard payment already consumed - Nothing else to do except inform user of successful payment ')
        message_to_display = success_message

    elif paysafe_get_serial_numbers_response['dispositionState'] == 'S':
        logging.info('ok_url - Paysafecard payment not yet consumed - we will now debit the payment')

        # Paysafecard has been assigned to disposition - we can now debit their account to finalize the transaction
        serial_numbers = paysafe_get_serial_numbers_response['serialNumbers']
        successful_debit = do_debit_and_update_vip_structures(userobject, merchant_transaction_id, serial_numbers)
        if successful_debit:
             message_to_display = success_message
             logging.info('ok_url - Paysafecard payment successfully debited')

        else:
            # debit failed - we don't generate an error message here, since a message was already generated
            # inside do_debit_and_update_vip_structures
            message_to_display = user_error_message
            logging.info('ok_url - Error - Paysafecard payment not debited')

    else:
        # Unknown disposition state - generate an error
        message_to_display = user_error_message
        internal_error_message = 'Un-handled disposition state of %s' % paysafe_get_serial_numbers_response['dispositionState']

    if internal_error_message:
        disposition_error_message = "Error caused in paysafe_get_serial_numbers_response: %s " % repr(paysafe_get_serial_numbers_response)
        error_reporting.log_exception(logging.critical, error_message=disposition_error_message)
        email_utils.send_admin_alert_email(disposition_error_message, subject = "%s Paysafe Error" % settings.APP_NAME)

    http_response = render_to_response('user_main_helpers/paysafecard_transaction_status.html', dict(
        {'message_to_display': message_to_display,
         }, **constants.template_common_fields))

    return http_response


def nok_url(request):
    message_to_display = ugettext("Transaction aborted by user. "
                                  "Your paysafecard will not be charged, and VIP status has not been awarded.")
    http_response = render_to_response('user_main_helpers/paysafecard_transaction_status.html', dict(
        {'message_to_display': message_to_display,
         }, **constants.template_common_fields))

    return http_response