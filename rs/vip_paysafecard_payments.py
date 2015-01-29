import logging
import urllib

from django.shortcuts import render_to_response
from django import http

import site_configuration, settings

from rs import email_utils
from rs import error_reporting
from rs import vip_payments_common
from paysafe_card.client.src import SOPGClassicMerchantClient


# We load the wsdl from our servers.
# For testing purposes we can generally load from localhost, as long as we
# are running a webserver locally. For release application, it is better to get the hostname from
# request.META.HTTP_HOST if possible.



pn_url = urllib.quote('http://www.%s/paysafecard/ipn/' % site_configuration.DOMAIN_NAME, '')


vip_paysafecard_valid_currencies = ['EUR', 'USD', 'MXN', 'USD_NON_US']


vip_paysafecard_prices_with_currency_units = vip_payments_common.generate_prices_with_currency_units(
    vip_payments_common.vip_standard_membership_prices, vip_paysafecard_valid_currencies)


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
        if not vip_payments_common.TESTING_COUNTRY:
            http_country_code = request.META.get('HTTP_X_APPENGINE_COUNTRY', None)
        else:
            error_reporting.log_exception(logging.error, error_message = "TESTING_COUNTRY is over-riding HTTP_X_APPENGINE_COUNTRY")
            http_country_code = vip_payments_common.TESTING_COUNTRY

        internal_currency_code = vip_payments_common.get_internal_currency_code(http_country_code, vip_paysafecard_valid_currencies)

        paysafecard_data = {}
        paysafecard_data['owner_nid'] = owner_nid
        paysafecard_data['currency_code'] = vip_payments_common.real_currency_codes[internal_currency_code]
        paysafecard_data['country_override'] = vip_payments_common.TESTING_COUNTRY
        paysafecard_data['testing_paysafecard'] = site_configuration.TESTING_PAYSAFECARD


        # if not site_configuration.TESTING_PAYSAFECARD:
        #     paysafecard_data['paysafecard_soap_username'] = site_configuration.PAYSAFE_SOAP_TEST_USERNAME
        #     paysafecard_data['paysafecard_soap_password'] = site_configuration.PAYSAFE_SOAP_TEST_PASSWORD
        #     paysafecard_data['paysafecard_merchant_id'] = site_configuration.PAYSAFE_TEST_MID
        #
        # else:
        #     paysafecard_data['paysafecard_soap_username'] = site_configuration.PAYSAFE_SOAP_USERNAME
        #     paysafecard_data['paysafecard_soap_password'] = site_configuration.PAYSAFE_SOAP_PASSWORD
        #     paysafecard_data['paysafecard_merchant_id'] = site_configuration.PAYSAFE_MID


        paysafecard_data['radio_options'] = generate_paysafe_radio_options(internal_currency_code)

        return paysafecard_data
    except:
        error_reporting.log_exception(logging.critical)
        return http.HttpResponseServerError('Error generating paysafecard data')


def create_disposition(request):

    try:
        # during development, request the wsdl document from the paysafecard servers, since
        # requesting it locally appears to cause the development server to hang - likely due to
        # a deadlock that occurs while waiting for localhost to respond to the request, but the
        # request is not filled until the current request executes .. or something along those lines.
        if site_configuration.DEVELOPMENT_SERVER:
            wsdl_url = settings.PAYSAFE_ENDPOINT + '?wsdl'
        else:
            wsdl_url = 'http://%s/xml/paysafecard_wsdl.xml' % request.META['HTTP_HOST']

        client = SOPGClassicMerchantClient.SOPGClassicMerchantClient(wsdl_url, settings.PAYSAFE_ENDPOINT)
        return http.HttpResponse('OK')

    except:
        try:
            # This is serious enough, that it warrants sending an email to the administrator.
            message_content = """Paysafecard error - unable to create disposition"""
            email_utils.send_admin_alert_email(message_content, subject = "%s Paysafe Error" % settings.APP_NAME)

        finally:
            error_reporting.log_exception(logging.critical, request=request)
            return http.HttpResponseServerError('Error in create_disposition')

