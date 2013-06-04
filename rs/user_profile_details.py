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


from django.utils.encoding import smart_unicode
import settings
import translation_helpers, localizations
from data_struct_utils import *
from translation_helpers import ugettext_tuple
if settings.BUILD_NAME == "friend_build":
    import friend_bazaar_specific_code


ugettext = lambda s: s # do nothing - but allows text to be tagged for translation at the source
def pgettext(x,y):
    return(x,y)


##################################################
class UserProfileDetails:
    # define all of the extra fields that will give additional information about the user


    change_password_fields_to_display_in_order = ['current_password', 'new_password', 'verify_new_password']
    # Note that the following data structures are populated with "choices" (not options). The
    # "options" portion of each data structure will be automatically generated in the code that 
    # follows the declarations. The options will contain a language-appropriate version, that has
    # been formatted for more direct use in HTML (ie. <option> and variable name included in each string)

    # The 'input_type' is used for specifying if this is a dropdown (select), or text, or password, etc.
    details_fields_to_display_in_order = ['height', 'body_type',  'hair_color', 'hair_length', 'eye_color','drinking_habits', 'smoker']
    details_fields = {
        'height' : {
            'label': ugettext_tuple(ugettext('Height (cm)')),
            'choices' : 
            [
            ('----',)       + ugettext_tuple(ugettext('----')),
            ('125',)        + ugettext_tuple(ugettext('<=125')),
            ('135',)        + ugettext_tuple(ugettext('126-135')),
            ('145',)        + ugettext_tuple(ugettext('136-145')),
            ('155',)        + ugettext_tuple(ugettext('146-155')), 
            ('165',)        + ugettext_tuple(ugettext('156-165')),
            ('175',)        + ugettext_tuple(ugettext('166-175')),
            ('185',)        + ugettext_tuple(ugettext('176-185')),
            ('195',)        + ugettext_tuple(ugettext('186-195')),
            ('205',)        + ugettext_tuple(ugettext('196-205')),
            ('215',)        + ugettext_tuple(ugettext('>205')),
            ('prefer_no_say',)        + ugettext_tuple(ugettext('Prefer not to say')),
            ],
            'options' : [],
             'input_type':  u'select',        
            },
           
        # Note: eye-color is over-written in the "english" translation file, which removed the suffix "eyes". However,
        # this is necessary for dis-ambiguating eye color from hair color
        'eye_color' : {
            'label' : ugettext_tuple(ugettext('Eye color')),
            'choices' : 
            [
            ('----',)               + ugettext_tuple(ugettext('----')),
            ('blue',)               + ugettext_tuple(ugettext('Blue eyes')),
            ('brown',)              + ugettext_tuple(ugettext('Brown eyes')),
            ('green',)              + ugettext_tuple(ugettext('Green eyes')),
            ('gray',)               + ugettext_tuple(ugettext('Gray eyes')),
            ('hazel',)              + ugettext_tuple(ugettext('Hazel eyes')),
            ('brown_green',)        + ugettext_tuple(ugettext('Brown-green eyes')),
            ('black',)              + ugettext_tuple(ugettext('Black eyes')),
            ('prefer_no_say',)      + ugettext_tuple(ugettext('Prefer not to say')),    
            ],
            'options' : [],
            'input_type':  u'select',
            },
        
        'body_type' : {
            'label' : ugettext_tuple(ugettext('Body type')),
            'choices' : 
            [
            ('----',)            + ugettext_tuple(ugettext('----')),
            ('slim',)            + ugettext_tuple(ugettext('Slim')),
            ('normal',)          + ugettext_tuple(ugettext('Normal')),
            ('fit',)             + ugettext_tuple(ugettext('Athletic')),
            ('curvy',)           + ugettext_tuple(ugettext('Curvy')),
            ('overweight',)      + ugettext_tuple(ugettext('Few kilos extra')),
            ('large',)           + ugettext_tuple(ugettext('Large')),        
            ('prefer_no_say',)   + ugettext_tuple(ugettext('Prefer not to say')),       
            ],
            'options' : [],
            'input_type':  u'select',
            },
        
        'hair_color' : {
            'label' : ugettext_tuple(ugettext('Hair color')),
            'choices' : 
            [
            ('----',)           + ugettext_tuple(ugettext('----')),
            ('blond',)          + ugettext_tuple(ugettext('Blond hair')),
            ('dirty_blond',)    + ugettext_tuple(ugettext('Light brown hair')),
            ('brown',)          + ugettext_tuple(ugettext('Brown hair')),
            ('dark_brown',)     + ugettext_tuple(ugettext('Dark brown hair')),
            ('black',)          + ugettext_tuple(ugettext('Black hair')),
            ('red',)            + ugettext_tuple(ugettext('Red hair')),
            ('gray',)           + ugettext_tuple(ugettext('Gray hair')),
            ('bald',)           + ugettext_tuple(ugettext('Bald hair')),
            ('prefer_no_say',)  + ugettext_tuple(ugettext('Prefer not to say')),        
            ],
            'options' : [],
            'input_type':  u'select',
            },
            
        'hair_length' : {
            'label' : ugettext_tuple(ugettext('Hair length')),
            'choices' : [
            ('----',)           + ugettext_tuple(ugettext('----')),
            ('short',)          + ugettext_tuple(ugettext('Short')),
            ('medium',)         + ugettext_tuple(ugettext('Medium')),
            ('long',)           + ugettext_tuple(ugettext('Long')),
            ('bald',)           + ugettext_tuple(ugettext('Bald')),
            ('prefer_no_say',)  + ugettext_tuple(ugettext('Prefer not to say')),        
            ],
            'options' : [],
            'input_type':  u'select',
            },
        
    
        'drinking_habits' : {
            'label' : ugettext_tuple(ugettext('Drinking habits')),
            'choices' :
            [
            ('----',)           + ugettext_tuple(ugettext('----')),
            ('non_drinker',)    + ugettext_tuple(ugettext('Non drinker')),
            ('occasionally',)   + ugettext_tuple(ugettext('Ocasionally')),
            ('regularly',)      + ugettext_tuple(ugettext('Often')),
            ('prefer_no_say',)  + ugettext_tuple(ugettext('Prefer not to say')),        
            ],
            'options' : [],
            'input_type':  u'select',
            },
        
        'smoker' : {
            'label' : ugettext_tuple(ugettext('Smoker')),
            'choices' : 
            [
            ('----',)            + ugettext_tuple(ugettext('----')),
            ('non_smoker',)      + ugettext_tuple(ugettext('Non smoker')),
            ('occasionally',)    + ugettext_tuple(ugettext('Ocasionally')),
            ('regularly',)       + ugettext_tuple(ugettext('Regularly')),
            ('trying_to_quit',)  + ugettext_tuple(ugettext('Trying to quit')),
            ('prefer_no_say',)   + ugettext_tuple(ugettext('Prefer not to say')),          
            ],
            'options' : [],
            'input_type':  u'select',
            },
    }
    
    details_fields_options_dict = {}
    generate_option_line_based_on_data_struct(details_fields, details_fields_options_dict)
    
    immediate_notification_of_message = ugettext('Immediate notification of new messages.')        
    daily_notification_of_message = ugettext('Daily notification of new messages.')
    weekly_notification_of_message = ugettext('Weekly notification of new messages.')
    monthly_notification_of_message = ugettext('Monthly notification of new messages.')    
    password_recovery_only = ugettext('I do not want to receive notificatoins of new messages or new contacts. My email is primarily to be used to recover my password.')

    if settings.BUILD_NAME != "language_build" and settings.BUILD_NAME != "friend_build":
        immediate_notification_of_message_or_contacts = ugettext('Immediate notification of new messages or contacts (a kiss, a wink, or a key).')
        daily_notification_of_message_or_contacts = ugettext('Daily notification of new messages or contacts (kisses, winks, or keys).')
        weekly_notification_of_message_or_contacts = ugettext('Weekly notification of new messages or contacts (kisses, winks, or keys).')
        monthly_notification_of_message_or_contacts = ugettext('Monthly notification of new messages or contacts (kisses, winks, or keys).')
        
    else: # language_build/friend_build -- no kisses or winks
        immediate_notification_of_message_or_contacts = ugettext('Immediate notification of new messages or contacts (a greeting or a key).')       
        daily_notification_of_message_or_contacts = ugettext('Daily notification of new messages or contacts (greetings or keys).')        
        weekly_notification_of_message_or_contacts = ugettext('Weekly notification of new messages or contacts (greetings or keys).')        
        monthly_notification_of_message_or_contacts = ugettext('Monthly notification of new messages or contacts (greetings or keys).')
        
    if settings.BUILD_NAME != "language_build":
        languages_list = localizations.languages_list + [    
            ('others',) +  ugettext_tuple(ugettext('Other languages')),
            ('prefer_no_say',) +  ugettext_tuple(ugettext('Prefer not to say')),]
        languages_label =  ugettext_tuple(ugettext('Languages I speak'))
        languages_end_sorting_index_offset = 2 #intentionally positive because this is defined as an offset from the end

    else:
        # don't allow people to leave an unspecified language in language_build
        languages_list = localizations.languages_list
        languages_label =  ugettext_tuple(ugettext('Languages I speak fluently (well enough to help someone else learn)'))
        languages_end_sorting_index_offset = 0

        
    # checkbox fields are updated depending on which build we are building - for this reason we have split it 
    # into numerous udpates.
    checkbox_fields = {}
    
    # the following variable keeps track of which checkbox fields are enabled for each build - this allows us to error
    # check only the necessary checkbox fields when we are verifying that the userobject has not been corrupted.
    enabled_checkbox_fields_list = []
    
    email_options_checkbox_fields = {

        'email_options' : {
            'label': ugettext_tuple(ugettext('Email notification settings')),
            'choices': [
                ('immediate_notification_of_new_messages_or_contacts',) + ugettext_tuple(immediate_notification_of_message_or_contacts),
                ('immediate_notification_of_new_messages',) + ugettext_tuple(immediate_notification_of_message),
                ('daily_notification_of_new_messages_or_contacts',) + ugettext_tuple(daily_notification_of_message_or_contacts),
                ('daily_notification_of_new_messages',) + ugettext_tuple(daily_notification_of_message),
                ('weekly_notification_of_new_messages_or_contacts',) + ugettext_tuple(weekly_notification_of_message_or_contacts),
                ('weekly_notification_of_new_messages',) + ugettext_tuple(weekly_notification_of_message),              
                ('monthly_notification_of_new_messages_or_contacts',) + ugettext_tuple(monthly_notification_of_message_or_contacts),
                ('monthly_notification_of_new_messages',) + ugettext_tuple(monthly_notification_of_message),
                ('only_password_recovery',) + ugettext_tuple(password_recovery_only),
                ],
            'options' : [],
            'input_type' : u'radio',
        }
    }
    checkbox_fields.update(email_options_checkbox_fields)    
    
    if settings.BUILD_NAME != "friend_build":
        languages_checkbox_fields = {
            'languages' : {
                'label': languages_label,
                'choices': languages_list,
                'start_sorting_index' : 0,
                'stop_sorting_index' : len(languages_list) - languages_end_sorting_index_offset,
                'options' : [],
                'input_type' : u'checkbox',

            },
        }
        checkbox_fields.update(languages_checkbox_fields)
        enabled_checkbox_fields_list.append("languages")
        
        entertainmnet_checkbox_fields = {
            'entertainment' : {
                'label': ugettext_tuple(ugettext('Hobbies')),
                'choices': [
                    ('crafts',) + ugettext_tuple(ugettext('Crafts')),
                    ('astrology',) + ugettext_tuple(ugettext('Astrology')),
                    ('dancing',) + ugettext_tuple(ugettext('Dancing')),
                    ('camping',) + ugettext_tuple(ugettext('Camping')),
                    ('dinner_parties',) + ugettext_tuple(ugettext('Dinner parties')),
                    ('movies',) + ugettext_tuple(ugettext('Movies')),
                    ('cooking',) + ugettext_tuple(ugettext('Cooking')),
                    ('concerts',) + ugettext_tuple(ugettext('Concerts')),
                    ('wine_tasting',) + ugettext_tuple(ugettext('Wine tasting')),
                    ('fashion_events',) + ugettext_tuple(ugettext('Fashion events')),
                    ('dance_clubs',) + ugettext_tuple(ugettext('Dance clubs')),
                    ('Writing',) + ugettext_tuple(ugettext('Writing')),
                    ('cultural_events',) + ugettext_tuple(ugettext('Cultural events')),
                    ('Photography',) + ugettext_tuple(ugettext('Photography')),
                    ('investing',) + ugettext_tuple(ugettext('Investing')),
                    ('shopping',) + ugettext_tuple(ugettext('Shopping')),
                    ('bars_pubs',) + ugettext_tuple(ugettext('Go for drinks')),
                    ('games',) + ugettext_tuple(ugettext('Traditional games')),
                    ('reading',) + ugettext_tuple(ugettext('Reading')),
                    ('internet',) + ugettext_tuple(ugettext('Surfing the web')),
                    ('news',) + ugettext_tuple(ugettext('News')),
                    ('walking',) + ugettext_tuple(ugettext('Walking')),
                    ('fishing',) + ugettext_tuple(ugettext('Fishing')),
                    ('Painting',) + ugettext_tuple(ugettext('Painting')),
                    ('poetry',) + ugettext_tuple(ugettext('Poetry')),
                    ('politics',) + ugettext_tuple(ugettext('Politics')),
                    ('restaurants',) + ugettext_tuple(ugettext('Restaurants')),
                    ('fine_dining',) + ugettext_tuple(ugettext('Fine dining')),
                    ('play_music',) + ugettext_tuple(ugettext('Play Music')),
                    ('tv',) + ugettext_tuple(ugettext('Watch TV')),
                    ('traveling',) + ugettext_tuple(ugettext('Travel')),
                    ('video_games',) + ugettext_tuple(ugettext('Video games')),
                    ('prefer_no_say',) + ugettext_tuple(ugettext('Prefer not to say')),
                    ],
                'start_sorting_index' : 0,
                'stop_sorting_index' : -1,
                'options' : [],
                'input_type' : u'checkbox',
            },
        }
        
        
        athletics_checkbox_fields = {
            'athletics' : {
                'label': ugettext_tuple(ugettext('Sports that I practice / like')),
                'choices' : [
                    ('aerobics',) + ugettext_tuple(ugettext('Aerobics')),
                    ('mountain_climbing',) + ugettext_tuple(ugettext('Mountain climbing')),
                    ('martial_arts',) + ugettext_tuple(ugettext('Martial Arts')),
                    ('basketball',) + ugettext_tuple(ugettext('Basketball')),
                    ('billiards',) + ugettext_tuple(ugettext('Billiards')),
                    ('diving',) + ugettext_tuple(ugettext('Diving')),
                    ('biking',) + ugettext_tuple(ugettext('Biking')),
                    ('jogging_running',) + ugettext_tuple(ugettext('Jogging / running')),
                    ('water_skiing',) + ugettext_tuple(ugettext('Water skiing')),
                    ('skiing',) + ugettext_tuple(ugettext('Snow skiing')),
                    ('snowboarding',) + ugettext_tuple(ugettext('Snowboarding')),
                    ('soccer',) + ugettext_tuple(ugettext('Soccer')),
                    ('golf',) + ugettext_tuple(ugettext('Golf')),
                    ('canoeing',) + ugettext_tuple(ugettext('Canoeing')),
                    ('bowling',) + ugettext_tuple(ugettext('Bowling')),
                    ('kitesurfing',) + ugettext_tuple(ugettext('Kitesurfing')),
                    ('kayaking',) + ugettext_tuple(ugettext('Kayaking')),
                    ('weight_lifting',) + ugettext_tuple(ugettext('Weight lifting')),
                    ('horseback_riding',) + ugettext_tuple(ugettext('Horseback Riding')),
                    ('hiking',) + ugettext_tuple(ugettext('Hiking')),
                    ('skating',) + ugettext_tuple(ugettext('Skating')),
                    ('swimming',) + ugettext_tuple(ugettext('Swimming')),
                    ('rugby',) + ugettext_tuple(ugettext('Rugby')),
                    ('surfing',) + ugettext_tuple(ugettext('Surfing')),
                    ('tennis',) + ugettext_tuple(ugettext('Tennis')),
                    ('sailing',) + ugettext_tuple(ugettext('Sailing')),
                    ('volleyball',) + ugettext_tuple(ugettext('Volleyball')),
                    ('windsurfing',) + ugettext_tuple(ugettext('Wind surfing')),
                    ('yoga',) + ugettext_tuple(ugettext('Yoga')),
                    ('prefer_no_say',) + ugettext_tuple(ugettext('Prefer not to say')),
                ],
                'start_sorting_index' : 0,
                'stop_sorting_index' : -1,
                'options' : [],
                'input_type' : u'checkbox',
            },
        }
        

        checkbox_fields.update(entertainmnet_checkbox_fields)
        checkbox_fields.update(athletics_checkbox_fields)

        enabled_checkbox_fields_list.append("entertainment")
        enabled_checkbox_fields_list.append("athletics")
    else:  # friend_build   
        friend_bazaar_specific_code.friend_bazaar_specific_choices(checkbox_fields, enabled_checkbox_fields_list)

    
    if settings.BUILD_NAME == "discrete_build" or settings.BUILD_NAME == "gay_build" or settings.BUILD_NAME == "swinger_build" \
       or settings.BUILD_NAME == "lesbian_build":
        turn_ons_checkbox_fields = {
            'turn_ons' : {
                'label' :  ugettext_tuple(ugettext('Turn ons')),
                'choices' : [
                    ('lingerie',) + ugettext_tuple(ugettext('Lingerie')),
                    ('safe_sex',) + ugettext_tuple(ugettext('Practice safe sex')),
                    ('go_slow',) + ugettext_tuple(ugettext('Goes slow')),
                    ('not_possesive',) + ugettext_tuple(ugettext('Not possessive')),
                    ('clean',) + ugettext_tuple(ugettext('Clean')),
                    ('asks_what_like',) + ugettext_tuple(ugettext('Asks what I like')),
                    ('says_what_like',) + ugettext_tuple(ugettext('Says what they like')),
                    ('gentle',) + ugettext_tuple(ugettext('Gentle')),
                    ('discression',) + ugettext_tuple(ugettext('Discretion')),
                    ('imagination',) + ugettext_tuple(ugettext('Good imagination')),
                    ('stamina',) + ugettext_tuple(ugettext('High stamina')),
                    ('take_control',) + ugettext_tuple(ugettext('Takes control')),
                    ('piercing',) + ugettext_tuple(ugettext('Piercing')),
                    ('tattoos',) + ugettext_tuple(ugettext('Tattoos')),
                    ('open_mind',) + ugettext_tuple(ugettext('Open mind')),
                    ('high_sex_drive',) + ugettext_tuple(ugettext('Strong libido')),
                    ('med_sex_drive',) + ugettext_tuple(ugettext('Normal libido')),
                    ('low_sex_drive',) + ugettext_tuple(ugettext('Low libido')),
                    ('prefer_no_say',) + ugettext_tuple(ugettext('Prefer not to say')),
                 
                    ],
                'start_sorting_index' : 0,
                'stop_sorting_index' : -1,
                'options' : [],
                'input_type' : u'checkbox',
                },
            }
        checkbox_fields.update(turn_ons_checkbox_fields)
        enabled_checkbox_fields_list.append("turn_ons")
        
            
    if settings.BUILD_NAME == "discrete_build" or settings.BUILD_NAME == "gay_build" or settings.BUILD_NAME == "swinger_build":
        adult_checkbox_fields = {
            'erotic_encounters' : {
                'label': ugettext_tuple(ugettext('Erotic encounters I am open to')),
                'choices' : [
                    ('sex_talk',) + ugettext_tuple(ugettext('Sex talk')),
                    ('cybersex',) + ugettext_tuple(ugettext('Cyber sex')),
                    ('sex_toys',) + ugettext_tuple(ugettext('Sex toys')),
                    ('normal_sex',) + ugettext_tuple(ugettext('Normal sex')),
                    ('oral_sex',) + ugettext_tuple(ugettext('Oral sex')),
                    ('one_night_stand',) + ugettext_tuple(ugettext('One night stand')),
                    ('erotic_movies',) + ugettext_tuple(ugettext('Erotic Movies')),
                    ('tantric_sex',) + ugettext_tuple(ugettext('Tantric sex')),
                    ('role_play',) + ugettext_tuple(ugettext('Role play')),
                    ('unusual_locs',) + ugettext_tuple(ugettext('Unusual locations for sex')),
                    ('soft_sex',) + ugettext_tuple(ugettext('Tenderness')),
                    ('costumes',) + ugettext_tuple(ugettext('Costumes&disgueses')),
                    ('transvestisim',) + ugettext_tuple(ugettext('Transvestisim')),
                    ('spanking',) + ugettext_tuple(ugettext('Spanking')),
                    ('threesomes',) + ugettext_tuple(ugettext('Threesomes')),
                    ('swinging',) + ugettext_tuple(ugettext('Swinging')),
                    ('erotic_photos',) + ugettext_tuple(ugettext('Erotic Photography')),
                    ('recording',) + ugettext_tuple(ugettext('Video')),
                    ('exhibitionism',) + ugettext_tuple(ugettext('Exhibitionism')),
                    ('vouyerism',) + ugettext_tuple(ugettext('Vouyerism')),
                    ('submission',) + ugettext_tuple(ugettext('Submission')),
                    ('domination',) + ugettext_tuple(ugettext('Domination')),
                    ('bondage',) + ugettext_tuple(ugettext('Bondage')),
                    ('latex',) + ugettext_tuple(ugettext('Latex/leather')),
                    ('whip',) + ugettext_tuple(ugettext('Whip')),
                    ('fetishes',) + ugettext_tuple(ugettext('Fetishes')),
                    ('prefer_no_say',) + ugettext_tuple(ugettext('Prefer not to say')),   
                    ],
                'start_sorting_index' : 0,
                'stop_sorting_index' : -1,
                'options' : [],
                'input_type' : u'checkbox',
            }
        }
        
        checkbox_fields.update(adult_checkbox_fields)
        enabled_checkbox_fields_list.append("erotic_encounters")
    
    if settings.BUILD_NAME == "language_build":
        languages_to_learn_checkbox_fields = {
            'languages_to_learn' : {
                'label': ugettext_tuple(ugettext('Languages I would like to practice')),
                'choices': languages_list,
                'start_sorting_index' : 0,
                'options' : [],
                'input_type' : u'checkbox',
            }
        }
        # copy the extra stuff into the main dict
        checkbox_fields.update(languages_to_learn_checkbox_fields)
        enabled_checkbox_fields_list.append("languages_to_learn")
    
    
    checkbox_options_dict = {}
    # now populate the 'options' arry for each of the above checkbox types.
    generate_option_line_based_on_data_struct(checkbox_fields, checkbox_options_dict)    
    
    change_password_fields = {    
            'current_password': {
                'label':        ugettext_tuple(ugettext('My current password')),
                'choices':      None,
                'options':      [],
                'input_type':   u'password',
                'required':     False},
            'new_password': {
                'label':        ugettext_tuple(ugettext('My new password')),
                'choices':      None,
                'options':      [],
                'input_type':   u'password',
                'required':     False},         
            'verify_new_password': {
                'label':        ugettext_tuple(ugettext('Verify new password')),
                'choices':      None,
                'options':      [],
                'input_type':   u'password',
                'required':     False},
    }