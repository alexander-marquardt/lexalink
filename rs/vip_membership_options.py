from django.utils.translation import ugettext_lazy
from rs import constants

#VIP_1_DAY = "1 day"
VIP_3_DAYS  = "3 days"
VIP_1_MONTH = "1 month"
VIP_3_MONTHS = "3 months"
VIP_6_MONTHS = "6 months"
VIP_1_YEAR  = "1 year"

# the following list will allow us to iterate over the various membership options in the correct order
vip_membership_categories = [VIP_3_DAYS, VIP_1_MONTH, VIP_3_MONTHS, VIP_6_MONTHS, VIP_1_YEAR]
SELECTED_VIP_DROPDOWN = VIP_3_MONTHS


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
vip_standard_membership_prices['USD_NON_US'] = vip_standard_membership_prices['USD']


# keep track of which currencies we currently support. This is used for initializing
# dictionaries that are used for efficiently looking up membership prices with the currency units.
vip_payment_valid_currencies = []
# The following represent the "real" currency-codes that will be passed to paypal - principally it is designed to over-ride
# the internally used 'USD_NON_US' value to become 'USD' when passing the currency-code into paypal
real_currency_codes = {}
for key in vip_standard_membership_prices.keys() :
    vip_payment_valid_currencies.append(key)
    real_currency_codes[key] = key

vip_payment_valid_currencies.append('USD_NON_US')
real_currency_codes['USD_NON_US'] = 'USD'

VIP_DEFAULT_CURRENCY = 'USD_NON_US' # International US dollars "$US" instead of just "$"


