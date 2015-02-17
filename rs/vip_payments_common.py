import logging

from django.utils.translation import ugettext_lazy
from django.utils.translation import ugettext

import settings
from rs import error_reporting

from rs.localization_files import currency_by_country



# Leave the following value set to None if we are not trying to force a particular country's options to be displayed
TESTING_COUNTRY = 'ES'
if not (settings.TESTING_PAYPAL_SANDBOX or settings.TESTING_PAYSAFECARD) and TESTING_COUNTRY:
    error_reporting.log_exception(logging.critical, error_message='Don\'t override payment country unless you are building a TESTING_* app')

#VIP_1_DAY = "1 day"
VIP_3_DAYS  = "3 days"
VIP_1_MONTH = "1 month"
VIP_3_MONTHS = "3 months"
VIP_6_MONTHS = "6 months"
VIP_1_YEAR  = "1 year"

# the following list will allow us to iterate over the various membership options in the correct order
vip_membership_categories = [VIP_3_DAYS, VIP_1_MONTH, VIP_3_MONTHS, VIP_6_MONTHS, VIP_1_YEAR]
DEFAULT_SELECTED_VIP_OPTION = VIP_3_MONTHS

USER_HAS_DISCOUNT_STRING = 'D'
USER_NO_DISCOUNT_STRING = 'N'

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


vip_standard_membership_prices = {
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
        VIP_3_DAYS: "99.95",
        VIP_1_MONTH: "299.95",
        VIP_3_MONTHS: "499.95",
        VIP_6_MONTHS: "699.95",
        VIP_1_YEAR: "999.95",
        },
}

vip_discounted_membership_prices = {
      'EUR': {
        #VIP_1_DAY: "6.95",
        VIP_3_DAYS: "8.95",
        VIP_1_MONTH: "25.95",
        VIP_3_MONTHS: "39.95",
        VIP_6_MONTHS: "51.95",
        VIP_1_YEAR: "69.95",
        },
    'USD': {
        #VIP_1_DAY: "6.95",
        VIP_3_DAYS: "8.95",
        VIP_1_MONTH: "25.95",
        VIP_3_MONTHS: "39.95",
        VIP_6_MONTHS: "51.95",
        VIP_1_YEAR: "69.95",
        },
    'MXN': {
        #VIP_1_DAY: "69.95",
        VIP_3_DAYS: "89.95",
        VIP_1_MONTH: "259.95",
        VIP_3_MONTHS: "399.95",
        VIP_6_MONTHS: "519.95",
        VIP_1_YEAR: "699.95",
        },
}

# Pricing for international customers outside of the US
# For the moment, keep these prices the same as the USD prices - we need to modify the IPN paymenmt
# processing code to distinguish between USD and USD_NON_US, which is currently does not do
# and therefore if these values are different than USD the payment will not be processed correctly.
vip_standard_membership_prices['USD_NON_US'] = vip_standard_membership_prices['USD']
vip_discounted_membership_prices['USD_NON_US'] = vip_discounted_membership_prices['USD']


# The following represent the "real" currency-codes that will be passed to paypal - principally it is designed to over-ride
# the internally used 'USD_NON_US' value to become 'USD' when passing the currency-code into paypal
real_currency_codes = {}
for key in vip_standard_membership_prices.keys() :
    real_currency_codes[key] = key

real_currency_codes['USD_NON_US'] = 'USD'


def generate_vip_price_to_membership_category_lookup(vip_standard_membership_prices):
    price_to_membership_category_lookup = {}
    for currency in vip_standard_membership_prices:
        price_to_membership_category_lookup[currency] = {}
        for k,v in vip_standard_membership_prices[currency].iteritems():
            price_to_membership_category_lookup[currency][v] = k
    return price_to_membership_category_lookup


vip_standard_price_to_membership_category_lookup  = generate_vip_price_to_membership_category_lookup(vip_standard_membership_prices)
vip_discounted_price_to_membership_category_lookup  = generate_vip_price_to_membership_category_lookup(vip_discounted_membership_prices)

def get_internal_currency_code(http_country_code, vip_valid_currencies, vip_default_currency):

    try:
        # Lookup currency for the country
        if http_country_code in currency_by_country.country_to_currency_map:
            internal_currency_code = currency_by_country.country_to_currency_map[http_country_code]
        else:
            internal_currency_code = vip_default_currency

        # make sure that we have defined the papal structures for the current currency
        if internal_currency_code not in vip_valid_currencies:
            internal_currency_code = vip_default_currency

        if internal_currency_code not in currency_by_country.currency_symbols:
            raise Exception('Verify that currency_symbols contains all expected currencies. Received %s' % internal_currency_code)

    except:
        # If there is any error, report it, and default to the "international" $US
        internal_currency_code = vip_default_currency
        error_reporting.log_exception(logging.error)

    return internal_currency_code



def generate_prices_with_currency_units(prices_to_loop_over, vip_valid_currencies):
    prices_dict_to_show = {}
    for currency in vip_valid_currencies:
        prices_dict_to_show[currency] = {}
        for category in vip_membership_categories:
            prices_dict_to_show[currency][category] = u"%s%s" % (currency_by_country.currency_symbols[currency], prices_to_loop_over[currency][category])
    return prices_dict_to_show


def compute_savings_percentage_discount(discounted_membership_prices, standard_membership_prices, vip_valid_currencies):
    discount_dict = {}
    for currency in vip_valid_currencies:
        discount_dict[currency] = {}
        for category in vip_membership_categories:
            discount = 100 * (1 - (float(discounted_membership_prices[currency][category]) / float(standard_membership_prices[currency][category])))
            discount_dict[currency][category] = "%.0f%%" % discount

    return discount_dict


def get_html_showing_savings(currency, member_category, vip_discounted_paysafe_prices_percentage_savings, original_prices_with_currency_units):

    if original_prices_with_currency_units:
        discount_percentage = vip_discounted_paysafe_prices_percentage_savings[currency][member_category]
        savings_html = '<span class="cl-text-6pt-format">(%s. %s: %s)</span>' % (
            ugettext('%(discount_percentage)s discount') % {'discount_percentage': discount_percentage},
            ugettext('Regular price'),
            original_prices_with_currency_units[currency][member_category],
        )
    else:
        savings_html = ''

    return savings_html