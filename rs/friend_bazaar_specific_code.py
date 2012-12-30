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

import localizations
from translation_helpers import ugettext_tuple, ugettext_currency_tuple

ugettext = lambda s: s # do nothing - but allows text to be tagged for translation at the source

list_of_friend_bazaar_specific_fields = []

# the following dictionary allows us to track which category list each checkbox_field is derived from. For example
# "outdoor_activities_for_sale" is derived from "outdoor_activities" - we then use this information when generating
# the dropdown menus. Contains a pointer to the actual list (as opposed to the name)
original_activity_list_used_to_derive_checkbox_list = {}

label_nums = {}
label_nums['for_sale'] = "1a."
label_nums['for_sale_sub_menu']  = "1b."
#label_nums['to_buy'] = "2a."
#label_nums['to_buy_sub_menu'] = "2b."

label_tuples = {}
label_tuples['for_sale']  = ugettext_tuple(ugettext('Interested in <span class="cl-nobold cl-text-10pt-format">and/or</span> selling'))
label_tuples['for_sale_sub_menu'] = ugettext_tuple(ugettext('Subcategory'))
#label_tuples['to_buy'] = ugettext_tuple(ugettext('Buying and/or Learning'))
#label_tuples['to_buy_sub_menu'] = ugettext_tuple(ugettext('Subcategory'))

all_activities_tuple = ('----',) +  ugettext_tuple(ugettext("All/any activity"))

categories_label_dict = {
    'athletics': {'for_sale': ugettext_tuple(ugettext('Sports'))}, 
    
    'culture_and_sightseeing': {'for_sale': ugettext_tuple(ugettext('Culture/Sightseeing'))},
    
    'dancing': {'for_sale' : ugettext_tuple(ugettext('Dancing'))},
    
    'domestic_help': {'for_sale' : ugettext_tuple(ugettext('Personal assistant'))},
    
    'games': {'for_sale' : ugettext_tuple(ugettext('Games'))}, 
    
    'going_out': {'for_sale' : ugettext_tuple(ugettext('Going out'))},
    
    'hanging_out': {'for_sale' : ugettext_tuple(ugettext('Hanging out (being a friend)'))},
    
    'hobbies': {'for_sale' : ugettext_tuple(ugettext('Hobbies/Crafts'))},
    
    'languages': {'for_sale' : ugettext_tuple(ugettext('Languages'))}, 
    
    'music': {'for_sale' : ugettext_tuple(ugettext('Music - teaching/performing'))},
    
    'outdoor_activities': {'for_sale' : ugettext_tuple(ugettext('Outdoor activities'))},
}

# definitions of the different activity categories (category lists) and activities within each category.
category_definitions_dict = {}
category_definitions_dict['athletics'] = [
    ('aerobics',) + ugettext_tuple(ugettext('Aerobics')),
    ('martial_arts',) + ugettext_tuple(ugettext('Martial Arts')),
    ('basketball',) + ugettext_tuple(ugettext('Basketball')),
    ('diving',) + ugettext_tuple(ugettext('Diving')),
    ('biking',) + ugettext_tuple(ugettext('Biking')),
    ('jogging_running',) + ugettext_tuple(ugettext('Jogging / running')),
    ('water_skiing',) + ugettext_tuple(ugettext('Water skiing')),
    ('skiing',) + ugettext_tuple(ugettext('Snow skiing')),
    ('snowboarding',) + ugettext_tuple(ugettext('Snowboarding')),
    ('soccer',) + ugettext_tuple(ugettext('Soccer')),
    ('golf',) + ugettext_tuple(ugettext('Golf')),
    ('bowling',) + ugettext_tuple(ugettext('Bowling')),
    ('paintball',) + ugettext_tuple(ugettext('Paintball')),
    ('kitesurfing',) + ugettext_tuple(ugettext('Kitesurfing')),
    ('kayaking',) + ugettext_tuple(ugettext('Kayaking')),
    ('weight_lifting',) + ugettext_tuple(ugettext('Weight lifting')),
    ('skating',) + ugettext_tuple(ugettext('Skating')),
    ('swimming',) + ugettext_tuple(ugettext('Swimming')),
    ('rugby',) + ugettext_tuple(ugettext('Rugby')),
    ('sailing',) + ugettext_tuple(ugettext('Sailing')),
    ('surfing',) + ugettext_tuple(ugettext('Surfing')),
    ('tennis',) + ugettext_tuple(ugettext('Tennis')),
    ('volleyball',) + ugettext_tuple(ugettext('Volleyball')),
    ('yoga',) + ugettext_tuple(ugettext('Yoga')),
    ('windsurfing',) + ugettext_tuple(ugettext('Wind surfing')),
]

category_definitions_dict['culture_and_sightseeing'] = [     
    ('traveling',) + ugettext_tuple(ugettext('Travel')),
    ('art_galleries',) + ugettext_tuple(ugettext('Art galleries')),
    ('museums',) + ugettext_tuple(ugettext('Museums')),
    ('opera',) + ugettext_tuple(ugettext('Opera')),
    ('fine_dining',) + ugettext_tuple(ugettext('Fine dining')),
    ('fashion_events',) + ugettext_tuple(ugettext('Fashion events')),
    ('wine_tasting',) + ugettext_tuple(ugettext('Wine tasting')),
    ('walking',) + ugettext_tuple(ugettext('Walking')),
]    

category_definitions_dict['dancing'] = [
    ('country_dancing',) + ugettext_tuple(ugettext('Country/Western dancing')),
    ('ballet_dancing',) + ugettext_tuple(ugettext('Ballet dancing')),
    ('disco_dancing',) + ugettext_tuple(ugettext('Disco dancing')),
    ('electronic_dancing',) + ugettext_tuple(ugettext('Electronic dancing')),
    ('hip_hop_dancing',) + ugettext_tuple(ugettext('Hip-hop dancing')),
    ('modern_dancing',) + ugettext_tuple(ugettext('Modern dancing')),
    ('pole_dancing',) + ugettext_tuple(ugettext('Pole dancing')),
    ('salsa_latin_dancing',) + ugettext_tuple(ugettext('Salsa/Latin')),
    ('swing_dancing',) + ugettext_tuple(ugettext('Swing dancing')),
    ('tap_dancing',) + ugettext_tuple(ugettext('Tap dancing')),
]

category_definitions_dict['domestic_help'] = [ 
    ('babysitting_help',) + ugettext_tuple(ugettext('Babysitting')),
    ('cooking_help',) + ugettext_tuple(ugettext('Cooking')),
    ('cleaning_help',) + ugettext_tuple(ugettext('Cleaning')),
    ('driving_help',) + ugettext_tuple(ugettext('Driving')),
    ('shopping_help',) + ugettext_tuple(ugettext('Shopping')),
    ('handyman_help',) + ugettext_tuple(ugettext('Handyman')), # Un manitas
]

category_definitions_dict['going_out'] =  [ # salir
    ('dinner_parties',) + ugettext_tuple(ugettext('Dinner parties')),
    ('coffee',) + ugettext_tuple(ugettext('Coffee')),
    ('movies',) + ugettext_tuple(ugettext('Movies')),
    ('concerts',) + ugettext_tuple(ugettext('Concerts')),
    ('karaoke',) + ugettext_tuple(ugettext('Karaoke')),
    ('dance_clubs',) + ugettext_tuple(ugettext('Dance clubs')),
    ('bars_pubs',) + ugettext_tuple(ugettext('Drinks/Bars')),
    ('restaurants',) + ugettext_tuple(ugettext('Restaurants')),
]

category_definitions_dict['games'] = [ # Juegos
    ('billiards',) + ugettext_tuple(ugettext('Billiards')),
    ('video_games',) + ugettext_tuple(ugettext('Video games')),
    ('board_games',) + ugettext_tuple(ugettext('Board games')),
    ('card_games',) + ugettext_tuple(ugettext('Card games')),
    ('role_playing',) + ugettext_tuple(ugettext('Role playing')),
    ('word_games',) + ugettext_tuple(ugettext('Word games')),
]

category_definitions_dict['hanging_out'] = [ #pasar el tiempo
    ('talking_listening',) + ugettext_tuple(ugettext('Talking/Listening')),
    ('friends_with_disabled',) + ugettext_tuple(ugettext('Friends w/ disabled')),
    ('friends_with_seniors',) + ugettext_tuple(ugettext('Friends w/ seniors')),
    ('teaching_culture',) + ugettext_tuple(ugettext('Teaching culture')),
    ('watching_tv',) + ugettext_tuple(ugettext('Watching TV')),
    ('discuss_news',) + ugettext_tuple(ugettext('Discussing the news')),
    ('discuss_books',) + ugettext_tuple(ugettext('Discuss books')),
    ('go_to_park',) + ugettext_tuple(ugettext('Go to a park')),
    ('go_to_beach',) + ugettext_tuple(ugettext('Go to the beach')),    
]

category_definitions_dict['hobbies'] = [ # aficiones
    ('artistic_painting',) + ugettext_tuple(ugettext('Painting (artistic)')),
    ('astrology',) + ugettext_tuple(ugettext('Astrology')),
    ('poetry',) + ugettext_tuple(ugettext('Poetry')),
    ('writing',) + ugettext_tuple(ugettext('Writing')),
    ('photography',) + ugettext_tuple(ugettext('Photography')),
]

category_definitions_dict['languages'] = localizations.languages_list 

category_definitions_dict['music'] = [
    ('accordion',) + ugettext_tuple(ugettext('Accordion')),
    ('bagpipes',) + ugettext_tuple(ugettext('Bagpipes')),
    ('bass',) + ugettext_tuple(ugettext('Bass')),
    ('baritone',) + ugettext_tuple(ugettext('Baritone')),
    ('clarinet',) + ugettext_tuple(ugettext('Clarinet')),
    ('drums',) + ugettext_tuple(ugettext('Drums')),
    ('dj_all',) + ugettext_tuple(ugettext('DJ (details in profile)')),
    #('dj_ambient',) + ugettext_tuple(ugettext('DJ-Ambient')),
    #('dj_country',) + ugettext_tuple(ugettext('DJ-Country')),
    #('dj_dance',) + ugettext_tuple(ugettext('DJ-Dance')),
    #('dj_disco',) + ugettext_tuple(ugettext('DJ-Disco')),
    #('dj_drum_and_bass',) + ugettext_tuple(ugettext('DJ-Drum and Bass')),
    #('dj_house',) + ugettext_tuple(ugettext('DJ-House')),
    #('dj_techno',) + ugettext_tuple(ugettext('DJ-Techno')),
    #('dj_trance',) + ugettext_tuple(ugettext('DJ-Trance')),
    #('dj_rock',) + ugettext_tuple(ugettext('DJ-Rock')),
    ('guitar',) + ugettext_tuple(ugettext('Guitar')),
    ('harmonica',) + ugettext_tuple(ugettext('Harmonica')),
    ('music_group_all',) + ugettext_tuple(ugettext('Music group-All/Other')),
    ('music_group_jazz',) + ugettext_tuple(ugettext('Music group-Jazz')),
    ('music_group_rock',) + ugettext_tuple(ugettext('Music group-Rock')),
    ('music_group_country',) + ugettext_tuple(ugettext('Music group-Country')),
    ('piano',) + ugettext_tuple(ugettext('Piano')),
    ('saxaphone',) + ugettext_tuple(ugettext('Saxaphone')),
    ('singing',) + ugettext_tuple(ugettext('Singing')),
    ('trumpet',) + ugettext_tuple(ugettext('Trumpet')),
    ('trombone',) + ugettext_tuple(ugettext('Trombone')),
    ('tuba',) + ugettext_tuple(ugettext('Tuba')),
    ('violin',) + ugettext_tuple(ugettext('Violin')),
    ('viola',) + ugettext_tuple(ugettext('Viola')),
]
    
category_definitions_dict['outdoor_activities'] = [ #actividades al aire libre
    ('camping',) + ugettext_tuple(ugettext('Camping')),
    ('canoeing',) + ugettext_tuple(ugettext('Canoeing')),
    ('fishing',) + ugettext_tuple(ugettext('Fishing')),        
    ('mountain_climbing',) + ugettext_tuple(ugettext('Mountain climbing')),
    ('horseback_riding',) + ugettext_tuple(ugettext('Horseback Riding')),
    ('hiking',) + ugettext_tuple(ugettext('Hiking')),
]   

prefer_no_say_tuple = ('prefer_no_say',) + ugettext_tuple(ugettext("None selected"))

def get_category_specific_other_tuple(category_name):
    return ('other_%s' % category_name,) + ugettext_tuple(ugettext('Other (details in profile)'))
    

def friend_bazaar_specific_choices(checkbox_fields, enabled_checkbox_fields_list):
    
    # This function sets up the appropriate structures required for displaying the checkbox fields in the user profile that allow 
    # the user to select which activities they are interested in doing (buying and/or selling)
    
    def add_list_to_checkbox_fields(category, field_name, sub_label_tuple, choices_list):
        
        sub_dict = {
            field_name : {
                'label': sub_label_tuple,
                'choices' : choices_list + [get_category_specific_other_tuple(category), prefer_no_say_tuple,], 
                'start_sorting_index' : 0,
                'stop_sorting_index' : -2,
                'options' : [],
                'input_type' : u'checkbox',
            },
        }
        checkbox_fields.update(sub_dict)
        
    for category in categories_label_dict.keys():
        for sale_or_buy in categories_label_dict[category].keys():
            assert(sale_or_buy == 'for_sale' or sale_or_buy ==  'to_buy')
            sub_label_tuple = categories_label_dict[category][sale_or_buy]
            choices_list = category_definitions_dict[category]
            field_name = '%s_%s' % (sale_or_buy, category)
            add_list_to_checkbox_fields(category, field_name, sub_label_tuple, choices_list)
            
            # the following structure is necessary for generating the dropdown lists in the search box - it allows us
            # to easily access the choices_list that was used to generate a particular checkbox. 
            original_activity_list_used_to_derive_checkbox_list[field_name] = choices_list
            
            # keep track of the fields that have been added, for generating the required structures and for error checking. 
            list_of_friend_bazaar_specific_fields.append(field_name)            

    enabled_checkbox_fields_list += list_of_friend_bazaar_specific_fields

    
    
def update_friend_bazaar_data_fields_dict(data_fields):
    # This function fills in the appropriate structures required for displaying drop-down menus in the search box. 
    new_entries = {}

    # the following vars are generate the base category menus
    base_choices_list = {}
    base_choices_list['for_sale'] = []
    #base_choices_list['to_buy'] = []    
    
    
    # generate the sub-menus (such as a "hobbies_for_sale" dropdown that will be displayed after the user has selected the category
    # that they want to display. Also, fill in some structures required for the base category menus.
    for category in categories_label_dict.keys():
        for sale_or_buy in categories_label_dict[category].keys():
            field_name = '%s_%s' % (sale_or_buy, category)
            new_entries[field_name] = {
                'label':        categories_label_dict[category][sale_or_buy], # this is set here just for debugging, will (probably) be over-written
                'choices':      original_activity_list_used_to_derive_checkbox_list[field_name] + [get_category_specific_other_tuple(category),],
                'start_sorting_index' : 0,
                'stop_sorting_index' : -1,
                'options':      [],
                'input_type':   u'select',
                'ordered_choices_tuples': 'to be computed',
                'required':     True
            }   
            
            # following code sets up structures that will be used in generation of the base category menus
            sub_label_tuple = categories_label_dict[category][sale_or_buy]
            choices_tuple = (field_name,) + sub_label_tuple
            base_choices_list[sale_or_buy].append(choices_tuple)
        
    data_fields.update(new_entries)        
       

    # Generate the "parent" menus
    base_entries = {}
    
    #for menu_name in ['for_sale', 'to_buy']:
    menu_name = 'for_sale'
    base_entries[menu_name] = {
        'label_num':    label_nums[menu_name],
        'label':        label_tuples[menu_name], 
        'choices':      [all_activities_tuple,] + base_choices_list[menu_name],
        'start_sorting_index' : 1,
        #'stop_sorting_index' : -2,
        'options':      [],
        'input_type':   u'select',
        'ordered_choices_tuples': 'to be computed',
        'required':     True
    }
        
    #for menu_name in ['for_sale_sub_menu', 'to_buy_sub_menu']:
    menu_name = 'for_sale_sub_menu'
    # These act as (basically empty except for the label) place-holders that will be dynamically set/overwritten
    # based on the base_menu value, through an ajax call
    base_entries[menu_name] = {
        'label_num':    label_nums[menu_name],
        'label':        label_tuples[menu_name], 
        'choices':      None, 
        'options':      [],
        'input_type':   u'select',
        'ordered_choices_tuples': 'to be computed',
        'required':     True
    }        

    data_fields.update(base_entries)     
        
    return data_fields


def get_search_fields_expected_keys(search_fields):
    
    # accepts a dictionary of all of the "search_fields" that have been defined.
    # Returns a list of keys corresponding to all of the search_fields, but with the 
    # for_sale "category" sub-menu entries removed. This is useful for efficiency later on in the 
    # program where we need to loop over all passed in search values - 
    # since we know that these "category" sub-menus will never be 
    # passed in, since they are not actual search fields (they are only used for setting up all the 
    # data structures required for lookups etc.)
    tmp_search_fields = search_fields.copy()
    
    for category in categories_label_dict.keys():
        field_name = '%s_%s' % ("for_sale", category)   
        del tmp_search_fields[field_name]
    
    # also remove the 'imortant_currencies_list' since it was only used for generating part of the friend_currencies dropdown menu
    del tmp_search_fields['important_currencies_list']
    
    return tmp_search_fields.keys()
        
        
def get_list_of_activity_categories():
    # returns the list of categories that have been stored on the userobject, that correspond to
    # the different types of activities that the user has indicated a preference for.
    # This is used in parts of the code for generating summaries of the activities that the user has 
    # indicated that they are interested in. 
    list_of_activity_categories = []
    for category in categories_label_dict.keys():
        field_name = '%s_%s' % ("for_sale", category)   
        list_of_activity_categories.append(field_name)
        
    return list_of_activity_categories

friend_prices_list = [
    # This is a list of the prices that we permit the users to charge
    ('0',) +         ugettext_tuple(ugettext('0 (Free)')), 
    ('2',) +        ugettext_tuple(ugettext('1-2')),     
    ('5',) +        ugettext_tuple(ugettext('3-5')),     
    ('10',) +        ugettext_tuple(ugettext('6-10')),     
    ('20',) +        ugettext_tuple(ugettext('11-20')),     
    ('50',) +        ugettext_tuple(ugettext('21-50')),     
    ('100',) +       ugettext_tuple(ugettext('51-100')),    
    ('200',) +       ugettext_tuple(ugettext('101-200')),     
    ('500',) +       ugettext_tuple(ugettext('200-500')),    
    ('1000',) +      ugettext_tuple(ugettext('501-1000')),    
    ('2000',) +      ugettext_tuple(ugettext('1001-2000')),    
    ('5000',) +      ugettext_tuple(ugettext('2001-5000')),    
    ('10000',) +      ugettext_tuple(ugettext('5001-10000')),    
    ('20000',) +      ugettext_tuple(ugettext('10001-20000')),    
    ('50000',) +      ugettext_tuple(ugettext('> 20000')),    
    ]


important_currencies_list = [
    # These countries will appear twice in the country/location list. Once at the beginning
    # and again in the entire list.
    ("EUR",) +  ugettext_currency_tuple(u"€", ugettext("Euro")), # Euro
    ("USD",) +  ugettext_currency_tuple(u"$", ugettext("US")), # US
    ("GBP",) +  ugettext_currency_tuple(u"£", ugettext("GB")), # UK
    ("ARS",) +  ugettext_currency_tuple(u"$", ugettext("AR")), # Argentina Peso
    ("CLP",) +  ugettext_currency_tuple(u"$", ugettext("CL")), # Chile Peso
    ("COP",) +  ugettext_currency_tuple(u"$", ugettext("CO")), # Colombia
    ("MXN",) +  ugettext_currency_tuple(u"$", ugettext("MX")), # Mexico 
    ("VEF",) +  ugettext_currency_tuple(u"Bs", ugettext("VE")), # Venezuela
    ]    

currencies_list = [
   
    ("ALL",) + ugettext_currency_tuple(u"L", ugettext("AL")), # Albania Lek
    ("DZD",) + ugettext_currency_tuple(u"د.ج", ugettext("DZ")), # Algeria dinar
    ("AOA",) + ugettext_currency_tuple(u"Kz", ugettext("AO")), # Angola Kwanza
    ("AMD",) + ugettext_currency_tuple(u"D", ugettext("AM")), # Armenia dram
    ("ARS",) +  ugettext_currency_tuple(u"$", ugettext("AR")), # Argentina Peso
    ("AUD",) +  ugettext_currency_tuple(u"$", ugettext("AU")), # Australia
    ("AZN",) +  ugettext_currency_tuple(u"m", ugettext("AZ")), # Azerbaijani manat
    ("BSD",) +  ugettext_currency_tuple(u"$", ugettext("BS")), # Bahamas dollar
    ("BHD",) +  ugettext_currency_tuple(u".د.ب", ugettext("BH")), # Bahraini dinar
    ("BDT",) +  ugettext_currency_tuple(u"Tk", ugettext("BD")), # Bangladeshi taka
    ("BBD",) +  ugettext_currency_tuple(u"Bds$", ugettext("BB")), # Barbados dollar
    ("BYR",) +  ugettext_currency_tuple(u"Br", ugettext("BY")), # Belarusian ruble
    ("BZD",) +  ugettext_currency_tuple(u"BZ$", ugettext("BZ")), # Belize dollar
    ("BMD",) +  ugettext_currency_tuple(u"BD$", ugettext("BM")), # Bermudian dollar
    ("BTN",) +  ugettext_currency_tuple(u"Nu.", ugettext("BT")), # Bhutanese ngultrum
    ("BOB",) +  ugettext_currency_tuple(u"$b", ugettext("BO")), # Bolivia Boliviano
    ("BAM",) +  ugettext_currency_tuple(u"KM", ugettext("BA")), # Bosnia and Herzegovina konvertibilna marka
    ("BRL",) +  ugettext_currency_tuple(u"R$", ugettext("BR")), # Brazil
    ("BND",) +  ugettext_currency_tuple(u"B$", ugettext("BN")), # Brunei dollar
    ("BGN",) +  ugettext_currency_tuple(u"лв", ugettext("BG")), # Bulgarian lev
    ("CAD",) +  ugettext_currency_tuple(u"$", ugettext("CA")), # Canada
    ("KYD",) +  ugettext_currency_tuple(u"KY$", ugettext("KY")), # Cayman Islands
    ("CLP",) +  ugettext_currency_tuple(u"$", ugettext("CL")), # Chile Peso
    ("CNY",) +  ugettext_currency_tuple(u"¥", ugettext("CN")), # China Yuan Renminbi
    ("COP",) +  ugettext_currency_tuple(u"$", ugettext("CO")), # Colombia
    ("CRC",) +  ugettext_currency_tuple(u"₡", ugettext("CR")), # Costa Rica Colon
    ("HRK",) +  ugettext_currency_tuple(u"kn", ugettext("HR")), # Croatian Kuna
    ("CUP",) +  ugettext_currency_tuple(u"₱", ugettext("CU")), # Cuba
    ("CZK",) +  ugettext_currency_tuple(u"Kč", ugettext("CZ")), # Czech koruna
    ("DKK",) +  ugettext_currency_tuple(u"Kr", ugettext("DK")), # Danish krone
    ("DOP",) +  ugettext_currency_tuple(u"RD$", ugettext("DO")), # Dominican peso
    ("EGP",) +  ugettext_currency_tuple(u"£", ugettext("EG")), # Egyption pound
    ("SVC",) +  ugettext_currency_tuple(u"$", ugettext("SV")), # El Salvador
    ("EUR",) +  ugettext_currency_tuple(u"€", ugettext("Euro")), # Euro    
    ("EEK",) +  ugettext_currency_tuple(u"Kr", ugettext("EE")), # Estonian Kroon
    ("FJD",) +  ugettext_currency_tuple(u"FJ$", ugettext("FJ")), # Fijian dollar
    ("CFP",) +  ugettext_currency_tuple(u"F", ugettext("FP")), # French Polynesia [CFP franc]

    ("GEL",) +  ugettext_currency_tuple(u"L", ugettext("GE")), # Georgian lari
    ("GIP",) +  ugettext_currency_tuple(u"£", ugettext("GI")), # Gibralter pound
    ("GTQ",) +  ugettext_currency_tuple(u"Q", ugettext("GT")), # Guatemala Quetzal
    ("GYD",) +  ugettext_currency_tuple(u"GY$", ugettext("GY")), # Guayanese dollar
    ("HNL",) +  ugettext_currency_tuple(u"L", ugettext("HN")), # Honduras Lempira
    ("HKD",) +  ugettext_currency_tuple(u"$", ugettext("HK")), # Hong Kong
    ("HUF",) +  ugettext_currency_tuple(u"Ft", ugettext("HU")), # Hungary Forint
    ("ISK",) +  ugettext_currency_tuple(u"Kr", ugettext("IS")), # Iceland Krona
    ("INR",) +  ugettext_currency_tuple(u"Rs", ugettext("IN")), # India
    ("IDR",) +  ugettext_currency_tuple(u"Rp", ugettext("ID")), # Indonesia
    ("IRR",) +  ugettext_currency_tuple(u"﷼", ugettext("IR")), # Iran Rial
    ("IQD",) +  ugettext_currency_tuple(u"د.ع", ugettext("IQ")), # Iraqui dinar
    ("ILS",) +  ugettext_currency_tuple(u"₪", ugettext("IL")), # Israel
    ("JMD",) +  ugettext_currency_tuple(u"J$", ugettext("JM")), # Jamaica
    ("JPY",) +  ugettext_currency_tuple(u"¥", ugettext("JP")), # Japan
    ("JOD",) +  ugettext_currency_tuple(u"JD", ugettext("JO")), # Jordanian dinar
    ("KZT",) +  ugettext_currency_tuple(u"T", ugettext("KZ")), # Kazakhstani tenge
    ("KRW",) +  ugettext_currency_tuple(u"₩", ugettext("KR")), # Korea, South
    ("KWD",) +  ugettext_currency_tuple(u"د.ك", ugettext("KW")), # Kuwaiti dinar
    ("KGS",) +  ugettext_currency_tuple(u"лв", ugettext("KG")), # Kyrgyzstani som
    ("LAK",) +  ugettext_currency_tuple(u"KN", ugettext("LA")), # Lao kip
    ("LVL",) +  ugettext_currency_tuple(u"Ls", ugettext("LV")), # Latvian lats
    ("LBP",) +  ugettext_currency_tuple(u"£", ugettext("LB")), # Lebanese lira
    ("LYD",) +  ugettext_currency_tuple(u"LD", ugettext("LY")), # Libyan dinar
    ("LTL",) +  ugettext_currency_tuple(u"Lt", ugettext("LT")), # Lithuanian litas

    ("MKD",) +  ugettext_currency_tuple(u"ден", ugettext("MK")), # Macedinian denar
    ("MYR",) +  ugettext_currency_tuple(u"RM", ugettext("MY")), # Malaysia
    ("MVR",) +  ugettext_currency_tuple(u"Rf", ugettext("MV")), # Maldives
    ("MXN",) +  ugettext_currency_tuple(u"$", ugettext("MX")), # Mexico 
    ("MDL",) +  ugettext_currency_tuple(u"L", ugettext("MD")), # Modolvan leu 
    ("MNT",) +  ugettext_currency_tuple(u"₮", ugettext("MN")), # Mongolian tugrik
    ("MAD",) +  ugettext_currency_tuple(u"د.م.", ugettext("MA")), # Moroccan dirham
    
    ("NZD",) +  ugettext_currency_tuple(u"$", ugettext("NZ")), # New Zealand
    ("NIO",) +  ugettext_currency_tuple(u"C$", ugettext("NI")), # Nicaragua

    ("NOK",) +  ugettext_currency_tuple(u"Kr", ugettext("NO")), # Norway
    ("OMR",) +  ugettext_currency_tuple(u"﷼", ugettext("OM")), # Oman
    ("PKR",) +  ugettext_currency_tuple(u"₨", ugettext("PK")), # Pakistan
    ("PAB",) +  ugettext_currency_tuple(u"B./", ugettext("PA")), # Panamanian balboa
    ("PGK",) +  ugettext_currency_tuple(u"K", ugettext("PG")), # Papua New Guinea kina
    ("PYG",) +  ugettext_currency_tuple(u"Gs", ugettext("PY")), # Paraguay
    ("PEN",) +  ugettext_currency_tuple(u"S/.", ugettext("PE")), # Peru Nuevo Sol       
    ("PHP",) +  ugettext_currency_tuple(u"₱", ugettext("PH")), # Philippines
    ("PLN",) +  ugettext_currency_tuple(u"zł", ugettext("PL")), # Polish zloty

    ("QAR",) +  ugettext_currency_tuple(u"﷼", ugettext("QA")), # Qatar
    ("RON",) +  ugettext_currency_tuple(u"lei", ugettext("RO")), # Romania
    ("RUB",) +  ugettext_currency_tuple(u"руб", ugettext("RU")), # Russian Federation
    
    ("SAR",) +  ugettext_currency_tuple(u"﷼", ugettext("SA")), # Saudi Arabia
    ("RSD",) +  ugettext_currency_tuple(u"Дин.", ugettext("RS")), # Serbia

    ("SGD",) +  ugettext_currency_tuple(u"$", ugettext("SG")), # Singapore

    ("ZAR",) +  ugettext_currency_tuple(u"R", ugettext("ZA")), # South Africa

    ("LKR",) +  ugettext_currency_tuple(u"₨", ugettext("LK")), # Sri Lanka
    ("SRD",) +  ugettext_currency_tuple(u"$", ugettext("SR")), # Suriname

    ("SEK",) +  ugettext_currency_tuple(u"Kr", ugettext("SE")), # Sweden
    ("CHF",) +  ugettext_currency_tuple(u"CHF", ugettext("CH")), # Switzerland
    ("SYP",) +  ugettext_currency_tuple(u"£", ugettext("SY")), # Syria
    ("TWD",) +  ugettext_currency_tuple(u"NT$", ugettext("TW")), # Taiwan

    ("THB",) +  ugettext_currency_tuple(u"฿", ugettext("TH")), # Thailand
    ("TTD",) +  ugettext_currency_tuple(u"TT$", ugettext("TT")), # Trinidad and Tobago dollar

    ("TND",) +  ugettext_currency_tuple(u"د.ت", ugettext("TN")), # Tunisia
    ("TRL",) +  ugettext_currency_tuple(u"TRL", ugettext("TR")), # Turkey
    ("TMT",) +  ugettext_currency_tuple(u"m", ugettext("TM")), # Turkmenistan (Turkmen manat)

    ("UAH",) +  ugettext_currency_tuple(u"£", ugettext("UA")), # Ukrainian hryvnia
    ("AED",) +  ugettext_currency_tuple(u"د.إ", ugettext("AE")), # UAE dirham
    ("GBP",) +  ugettext_currency_tuple(u"£", ugettext("GB")), # UK
    ("USD",) +  ugettext_currency_tuple(u"$", ugettext("US")), # US
    ("UYU",) +  ugettext_currency_tuple(u"$U", ugettext("UY")), # Uruguay
    ("UZS",) +  ugettext_currency_tuple(u"сўм", ugettext("UZ")), # Uzbekistani som

    ("VEB",) +  ugettext_currency_tuple(u"Bs", ugettext("VE")), # Venezuela
    ("VND",) +  ugettext_currency_tuple(u"₫", ugettext("VN")), # Vietnam
    
    ("YER",) +  ugettext_currency_tuple(u"﷼", ugettext("YE")), # Yemeni rial

    ]

# The following mapping is used for automatically setting the correct currency when the user selects a given country. 
# We include two commas after the country code, because this is the format that we have used internally for distinguishing
# countries versus regions and sub-regions.
country_to_currency_map = {
    'AL,,' : 'ALL', # Albania
    'DZ,,' : 'DZD', # Algeria
    'AD,,' : 'EUR', # Andorra
    'AO,,' : 'AOA', # Angola
    'AQ,,' : 'USD', # Antarctica
    'AR,,' : 'ARS', # Argentina
    'AM,,' : 'AMD', # Armenia
    'AU,,' : 'AUD', # Australia
    'AT,,' : 'EUR', # Austria
    'AZ,,' : 'AZN', # Azerbaijan
    'BS,,' : 'BSD', # Bahamas
    'BH,,' : 'BHD', # Bahrain
    'BD,,' : 'BDT', # Bangladesh
    'BB,,' : 'BBD', # Barbados
    'BY,,' : 'BYR', # Belarus
    'BE,,' : 'EUR', # Belgium
    'BZ,,' : 'BZD', # Belize
    'BM,,' : 'BMD', # Bermuda
    'BT,,' : 'BTN', # Bhutan
    'BO,,' : 'BOB', # Bolivia
    'BA,,' : 'BAM', # Bosnia and Herzegovina
    'BR,,' : 'BRL', # Brazil
    'BN,,' : 'BND', # Brunei Darussalam
    'BG,,' : 'BGN', # Bulgaria
    'KH,,' : 'USD', # Cambodia
    'CA,,' : 'CAD', # Canada
    'KY,,' : 'KYD', # Cayman Islands
    'CL,,' : 'CLP', # Chile
    'CN,,' : 'CNY', # China
    'CO,,' : 'COP', # Colombia
    'CR,,' : 'CRC', # Costa Rica
    'HR,,' : 'HRK', # Croatia
    'CU,,' : 'CUP', # Cuba
    'CY,,' : 'EUR', # Cyprus
    'CZ,,' : 'CZK', # Czech Republic
    'DK,,' : 'DKK', # Denmark
    'DO,,' : 'DOP', # Dominican Republic
    'EC,,' : 'USD', # Ecuador
    'EG,,' : 'EGP', # Egypt
    'SV,,' : 'SVC', # El Salvador
    'EE,,' : 'EEK', # Estonia
    'FJ,,' : 'FJD', # Fiji
    'FI,,' : 'EUR', # Finland
    'FR,,' : 'EUR', # France
    'GF,,' : 'EUR', # French Guiana
    'PF,,' : 'CFP', # French Polynesia
    'GE,,' : 'GEL', # Georgia
    'DE,,' : 'EUR', # Germany
    'GI,,' : 'GIP', # Gibraltar
    'GR,,' : 'EUR', # Greece
    'GL,,' : 'DKK', # Greenland
    'GT,,' : 'GTQ', # Guatemala
    'GY,,' : 'GYD', # Guyana
    'HN,,' : 'HNL', # Honduras
    'HK,,' : 'HKD', # Hong Kong
    'HU,,' : 'HUF', # Hungary
    'IS,,' : 'ISK', # Iceland
    'IN,,' : 'INR', # India
    'ID,,' : 'IDR', # Indonesia
    'IR,,' : 'IRR', # Iran
    'IQ,,' : 'IQD', # Iraq
    'IE,,' : 'EUR', # Ireland
    'IL,,' : 'ILS', # Israel
    'IT,,' : 'EUR', # Italy
    'JM,,' : 'JMD', # Jamaica
    'JP,,' : 'JPY', # Japan
    'JO,,' : 'JOD', # Jordan
    'KZ,,' : 'KZT', # Kazakhstan
    'KR,,' : 'KRW', # Korea, South
    'KW,,' : 'KWD', # Kuwait
    'KG,,' : 'KGS', # Kyrgyzstan
    'LA,,' : 'LAK', # Laos
    'LV,,' : 'LVL', # Latvia
    'LB,,' : 'LBP', # Lebanon
    'LY,,' : 'LYD', # Libya
    'LI,,' : 'CHF', # Liechtenstein
    'LT,,' : 'LTL', # Lithuania
    'LU,,' : 'EUR', # Luxembourg
    'MO,,' : 'HKD', # Macau
    'MK,,' : 'MKD', # Macedonia
    'MY,,' : 'MYR', # Malaysia
    'MV,,' : 'MVR', # Maldives
    'MT,,' : 'EUR', # Malta
    'MX,,' : 'MXN', # Mexico
    'MD,,' : 'MDL', # Moldova
    'MC,,' : 'EUR', # Monaco
    'MN,,' : 'MNT', # Mongolia
    'MA,,' : 'MAD', # Morocco
    'NL,,' : 'EUR', # Netherlands
    'NZ,,' : 'NZD', # New Zealand
    'NI,,' : 'NIO', # Nicaragua
    'NO,,' : 'NOK', # Norway
    'OM,,' : 'OMR', # Oman
    'PK,,' : 'PKR', # Pakistan
    'PA,,' : 'PAB', # Panama
    'PG,,' : 'PGK', # Papua New Guinea
    'PY,,' : 'PYG', # Paraguay
    'PE,,' : 'PEN', # Peru
    'PH,,' : 'PHP', # Philippines
    'PL,,' : 'PLN', # Poland
    'PT,,' : 'PT', # Portugal
    'PR,,' : 'EUR', # Puerto Rico
    'QA,,' : 'QAR', # Qatar
    'RO,,' : 'RON', # Romania
    'RU,,' : 'RUB', # Russian Federation
    'SA,,' : 'SAR', # Saudi Arabia
    'RS,,' : 'RSD', # Serbia
    'SG,,' : 'SGD', # Singapore
    'SK,,' : 'EUR', # Slovakia
    'SI,,' : 'EUR', # Slovenia
    'ZA,,' : 'ZAR', # South Africa
    'ES,,' : 'EUR', # Spain
    'LK,,' : 'LKR', # Sri Lanka
    'SR,,' : 'SRD', # Suriname
    'SE,,' : 'SEK', # Sweden
    'CH,,' : 'CHF', # Switzerland
    'SY,,' : 'SYP', # Syria
    'TW,,' : 'TWD', # Taiwan
    'TH,,' : 'THB', # Thailand
    'TL,,' : 'USD', # Timor-Leste
    'TT,,' : 'TTD', # Trinidad and Tobago
    'TN,,' : 'TND', # Tunisia
    'TR,,' : 'TRL', # Turkey
    'TM,,' : 'TMT', # Turkmenistan
    'UA,,' : 'UAH', # Ukraine
    'AE,,' : 'AED', # United Arab Emirates
    'GB,,' : 'GBP', # United Kingdom
    'US,,' : 'USD', # United States of America
    'UY,,' : 'UYU', # Uruguay
    'UZ,,' : 'UZS', # Uzbekistan
    'VE,,' : 'VEB', # Venezuela
    'VN,,' : 'VND', # Vietnam
    'EH,,' : 'MAD', # Western Sahara (use multiple currencies - set to moroccan dirham)
    'YE,,' : 'YER', # Yemen

}