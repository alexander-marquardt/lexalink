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
from translation_helpers import ugettext_tuple

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
label_tuples['for_sale']  = ugettext_tuple(ugettext('Interested in'))
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
    
    'languages': {'for_sale' : ugettext_tuple(ugettext('language_builds'))}, 
    
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
    ('friends_with_disabled',) + ugettext_tuple(ugettext('friend_builds w/ disabled')),
    ('friends_with_seniors',) + ugettext_tuple(ugettext('friend_builds w/ seniors')),
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




