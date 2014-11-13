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


from django.utils.translation import ugettext_lazy, ugettext

from localization_files import currency_by_country

#VIP_1_DAY = "1 day"
VIP_3_DAYS  = "3 days"
VIP_1_MONTH = "1 month"
VIP_3_MONTHS = "3 months"
VIP_6_MONTHS = "6 months"
VIP_1_YEAR  = "1 year"

# the following list will allow us to iterate over the various membership options in the correct order
vip_membership_categories = [VIP_3_DAYS, VIP_1_MONTH, VIP_3_MONTHS, VIP_6_MONTHS, VIP_1_YEAR]
SELECTED_VIP_DROPDOWN = VIP_3_MONTHS

# Leave the following value set to None if we are not trying to force a particular country's options to be displayed
TESTING_COUNTRY = ''

num_days_in_vip_membership_category = {
    #VIP_1_DAY : 1,
    VIP_3_DAYS  : 3,
    VIP_1_MONTH : 31,
    VIP_3_MONTHS : 93,
    VIP_6_MONTHS : 183,
    VIP_1_YEAR  : 365,
}

vip_option_values = {
    # this is broken up like this so that the lazy translation isn't done until the value is read.
    #VIP_1_DAY : {'duration' : "1", 'duration_units' : ugettext_lazy("day")},
    VIP_3_DAYS : {'duration': "3", 'duration_units' : ugettext_lazy("days")},
    VIP_1_MONTH: {'duration': "1", 'duration_units' : ugettext_lazy("month")},
    VIP_3_MONTHS: {'duration': "3", 'duration_units' : ugettext_lazy("months")},
    VIP_6_MONTHS: {'duration': "6", 'duration_units' : ugettext_lazy("months")},
    VIP_1_YEAR: {'duration': "1", 'duration_units' : ugettext_lazy("year")},
}


vip_paypal_prices = {
    'EUR': {
        #VIP_1_DAY: "6.95",
        VIP_3_DAYS: "9.95",
        VIP_1_MONTH: "29.95",
        VIP_3_MONTHS: "49.95",
        VIP_6_MONTHS: "69.95",
        VIP_1_YEAR: "99.95",
        },
    'USD': {
        #VIP_1_DAY: "6.95",
        VIP_3_DAYS: "9.95",
        VIP_1_MONTH: "29.95",
        VIP_3_MONTHS: "49.95",
        VIP_6_MONTHS: "69.95",
        VIP_1_YEAR: "99.95",
        }, 
    'MXN': {
        #VIP_1_DAY: "69.95",
        VIP_3_DAYS: "99.15",
        VIP_1_MONTH: "299.95",
        VIP_3_MONTHS: "499.95",
        VIP_6_MONTHS: "699.95",
        VIP_1_YEAR: "999.95",
        },    
    #'GBP' : {
        #VIP_1_WEEK: ".95",
        #VIP_1_MONTH: "16.95",
        #VIP_3_MONTHS: "39.95",
        #VIP_6_MONTHS: "49.95",
        #VIP_1_YEAR: "99.95",
        #},

}
# Pricing for international customers outside of the US
# For the moment, keep these prices the same as the USD prices - we need to modify the IPN paymenmt 
# processing code to distinguish between USD and USD_NON_US, which is currently does not do
# and therefore if these values are different than USD the payment will not be processed correctly.
vip_paypal_prices['USD_NON_US'] = vip_paypal_prices['USD']


# keep track of which currencies we currently support. This is used for initializing 
# dictionaries that are used for efficiently looking up membership prices with the currency units.
paypal_valid_currencies = []
# The following represent the "real" currency-codes that will be passed to paypal - principally it is designed to over-ride
# the internally used 'USD_NON_US' value to become 'USD' when passing the currency-code into paypal
real_currency_codes = {}
for key in vip_paypal_prices.keys() :
    paypal_valid_currencies.append(key)
    real_currency_codes[key] = key
    
paypal_valid_currencies.append('USD_NON_US')
real_currency_codes['USD_NON_US'] = 'USD'

PAYPAL_DEFAULT_CURRENCY = 'USD_NON_US' # International US dollars "$US" instead of just "$"

# generate the dictionary that will allow us to do a reverse lookup when we receive a payment amount
# to the corresponding membership category
vip_price_to_membership_category_lookup = {}
for currency in vip_paypal_prices:
    vip_price_to_membership_category_lookup[currency] = {}
    for k,v in vip_paypal_prices[currency].iteritems():
        vip_price_to_membership_category_lookup[currency][v] = k
    


def generate_prices_with_currency_units(prices_to_loop_over):
    prices_dict_to_show = {}
    for currency in paypal_valid_currencies:
        prices_dict_to_show[currency] = {}
        for category in vip_membership_categories:
            prices_dict_to_show[currency][category] = u"%s%s" % (currency_by_country.currency_symbols[currency], prices_to_loop_over[currency][category])
    return prices_dict_to_show
    
vip_prices_with_currency_units = generate_prices_with_currency_units(vip_paypal_prices)
        

def generate_paypal_dropdown_options(currency):
    # for efficiency don't call this from outside this module, instead perform a lookup in
    # paypal_dropdown_options
    generated_html = u''
    for member_category in vip_membership_categories:
        duration = u"%s" % vip_option_values[member_category]['duration']
        duration_units = u"%s" % vip_option_values[member_category]['duration_units']
        
        if member_category == SELECTED_VIP_DROPDOWN:
            selected = "checked"
        else:
            selected = ''

        generated_html += u"""<input type="radio" name="os0" value="%(duration)s %(duration_units)s" %(selected)s>
        <strong>%(duration)s %(duration_units)s</strong>: %(total_price)s<br>\n""" % {
            'duration': duration, 'duration_units' : duration_units, 
            'selected' : selected,                
            'total_price' : vip_prices_with_currency_units[currency][member_category]}
            
    return generated_html

def generate_paypal_dropdown_options_hidden_fields(currency):
    
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
    for member_category in vip_membership_categories:
        generated_html += u'<input type="hidden" name="option_select%d" value="%s %s">' % (
            counter, vip_option_values[member_category]['duration'], vip_option_values[member_category]['duration_units'])
        generated_html += u'<input type="hidden" name="option_amount%d" value="%s">' % (counter, vip_paypal_prices[currency][member_category])
        counter += 1
        
    return generated_html



