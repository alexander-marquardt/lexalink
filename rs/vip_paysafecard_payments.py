import logging
import sys
import time
import urllib

from django.shortcuts import render_to_response
from django import http

import site_configuration, settings

from rs import email_utils
from rs import error_reporting
from rs import utils
from rs import utils_top_level
from rs import vip_payments_common
from paysafe_card.client.src import SOPGClassicMerchantClient


# Leave the following value set to None if we are not trying to force a particular country's options to be displayed
TESTING_COUNTRY = 'ES'

pn_url = urllib.quote('http://www.%s/paysafecard/ipn/' % site_configuration.DOMAIN_NAME, '')


vip_paysafecard_valid_currencies = ['EUR', 'USD', 'MXN', 'USD_NON_US']


vip_paysafecard_prices_with_currency_units = vip_payments_common.generate_prices_with_currency_units(
    vip_payments_common.vip_standard_membership_prices, vip_paysafecard_valid_currencies)

# If we are testing paysafe, then get suds to output the server requests that it is making.
if site_configuration.TESTING_PAYSAFECARD:
    handler = logging.StreamHandler(sys.stderr)
    logger = logging.getLogger('suds.transport.http')
    logger.setLevel(logging.DEBUG), handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    class OutgoingFilter(logging.Filter):
        def filter(self, record):
            return record.msg.startswith('sending:')


    handler.addFilter(OutgoingFilter())

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

        internal_currency_code = vip_payments_common.get_internal_currency_code(http_country_code, vip_paysafecard_valid_currencies)

        paysafecard_data = {}
        paysafecard_data['owner_nid'] = owner_nid
        paysafecard_data['currency_code'] = vip_payments_common.real_currency_codes[internal_currency_code]
        paysafecard_data['country_override'] = TESTING_COUNTRY
        paysafecard_data['testing_paysafecard'] = site_configuration.TESTING_PAYSAFECARD
        paysafecard_data['radio_options'] = generate_paysafe_radio_options(internal_currency_code)

        return paysafecard_data
    except:
        error_reporting.log_exception(logging.critical)
        return http.HttpResponseServerError('Error generating paysafecard data')


def create_disposition(request):

    try:

        uid = utils_top_level.get_uid_from_request(request)
        nid = utils.get_nid_from_uid(uid)

        if request.method != 'POST':
            error_message = "create_disposition was not called with POST data"
            error_reporting.log_exception(logging.critical, error_message = error_message)
            return http.HttpResponseBadRequest(error_message)


        amount = request.POST.get('amount', None); assert(amount)
        currency_code = request.POST.get('currency_code', None); assert(currency_code)

        # during development, request the wsdl document from the paysafecard servers, since
        # requesting it locally appears to cause the development server to hang - likely due to
        # a deadlock that occurs while waiting for localhost to respond to the request, but the
        # request is not filled until the current request executes .. or something along those lines.
        if site_configuration.DEVELOPMENT_SERVER:
            # running developement server, get the wsdl document directly from paysafe.
            wsdl_url = settings.PAYSAFE_ENDPOINT + '?wsdl'

            # Give "real" URLs so that we can check if payment notifications are being received.
            ok_url = urllib.quote('http://paysafecard.romancesapp.appspot.com/paysafecard/okurl/', '')
            nok_url = urllib.quote('http://paysafecard.romancesapp.appspot.com/paysafecard/nokurl/', '')
            pn_url = urllib.quote('http://paysafecard.romancesapp.appspot.com/paysafecard/payment_notification/', '')

        else:
            # We are running on production server, get the wsdl document directly from the
            # production server.
            wsdl_url = 'http://%s/xml/paysafecard_wsdl.xml' % request.META['HTTP_HOST']
            ok_url = urllib.quote('http://%s/paysafecard/okurl/' % request.META['HTTP_HOST'], '')
            nok_url = urllib.quote('http://%s/paysafecard/nokurl/' % request.META['HTTP_HOST'], '')
            pn_url = urllib.quote('http://%s/paysafecard/payment_notification/' % request.META['HTTP_HOST'], '')

        # Don't see the reason for passing IP address, and it may be difficult to get accurately if passed throug
        # proxies, etc. Set to None for now.
        client_ip = None

        if site_configuration.TESTING_PAYSAFECARD:
            username = site_configuration.PAYSAFE_SOAP_TEST_USERNAME
            password = site_configuration.PAYSAFE_SOAP_TEST_PASSWORD

        else:
            username = site_configuration.PAYSAFE_SOAP_USERNAME
            password = site_configuration.PAYSAFE_SOAP_PASSWORD

        merchant_transaction_id = str(nid) + '-' + str(time.time())

        client = SOPGClassicMerchantClient.SOPGClassicMerchantClient(wsdl_url, settings.PAYSAFE_ENDPOINT)
        paysafecard_disposition_response = client.createDisposition(
            username,
            password,
            merchant_transaction_id,
            None,
            amount,
            currency_code,
            ok_url,
            nok_url,
            nid,
            pn_url,
            client_ip)

        logging.info('paysafecard_disposition_response: %s'  % repr(paysafecard_disposition_response))
        if paysafecard_disposition_response['errorCode'] != 0:
            logging.error('paysafecard error in disposition. errorCode = %d' % paysafecard_disposition_response['errorCode'])

        assert(paysafecard_disposition_response['resultCode'] == 0)

        return http.HttpResponse('OK')

    except:
        try:
            # This is serious enough, that it warrants sending an email to the administrator.
            message_content = """Paysafecard error - unable to create disposition"""
            email_utils.send_admin_alert_email(message_content, subject = "%s Paysafe Error" % settings.APP_NAME)

        finally:
            error_reporting.log_exception(logging.critical, request=request)
            return http.HttpResponseServerError('Error in create_disposition')



def payment_notification(request):

    try:
        if request.method != 'POST':
            error_message = "payment_notification was not called with POST data"
            error_reporting.log_exception(logging.critical, error_message = error_message)
            return http.HttpResponseBadRequest(error_message)

        logging.info('request = %s ' % repr(request))
        merchant_transaction_id = request.POST.get('mtid', None); assert(merchant_transaction_id)
        serial_numbers = request.POST.get('serialNumbers', None); assert(serial_numbers)

    except:
        try:
            # This is serious enough, that it warrants sending an email to the administrator.
            message_content = """Paysafecard error - unable to process payment notification"""
            email_utils.send_admin_alert_email(message_content, subject = "%s Paysafe Error" % settings.APP_NAME)

        finally:
            error_reporting.log_exception(logging.critical, request=request)
            return http.HttpResponseServerError('Error in payment_notification')