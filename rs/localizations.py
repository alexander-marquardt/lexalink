# -*- coding: utf-8 -*-     
# dictionary first element contains the language in which the countries are listed

# Dummy ugettext, so that the translator can find the strings that we are passing into other functions.
# the functions that this is passed into will have the real ugettext
ugettext = lambda s: s


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


from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext as real_ugettext # we cannot use the name ugettext, because it is overloaded
from translation_helpers import ugettext_tuple,  translate_text

import settings, data_struct_utils, utils_top_level

from localization_files import AR, AU, BO, BR, CA, CL, CN, CR, CO, DE, DO, EC, ES, FR, GB, GT, HN, IT, JP, KR, MX, PA, PE, PR, PY, RU,  SV, US, UY, VE, other_countries


############################################

# DO NOT CHANGE THE KEY VALUEs -- even if there is a spelling error. These are used for indexing
# in the database, and changing the key value will cause existing installations to function 
# incorrectly.

important_languages_list = [
    # This is a list of the languages that will appear at the top of the selector.
    # These are also re-declared in the main part of the list so that they will appear twice.
    ('arabic',) +       ugettext_tuple(ugettext('Arabic')),
    ('mandarin',) +     ugettext_tuple(ugettext('Chinese-Mandarin (Guan)')),
    ('english',) +      ugettext_tuple(ugettext('English')),
    ('french',) +       ugettext_tuple(ugettext('French')), 
    ('german',) +       ugettext_tuple(ugettext('German')), 
    ('italian',) +      ugettext_tuple(ugettext('Italian')),
    ('japanese',) +     ugettext_tuple(ugettext('Japanese')),
    ('korean',) +       ugettext_tuple(ugettext('Korean')),
    ('russian',) +      ugettext_tuple(ugettext('Russian')),   
    ('spanish',) +      ugettext_tuple(ugettext('Spanish')),
]


languages_list =  [
    ('arabic',) +       ugettext_tuple(ugettext('Arabic')),
    ('basque',) +       ugettext_tuple(ugettext('Basque')),
    ('bulgarian',) +    ugettext_tuple(ugettext('Bulgarian')),
    ('catalan',) +      ugettext_tuple(ugettext('Catalan')),
    ('mandarin',) +     ugettext_tuple(ugettext('Chinese-Mandarin (Guan)')),
    ('czech',) +        ugettext_tuple(ugettext('Czech')),
    ('danish',) +       ugettext_tuple(ugettext('Danish')),
    ('dutch',) +        ugettext_tuple(ugettext('Dutch')),
    ('english',) +      ugettext_tuple(ugettext('English')),
    ('finnish',) +      ugettext_tuple(ugettext('Finnish')),
    ('french',) +       ugettext_tuple(ugettext('French')), 
    ('galician',) +     ugettext_tuple(ugettext('Galician')),
    ('german',) +       ugettext_tuple(ugettext('German')),
    ('greek',) +        ugettext_tuple(ugettext('Greek')),
    ('hebrew',) +       ugettext_tuple(ugettext('Hebrew')),
    ('hungarian',) +    ugettext_tuple(ugettext('Hungarian')),
    ('italian',) +      ugettext_tuple(ugettext('Italian')),
    ('japanese',) +     ugettext_tuple(ugettext('Japanese')),
    ('korean',) +       ugettext_tuple(ugettext('Korean')),
    ('kurdish',) +      ugettext_tuple(ugettext('Kurdish')), 
    ('norewegian',) +   ugettext_tuple(ugettext('Norwegian')),
    ('persian',) +      ugettext_tuple(ugettext('Persian')),
    ('polish',) +       ugettext_tuple(ugettext('Polish')),
    ('portuguese',) +   ugettext_tuple(ugettext('Portuguese')),
    ('romanian',) +     ugettext_tuple(ugettext('Romanian')),
    ('russian',) +      ugettext_tuple(ugettext('Russian')),
    ('serbian',) +      ugettext_tuple(ugettext('Serbian')),
    ('slovak',) +       ugettext_tuple(ugettext('Slovak')),
    ('spanish',) +      ugettext_tuple(ugettext('Spanish')),
    ('sweedish',) +     ugettext_tuple(ugettext('Swedish')), #key is mis-spelled - do not change without fixing database
    ('turkish',) +      ugettext_tuple(ugettext('Turkish')),
    ('ukrainian',) +    ugettext_tuple(ugettext('Ukrainian')),
]
    
if settings.BUILD_NAME == 'language_build':
    languages_list +=  [    
        # Additional languages, but not for the dating websites
        
        ('gan',) +          ugettext_tuple(ugettext('Chinese-Gan')),
        ('hakka',) +        ugettext_tuple(ugettext('Chinese-Hakka (Kejia)')),
        ('jinyu',) +        ugettext_tuple(ugettext('Chinese-Jin')),
        ('min_nan',) +      ugettext_tuple(ugettext('Chinese-Min')),
        ('wu',) +           ugettext_tuple(ugettext('Chinese-Wu')),
        ('xiang',) +        ugettext_tuple(ugettext('Chinese-Xiang')),
        ('yue',) +          ugettext_tuple(ugettext('Chinese-Cantonese (Yue)')),            
        
        ('azerbaijani',) +   ugettext_tuple(ugettext('Azerbaijani')),
        #('awadhi',) +        ugettext_tuple(ugettext('Awadhi')),
        ('bengali',) +       ugettext_tuple(ugettext('Bengali')),
        ('bhojpuri',) +      ugettext_tuple(ugettext('Bhojpuri')),
        ('estonian',) +      ugettext_tuple(ugettext('Estonian')),
        ('georgian',) +      ugettext_tuple(ugettext('Georgian')),
        ('gujarati',) +      ugettext_tuple(ugettext('Gujarati')),
        ('hausa',) +         ugettext_tuple(ugettext('Hausa')),
        ('hindi',) +        ugettext_tuple(ugettext('Hindi')),
        ('indonesian',) +   ugettext_tuple(ugettext('Indonesian')),
        ('javanese',) +     ugettext_tuple(ugettext('Javanese (basa Jawa)')),
        ('kannada',) +      ugettext_tuple(ugettext('Kannada')),
        ('latvian',) +      ugettext_tuple(ugettext('Latvian')),
        ('lithuanian',) +   ugettext_tuple(ugettext('Lithuanian')),
        ('malay',)  +       ugettext_tuple(ugettext('Malay')),
        ('malayalam',) +    ugettext_tuple(ugettext('Malayalam')),
        ('marathi',) +      ugettext_tuple(ugettext('Marathi')),
        ('oriya',) +        ugettext_tuple(ugettext('Oriya')),
        ('punjabi',) +      ugettext_tuple(ugettext('Punjabi')),
        ('sindhi',) +       ugettext_tuple(ugettext('Sindhi')),
        ('tagalog',) +      ugettext_tuple(ugettext('Tagalog')),
        ('tamil',) +        ugettext_tuple(ugettext('Tamil')),
        ('tatar',) +        ugettext_tuple(ugettext('Tatar')),
        ('telugu',) +       ugettext_tuple(ugettext('Telugu')),        
        ('thai',) +         ugettext_tuple(ugettext('Thai')),        
        ('urdu',) +         ugettext_tuple(ugettext('Urdu')),
        ('uzbek',) +        ugettext_tuple(ugettext('Uzbek')),
        ('vietnamese',) +   ugettext_tuple(ugettext('Vietnamese')),

        ('yoruba',) +       ugettext_tuple(ugettext('Yoruba')),          
    ]
    
    
# we use the following to translate from the browser language code to the languages_list
# values. This is used for setting the inital value for the languages that the user speaks.

language_code_transaltion = {'en' : 'english', 'es' : 'spanish'}

# This data structure contains the language-appropriate country names for the languages 
# in which our system will be available.
# countries will be accessed by their two digit ISO 3166 (and sometimes HASC codes when ISO 3166 not available)
# codes in the database so that they have a consistent access mechanism across all languages. 


if settings.BUILD_NAME != "language_build":
    
    important_countries_list = [       
        # These countries will appear twice in the country/location list. Once at the beginning
        # and again in the entire list.
        ("AR",) +  ugettext_tuple(ugettext("AR")), # Argentina
        #("AU",) +  ugettext_tuple(ugettext("AU")), # Australia
        #("CA",) +  ugettext_tuple(ugettext("CA")), # Canada
        ("CL",) +  ugettext_tuple(ugettext("CL")), # Chile
        ("CO",) +  ugettext_tuple(ugettext("CO")), # Colombia
        ("CR",) +  ugettext_tuple(ugettext("CR")), # Costa Rica
        ("MX",) +  ugettext_tuple(ugettext("MX")), # Mexico 
        ("PE",) +  ugettext_tuple(ugettext("PE")), # Peru        
        ("ES",) +  ugettext_tuple(ugettext("ES")), # Spain
        ("US",) +  ugettext_tuple(ugettext("US")), # United States of America
        ("GB",) +  ugettext_tuple(ugettext("GB")), # United Kingdom
        #("VE",) +  ugettext_tuple(ugettext("VE")), # Venezuela
        ]
    
    
else:
    important_countries_list = [
        # These countries will appear twice in the country/location list. Once at the beginning
        # and again in the entire list.
        ("AU",) +  ugettext_tuple(ugettext("AU")), # Australia
        ("CA",) +  ugettext_tuple(ugettext("CA")), # Canada                
        ("CN",) +  ugettext_tuple(ugettext("CN")), # China
        ("FR",) +  ugettext_tuple(ugettext("FR")), # France
        ("DE",) +  ugettext_tuple(ugettext("DE")), # Germany
        ("IT",) +  ugettext_tuple(ugettext("IT")), # Italy
        ("JP",) +  ugettext_tuple(ugettext("JP")), # Japan
        ("KR",) +  ugettext_tuple(ugettext("KR")), # Korea (South)
        ("MX",) +  ugettext_tuple(ugettext("MX")), # Mexico    
        ("RU",) +  ugettext_tuple(ugettext("RU")), # Russian Federation
        ("ES",) +  ugettext_tuple(ugettext("ES")), # Spain
        ("GB",) +  ugettext_tuple(ugettext("GB")), # United Kingdom
        ("US",) +  ugettext_tuple(ugettext("US")), # United States of America        
        ]

countries_list = [
    # Note: the ugettext_tuple will overwrite the given code for ALL languages (including english)
    # to reflect the country name in the given language. We have used the ISO code
    # as the tranlslation key because it is easier to find translations keyed to ISO code on the internet, than
    # to find them keyed to english)
    
    # Note: In order to make it easier for our principal clients to find their countries, we will show
    # the most important countries first, followed by the rest of the countries
    # with the important countries repeated in the full list.
    
    # This list should include all countries that are listed in the important_countries_list
    
    # Note: I have commented out countries with low populations and low GDP per capita.
    
    #("AF",) +  ugettext_tuple(ugettext("AF")), # Afghanistan
    #("AX",) +  ugettext_tuple(ugettext("AX")), # Åland
    ("AL",) +  ugettext_tuple(ugettext("AL")), # Albania
    ("DZ",) +  ugettext_tuple(ugettext("DZ")), # Algeria
    #("AS",) +  ugettext_tuple(ugettext("AS")), # American Samoa
    ("AD",) +  ugettext_tuple(ugettext("AD")), # Andorra
    ("AO",) +  ugettext_tuple(ugettext("AO")), # Angola
    #("AI",) +  ugettext_tuple(ugettext("AI")), # Anguilla
    ("AQ",) +  ugettext_tuple(ugettext("AQ")), # Antarctica
    #("AG",) +  ugettext_tuple(ugettext("AG")), # Antigua and Barbuda
    ("AR",) +  ugettext_tuple(ugettext("AR")), # Argentina
    ("AM",) +  ugettext_tuple(ugettext("AM")), # Armenia
    #("AW",) +  ugettext_tuple(ugettext("AW")), # Aruba
    ("AU",) +  ugettext_tuple(ugettext("AU")), # Australia
    ("AT",) +  ugettext_tuple(ugettext("AT")), # Austria
    ("AZ",) +  ugettext_tuple(ugettext("AZ")), # Azerbaijan
    ("BS",) +  ugettext_tuple(ugettext("BS")), # Bahamas
    ("BH",) +  ugettext_tuple(ugettext("BH")), # Bahrain
    ("BD",) +  ugettext_tuple(ugettext("BD")), # Bangladesh
    ("BB",) +  ugettext_tuple(ugettext("BB")), # Barbados
    ("BY",) +  ugettext_tuple(ugettext("BY")), # Belarus
    ("BE",) +  ugettext_tuple(ugettext("BE")), # Belgium
    ("BZ",) +  ugettext_tuple(ugettext("BZ")), # Belize
    #("BJ",) +  ugettext_tuple(ugettext("BJ")), # Benin
    ("BM",) +  ugettext_tuple(ugettext("BM")), # Bermuda
    ("BT",) +  ugettext_tuple(ugettext("BT")), # Bhutan
    ("BO",) +  ugettext_tuple(ugettext("BO")), # Bolivia
    ("BA",) +  ugettext_tuple(ugettext("BA")), # Bosnia and Herzegovina
    #("BW",) +  ugettext_tuple(ugettext("BW")), # Botswana
    #("BV",) +  ugettext_tuple(ugettext("BV")), # Bouvet Island
    ("BR",) +  ugettext_tuple(ugettext("BR")), # Brazil
    #("IO",) +  ugettext_tuple(ugettext("IO")), # British Indian Ocean Territory
    ("BN",) +  ugettext_tuple(ugettext("BN")), # Brunei Darussalam
    ("BG",) +  ugettext_tuple(ugettext("BG")), # Bulgaria
    #("BF",) +  ugettext_tuple(ugettext("BF")), # Burkina Faso
    #("BI",) +  ugettext_tuple(ugettext("BI")), # Burundi
    ("KH",) +  ugettext_tuple(ugettext("KH")), # Cambodia
    #("CM",) +  ugettext_tuple(ugettext("CM")), # Cameroon
    ("CA",) +  ugettext_tuple(ugettext("CA")), # Canada
    #("CV",) +  ugettext_tuple(ugettext("CV")), # Cape Verde
    ("KY",) +  ugettext_tuple(ugettext("KY")), # Cayman Islands
    #("CF",) +  ugettext_tuple(ugettext("CF")), # Central African Republic
    #("TD",) +  ugettext_tuple(ugettext("TD")), # Chad
    ("CL",) +  ugettext_tuple(ugettext("CL")), # Chile
    ("CN",) +  ugettext_tuple(ugettext("CN")), # China
    #("CX",) +  ugettext_tuple(ugettext("CX")), # Christmas Island
    #("CC",) +  ugettext_tuple(ugettext("CC")), # Cocos (Keeling) Islands
    ("CO",) +  ugettext_tuple(ugettext("CO")), # Colombia
    #("KM",) +  ugettext_tuple(ugettext("KM")), # Comoros
    #("CG",) +  ugettext_tuple(ugettext("CG")), # Congo (Brazzaville)
    #("CD",) +  ugettext_tuple(ugettext("CD")), # Congo (Kinshasa)
    #("CK",) +  ugettext_tuple(ugettext("CK")), # Cook Islands
    ("CR",) +  ugettext_tuple(ugettext("CR")), # Costa Rica
    #("CI",) +  ugettext_tuple(ugettext("CI")), # Côte d'Ivoire
    ("HR",) +  ugettext_tuple(ugettext("HR")), # Croatia
    ("CU",) +  ugettext_tuple(ugettext("CU")), # Cuba
    ("CY",) +  ugettext_tuple(ugettext("CY")), # Cyprus
    ("CZ",) +  ugettext_tuple(ugettext("CZ")), # Czech Republic
    ("DK",) +  ugettext_tuple(ugettext("DK")), # Denmark
    #("DJ",) +  ugettext_tuple(ugettext("DJ")), # Djibouti
    #("DM",) +  ugettext_tuple(ugettext("DM")), # Dominica
    ("DO",) +  ugettext_tuple(ugettext("DO")), # Dominican Republic
    ("EC",) +  ugettext_tuple(ugettext("EC")), # Ecuador
    ("EG",) +  ugettext_tuple(ugettext("EG")), # Egypt
    ("SV",) +  ugettext_tuple(ugettext("SV")), # El Salvador
    #("GQ",) +  ugettext_tuple(ugettext("GQ")), # Equatorial Guinea
    #("ER",) +  ugettext_tuple(ugettext("ER")), # Eritrea
    ("EE",) +  ugettext_tuple(ugettext("EE")), # Estonia
    #("ET",) +  ugettext_tuple(ugettext("ET")), # Ethiopia
    #("FK",) +  ugettext_tuple(ugettext("FK")), # Falkland Islands
    #("FO",) +  ugettext_tuple(ugettext("FO")), # Faroe Islands
    ("FJ",) +  ugettext_tuple(ugettext("FJ")), # Fiji
    ("FI",) +  ugettext_tuple(ugettext("FI")), # Finland
    ("FR",) +  ugettext_tuple(ugettext("FR")), # France
    ("GF",) +  ugettext_tuple(ugettext("GF")), # French Guiana
    ("PF",) +  ugettext_tuple(ugettext("PF")), # French Polynesia
    #("TF",) +  ugettext_tuple(ugettext("TF")), # French Southern Lands
    #("GA",) +  ugettext_tuple(ugettext("GA")), # Gabon
    #("GM",) +  ugettext_tuple(ugettext("GM")), # Gambia
    ("GE",) +  ugettext_tuple(ugettext("GE")), # Georgia
    ("DE",) +  ugettext_tuple(ugettext("DE")), # Germany
    #("GH",) +  ugettext_tuple(ugettext("GH")), # Ghana
    ("GI",) +  ugettext_tuple(ugettext("GI")), # Gibraltar
    ("GR",) +  ugettext_tuple(ugettext("GR")), # Greece
    ("GL",) +  ugettext_tuple(ugettext("GL")), # Greenland
    #("GD",) +  ugettext_tuple(ugettext("GD")), # Grenada
    #("GP",) +  ugettext_tuple(ugettext("GP")), # Guadeloupe
    #("GU",) +  ugettext_tuple(ugettext("GU")), # Guam
    ("GT",) +  ugettext_tuple(ugettext("GT")), # Guatemala
    #("GG",) +  ugettext_tuple(ugettext("GG")), # Guernsey
    #("GN",) +  ugettext_tuple(ugettext("GN")), # Guinea
    #("GW",) +  ugettext_tuple(ugettext("GW")), # Guinea-Bissau
    ("GY",) +  ugettext_tuple(ugettext("GY")), # Guyana
    #("HT",) +  ugettext_tuple(ugettext("HT")), # Haiti
    #("HM",) +  ugettext_tuple(ugettext("HM")), # Heard and McDonald Islands
    ("HN",) +  ugettext_tuple(ugettext("HN")), # Honduras
    ("HK",) +  ugettext_tuple(ugettext("HK")), # Hong Kong
    ("HU",) +  ugettext_tuple(ugettext("HU")), # Hungary
    ("IS",) +  ugettext_tuple(ugettext("IS")), # Iceland
    ("IN",) +  ugettext_tuple(ugettext("IN")), # India
    ("ID",) +  ugettext_tuple(ugettext("ID")), # Indonesia
    ("IR",) +  ugettext_tuple(ugettext("IR")), # Iran
    ("IQ",) +  ugettext_tuple(ugettext("IQ")), # Iraq
    ("IE",) +  ugettext_tuple(ugettext("IE")), # Ireland
    #("IM",) +  ugettext_tuple(ugettext("IM")), # Isle of Man
    ("IL",) +  ugettext_tuple(ugettext("IL")), # Israel
    ("IT",) +  ugettext_tuple(ugettext("IT")), # Italy
    ("JM",) +  ugettext_tuple(ugettext("JM")), # Jamaica
    ("JP",) +  ugettext_tuple(ugettext("JP")), # Japan
    #("JE",) +  ugettext_tuple(ugettext("JE")), # Jersey
    ("JO",) +  ugettext_tuple(ugettext("JO")), # Jordan
    ("KZ",) +  ugettext_tuple(ugettext("KZ")), # Kazakhstan
    #("KE",) +  ugettext_tuple(ugettext("KE")), # Kenya
    #("KI",) +  ugettext_tuple(ugettext("KI")), # Kiribati
    #("KP",) +  ugettext_tuple(ugettext("KP")), # Korea, North
    ("KR",) +  ugettext_tuple(ugettext("KR")), # Korea, South
    ("KW",) +  ugettext_tuple(ugettext("KW")), # Kuwait
    ("KG",) +  ugettext_tuple(ugettext("KG")), # Kyrgyzstan
    ("LA",) +  ugettext_tuple(ugettext("LA")), # Laos
    ("LV",) +  ugettext_tuple(ugettext("LV")), # Latvia
    ("LB",) +  ugettext_tuple(ugettext("LB")), # Lebanon
    #("LS",) +  ugettext_tuple(ugettext("LS")), # Lesotho
    #("LR",) +  ugettext_tuple(ugettext("LR")), # Liberia
    ("LY",) +  ugettext_tuple(ugettext("LY")), # Libya
    ("LI",) +  ugettext_tuple(ugettext("LI")), # Liechtenstein
    ("LT",) +  ugettext_tuple(ugettext("LT")), # Lithuania
    ("LU",) +  ugettext_tuple(ugettext("LU")), # Luxembourg
    ("MO",) +  ugettext_tuple(ugettext("MO")), # Macau
    ("MK",) +  ugettext_tuple(ugettext("MK")), # Macedonia
    #("MG",) +  ugettext_tuple(ugettext("MG")), # Madagascar
    #("MW",) +  ugettext_tuple(ugettext("MW")), # Malawi
    ("MY",) +  ugettext_tuple(ugettext("MY")), # Malaysia
    ("MV",) +  ugettext_tuple(ugettext("MV")), # Maldives
    #("ML",) +  ugettext_tuple(ugettext("ML")), # Mali
    ("MT",) +  ugettext_tuple(ugettext("MT")), # Malta
    #("MH",) +  ugettext_tuple(ugettext("MH")), # Marshall Islands
    #("MQ",) +  ugettext_tuple(ugettext("MQ")), # Martinique
    #("MR",) +  ugettext_tuple(ugettext("MR")), # Mauritania
    #("MU",) +  ugettext_tuple(ugettext("MU")), # Mauritius
    #("YT",) +  ugettext_tuple(ugettext("YT")), # Mayotte
    ("MX",) +  ugettext_tuple(ugettext("MX")), # Mexico
    #("FM",) +  ugettext_tuple(ugettext("FM")), # Micronesia
    ("MD",) +  ugettext_tuple(ugettext("MD")), # Moldova
    ("MC",) +  ugettext_tuple(ugettext("MC")), # Monaco
    ("MN",) +  ugettext_tuple(ugettext("MN")), # Mongolia
    #("ME",) +  ugettext_tuple(ugettext("ME")), # Montenegro
    #("MS",) +  ugettext_tuple(ugettext("MS")), # Montserrat
    ("MA",) +  ugettext_tuple(ugettext("MA")), # Morocco
    #("MZ",) +  ugettext_tuple(ugettext("MZ")), # Mozambique
    #("MM",) +  ugettext_tuple(ugettext("MM")), # Myanmar
    #("NA",) +  ugettext_tuple(ugettext("NA")), # Namibia
    #("NR",) +  ugettext_tuple(ugettext("NR")), # Nauru
    #("NP",) +  ugettext_tuple(ugettext("NP")), # Nepal
    ("NL",) +  ugettext_tuple(ugettext("NL")), # Netherlands
    #("AN",) +  ugettext_tuple(ugettext("AN")), # Netherlands Antilles
    #("NC",) +  ugettext_tuple(ugettext("NC")), # New Caledonia
    ("NZ",) +  ugettext_tuple(ugettext("NZ")), # New Zealand
    ("NI",) +  ugettext_tuple(ugettext("NI")), # Nicaragua
    #("NE",) +  ugettext_tuple(ugettext("NE")), # Niger
    #("NG",) +  ugettext_tuple(ugettext("NG")), # Nigeria
    #("NU",) +  ugettext_tuple(ugettext("NU")), # Niue
    #("NF",) +  ugettext_tuple(ugettext("NF")), # Norfolk Island
    #("MP",) +  ugettext_tuple(ugettext("MP")), # Northern Mariana Islands
    ("NO",) +  ugettext_tuple(ugettext("NO")), # Norway
    ("OM",) +  ugettext_tuple(ugettext("OM")), # Oman
    ("PK",) +  ugettext_tuple(ugettext("PK")), # Pakistan
    #("PW",) +  ugettext_tuple(ugettext("PW")), # Palau
    #("PS",) +  ugettext_tuple(ugettext("PS")), # Palestine
    ("PA",) +  ugettext_tuple(ugettext("PA")), # Panama
    ("PG",) +  ugettext_tuple(ugettext("PG")), # Papua New Guinea
    ("PY",) +  ugettext_tuple(ugettext("PY")), # Paraguay
    ("PE",) +  ugettext_tuple(ugettext("PE")), # Peru
    ("PH",) +  ugettext_tuple(ugettext("PH")), # Philippines
    #("PN",) +  ugettext_tuple(ugettext("PN")), # Pitcairn
    ("PL",) +  ugettext_tuple(ugettext("PL")), # Poland
    ("PT",) +  ugettext_tuple(ugettext("PT")), # Portugal
    ("PR",) +  ugettext_tuple(ugettext("PR")), # Puerto Rico
    ("QA",) +  ugettext_tuple(ugettext("QA")), # Qatar
    #("RE",) +  ugettext_tuple(ugettext("RE")), # Reunion
    ("RO",) +  ugettext_tuple(ugettext("RO")), # Romania
    ("RU",) +  ugettext_tuple(ugettext("RU")), # Russian Federation
    #("RW",) +  ugettext_tuple(ugettext("RW")), # Rwanda
    #("BL",) +  ugettext_tuple(ugettext("BL")), # Saint Barthélemy
    #("SH",) +  ugettext_tuple(ugettext("SH")), # Saint Helena
    #("KN",) +  ugettext_tuple(ugettext("KN")), # Saint Kitts and Nevis
    #("LC",) +  ugettext_tuple(ugettext("LC")), # Saint Lucia
    #("MF",) +  ugettext_tuple(ugettext("MF")), # Saint Martin (French part)
    #("PM",) +  ugettext_tuple(ugettext("PM")), # Saint Pierre and Miquelon
    #("VC",) +  ugettext_tuple(ugettext("VC")), # Grenadines
    #("WS",) +  ugettext_tuple(ugettext("WS")), # Samoa
    #("SM",) +  ugettext_tuple(ugettext("SM")), # San Marino
    #("ST",) +  ugettext_tuple(ugettext("ST")), # Sao Tome and Principe
    ("SA",) +  ugettext_tuple(ugettext("SA")), # Saudi Arabia
    #("SN",) +  ugettext_tuple(ugettext("SN")), # Senegal
    ("RS",) +  ugettext_tuple(ugettext("RS")), # Serbia
    #("SC",) +  ugettext_tuple(ugettext("SC")), # Seychelles
    #("SL",) +  ugettext_tuple(ugettext("SL")), # Sierra Leone
    ("SG",) +  ugettext_tuple(ugettext("SG")), # Singapore
    ("SK",) +  ugettext_tuple(ugettext("SK")), # Slovakia
    ("SI",) +  ugettext_tuple(ugettext("SI")), # Slovenia
    #("SB",) +  ugettext_tuple(ugettext("SB")), # Solomon Islands
    #("SO",) +  ugettext_tuple(ugettext("SO")), # Somalia
    ("ZA",) +  ugettext_tuple(ugettext("ZA")), # South Africa
    #("GS",) +  ugettext_tuple(ugettext("GS")), # Sandwich Islands
    ("ES",) +  ugettext_tuple(ugettext("ES")), # Spain
    ("LK",) +  ugettext_tuple(ugettext("LK")), # Sri Lanka
    #("SD",) +  ugettext_tuple(ugettext("SD")), # Sudan
    ("SR",) +  ugettext_tuple(ugettext("SR")), # Suriname
    #("SJ",) +  ugettext_tuple(ugettext("SJ")), # Svalbard and JAan Mayen Islands
    #("SZ",) +  ugettext_tuple(ugettext("SZ")), # Swaziland
    ("SE",) +  ugettext_tuple(ugettext("SE")), # Sweden
    ("CH",) +  ugettext_tuple(ugettext("CH")), # Switzerland
    ("SY",) +  ugettext_tuple(ugettext("SY")), # Syria
    ("TW",) +  ugettext_tuple(ugettext("TW")), # Taiwan
    #("TJ",) +  ugettext_tuple(ugettext("TJ")), # Tajikistan
    #("TZ",) +  ugettext_tuple(ugettext("TZ")), # Tanzania
    ("TH",) +  ugettext_tuple(ugettext("TH")), # Thailand
    ("TL",) +  ugettext_tuple(ugettext("TL")), # Timor-Leste
    #("TG",) +  ugettext_tuple(ugettext("TG")), # Togo
    #("TK",) +  ugettext_tuple(ugettext("TK")), # Tokelau
    #("TO",) +  ugettext_tuple(ugettext("TO")), # Tonga
    ("TT",) +  ugettext_tuple(ugettext("TT")), # Trinidad and Tobago
    ("TN",) +  ugettext_tuple(ugettext("TN")), # Tunisia
    ("TR",) +  ugettext_tuple(ugettext("TR")), # Turkey
    ("TM",) +  ugettext_tuple(ugettext("TM")), # Turkmenistan
    #("TC",) +  ugettext_tuple(ugettext("TC")), # Turks and Caicos Islands
    #("TV",) +  ugettext_tuple(ugettext("TV")), # Tuvalu
    #("UG",) +  ugettext_tuple(ugettext("UG")), # Uganda
    ("UA",) +  ugettext_tuple(ugettext("UA")), # Ukraine
    ("AE",) +  ugettext_tuple(ugettext("AE")), # United Arab Emirates
    ("GB",) +  ugettext_tuple(ugettext("GB")), # United Kingdom
    #("UM",) +  ugettext_tuple(ugettext("UM")), # United States Minor Outlying Islands
    ("US",) +  ugettext_tuple(ugettext("US")), # United States of America
    ("UY",) +  ugettext_tuple(ugettext("UY")), # Uruguay
    ("UZ",) +  ugettext_tuple(ugettext("UZ")), # Uzbekistan
    #("VU",) +  ugettext_tuple(ugettext("VU")), # Vanuatu
    #("VA",) +  ugettext_tuple(ugettext("VA")), # Vatican City
    ("VE",) +  ugettext_tuple(ugettext("VE")), # Venezuela
    ("VN",) +  ugettext_tuple(ugettext("VN")), # Vietnam
    #("VG",) +  ugettext_tuple(ugettext("VG")), # Virgin Islands, British
    #("VI",) +  ugettext_tuple(ugettext("VI")), # Virgin Islands, U.S.
    #("WF",) +  ugettext_tuple(ugettext("WF")), # Wallis and Futuna Islands
    ("EH",) +  ugettext_tuple(ugettext("EH")), # Western Sahara
    ("YE",) +  ugettext_tuple(ugettext("YE")), # Yemen
    #("ZM",) +  ugettext_tuple(ugettext("ZM")), # Zambia
    #("ZW",) +  ugettext_tuple(ugettext("ZW")), # Zimbabwe
]

forbidden_countries = {
    "BJ" :"Benin",
    "BT" :"Bhutan",
    "BW" :"Botswana",
    "BF" :"Burkina Faso",
    "BI" :"Burundi",
    "CM" :"Cameroon",
    "CV" :"Cape Verde",
    "CF" :"Central African Republic",
    "TD" :"Chad",
    "KM" :"Comoros",
    "CG" :"Congo (Brazzaville)",
    "CD" :"Congo (Kinshasa)",
    "CI" :"Cote d'Ivoire",
    "DJ" :"Djibouti",
    "GQ" :"Equatorial Guinea",
    "ER" :"Eritrea",
    "ET" :"Ethiopia",
    "GA" :"Gabon",
    "GM" :"Gambia",
    "GH" :"Ghana",
    "GN" :"Guinea",
    "GW" :"Guinea-Bissau",
    "KE" :"Kenya",
    "KI" :"Kiribati",
    "LS" :"Lesotho",
    "LR" :"Liberia",
    "MG" :"Madagascar",
    "MW" :"Malawi",
    "ML" :"Mali",
    "MZ" :"Mozambique",
    "MM" :"Myanmar",
    "NA" :"Namibia",
    "NP" :"Nepal",
    "NE" :"Niger",
    "NG" :"Nigeria",
    "RW" :"Rwanda",
    "SN" :"Senegal",
    "SC" :"Seychelles",
    "SL" :"Sierra Leone",
    "SO" :"Somalia",
    "SD" :"Sudan",
    "SZ" :"Swaziland",
    "TZ" :"Tanzania",
    "TG" :"Togo",
    "TO" :"Tonga",
    "UG" :"Uganda",
    "ZM" :"Zambia",
    "ZW" :"Zimbabwe",
}

#################


# Regions will only be stored in the region-appropriate language (ie. only one region list per country)
# In order to allow indexing into the database without unicode, the ascii compliant ISO 3166-2 code for 
# each region will be used as an index. 

# DO NOT CHANGE REGION CODES -- even if they are incorrect, unless you are aware
# of the implications on the database interactions. These codes are used for 
# indexing the different regions, and if codes are modified, then regions
# previously stored in the database (as a code) will have undefined values.
#
# By convention (of mine), regions that are numbers have included the country in the region code,
# and regions that are letters do not include the country code in the region code.
region_list = {}


region_list['AR'] = AR.AR_regions # Argentina
region_list['AU'] = AU.AU_regions # Australia
region_list['BZ'] = other_countries.BZ_regions # Belice
region_list['BO'] = BO.BO_regions # Bolivia
region_list['BR'] = BR.BR_regions # Brazil
region_list['CA'] = CA.CA_regions # Canada
region_list['CL'] = CL.CL_regions # Chile
region_list['CN'] = CN.CN_regions # China
region_list['CO'] = CO.CO_regions # Colombia
region_list['CR'] = CR.CR_regions # Costa Rica
region_list['DO'] = DO.DO_regions # Dominican republic
region_list['EC'] = EC.EC_regions # Ecuador
region_list['SV'] = SV.SV_regions # El Salvidor
region_list['GB'] = GB.GB_regions # United Kingdom (UK)
region_list['FR'] = FR.FR_regions # France
region_list['DE'] = DE.DE_regions # Germany
region_list['GT'] = GT.GT_regions # Guatemala
region_list['HN'] = HN.HN_regions #Honduras
region_list['IT'] = IT.IT_regions # Italy
region_list['JP'] = JP.JP_regions # Japan
region_list['KR'] = KR.KR_regions # Korea (South)
region_list['PH'] = other_countries.PH_regions # Philipines
region_list['MX'] = MX.MX_regions # Mexico
region_list['MA'] = other_countries.MA_regions #Morroco
region_list['NI'] = other_countries.NI_regions #Nicaragua
region_list['PA'] = PA.PA_regions # Panama
region_list['PY'] = PY.PY_regions # Paraguay
region_list['PT'] = other_countries.PT_regions # Portugal
region_list['PE'] = PE.PE_regions # Peru
region_list['PR'] = PR.PR_regions # Puerto Rico
region_list['RU'] = RU.RU_regions # Russian Federation
region_list['US'] = US.US_regions # United States
region_list['ES'] = ES.ES_regions # Spain
region_list['UY'] = UY.UY_regions # Uruguay
# Venezuela
region_list['VE'] = VE.VE_regions # Venezuela


def create_tuple(encoding, name) :
    # creates a tuple consisting of encoding and name
    comma_seperated_array = []
    comma_seperated_array.append(encoding)
    comma_seperated_array.append(name)
    comma_seperated_tuple = tuple(comma_seperated_array)
    return comma_seperated_tuple


def country_list_convert_location_codes_to_comma_seperated(countries_list_of_tuples):
    
    new_list = []
    
    for curr_tuple in countries_list_of_tuples:
        tuple_key = curr_tuple[0]  
        new_tuple_key_fake_list = [] # I do this because I couldn't figure out how to join a non-array value with an array
        new_tuple_key_fake_list.append("%s,," % tuple_key)
        remainder_of_tuple = list(curr_tuple[1:])
        new_array = new_tuple_key_fake_list + remainder_of_tuple
        new_tuple = tuple(new_array)
        new_list.append(new_tuple)
    
    return new_list
    
###############

# defines which colum in the countries_list (and many other) tuples contains the language-correct
# version of the country names.

input_field_lang_idx = {}
lang_code_by_idx = []

# the following will hold an array where each element is a list of tuples in the form (CountryCode, CountryName)
# The array will be indexed by the current language, and will be sorted based on the Country Names.
array_of_important_country_tuples = []
array_of_country_tuples = [] 
dict_of_region_array_tuples = {} # indexed by country code. ie. dict_of_region_array_tuples['CA,,'] will return a list containing (tuples of) all the regions in Canada.
dict_of_sub_region_array_tuples = {} # indexed by country code and region code. ie. dict_of_sub_region_array_tuples['CA,,']['MB,,] will 
                                     # return a list containing (tuples of) all the sub-regions in Manitoba, Canada.

for lang_idx, language_tuple in enumerate(settings.LANGUAGES):
    language = language_tuple[0]
    

    # the input fields language does not have an offset with respect to the ordering of the languages. 
    # Input fields refers to text fields that are not tied to the database,
    # and to internal data structures that do not have a key as the first entry of the tuple/array.
    input_field_lang_idx[language] = lang_idx 
    lang_code_by_idx.append(language)
        
    # The following code snippet is used for computing the array_of_country_tuples, 
    # which is a list containing pairs of country key and country name in the current language. 
    # Currently this is only computed upon import of this module.    

    comma_seperated_important_countries_list = country_list_convert_location_codes_to_comma_seperated(important_countries_list)
    
    list_of_important_pairs_in_current_language = \
     data_struct_utils.get_pairs_in_current_langauge(comma_seperated_important_countries_list, lang_idx, do_sort = True)
    array_of_important_country_tuples.append(list_of_important_pairs_in_current_language)
    
    comma_seperated_important_countries_list = country_list_convert_location_codes_to_comma_seperated(countries_list)
        
    list_of_pairs_in_current_language = \
     data_struct_utils.get_pairs_in_current_langauge(comma_seperated_important_countries_list, lang_idx, do_sort = True)
    array_of_country_tuples.append(list_of_pairs_in_current_language)
    


#############
# This is an array that will hold a flattend htmlish version of available
# locations which can be entered for searches and for profile information.

country_options= [] # indexed by country_options[lang_idx][country_code] -> gives country name in current lang
country_search_options = [] # same as country_options, but will contain an option for "All countries"

# note: the following two vars have been stored as html directly for efficiency in passing back
# from the ajax calls.
region_options_html = {}
sub_region_options_html = {}

# the dictionary will contain the code that allows for lookups of the location in the 
# current language, given the location code. 
location_dict = [] 


def get_country_option_html(country_tuple):
    
    country_letter_code = country_tuple[0]
    country_name_in_current_language = country_tuple[1]
    option_html =u"<option value='%s'>%s\n" % ( country_letter_code, country_name_in_current_language)   
            
    return (option_html, country_letter_code)
            

                
################################
def populate_country_options():
    # this should only be called once by default, and this should ideally occur
    # the first time this module is included. Therefore, we have placed an explicit
    # call to this function at the end of this module. This will populate the 
    # country_options array when this module is imported.
    
    for lang_idx, language_tuple in enumerate(settings.LANGUAGES):
        
        lang_code = language_tuple[0]
        
        country_options.append([])
        country_search_options.append([])
        location_dict.append({})
        
        # Only append the following to the search values -- not valid for logging in
        # or for selecting where the user lives.
        option_html = u"<option value='----'>%s\n" % (translate_text(lang_code, (ugettext("All Countries"))))
        country_search_options[lang_idx].append(option_html)
        
        # Sort the "important" country list
        for (country_tuple) in array_of_important_country_tuples[lang_idx]:
            (option_html, country_encoded) = get_country_option_html(country_tuple)
            country_options[lang_idx].append(option_html)
            country_search_options[lang_idx].append(option_html)
            
        country_options[lang_idx].append(u"<option value='----'>----\n")    
        country_search_options[lang_idx].append(u"<option value='----'>----\n")    
        
        option_html = u"<option value='----'>%s\n" % (translate_text(lang_code, (ugettext("All Countries"))))
        country_search_options[lang_idx].append(option_html)
        
        # Sort the "normal" country list
        for (country_tuple) in array_of_country_tuples[lang_idx]:
            (option_html, country_encoded) = get_country_option_html(country_tuple)
            country_options[lang_idx].append(option_html)
            country_search_options[lang_idx].append(option_html)
            location_dict[lang_idx][country_encoded] = country_tuple[1]
            
        
        # We setup data structure for the countries for which we have regional data
        for country_letter_code in region_list.keys():
            # each country will have a list of regions (if they are defined).  
            # Note: Regions are not language dependent - they are displayed in the native language
            # of the country which the region is in.
            country_encoded = "%s,%s,%s" % (country_letter_code, '','')
            region_options_html[country_encoded] = ''
            dict_of_region_array_tuples[country_encoded] = []
            dict_of_sub_region_array_tuples[country_encoded] = {}
            sub_region_options_html[country_encoded] = {}
            
            for (region_tuple, sub_region_list) in region_list[country_letter_code]:
                region_code = region_tuple[0]
                # currently region names are only specified in native language. So we index directly.
                region_name = region_tuple[1]
            
                region_encoded = "%s,%s,%s" % (country_letter_code, region_code,'')
                location_dict[lang_idx][region_encoded] = region_name

                encoded_region_tuple = create_tuple(region_encoded, region_name)
                dict_of_region_array_tuples[country_encoded].append(encoded_region_tuple)

                dict_of_sub_region_array_tuples[country_encoded][region_encoded] = []
                region_options_html[country_encoded] += u"<option value='%s'>%s\n" % (region_encoded, region_name)
                sub_region_options_html[country_encoded][region_encoded] = ''
                
                for sub_region_tuple in sub_region_list:
                    
                    sub_region_code = sub_region_tuple[0]
                    # currently sub-region names are only specified in native language. So we index directly.
                    sub_region_name = sub_region_tuple[1]
    
                    sub_region_encoded = "%s,%s,%s" % (country_letter_code, region_code,sub_region_code)
                    location_dict[lang_idx][sub_region_encoded] = sub_region_name
                    
                    encoded_sub_region_tuple = create_tuple(sub_region_encoded, sub_region_name)
                    dict_of_sub_region_array_tuples[country_encoded][region_encoded].append(encoded_sub_region_tuple)
                    
                    sub_region_options_html[country_encoded][region_encoded] += \
                                           u"<option value='%s'>%s\n" % ( sub_region_encoded, sub_region_name)
                    
    
                 
                    
                
################################            
populate_country_options()