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

currency_symbols = {
    'EUR' : u'€',
    #'GBP' : u'£', 
    'MXN' : u'MX$',
    'USD' : u'$',
    'USD_NON_US' : u'US$', # For people outside the US, we show the US$ as the symbol instead of $ to prevent confusion
                           # with other international currencies that may also use the US symbol. 
                           # This value must not be passed to paypal as a currency_code as it is not valid - overwrite
                           # it with 'USD' before passing to paypal
    }


# The following mapping is used for automatically setting the correct currency when the user selects a given country. 
# We include two commas after the country code, because this is the format that we have used internally for distinguishing
# countries versus regions and sub-regions.
country_to_currency_map = {
    
    # Get the ISO 3155-1 alpha-2 (2 Letter) country code, which we then use for a lookup of the 
    # appropriate currency to display. 
    
    
    # Note we currently only support a limited set of currencies due to fluctuating exchange rates etc. 
    # Eventually if we see an uptick in traffic from a country, we will add their currency to the list
    # of supported currencies. 
    
    #'AL' : 'ALL', # Albania
    #'DZ' : 'DZD', # Algeria
    'AD' : 'EUR', # Andorra
    #'AO' : 'AOA', # Angola
    #'AQ' : 'USD', # Antarctica
    'AR' : 'ARS', # Argentina
    #'AM' : 'AMD', # Armenia
    #'AU' : 'AUD', # Australia
    'AT' : 'EUR', # Austria
    #'AZ' : 'AZN', # Azerbaijan
    #'BS' : 'BSD', # Bahamas
    #'BH' : 'BHD', # Bahrain
    #'BD' : 'BDT', # Bangladesh
    #'BB' : 'BBD', # Barbados
    #'BY' : 'BYR', # Belarus
    'BE' : 'EUR', # Belgium
    #'BZ' : 'BZD', # Belize
    #'BM' : 'BMD', # Bermuda
    #'BT' : 'BTN', # Bhutan
    #'BO' : 'BOB', # Bolivia
    #'BA' : 'BAM', # Bosnia and Herzegovina
    #'BR' : 'BRL', # Brazil
    #'BN' : 'BND', # Brunei Darussalam
    #'BG' : 'BGN', # Bulgaria
    #'KH' : 'USD', # Cambodia
    #'CA' : 'CAD', # Canada
    #'KY' : 'KYD', # Cayman Islands
    'CL' : 'CLP', # Chile
    #'CN' : 'CNY', # China
    'CO' : 'COP', # Colombia
    #'CR' : 'CRC', # Costa Rica
    #'HR' : 'HRK', # Croatia
    #'CU' : 'CUP', # Cuba
    'CY' : 'EUR', # Cyprus
    #'CZ' : 'CZK', # Czech Republic
    #'DK' : 'DKK', # Denmark
    #'DO' : 'DOP', # Dominican Republic
    #'EC' : 'USD', # Ecuador
    #'EG' : 'EGP', # Egypt
    #'SV' : 'SVC', # El Salvador
    #'EE' : 'EEK', # Estonia
    #'FJ' : 'FJD', # Fiji
    'FI' : 'EUR', # Finland
    'FR' : 'EUR', # France
    'GF' : 'EUR', # French Guiana
    #'PF' : 'CFP', # French Polynesia
    #'GE' : 'GEL', # Georgia
    'DE' : 'EUR', # Germany
    #'GI' : 'GIP', # Gibraltar
    'GR' : 'EUR', # Greece
    #'GL' : 'DKK', # Greenland
    #'GT' : 'GTQ', # Guatemala
    #'GY' : 'GYD', # Guyana
    #'HN' : 'HNL', # Honduras
    #'HK' : 'HKD', # Hong Kong
    #'HU' : 'HUF', # Hungary
    #'IS' : 'ISK', # Iceland
    #'IN' : 'INR', # India
    #'ID' : 'IDR', # Indonesia
    #'IR' : 'IRR', # Iran
    #'IQ' : 'IQD', # Iraq
    'IE' : 'EUR', # Ireland
    #'IL' : 'ILS', # Israel
    'IT' : 'EUR', # Italy
    #'JM' : 'JMD', # Jamaica
    #'JP' : 'JPY', # Japan
    #'JO' : 'JOD', # Jordan
    #'KZ' : 'KZT', # Kazakhstan
    #'KR' : 'KRW', # Korea, South
    #'KW' : 'KWD', # Kuwait
    #'KG' : 'KGS', # Kyrgyzstan
    #'LA' : 'LAK', # Laos
    #'LV' : 'LVL', # Latvia
    #'LB' : 'LBP', # Lebanon
    #'LY' : 'LYD', # Libya
    #'LI' : 'CHF', # Liechtenstein
    #'LT' : 'LTL', # Lithuania
    'LU' : 'EUR', # Luxembourg
    #'MO' : 'HKD', # Macau
    #'MK' : 'MKD', # Macedonia
    #'MY' : 'MYR', # Malaysia
    #'MV' : 'MVR', # Maldives
    'MT' : 'EUR', # Malta
    'MX' : 'MXN', # Mexico
    #'MD' : 'MDL', # Moldova
    'MC' : 'EUR', # Monaco
    #'MN' : 'MNT', # Mongolia
    #'MA' : 'MAD', # Morocco
    'NL' : 'EUR', # Netherlands
    #'NZ' : 'NZD', # New Zealand
    #'NI' : 'NIO', # Nicaragua
    #'NO' : 'NOK', # Norway
    #'OM' : 'OMR', # Oman
    #'PK' : 'PKR', # Pakistan
    #'PA' : 'PAB', # Panama
    #'PG' : 'PGK', # Papua New Guinea
    #'PY' : 'PYG', # Paraguay
    #'PE' : 'PEN', # Peru
    #'PH' : 'PHP', # Philippines
    #'PL' : 'PLN', # Poland
    #'PT' : 'PT', # Portugal
    'PR' : 'USD', # Puerto Rico
    #'QA' : 'QAR', # Qatar
    #'RO' : 'RON', # Romania
    #'RU' : 'RUB', # Russian Federation
    #'SA' : 'SAR', # Saudi Arabia
    #'RS' : 'RSD', # Serbia
    #'SG' : 'SGD', # Singapore
    'SK' : 'EUR', # Slovakia
    'SI' : 'EUR', # Slovenia
    #'ZA' : 'ZAR', # South Africa
    'ES' : 'EUR', # Spain
    #'LK' : 'LKR', # Sri Lanka
    #'SR' : 'SRD', # Suriname
    #'SE' : 'SEK', # Sweden
    #'CH' : 'CHF', # Switzerland
    #'SY' : 'SYP', # Syria
    #'TW' : 'TWD', # Taiwan
    #'TH' : 'THB', # Thailand
    #'TL' : 'USD', # Timor-Leste
    #'TT' : 'TTD', # Trinidad and Tobago
    #'TN' : 'TND', # Tunisia
    #'TR' : 'TRL', # Turkey
    #'TM' : 'TMT', # Turkmenistan
    #'UA' : 'UAH', # Ukraine
    #'AE' : 'AED', # United Arab Emirates
    #'GB' : 'GBP', # United Kingdom
    'US' : 'USD', # United States of America
    #'UY' : 'UYU', # Uruguay
    #'UZ' : 'UZS', # Uzbekistan
    #'VE' : 'VEB', # Venezuela
    #'VN' : 'VND', # Vietnam
    #'EH' : 'MAD', # Western Sahara (use multiple currencies - set to moroccan dirham)
    #'YE' : 'YER', # Yemen

}