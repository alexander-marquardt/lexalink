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
            ('wite',)           + ugettext_tuple(ugettext('White hair')), 
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
                    ('astrology',) + ugettext_tuple(ugettext('Astrology')),
                    ('bars_pubs',) + ugettext_tuple(ugettext('Go for drinks')),
                    ('camping',) + ugettext_tuple(ugettext('Camping')),
                    ('cooking',) + ugettext_tuple(ugettext('Cooking')),
                    ('concerts',) + ugettext_tuple(ugettext('Concerts')),
                    ('computers',) + ugettext_tuple(ugettext('Computers')),
                    ('crafts',) + ugettext_tuple(ugettext('Crafts')),
                    ('cultural_events',) + ugettext_tuple(ugettext('Cultural events')),
                    ('dancing',) + ugettext_tuple(ugettext('Dancing')),
                    ('dance_clubs',) + ugettext_tuple(ugettext('Dance clubs')),
                    ('dinner_parties',) + ugettext_tuple(ugettext('Dinner parties')),
                    ('fashion_events',) + ugettext_tuple(ugettext('Fashion events')),
                    ('fine_dining',) + ugettext_tuple(ugettext('Fine dining')),
                    ('fishing',) + ugettext_tuple(ugettext('Fishing')),
                    ('games',) + ugettext_tuple(ugettext('Traditional games')),
                    ('internet',) + ugettext_tuple(ugettext('Surfing the web')),
                    ('investing',) + ugettext_tuple(ugettext('Investing')),
                    ('listen_to_music',) + ugettext_tuple(ugettext('Listen to music')),
                    ('movies',) + ugettext_tuple(ugettext('Movies')),
                    ('news',) + ugettext_tuple(ugettext('News')),
                    ('Painting',) + ugettext_tuple(ugettext('Painting')),
                    ('Photography',) + ugettext_tuple(ugettext('Photography')),
                    ('play_music',) + ugettext_tuple(ugettext('Play Music')),
                    ('poetry',) + ugettext_tuple(ugettext('Poetry')),
                    ('politics',) + ugettext_tuple(ugettext('Politics')),
                    ('reading',) + ugettext_tuple(ugettext('Reading')),
                    ('restaurants',) + ugettext_tuple(ugettext('Restaurants')),
                    ('shopping',) + ugettext_tuple(ugettext('Shopping')),
                    ('traveling',) + ugettext_tuple(ugettext('Travel')),
                    ('tv',) + ugettext_tuple(ugettext('Watch TV')),
                    ('video_games',) + ugettext_tuple(ugettext('Video games')),
                    ('walking',) + ugettext_tuple(ugettext('Walking')),
                    ('wine_tasting',) + ugettext_tuple(ugettext('Wine tasting')),
                    ('Writing',) + ugettext_tuple(ugettext('Writing')),
                    ('prefer_no_say',) + ugettext_tuple(ugettext('Prefer not to say')),
                    ],

                'wrap_choice_with_anchor' : {
                    'camping': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=camping&linkCode=ur2&rh=n%3A2454136031%2Ck%3Acamping&tag=wwwlexabitcom-21&url=search-alias%3Dsporting">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'crafts': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=artesania&linkCode=ur2&rh=n%3A599391031%2Ck%3Aartesania&sprefix=artesania%2Ckitchen%2C225&tag=wwwlexabitcom-21&url=search-alias%3Dkitchen">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'cooking': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=cocinar&linkCode=ur2&rh=n%3A599364031%2Ck%3Acocinar&tag=wwwlexabitcom-21&url=search-alias%3Dstripbooks">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'fishing': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=pescar&linkCode=ur2&tag=wwwlexabitcom-21&url=search-alias%3Dsporting">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'games': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=juegos%20de%20mesa%20adultos&linkCode=ur2&rh=n%3A599385031%2Ck%3Ajuegos%20de%20mesa%20adultos&sprefix=juegos%20de%20mesa%20para%20ni%C3%B1os%2Cshoes%2C223&tag=wwwlexabitcom-21&url=search-alias%3Dtoys">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'computers': {'es': u'<a target="_blank" href="http://www.amazon.es/b/?_encoding=UTF8&ajr=0&camp=3626&creative=24822&linkCode=ur2&node=667049031&tag=wwwlexabitcom-21">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'investing': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=invertir&linkCode=ur2&rh=n%3A599364031%2Ck%3Ainvertir&tag=wwwlexabitcom-21&url=search-alias%3Dstripbooks">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'listen_to_music': {'es': u'<a target="_blank" href="http://www.amazon.es/b/?_encoding=UTF8&camp=3626&creative=24822&linkCode=ur2&node=664684031&tag=wwwlexabitcom-21">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'movies': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=peliculas&linkCode=ur2&sprefix=peliculas%2Caps%2C236&tag=wwwlexabitcom-21&url=search-alias%3Ddvd">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'Painting': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=juego%20de%20pintura&linkCode=ur2&rh=i%3Aaps%2Ck%3Ajuego%20de%20pintura&tag=wwwlexabitcom-21&url=search-alias%3Daps">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'Photography': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=cameras%20digitales&linkCode=ur2&rh=i%3Aaps%2Ck%3Acameras%20digitales&sprefix=cameras%2Cshoes%2C261&tag=wwwlexabitcom-21&url=search-alias%3Daps">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'play_music': {'es': u'<a target="_blank" href="http://www.amazon.es/b/?_encoding=UTF8&ajr=0&camp=3626&creative=24822&linkCode=ur2&node=3628866031&tag=wwwlexabitcom-21">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'poetry': {'es':u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=poesia&linkCode=ur2&rh=n%3A599364031%2Ck%3Apoesia&tag=wwwlexabitcom-21&url=search-alias%3Dstripbooks">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'reading': {'es': u'<a target="_blank" href="http://www.amazon.es/b/?_encoding=UTF8&ajr=0&camp=3626&creative=24822&linkCode=ur2&node=599364031&tag=wwwlexabitcom-21">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'tv': {'es': u'<a target="_blank" href="http://www.amazon.es/b/?_encoding=UTF8&camp=3626&creative=24822&linkCode=ur2&node=664659031&pf_rd_i=televisiones&pf_rd_m=A1AT7YVPFBWXBL&pf_rd_p=505144087&pf_rd_r=1N72X0NQP2B6JBA9QHQ4&pf_rd_s=auto-sparkle&pf_rd_t=301&tag=wwwlexabitcom-21">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'video_games': {'es': u'<a target="_blank" href="http://www.amazon.es/b/?_encoding=UTF8&ajr=0&camp=3626&creative=24822&linkCode=ur2&node=599382031&tag=wwwlexabitcom-21">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},

                },
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
                    ('basketball',) + ugettext_tuple(ugettext('Basketball')),
                    ('biking',) + ugettext_tuple(ugettext('Biking')),
                    ('billiards',) + ugettext_tuple(ugettext('Billiards')),
                    ('bowling',) + ugettext_tuple(ugettext('Bowling')),
                    ('canoeing',) + ugettext_tuple(ugettext('Canoeing')),
                    ('diving',) + ugettext_tuple(ugettext('Diving')),
                    ('golf',) + ugettext_tuple(ugettext('Golf')),
                    ('hiking',) + ugettext_tuple(ugettext('Hiking')),
                    ('horseback_riding',) + ugettext_tuple(ugettext('Horseback Riding')),
                    ('jogging_running',) + ugettext_tuple(ugettext('Jogging / running')),
                    ('kayaking',) + ugettext_tuple(ugettext('Kayaking')),
                    ('kitesurfing',) + ugettext_tuple(ugettext('Kitesurfing')),
                    ('martial_arts',) + ugettext_tuple(ugettext('Martial Arts')),
                    ('mountain_climbing',) + ugettext_tuple(ugettext('Mountain climbing')),
                    ('rugby',) + ugettext_tuple(ugettext('Rugby')),
                    ('sailing',) + ugettext_tuple(ugettext('Sailing')),
                    ('skating',) + ugettext_tuple(ugettext('Skating')),
                    ('skiing',) + ugettext_tuple(ugettext('Snow skiing')),
                    ('snowboarding',) + ugettext_tuple(ugettext('Snowboarding')),
                    ('soccer',) + ugettext_tuple(ugettext('Soccer')),
                    ('surfing',) + ugettext_tuple(ugettext('Surfing')),
                    ('swimming',) + ugettext_tuple(ugettext('Swimming')),
                    ('tennis',) + ugettext_tuple(ugettext('Tennis')),
                    ('volleyball',) + ugettext_tuple(ugettext('Volleyball')),
                    ('water_skiing',) + ugettext_tuple(ugettext('Water skiing')),
                    ('weight_lifting',) + ugettext_tuple(ugettext('Weight lifting')),
                    ('windsurfing',) + ugettext_tuple(ugettext('Wind surfing')),
                    ('yoga',) + ugettext_tuple(ugettext('Yoga')),
                    ('prefer_no_say',) + ugettext_tuple(ugettext('Prefer not to say')),
                ],
                'wrap_choice_with_anchor' : {
                    'aerobics': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=aerobic&linkCode=ur2&sprefix=aerobic%2Caps&tag=wwwlexabitcom-21&url=search-alias%3Daps">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'basketball': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=Baloncesto&linkCode=ur2&rh=i%3Aaps%2Ck%3ABaloncesto&tag=wwwlexabitcom-21&url=search-alias%3Daps">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'biking': {'es': u'<a target="_blank" href="http://www.amazon.es/Ciclismo-Bicicletas-Cascos-Luces-Herramientas/b/?_encoding=UTF8&camp=3626&creative=24822&linkCode=ur2&node=2928487031&pf_rd_i=ciclismo&pf_rd_m=A1AT7YVPFBWXBL&pf_rd_p=506092667&pf_rd_r=0BNNX1A815RDAJZ6B479&pf_rd_s=auto-sparkle&pf_rd_t=301&tag=wwwlexabitcom-21">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'billards': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=billar&linkCode=ur2&tag=wwwlexabitcom-21&url=search-alias%3Daps">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'canoeing': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=canoa&linkCode=ur2&rh=n%3A2454136031%2Ck%3Acanoa&tag=wwwlexabitcom-21&url=search-alias%3Dsporting">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'diving': {'es': u'<a target="_blank" href="http://www.amazon.es/gp/search/?ie=UTF8&camp=3626&creative=24822&keywords=buceo&linkCode=ur2&qid=1417198333&rh=i%3Asporting%2Ck%3Abuceo&tag=wwwlexabitcom-21">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'golf': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=golf&linkCode=ur2&rh=n%3A2454136031%2Ck%3Agolf&tag=wwwlexabitcom-21&url=search-alias%3Dsporting">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'hiking': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=excursionismo&linkCode=ur2&rh=n%3A2454136031%2Ck%3Aexcursionismo&tag=wwwlexabitcom-21&url=search-alias%3Dsporting">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'horseback_riding': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=montar%20caballo&linkCode=ur2&rh=n%3A2454136031%2Ck%3Amontar%20caballo&tag=wwwlexabitcom-21&url=search-alias%3Dsporting">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'jogging_running': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=correr&linkCode=ur2&rh=n%3A2454136031%2Ck%3Acorrer&tag=wwwlexabitcom-21&url=search-alias%3Dsporting">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'kayaking': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=kayak&linkCode=ur2&rh=n%3A2454136031%2Ck%3Akayak&tag=wwwlexabitcom-21&url=search-alias%3Dsporting">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'kitesurfing': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=kitesurf&linkCode=ur2&rh=n%3A2454136031%2Ck%3Akitesurf&tag=wwwlexabitcom-21&url=search-alias%3Dsporting">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'martial_arts': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=artes%20marciales&linkCode=ur2&rh=n%3A2454136031%2Ck%3Aartes%20marciales&tag=wwwlexabitcom-21&url=search-alias%3Dsporting">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'mountain_climbing': {'es': u'<a target="_blank" href="http://www.amazon.es/gp/search/?ie=UTF8&camp=3626&creative=24822&keywords=monta%C3%B1ismo&linkCode=ur2&qid=1417195260&rh=i%3Asporting%2Ck%3Amonta%C3%B1ismo&tag=wwwlexabitcom-21">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'rugby': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=rugby&linkCode=ur2&rh=n%3A2454136031%2Ck%3Arugby&tag=wwwlexabitcom-21&url=search-alias%3Dsporting">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'sailing': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=navegaci%C3%B3n&linkCode=ur2&rh=n%3A2454136031%2Ck%3Anavegaci%C3%B3n&tag=wwwlexabitcom-21&url=search-alias%3Dsporting">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'skating': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=patinaje&linkCode=ur2&rh=n%3A2454136031%2Ck%3Apatinaje&tag=wwwlexabitcom-21&url=search-alias%3Dsporting">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'skiing': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=esqui&linkCode=ur2&rh=n%3A2454136031%2Ck%3Aesqui&tag=wwwlexabitcom-21&url=search-alias%3Dsporting">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'snowboarding': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=snowboard&linkCode=ur2&rh=n%3A2454136031%2Ck%3Asnowboard&tag=wwwlexabitcom-21&url=search-alias%3Dsporting">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'soccer': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=futbol&linkCode=ur2&rh=n%3A2454136031%2Ck%3Afutbol&tag=wwwlexabitcom-21&url=search-alias%3Dsporting">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'surfing': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=surf&linkCode=ur2&rh=n%3A2454136031%2Ck%3Asurf&tag=wwwlexabitcom-21&url=search-alias%3Dsporting">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'tennis': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=tenis&linkCode=ur2&rh=n%3A2454136031%2Ck%3Atenis&tag=wwwlexabitcom-21&url=search-alias%3Dsporting">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'volleyball': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=voleibol&linkCode=ur2&rh=n%3A2454136031%2Ck%3Avoleibol&tag=wwwlexabitcom-21&url=search-alias%3Dsporting">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'water_skiing': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=esqui%20acuatico&linkCode=ur2&rh=n%3A2454136031%2Ck%3Aesqui%20acuatico&tag=wwwlexabitcom-21&url=search-alias%3Dsporting">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'weight_lifting': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=levantar%20pesas&linkCode=ur2&rh=n%3A2454136031%2Ck%3Alevantar%20pesas&tag=wwwlexabitcom-21&url=search-alias%3Dsporting">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'windsurfing': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=windsurf&linkCode=ur2&rh=n%3A2454136031%2Ck%3Awindsurf&tag=wwwlexabitcom-21&url=search-alias%3Dsporting">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'yoga': {'es': u'<a target="_blank" href="http://www.amazon.es/mn/search/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=nadar&linkCode=ur2&rh=n%3A2454136031%2Ck%3Anadar&tag=wwwlexabitcom-21&url=search-alias%3Dsporting">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                },
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
                    ('asks_what_like',) + ugettext_tuple(ugettext('Asks what I like')),
                    ('clean',) + ugettext_tuple(ugettext('Clean')),
                    ('discression',) + ugettext_tuple(ugettext('Discretion')),
                    ('gentle',) + ugettext_tuple(ugettext('Gentle')),
                    ('give_massage',) + ugettext_tuple(ugettext('Give a massage')),
                    ('go_slow',) + ugettext_tuple(ugettext('Goes slow')),
                    ('high_sex_drive',) + ugettext_tuple(ugettext('Strong libido')),
                    ('imagination',) + ugettext_tuple(ugettext('Good imagination')),
                    ('lingerie',) + ugettext_tuple(ugettext('Lingerie')),
                    ('low_sex_drive',) + ugettext_tuple(ugettext('Low libido')),
                    ('med_sex_drive',) + ugettext_tuple(ugettext('Normal libido')),
                    ('not_possesive',) + ugettext_tuple(ugettext('Not possessive')),
                    ('open_mind',) + ugettext_tuple(ugettext('Open mind')),
                    ('piercing',) + ugettext_tuple(ugettext('Piercing')),
                    ('receive_massage',) + ugettext_tuple(ugettext('Receive a massage')),
                    ('safe_sex',) + ugettext_tuple(ugettext('Practice safe sex')),
                    ('says_what_like',) + ugettext_tuple(ugettext('Says what they like')),
                    ('scented_candles',)  + ugettext_tuple(ugettext('Scented candles')),
                    ('stamina',) + ugettext_tuple(ugettext('High stamina')),
                    ('take_control',) + ugettext_tuple(ugettext('Takes control')),
                    ('tattoos',) + ugettext_tuple(ugettext('Tattoos')),
                    ('prefer_no_say',) + ugettext_tuple(ugettext('Prefer not to say')),
                    ],
                'wrap_choice_with_anchor': {
                    'give_massage': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=aceite%20masaje&linkCode=ur2&rh=n%3A599391031%2Ck%3Aaceite%20masaje&tag=wwwlexabitcom-21&url=search-alias%3Dkitchen">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'high_sex_drive': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=libido&linkCode=ur2&rh=n%3A599391031%2Ck%3Alibido&tag=wwwlexabitcom-21&url=search-alias%3Dkitchen">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'low_sex_drive': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=libido&linkCode=ur2&rh=n%3A599391031%2Ck%3Alibido&tag=wwwlexabitcom-21&url=search-alias%3Dkitchen">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'med_sex_drive': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=libido&linkCode=ur2&rh=n%3A599391031%2Ck%3Alibido&tag=wwwlexabitcom-21&url=search-alias%3Dkitchen">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'lingerie': {'es': u'<a target="_blank" href="http://www.amazon.es/gp/search/?ie=UTF8&camp=3626&creative=24822&keywords=lenceria&linkCode=ur2&qid=1417140235&rh=i%3Aaps%2Ck%3Alenceria&tag=wwwlexabitcom-21">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'piercing': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=piercing&linkCode=ur2&rh=n%3A599391031%2Ck%3Apiercing&tag=wwwlexabitcom-21&url=search-alias%3Dkitchen">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'receive_massage': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=masajeador&linkCode=ur2&rh=i%3Aaps%2Ck%3Amasajeador&sprefix=masajes%2Ckitchen%2C529&tag=wwwlexabitcom-21&url=search-alias%3Daps">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'safe_sex': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=condones&linkCode=ur2&rh=i%3Aaps%2Ck%3Acondones&tag=wwwlexabitcom-21&url=search-alias%3Daps">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'scented_candles': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=velas%20aromaticas&linkCode=ur2&rh=n%3A599391031%2Ck%3Avelas%20aromaticas&tag=wwwlexabitcom-21&url=search-alias%3Dkitchen">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    },
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
                    ('bondage',) + ugettext_tuple(ugettext('Bondage')),
                    ('costumes',) + ugettext_tuple(ugettext('Costumes')),
                    ('cybersex',) + ugettext_tuple(ugettext('Cyber sex')),
                    # ('dildo',) + ugettext_tuple(ugettext('Use a dildo')),
                    ('domination',) + ugettext_tuple(ugettext('Domination')),
                    ('erotic_movies',) + ugettext_tuple(ugettext('Erotic Movies')),
                    ('erotic_photos',) + ugettext_tuple(ugettext('Erotic Photography')),
                    ('exhibitionism',) + ugettext_tuple(ugettext('Exhibitionism')),
                    ('fetishes',) + ugettext_tuple(ugettext('Fetishes')),
                    ('latex',) + ugettext_tuple(ugettext('Latex/leather')),
                    ('male_toys',) + ugettext_tuple(ugettext('Toys for men')),
                    ('normal_sex',) + ugettext_tuple(ugettext('Normal sex')),
                    ('oral_sex',) + ugettext_tuple(ugettext('Oral sex')),
                    ('one_night_stand',) + ugettext_tuple(ugettext('One night stand')),
                    ('penis_pump',) + ugettext_tuple(ugettext('Use erection pump')),
                    ('recording',) + ugettext_tuple(ugettext('Video')),
                    ('role_play',) + ugettext_tuple(ugettext('Role play')),
                    ('sex_talk',) + ugettext_tuple(ugettext('Sex talk')),
                    ('sex_toys',) + ugettext_tuple(ugettext('Erotic toys')),
                    ('soft_sex',) + ugettext_tuple(ugettext('Tenderness')),
                    ('spanking',) + ugettext_tuple(ugettext('Spanking')),
                    ('submission',) + ugettext_tuple(ugettext('Submission')),
                    ('swinging',) + ugettext_tuple(ugettext('Swinging')),
                    ('tantric_sex',) + ugettext_tuple(ugettext('Tantric sex')),
                    ('threesomes',) + ugettext_tuple(ugettext('Threesomes')),
                    ('transvestisim',) + ugettext_tuple(ugettext('Transvestisim')),
                    ('unusual_locs',) + ugettext_tuple(ugettext('Unusual locations')),
                    ('vibrator',) + ugettext_tuple(ugettext('Use a vibrator')),
                    ('vouyerism',) + ugettext_tuple(ugettext('Vouyerism')),
                    ('whip',) + ugettext_tuple(ugettext('Whip')),
                    ('prefer_no_say',) + ugettext_tuple(ugettext('Prefer not to say')),
                    ],
                'wrap_choice_with_anchor' : {
                    'bondage': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=juguetes%20servidumbre&linkCode=ur2&rh=i%3Aaps%2Ck%3Ajuguetes%20servidumbre&tag=wwwlexabitcom-21&url=search-alias%3Daps">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'costumes': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=disfraces%20eroticos&linkCode=ur2&rh=i%3Aaps%2Ck%3Adisfraces%20eroticos&tag=wwwlexabitcom-21&url=search-alias%3Daps">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'domination': {'es':u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=juguetes%20servidumbre&linkCode=ur2&rh=i%3Aaps%2Ck%3Ajuguetes%20servidumbre&tag=wwwlexabitcom-21&url=search-alias%3Daps">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'fetishes': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=fetish&linkCode=ur2&rh=n%3A599391031%2Ck%3Afetish&tag=wwwlexabitcom-21&url=search-alias%3Dkitchen">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'normal_sex': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=lubricante%20sexual&linkCode=ur2&rh=n%3A599391031%2Ck%3Alubricante%20sexual&tag=wwwlexabitcom-21&url=search-alias%3Dkitchen">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'oral_sex': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=sexo%20oral&linkCode=ur2&rh=n%3A599391031%2Ck%3Asexo%20oral&tag=wwwlexabitcom-21&url=search-alias%3Dkitchen">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'one_night_stand': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=condones&linkCode=ur2&rh=i%3Aaps%2Ck%3Acondones&tag=wwwlexabitcom-21&url=search-alias%3Daps">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'recording': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=videocamara&linkCode=ur2&rh=n%3A599370031%2Ck%3Avideocamara&sprefix=video%2Csporting%2C221&tag=wwwlexabitcom-21&url=search-alias%3Delectronics">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'sex_toys' : {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=juguetes%20eroticos&linkCode=ur2&rh=i%3Aaps%2Ck%3Ajuguetes%20eroticos&tag=wwwlexabitcom-21&url=search-alias%3Daps">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'submission' : {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=juguetes%20servidumbre&linkCode=ur2&rh=i%3Aaps%2Ck%3Ajuguetes%20servidumbre&tag=wwwlexabitcom-21&url=search-alias%3Daps">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'tantric_sex': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=sexo%20tantrico&linkCode=ur2&rh=i%3Aaps%2Ck%3Asexo%20tantrico&tag=wwwlexabitcom-21&url=search-alias%3Daps">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    # 'dildo': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=dildos&linkCode=ur2&rh=n%3A599391031%2Ck%3Adildos&tag=wwwlexabitcom-21&url=search-alias%3Dkitchen">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'penis_pump': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=bomba%20ereccion&linkCode=ur2&rh=n%3A599391031%2Ck%3Abomba%20ereccion&tag=wwwlexabitcom-21&url=search-alias%3Dkitchen">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'male_toys': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=masturbacion%20masculina&linkCode=ur2&rh=n%3A599391031%2Ck%3Amasturbacion%20masculina&tag=wwwlexabitcom-21&url=search-alias%3Dkitchen">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                    'vibrator': {'es': u'<a target="_blank" href="http://www.amazon.es/s/?_encoding=UTF8&camp=3626&creative=24822&field-keywords=vibradores&linkCode=ur2&rh=n%3A599391031%2Ck%3Avibradores&tag=wwwlexabitcom-21&url=search-alias%3Dkitchen">{option_string}</a><img src="https://ir-es.amazon-adsystem.com/e/ir?t=wwwlexabitcom-21&l=ur2&o=30" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;" />'},
                },
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