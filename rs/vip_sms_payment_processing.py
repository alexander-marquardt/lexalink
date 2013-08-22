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

from django.utils.translation import  ungettext
import hashlib

from localization_files import currency_by_country
import settings

""" Setup the structures that will be used in processing SMS payments. 
    Currently we are using fortumo.com as our payment processor.
    
    
    Currently we are offering SMS payment in Argentina, Chile, Colombia, Mexico, and Spain"""


if settings.TESTING_FORTUMO_PAYMENTS:
    TESTING_COUNTRY = 'ES'    
    TEST_VAL = "ok" # can be None, "ok" (simulate a successfull payment), or "fail" (simulate a failed payment)
else:
    TESTING_COUNTRY = ''        
    TEST_VAL = ''

# We  detect that an SMS payment has come from a given country, and verify that it is 
# of the expected amount. Once these two conditions are met, then the following number of VIP days
# will be awarded to the member.
payment_options = { 
    # for each country, specify a dictionary of the form {price : days awarded}
    #'AR' : {"9.99" : 1},    # $1.75 USD
    #'CL' : {"900.00" : 1},  # $1.70 USD
    #'CO' : {"6960.00" : 3}, # $3.46 USD
    #'MX' : {"30.26" : 2},   # $2.16 USD
    'ES' : {"5.20" : 1, 
            "7.26" : 3},    # $9.18 USD 
}

payment_options_tc_ids = {
    # These are identifiers (tc_id) provided by fortumo.com, which can been seen in the XML file
    # seen at http://fortumo.com/mobile_payments/[service_id].xml. These are necessary for calling
    # the checkout page directly, with a value already selected. 
    'ES' : {"3.63" : 299,
            "5.20" : 298, 
            "7.26" : 301}, 
}

default_selected_option = {
    'ES' : "7.26",
}



valid_countries = []
ordered_payment_options_price_points = {}
for country in payment_options.keys():
    valid_countries.append(country)
    ordered_payment_options_price_points[country] = payment_options[country].keys()
    ordered_payment_options_price_points[country].sort()    
    
    
# http://fortumo.com/mobile_payments/b364da18148a355f8b87303fe0ad1794/fortumo-test-6fb84aed?test=ok&tc_amount=7&tc_id=301&sig=3ef90b89383d9d3eb912f8e10833e5dd

def generate_fortumo_options(country, owner_nid):
    
    # Generate the payment options (radio boxes) for fortumo paymens
    
    generated_html = u''
    for price_point in ordered_payment_options_price_points[country]:
        days_awarded = payment_options[country][price_point]
        duration_txt = ungettext(
                    '%(days)s day',
                    '%(days)s days',
                    days_awarded
            ) % {
                'days': days_awarded,
            }     
        
        currency = currency_by_country.country_to_currency_map[country]
        currency_symbol = currency_by_country.currency_symbols[currency]
    
        if price_point == default_selected_option[country] :
            selected = "checked"
        else:
            selected = ''
                  
        # to prevent fraud, we have to compute a hash of certain values. 
        # See: http://developers.fortumo.com/mobile-payments-for-web-apps/advanced-integration/ for details
        calculation_string = ''
        cuid = owner_nid
        calculation_string += 'cuid=%s' % cuid
        tc_amount = days_awarded;
        calculation_string += 'tc_amount=%d' % tc_amount
        tc_id = payment_options_tc_ids[country][price_point]
        calculation_string += 'tc_id=%d' % tc_id
        if TEST_VAL:
            calculation_string += 'test=%s' % TEST_VAL
            test_param = 'test=%s&' % TEST_VAL
        else:
            test_param = ''
            
        secret = settings.fortumo_web_apps_secret
        calculation_string += secret
        sig = hashlib.md5(calculation_string).hexdigest()
            
        fortumo_url = "http://fortumo.com/mobile_payments/%(service_id)s?%(test_param)scuid=%(cuid)s&tc_amount=%(tc_amount)s&tc_id=%(tc_id)s&sig=%(sig)s" % {
            'service_id' : settings.fortumo_web_apps_service_id,
            'cuid' : cuid,
            'test_param' : test_param,
            'tc_amount' : tc_amount,
            'tc_id' : tc_id,
            'sig' : sig,
            }
        
        generated_html += u"""<input type="radio" name="fortumo_price_point" value="%(fortumo_url)s" %(selected)s>
        <strong>%(duration_txt)s</strong>: %(currency_symbol)s%(price)s<br>\n""" % {
            'fortumo_url' : fortumo_url,
            'duration_txt': duration_txt, 
            'selected' : selected,  
            'currency_symbol' : currency_symbol,
            'price' : price_point}
    
    return generated_html