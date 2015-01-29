import logging

from django.shortcuts import render_to_response
from django import http

import site_configuration

from rs import error_reporting
from rs import vip_payments_common

vip_paysafecard_valid_currencies = ['EUR', 'USD', 'MXN', 'USD_NON_US']


vip_paysafecard_prices_with_currency_units = vip_payments_common.generate_prices_with_currency_units(
    vip_payments_common.vip_standard_membership_prices, vip_paysafecard_valid_currencies)

def paysafecard_sopg_wsdl(request):
    try:
        http_response = render_to_response("paysafecard_wsdl.xml", {})

        return http_response
    except:
        error_reporting.log_exception(logging.critical)
        return http.HttpResponseServerError('Error accessing paysafecard_wsdl.xml document')
    

def generate_paysafe_dropdown_options(currency):
    # for efficiency don't call this from outside this module, instead perform a lookup in
    # paypal_dropdown_options
    generated_html = u''
    for member_category in vip_payments_common.vip_membership_categories:
        duration = u"%s" % vip_payments_common.vip_option_values[member_category]['duration']
        duration_units = u"%s" % vip_payments_common.vip_option_values[member_category]['duration_units']

        if member_category == vip_payments_common.SELECTED_VIP_DROPDOWN:
            selected = "checked"
        else:
            selected = ''

        generated_html += u"""<input type="radio" name="amount" value="%(total_price)s" %(selected)s>
        <strong>%(duration)s %(duration_units)s</strong>: %(total_price)s<br>\n""" % {
            'duration': duration, 'duration_units' : duration_units,
            'selected' : selected,
            'total_price' : vip_paysafecard_prices_with_currency_units[currency][member_category]}

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


        paysafecard_data['dropdown_options'] = generate_paysafe_dropdown_options(internal_currency_code)

        return paysafecard_data
    except:
        error_reporting.log_exception(logging.critical)
        return http.HttpResponseServerError('Error generating paysafecard data')