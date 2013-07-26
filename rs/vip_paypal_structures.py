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


from django.utils.translation import ugettext_lazy, ugettext

from localization_files import currency_by_country

#VIP_1_DAY = "1_day" # for testing only
VIP_1_WEEK  = "1_week"
VIP_1_MONTH = "1_month"
VIP_3_MONTHS = "3_months"
VIP_6_MONTHS = "6_months"
VIP_1_YEAR  = "1_year"

# the following list will allow us to iterate over the various membership options in the correct order
vip_membership_categories = [VIP_1_WEEK, VIP_1_MONTH, VIP_3_MONTHS, VIP_6_MONTHS, VIP_1_YEAR]
SELECTED_VIP_DROPDOWN = VIP_6_MONTHS
DEFAULT_CURRENCY = 'USD_NON_US' # International US dollars "$US" instead of just "$"

# Leave the following value set to None if we are not trying to force a particular country's options to be displayed
TESTING_COUNTRY = ''


num_months_in_vip_membership_category = {
    #VIP_1_DAY : 1/float(30),
    VIP_1_WEEK  : 7/float(30),
    VIP_1_MONTH : 1,
    VIP_3_MONTHS : 3,
    VIP_6_MONTHS : 6,
    VIP_1_YEAR  : 12,
}

num_days_in_vip_membership_category = {
    #VIP_1_DAY : 1,
    VIP_1_WEEK  : 7,
    VIP_1_MONTH : 31,
    VIP_3_MONTHS : 92,
    VIP_6_MONTHS : 183,
    VIP_1_YEAR  : 365,    
}

vip_option_values = {
    # this is broken up like this so that the lazy translation isn't done until the value is read.
    #VIP_1_DAY : {'duration' : "1", 'duration_units' : "day"},
    VIP_1_WEEK : {'duration': "1", 'duration_units' : ugettext_lazy("week")}, 
    VIP_1_MONTH: {'duration': "1", 'duration_units' : ugettext_lazy("month")},
    VIP_3_MONTHS: {'duration': "3", 'duration_units' : ugettext_lazy("months")},
    VIP_6_MONTHS: {'duration': "6", 'duration_units' : ugettext_lazy("months")},
    VIP_1_YEAR: {'duration': "1", 'duration_units' : ugettext_lazy("year")},
}


vip_paypal_prices = {
    'EUR': {
        VIP_1_WEEK: "6.95",
        VIP_1_MONTH: "17.95",
        VIP_3_MONTHS: "34.95",
        VIP_6_MONTHS: "49.95",
        VIP_1_YEAR: "99.95",
        },
    'USD' : {
        VIP_1_WEEK: "6.95",
        VIP_1_MONTH: "17.95",
        VIP_3_MONTHS: "34.95",
        VIP_6_MONTHS: "49.95",
        VIP_1_YEAR: "99.95",
        },
    'USD_NON_US' : {
        # Pricing for international customers outside of the US
        VIP_1_WEEK: "5.95",
        VIP_1_MONTH: "16.95",
        VIP_3_MONTHS: "27.95",
        VIP_6_MONTHS: "39.85",
        VIP_1_YEAR: "78.95",
        },   
    'MXN' : {
        # 1 USD = 13 MXN
        VIP_1_WEEK: "69.95",    # 
        VIP_1_MONTH: "179.95",  # 
        VIP_3_MONTHS: "349.95", # 
        VIP_6_MONTHS: "499.95", # 
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


# keep track of which currencies we currently support. This is used in the for initializing 
# dictionaries that are used for efficiently looking up membership prices with the currency units.
valid_currencies = []
# The following represent the "real" currency-codes that will be passed to paypal - principally it is designed to over-ride
# the internally used 'USD_NON_US' value to become 'USD' when passing the currency-code into paypal
real_currency_codes = {}
for key, value in vip_paypal_prices.iteritems() :
    valid_currencies.append(key)
    real_currency_codes[key] = key
real_currency_codes['USD_NON_US'] = 'USD'

# generate the dictionary that will allow us to do a reverse lookup when we receive a payment amount
# to the corresponding membership category
vip_price_to_membership_category_lookup = {}
for currency in vip_paypal_prices:
    vip_price_to_membership_category_lookup[currency] = {}
    for k,v in vip_paypal_prices[currency].iteritems():
        vip_price_to_membership_category_lookup[currency][v] = k
    


def generate_prices_with_currency_units(prices_to_loop_over):
    prices_dict_to_show = {}
    for currency in valid_currencies:
        prices_dict_to_show[currency] = {}
        for category in vip_membership_categories:
            prices_dict_to_show[currency][category] = u"%s%s" % (currency_by_country.currency_symbols[currency], prices_to_loop_over[currency][category])
    return prices_dict_to_show
    
vip_prices_with_currency_units = generate_prices_with_currency_units(vip_paypal_prices)

vip_prices_per_month = {}
for currency in valid_currencies:
    vip_prices_per_month[currency] =  {}
    for category in vip_membership_categories:
        vip_prices_per_month[currency][category] = "%.2f" % (
            float(vip_paypal_prices[currency][category]) / num_months_in_vip_membership_category[category])
        
vip_prices_per_month_with_currency_units = generate_prices_with_currency_units(vip_prices_per_month)

def generate_paypal_dropdown_options(currency):
    
    generated_html = u''
    for member_category in vip_membership_categories:
        duration = u"%s" % vip_option_values[member_category]['duration']
        duration_units = u"%s" % vip_option_values[member_category]['duration_units']
        
        if member_category == SELECTED_VIP_DROPDOWN:
            selected = "selected"
        else:
            selected = ''
            
        if member_category == VIP_1_WEEK or member_category == VIP_1_MONTH:
            generated_html += u"""<option value="%(duration)s %(duration_units)s" %(selected)s>
                        %(duration)s %(duration_units)s: %(total_price)s</option>\n""" % {
                            'duration': duration, 'duration_units' : duration_units, 
                            'selected' : selected,
                            'total_price' : vip_prices_with_currency_units[currency][member_category]}            
        else:
            generated_html += u"""<option value="%(duration)s %(duration_units)s" %(selected)s>
            %(duration)s %(duration_units)s: %(price_per_month)s/%(month_txt)s  (%(one_payment_txt)s %(total_price)s)</option>\n""" % {
                'duration': duration, 'duration_units' : duration_units, 
                'selected' : selected,                
                'price_per_month' : vip_prices_per_month_with_currency_units[currency][member_category], 
                'one_payment_txt': ugettext('total of'), 'month_txt' : ugettext('month'),
                'total_price' : vip_prices_with_currency_units[currency][member_category]}
            
    return generated_html

def generate_paypal_dropdown_options_hidden_fields(currency):
    
    generated_html = ''
    counter = 0
    for member_category in vip_membership_categories:
        generated_html += u'<input type="hidden" name="option_select%d" value="%s %s">' % (
            counter, vip_option_values[member_category]['duration'], vip_option_values[member_category]['duration_units'])
        generated_html += u'<input type="hidden" name="option_amount%d" value="%s">' % (counter, vip_paypal_prices[currency][member_category])
        counter += 1
        
    return generated_html



