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


# Dummy ugettext, so that the translator can find the strings that we are passing into other functions.
# the functions that this is passed into will have the read ugettext
ugettext = lambda s: s

import logging
import settings
from django.utils.encoding import smart_unicode
from data_struct_utils import *
import constants,  localizations, friend_bazaar_specific_code
from translation_helpers import ugettext_tuple

if settings.BUILD_NAME == "friend_build":
    # *hack* April 18 2012 **  
    # This is a hack - user_profile_details must be imported before user_profile_main in order to setup 
    # the original_activity_list_used_to_derive_checkbox_list data structure. 
    from rs import user_profile_details    


class UserSpec():
    
    # Note, this class should only be called once during execution. It should not be instantiated as an object, but rather
    # only used as a "class object". For this reason, the multi-language customizations here are different than in other 
    # places. It is necessary to set up and store all language translations in one go, which means that we store information
    # for different languages in arrays that will be indexed by the current language configuration. 
    
    
    #specify which fields will be required for login or signup
    left_side_fields_to_display_in_order = ['username_email', 'password']
    
    if settings.BUILD_NAME != 'language_build' and settings.BUILD_NAME != "friend_build":
        principal_user_data = ['sex', 'preference', 'relationship_status', 'age', 'country', 'username',]
        simple_search_fields = [ 'sex', 'country', 'relationship_status','preference', 'region', 'query_order', 'age', 'sub_region',   ]

    else:
        if settings.BUILD_NAME == 'language_build':
            principal_user_data = ['native_language', 'language_to_learn',  'age', 'sex', 'country',  'username',]
            simple_search_fields = [ 'language_to_learn',   'country', 'age', 'language_to_teach', 'region', 'query_order',  'sex', 'sub_region',   ]  
        elif settings.BUILD_NAME == 'friend_build':
            principal_user_data = [ 'username', 'age',  'sex',  'country', ]
            simple_search_fields = ['for_sale',          'country',    'age',
                                    'for_sale_sub_menu', 'region',     'query_order',
                                    'sex',               'sub_region',]  
        else:
            assert(0)
            
    signup_fields_to_display_in_order =  principal_user_data + ['email_address', 'password', 'password_verify', ]
    #define fields that will show up in the "simple" search bar on the users main page
    
    # define don't care in the languages that we will use
    dont_care_tuple = ('----',)        +  ugettext_tuple(ugettext("Not Important"))
    anything_tuple = ('----',)        +  ugettext_tuple(ugettext("Anything"))
    show_all_tuple = ('----',)        +  ugettext_tuple(ugettext("Show All"))
    
    if settings.BUILD_NAME != "lesbian_build":
        gender_dont_care_tuple = ('----',) +  ugettext_tuple(ugettext("All People"))
    else:
        gender_dont_care_tuple = ('----',) +  ugettext_tuple(ugettext("All Lesbian Types"))


    # define the genders that will be used for registering and searching the database. Will be populated
    # with the language-appropriate translations when necessary. 
    # Currently Spanish is at location offset 1. 
    
    if settings.BUILD_NAME == 'discrete_build':
        gender_categories = [
            ('female',)        + ugettext_tuple(ugettext('Female')), 
            ('male',)          + ugettext_tuple(ugettext('Male')), 
            ('couple',)        + ugettext_tuple(ugettext('Swinger (Couple)')),
            ('tstvtg',)        + ugettext_tuple(ugettext('Transvestite / Transgendered'))]    
        
        # Note, we define two seperate fields below because gender_*search*_categories will have don't care added, while
        # gender_categories should not be modified.
        gender_preference_categories =  [
            ('female',)        + ugettext_tuple(ugettext('Females')), 
            ('male',)          + ugettext_tuple(ugettext('Males')), 
            ('couple',)        + ugettext_tuple(ugettext('Swingers (Couples)')),
            ('tstvtg',)        + ugettext_tuple(ugettext('Transvestites / Transgendered'))] 
        
 
    if settings.BUILD_NAME =='swinger_build':
        gender_categories = [
            ('couple',)            + ugettext_tuple(ugettext('Swinger (Couple)')),
            ('female',)            + ugettext_tuple(ugettext('Female')), 
            ('male',)              + ugettext_tuple(ugettext('Male')), 
            ('tstvtg',)            + ugettext_tuple(ugettext('Transvestite / Transgendered')),
            ('other',)             + ugettext_tuple(ugettext('Other (Details In Profile)')),
            ]    
        
        # Note, we define two seperate fields below because gender_search_categories will have don't care added, while
        # gender_categories should not be modified.
        gender_preference_categories =  [
            ('couple',)            + ugettext_tuple(ugettext('Swingers (Couples)')),
            ('female',)            + ugettext_tuple(ugettext('Females')), 
            ('male',)              + ugettext_tuple(ugettext('Males')), 
            ('tstvtg',)            + ugettext_tuple(ugettext('Transvestites / Transgendered')),
            ('other',)             + ugettext_tuple(ugettext('Others (Details In Profile)')),
            ]   
        
    if settings.BUILD_NAME =='gay_build':
        gender_categories = [
            ('active',)            + ugettext_tuple(ugettext('Active Gay')),
            ('passive',)        + ugettext_tuple(ugettext('Passive Gay')),
            ('versatile',)    + ugettext_tuple(ugettext('Versatile Gay')),
            ('bisexual',)            + ugettext_tuple(ugettext('Bisexual')), 
            ('tstvtg',)            + ugettext_tuple(ugettext('Transvestite / Transgendered')),
            ('other',)             + ugettext_tuple(ugettext('Other (Details In Profile)')),
            ]    
        
        
        gender_preference_categories = [
            ('active',)            + ugettext_tuple(ugettext('Active Gays')),
            ('passive',)        + ugettext_tuple(ugettext('Passive Gays')),
            ('versatile',)    + ugettext_tuple(ugettext('Versatile Gays')),
            ('bisexual',)            + ugettext_tuple(ugettext('Bisexuals')), 
            ('tstvtg',)            + ugettext_tuple(ugettext('Transvestites / Transgendered')),
            ('other',)             + ugettext_tuple(ugettext('Others (Details In Profile)')),
            ]    
        
 
        
    if settings.BUILD_NAME == 'discrete_build' or settings.BUILD_NAME == 'swinger_build' or settings.BUILD_NAME == 'gay_build':    
               
        # relationship_categories specifies what status people are allowed to declare. 
        relationship_categories = [
            ('single',)        + ugettext_tuple(ugettext('Single')), 
            ('in_relation',)   + ugettext_tuple(ugettext('Attached')),
            ('married',)       + ugettext_tuple(ugettext('Married')),
            ('prefer_no_say',) + ugettext_tuple(ugettext('Prefer Not To Say'))
        ]
        # relationship_search_categories specifies what status people are allowed to search_for. 
        relationship_search_categories = [dont_care_tuple,
            ('single',)        + ugettext_tuple(ugettext('Single')), 
            ('in_relation',)   + ugettext_tuple(ugettext('Attached')),
            ('married',)       + ugettext_tuple(ugettext('Married')),
            ('prefer_no_say',) + ugettext_tuple(ugettext("Secret")),]

    # LOCUS LOFT CONFIGURATION
    elif settings.BUILD_NAME == 'single_build' or settings.BUILD_NAME == 'mature_build': 
        gender_categories = [
            ('female',)     + ugettext_tuple(ugettext('Female')), 
            ('male',)       + ugettext_tuple(ugettext('Male')),
        ]   
        # Note: this is different than gender categories since it is pluralized.
        gender_preference_categories =  [
            ('female',)     + ugettext_tuple(ugettext('Females')), 
            ('male',)       + ugettext_tuple(ugettext('Males')),
        ]    
        
        # relationship_categories specifies what status people are allowed to declare. 
        relationship_categories = [
            ('friendship',)    + ugettext_tuple(ugettext('Friendship')), 
            ('dating',)        + ugettext_tuple(ugettext('Dating')),
            ('relationship',)   + ugettext_tuple(ugettext('Long Term Relationship')),
        ]
        # relationship_search_categories specifies what status people are allowed to search_for. 
        relationship_search_categories = [anything_tuple] + relationship_categories
        
    # LINGO LOFT CONFIGURATION    
    elif settings.BUILD_NAME == 'language_build':
        gender_categories = [
            ('female',)        + ugettext_tuple(ugettext('Female')), 
            ('male', )         + ugettext_tuple(ugettext('Male')),
            ('prefer_no_say',) + ugettext_tuple(ugettext('Prefer Not To Say')),        
        ]      
        gender_preference_categories =  [ # only used for setting up the gender_search_categories below
            ('female',)        + ugettext_tuple(ugettext('Females')), 
            ('male',)          + ugettext_tuple(ugettext('Males')),
            ('prefer_no_say',) + ugettext_tuple(ugettext("People Who Don't Specify")),       
        ]               
        
      
    elif settings.BUILD_NAME == 'friend_build':
        gender_categories = [
            ('female',)        + ugettext_tuple(ugettext('Female')), 
            ('male', )         + ugettext_tuple(ugettext('Male')),
        ]      
        gender_preference_categories =  [ # only used for setting up the gender_search_categories below
            ('female',)        + ugettext_tuple(ugettext('Females')), 
            ('male',)          + ugettext_tuple(ugettext('Males')),
        ]               

    elif settings.BUILD_NAME == 'lesbian_build': 
        gender_categories = [
            ('femme',)       + ugettext_tuple(ugettext('Femme (Feminine Lesbian)')),
            ('bisexual',)       + ugettext_tuple(ugettext('Bisexual Lesbian')),
            ('butch',)     + ugettext_tuple(ugettext('Butch (Masculine Lesbian)')), 
            ('prefer_no_say',)       + ugettext_tuple(ugettext("Unlabeled Lesbian")),
        ]   
        # Note: this is different than gender categories since it is pluralized.
        gender_preference_categories =  [
            ('femme',)       + ugettext_tuple(ugettext('Femmes (Feminine Lesbians)')),
            ('bisexual',)       + ugettext_tuple(ugettext('Bisexual Lesbians')),
            ('butch',)     + ugettext_tuple(ugettext('Butches (Masculine Lesbians)')), 
            ('prefer_no_say',)       + ugettext_tuple(ugettext("Unlabeled Lesbians")),
        ]    
        
        # relationship_categories specifies what status people are allowed to declare. 
        relationship_categories = [
            ('friendship',)    + ugettext_tuple(ugettext('Friendship')), 
            ('dating',)        + ugettext_tuple(ugettext('Dating')),
            ('relationship',)   + ugettext_tuple(ugettext('Long Term Relationship')),
            ('sexual_relationship',)   + ugettext_tuple(ugettext('Physical Relationship')),
        ]
        # relationship_search_categories specifies what status people are allowed to search_for. 
        relationship_search_categories = [anything_tuple] + relationship_categories
                
        
    else: # Unknown configuration
        assert False
        
    gender_search_categories = [gender_dont_care_tuple,] + gender_preference_categories
        
    # common to different builds     
    if settings.BUILD_NAME != "language_build" and settings.BUILD_NAME != "friend_build":
        preference_search_categories = [dont_care_tuple,] + gender_preference_categories    
    
        
    # the age category follows the same format as all other data structures so that 
    # special case code is not required. This is why it is repeated 3x. Note that the keys
    # are the value in the first column -- these are the lower bound of the age range, so that
    # if we decide to increase the number of choices in the future, the keys do not need to be
    # modified (just add new ones between the existing ones).
    
    if settings.BUILD_NAME != "language_build" and settings.BUILD_NAME != "mature_build":
        age_categories = [
            ('18',) + ugettext_tuple('18-21'),
            ('22',) + ugettext_tuple('22-25'),
            ('26',) + ugettext_tuple('26-30'),
            ('30',) + ugettext_tuple('30-33'),
            ('34',) + ugettext_tuple('34-37'),
            ('38',) + ugettext_tuple('38-41'),
            ('42',) + ugettext_tuple('42-45'),
            ('46',) + ugettext_tuple('46-49'),       
            ('50',) + ugettext_tuple('50-53'),
            ('54',) + ugettext_tuple('54-57'),
            ('58',) + ugettext_tuple('58-61'),          
            ('62',) + ugettext_tuple('62-65'),        
            ('66',) + ugettext_tuple('66-69'),
            ('70',) + ugettext_tuple('70+'),
        ]
    elif settings.BUILD_NAME == "language_build":
        age_categories = [
            ('14',) + ugettext_tuple('14-17'), 
            ('18',) + ugettext_tuple('18-25'),
            ('26',) + ugettext_tuple('26-33'),
            ('34',) + ugettext_tuple('34-41'),
            ('42',) + ugettext_tuple('42-49'),
            ('50',) + ugettext_tuple('50-57'),
            ('58',) + ugettext_tuple('58-65'),          
            ('66',) + ugettext_tuple('66-73'),
            ('74',) + ugettext_tuple('74-81'),
            ('82',) + ugettext_tuple('82-89'),
            ('90',) + ugettext_tuple('90+'),
        ]
        
    elif settings.BUILD_NAME == "mature_build":
        age_categories = [
            ('50',) + ugettext_tuple('50-57'),
            ('58',) + ugettext_tuple('58-65'),          
            ('66',) + ugettext_tuple('66-73'),
            ('74',) + ugettext_tuple('74-81'),
            ('82',) + ugettext_tuple('82-89'),
            ('90',) + ugettext_tuple('90+'),   
        ]
        
    else:
        assert(0)
        
        
    if settings.BUILD_NAME == "friend_build":
        assert(constants.minimum_registration_age == 16)
        age_categories = [
            #('14',) + ugettext_tuple('14-15'),
            ('16',) + ugettext_tuple('16-17'),
        ] + age_categories
            
    age_search_categories = [dont_care_tuple,] + age_categories
    
    order_categories = [
        ('unique_last_login',) + ugettext_tuple(ugettext('Completed Profiles First')), 
        ('last_login_string',) + ugettext_tuple(ugettext('Recent Logins First')), ]    
    
    # signup_fields is an dictionary indicating the input fields that are available. 
    # If new input fields are added, then required must be set to false until it is guaranteed that the database 
    # has the required field -- otherwise any queries on an object that is missing the field will result in an
    # exception. This will become an issue once the server is running in production mode.
    
    # Note that the "label" is the information that appears for the field in the login/signup page
    # The "label" is the information taht appears beside the field in the search section. 
    if settings.BUILD_NAME == "language_build" or settings.BUILD_NAME == "friend_build":
        signup_country_label_tuple = ugettext_tuple(ugettext('I Am Currently In'))
    elif settings.BUILD_NAME == "swinger_build":
        signup_country_label_tuple = ugettext_tuple(ugettext('I / We Live In'))
    else:
        signup_country_label_tuple = ugettext_tuple(ugettext('I Live In'))

        

    if settings.BUILD_NAME == "lesbian_build":
        signup_preference_label_tuple = ugettext_tuple(ugettext('I Prefer'))
    elif settings.BUILD_NAME == "swinger_build":
        signup_preference_label_tuple = ugettext_tuple(ugettext('I / We Would Like To Meet'))
    else:
        signup_preference_label_tuple = ugettext_tuple(ugettext('I Would Like To Meet'))

        

    signup_email_address_label_tuple = ugettext_tuple(ugettext('Email Address (Confidential)'))
    signup_password_verify_label_tuple = ugettext_tuple(ugettext('Verify Password'))
    signup_password_label_tuple = ugettext_tuple(ugettext('Password'))
    signup_username_label_tuple = ugettext_tuple(ugettext('Username (Visible To Others)'))
    
    if settings.BUILD_NAME != "swinger_build":
        signup_sex_label_tuple = ugettext_tuple(ugettext('I Am'))
        signup_age_label_tuple = ugettext_tuple(ugettext('My Age'))
    else:
        signup_sex_label_tuple = ugettext_tuple(ugettext('I Am / We Are'))
        signup_age_label_tuple = ugettext_tuple(ugettext('My / Our Age (Average)'))


    signup_sub_region_label_tuple = ugettext_tuple(ugettext('Sub Region'))
    signup_region_label_tuple = ugettext_tuple(ugettext('Region'))
    
    if settings.BUILD_NAME == 'discrete_build' or settings.BUILD_NAME == 'gay_build':
        signup_relationship_status_label_tuple = ugettext_tuple(ugettext('My Relationship Status')) # this is the clients status
    elif settings.BUILD_NAME == 'swinger_build':
        signup_relationship_status_label_tuple = ugettext_tuple(ugettext('My / Our Relationship Status')) 
    elif settings.BUILD_NAME == 'single_build' or settings.BUILD_NAME == 'lesbian_build' or settings.BUILD_NAME == 'mature_build':
        signup_relationship_status_label_tuple = ugettext_tuple(ugettext('Type Of Relationship')) # this is the clients status
    elif settings.BUILD_NAME == 'language_build' :
        signup_language_to_learn_label_tuple = ugettext_tuple(ugettext('Language That I Want To Practice'))
        signup_native_language_label_tuple = ugettext_tuple(ugettext('My Native Language'))
    elif settings.BUILD_NAME == "friend_build":
        pass
    else:
        assert(False)
        
    
        
    common_signup_fields = {
        
        'country': 
        {'label':        signup_country_label_tuple,
         'choices':      None,          
         # note, locations_options is complicated, and so is computed 
         # in a seperate file
         'options':      localizations.country_options,
         # set choices to "None" so that the code that we call later, which 
         # generates options based on the data in 'choices' will not be called.
         'input_type':   u'select'},
                
        'region': 
        {'label':        signup_region_label_tuple,
         'choices':      None,
         'options':      [], # signup_fields_options_dict['region'] is assigned to localizations.location_dict below
         'input_type':   u'select',
         'required':     True},
        
        'sub_region': 
        {'label':        signup_sub_region_label_tuple,
         'choices':      None,
         'options':      [], # signup_fields_options_dict['sub_region'] is assigned to localizations.location_dict below
         'input_type':   u'select',
         'required':     True},
                
        'sex': 
        {'label':        signup_sex_label_tuple,
         'choices':      gender_categories,
          # 'options' lists are populated by the funcion called immediately after
          # this data structure declaration.
         'options':      [],
         'input_type':   u'select'},
        
        'age': 
        {'label':         signup_age_label_tuple, # this is the clients age
         'choices':       age_categories,
         'options':       [],
         'input_type':    u'select'},
            
        'username':
        {'label':        signup_username_label_tuple,
         'choices':      None,
         'options':      [],
         'input_type':   u'text',
         'max_length':   constants.MAX_USERNAME_LEN},
            
        'password':
        {'label':        signup_password_label_tuple,
         'choices':      None,
         'options':      [],
         'input_type':   u'password'},
                         
        'password_verify': 
        {'label':        signup_password_verify_label_tuple,
         'choices':      None,
         'options':      [],
         'input_type':   u'password'},
        
        'email_address': 
        {'label':        signup_email_address_label_tuple,
         'choices':      None,
         'options':      [],
         'input_type':   u'text'},
 
    }
    
    
    if settings.BUILD_NAME != 'language_build' and settings.BUILD_NAME != "friend_build":
        custom_signup_fields =  {            

            # At some point in the future, this could (possibly) be made into a checkbox, so as to allow
            # multiple preferences
            # to be defined.
            
            # The preference refers to the sex that other people would like to mee (ie. I am a man, so I want to
            # see profiles of people who have a preference for men)
            'preference': 
            {'label':        signup_preference_label_tuple,
             # Do not set this to "gender_search_categories" because having a don't care here will mean that
             # this user will not show up in any searches except for when the searcher doesn't care.
             'choices':      gender_preference_categories,
             'options':      [],
             'input_type':   u'select'},
            
            'relationship_status':
            {'label':        signup_relationship_status_label_tuple,
             'choices':      relationship_categories,
             'options':      [],
             'input_type': u'select'},
                
        }
    
    else:
        if settings.BUILD_NAME == 'language_build':
            custom_signup_fields = {
                
                'important_languages_list': 
                # This is a dummy data structure that allows us to generate the sorted options for the "important" part
                # of the languages list.
                {'label':        "This should never appear to the user - it is for internal use only",
                 'choices':      localizations.important_languages_list,
                 'start_sorting_index' : 0,
                 'options':      [],
                 'input_type':   u'select',
                 'required':     True},    
    
                'native_language': 
                {'label':        signup_native_language_label_tuple,
                 'choices':      localizations.languages_list,
                 'start_sorting_index' : 0,
                 'options':      [],
                 'input_type':   u'select'},
                
                'language_to_learn':
                {'label':        signup_language_to_learn_label_tuple,
                 'choices':      localizations.languages_list,
                 'start_sorting_index' : 0,
                 'options':      [],
                 'input_type': u'select'},
                    
            }    
        elif settings.BUILD_NAME == 'friend_build':
            custom_signup_fields = {
            }
    
        else:
            assert(0);
    
    # copy the common and custom signup fields
    signup_fields = {}
    signup_fields.update(custom_signup_fields)
    signup_fields.update(common_signup_fields)
    
    if settings.BUILD_NAME == 'friend_build':
        list_of_activity_categories = friend_bazaar_specific_code.get_list_of_activity_categories()
    
    signup_fields_options_dict = {}
    # populate the 'options' data structure inside each of the fields specified
    # in the signup_fields. Also (almost as a side effect), compute the 
    # signup_fields_options_dict, which will allow reverse lookups from the selector "key" to the
    # name that corresponds to the key in the current language.
    generate_option_line_based_on_data_struct(signup_fields, signup_fields_options_dict)
    # Note, country, region, and sub_region can all use the same dictionary, because of the encoding
    # we have used which is compatible for all locations levels. If it is a country the key will be "CO,,", if it
    # is a region, it will be "CO,RE," and sub-region "CO,RE,SR" (where CO means country code, RE is 
    # region code, and SR is sub-region code) - Notice that these can all be stored in the same dictionary without
    # conflicts.
    signup_fields_options_dict['country'] = localizations.location_dict
    signup_fields_options_dict['region'] = localizations.location_dict
    signup_fields_options_dict['sub_region'] = localizations.location_dict
        
    if settings.BUILD_NAME == "language_build":
        # copy the "important" languages to the top of the lists
        for lang_idx, language_tuple in enumerate(settings.LANGUAGES):
            signup_fields['language_to_learn']['options'][lang_idx] = signup_fields['important_languages_list']['options'][lang_idx] + \
                         [u'<option value="----">----\n', ] + \
                         signup_fields['language_to_learn']['options'][lang_idx]
            signup_fields['native_language']['options'][lang_idx] = signup_fields['important_languages_list']['options'][lang_idx] + \
                         [u'<option value="----">----\n', ] + \
                         signup_fields['native_language']['options'][lang_idx]    
           
            
    #### START SEARCH FIELDS DECLARATION HERE #############         
    
    # Search fields is a dictionary that is analogous to the signup_fields, but it allows for more flexibility in
    # terms of specifying the labels etc. 
    search_country_label_tuple = ugettext_tuple(ugettext('Country'))
    search_region_label_tuple = ugettext_tuple(ugettext('Region'))
    search_sub_region_label_tuple = ugettext_tuple(ugettext('Sub region'))
    search_sex_label_tuple = ugettext_tuple(ugettext('Sex'))
    search_age_label_tuple = ugettext_tuple(ugettext('Age')) # this is the age that the client is searching for
    search_query_order_label_tuple = ugettext_tuple(ugettext('Order'))       
    
    if settings.BUILD_NAME != 'language_build' and settings.BUILD_NAME != "friend_build":
        search_sex_label_tuple = ugettext_tuple(ugettext('I Would Like To See'))
        if settings.BUILD_NAME != 'lesbian_build':
            search_preference_label_tuple = ugettext_tuple(ugettext('That Are Interested In'))
        else:
            search_preference_label_tuple = ugettext_tuple(ugettext('That Prefer'))
        search_age_label_tuple = ugettext_tuple(ugettext('Their Age')) # this is the age that the client is searching for
        if settings.BUILD_NAME == 'discrete_build' or settings.BUILD_NAME == 'gay_build' or settings.BUILD_NAME == "swinger_build":
            search_relationship_status_label_tuple = ugettext_tuple(ugettext('Relationship Status')) # this is the clients status
        else: #single_build and lesbian_build
            search_relationship_status_label_tuple = ugettext_tuple(ugettext('Looking For')) # this is the type of relationship they want
            
        search_sex_label_num = "1."
        search_preference_label_num = "2."
        search_age_label_num = "3."
        search_country_label_num = "4a."
        search_region_label_num = "4b."
        search_sub_region_label_num = "4c."
        search_relationship_status_label_num = "5."
        search_query_order_label_num = "6."
        
            
    else: 
        if settings.BUILD_NAME == "language_build":
            search_language_to_learn_label_tuple = ugettext_tuple(ugettext('Language That I Want To Practice'))
            search_language_to_teach_label_tuple = ugettext_tuple(ugettext('In Exchange For (I Speak)'))
            search_sex_label_tuple = ugettext_tuple(ugettext('With People That Are'))
            search_age_label_tuple = ugettext_tuple(ugettext('Age')) # this is the age that the client is searching for
            search_query_order_label_tuple = ugettext_tuple(ugettext('Order'))
            
            search_language_to_learn_label_num = "1."
            search_language_to_teach_label_num = "2."
            search_sex_label_num = "3."
            search_country_label_num = "4a."
            search_region_label_num = "4b."
            search_sub_region_label_num = "4c."
            search_age_label_num = "5."
            search_query_order_label_num = "6."
            
        
        if settings.BUILD_NAME == "friend_build":
            
            # Note: the other friend_build labels are defined directly in friend_bazaar_specific_code.py 
            #       (I wanted to define them here, but this would require importing this file into friend_bazaar_specific_code
            #        which would create a circular dependency since we also have imported friend_bazaar_specific_code into this module)     
            
            #label_nums['for_sale'] = "1a."  # see friend_bazaar_specific_code.py for definition
            #label_nums['for_sale_sub_menu']  = "1b."  # see friend_bazaar_specific_code.py for definition
            search_sex_label_num = "2."           
            search_country_label_num = "3a."
            search_region_label_num = "3b."
            search_sub_region_label_num = "3c."
            search_age_label_num = "4."
            search_query_order_label_num = "5."
        
    common_search_fields = {
        # note "preference" refers to the sex of the current user, because this would be the prefernce that
        # other users are looking for when we are doing a search.

        'sex': 
        { 
            'label':        search_sex_label_tuple,
            'label_num':        search_sex_label_num,
            'choices':      gender_search_categories,
            'options':      [],
            'input_type':   u'select',
            # ordered_choices_tuples is used for getting a list of all of the choices, that will have the same
            # order as the "options" list, but without all the html that "options" has. This
            # will contain an array indexed by index, where each index will contain an array
            # of tuples that are ordered the same as the options list. 
            # I.e. ordered_choices_tuples[lang_idx][field_value_index]
            'ordered_choices_tuples': 'to be computed', 
            'required':     True
            },
        

        
        'country': 
        {
            'label':        search_country_label_tuple,
            'label_num':        search_country_label_num,
            'choices':      None,
            'options':      localizations.country_search_options,
            'input_type':   u'select',
            'ordered_choices_tuples': 'to be computed',
            'required':     True},
        
        
        'region':  # this is basically a place-holder that will be dynamically set (ajax call) based on the country
        {
            'label':        search_region_label_tuple,
            'label_num':        search_region_label_num,
            'choices':      None,
            'options':      [],
            'input_type':   u'select',
            'ordered_choices_tuples': 'to be computed', # this will be ignored since we will just pull location info directly from localizations data structs
            'required':     True},
           
        
        'sub_region': # this is basically a place-holder that will be dynamically set (ajax call) based on the region
        {
            'label':        search_sub_region_label_tuple,
            'label_num':        search_sub_region_label_num,
            'choices':      None,
            'options':      [],
            'input_type':   u'select',
            'ordered_choices_tuples': 'to be computed', # this will be ignored since we will just pull location info directly from localizations data structs
            'required':     True},
        
        
        'age': 
        {
            'label':        search_age_label_tuple, # this is the age that the client is searching for
            'label_num':        search_age_label_num, # this is the age that the client is searching for
            'choices':      age_search_categories,
            'options':      [],
            'input_type':   u'select',
            'ordered_choices_tuples': 'to be computed',
            'required':     True},  
        
        'query_order': 
        {
            'label':        search_query_order_label_tuple,
            'label_num':        search_query_order_label_num,
            'choices':      order_categories,
            'options':      [],
            'input_type':   u'select',
            'ordered_choices_tuples': 'to be computed',
            'required':     True},  
        
    }

    if settings.BUILD_NAME != 'language_build' and settings.BUILD_NAME != "friend_build":
        search_fields = {        
            'relationship_status':
            {
                'label':        search_relationship_status_label_tuple, 
                'label_num':        search_relationship_status_label_num, 
                'choices':      relationship_search_categories,
                'options':      [],
                'input_type':   u'select',
                'ordered_choices_tuples': 'to be computed',
                'required':     True},
               
            'preference': 
            {
                'label':        search_preference_label_tuple,
                'label_num':        search_preference_label_num,
                'choices':      preference_search_categories,
                'options':      [],
                'input_type':   u'select',
                'ordered_choices_tuples': 'to be computed',
                'required':     True},
        }
    else:
        
        if settings.BUILD_NAME == 'language_build':
            important_language_search_categories =  [('----',) + \
                            ugettext_tuple(ugettext("Any Language")),] + localizations.important_languages_list 
            language_search_categories = [('----',) + ugettext_tuple(ugettext("Any Language")),] + localizations.languages_list            

            search_fields = {       
                
                
                'important_languages_list': 
                # This is a dummy data structurethat allows us to generate the sorted options for the "important" part
                # of the languages list.
                {
                    'label':        "This label should never appear to the user - defined here for consistency only",
                    'choices':      important_language_search_categories,
                    'start_sorting_index' : 1, # first value is for all languages
                    'options':      [],
                    'input_type':   u'select',
                    'ordered_choices_tuples': 'to be computed',
                    'required':     True},                 
                
                'language_to_learn': 
                {
                    'label':        search_language_to_learn_label_tuple,
                    'label_num':    search_language_to_learn_label_num,
                    'choices':      language_search_categories,
                    'start_sorting_index' : 1, # first value is for all languages
                    'options':      [],
                    'input_type':   u'select',
                    'ordered_choices_tuples': 'to be computed',
                    'required':     True},     
                
                'language_to_teach': 
                {
                    'label':        search_language_to_teach_label_tuple, 
                    'label_num':    search_language_to_teach_label_num, 
                    'choices':      language_search_categories, 
                    'start_sorting_index' : 1,
                    'options':      [],
                    'input_type':   u'select',
                    'ordered_choices_tuples': 'to be computed',
                    'required':     True},    
            }
        
        if settings.BUILD_NAME == "friend_build":

            search_fields = {
            }            
            friend_bazaar_specific_code.update_friend_bazaar_data_fields_dict(search_fields)
        
    # copy the common search fields
    search_fields.update(common_search_fields)
    
    
    if settings.BUILD_NAME == "friend_build":
        # create a list of keys that has removed extra sub-menu keys for efficiency later on
        search_fields_expected_keys = friend_bazaar_specific_code.get_search_fields_expected_keys(search_fields)
    else:
        search_fields_expected_keys = search_fields.keys()
        
    
    # see comments in previous call to this function for more info.
    search_fields_options_dict = {}
    
    generate_option_line_based_on_data_struct(search_fields, search_fields_options_dict)
    search_fields_options_dict['country'] = localizations.location_dict
    search_fields_options_dict['region'] = localizations.location_dict
    search_fields_options_dict['sub_region'] = localizations.location_dict
    
    if settings.BUILD_NAME == "language_build":
        # copy the "important" languages to the top of the lists (these dropdowns are only available in language_build)
        for lang_idx, language_tuple in enumerate(settings.LANGUAGES):
            search_fields['language_to_learn']['options'][lang_idx] = search_fields['important_languages_list']['options'][lang_idx] + \
                         [u'<option value="----">----\n', ] + \
                         search_fields['language_to_learn']['options'][lang_idx]
            search_fields['language_to_teach']['options'][lang_idx] = search_fields['important_languages_list']['options'][lang_idx] + \
                         [u'<option value="----">----\n', ] + \
                         search_fields['language_to_teach']['options'][lang_idx]

