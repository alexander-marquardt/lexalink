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
import settings, error_reporting, logging, utils_top_level, constants

def get_pairs_in_current_langauge(tuple_list, lang_idx, do_sort = False):
    
    # accepts a list that contains tuples consisting of a key (in position 0) followed by the translation
    # of the key in the languages that are currently suppored, (in positions 1 through N). 
    #
    # Generates a list of 2-item tuples, consisting of the tuple key, and the value of the key in the 
    # selected language, and (if do_sort = True) sorted alphabetically in the current language.

    
    tmp_key_list = []
    tmp_value_list = []
    
    lang_idx_offset = 1


    for curr_tuple in tuple_list:
        tuple_key = curr_tuple[0]
        tuple_value_in_current_language = curr_tuple[lang_idx + lang_idx_offset]
        tmp_key_list.append(tuple_key)
        tmp_value_list.append(tuple_value_in_current_language)
        
            
    list_of_tuples_in_current_language = zip(tmp_key_list, tmp_value_list)
        
    # sort the list of tuples so that it is alphabetical in the current language
    # always sort on location 1, which contains the word in the current language, as opposed to 
    # location 0 which contains the key.
    if do_sort:
        list_of_tuples_in_current_language.sort(key=lambda x: x[1])
    

    del tmp_key_list
    del tmp_value_list
    
    return (list_of_tuples_in_current_language)
    

#def transpose_checkbox_rows_into_columns(list_of_sorted_pairs):
    #""" 
    #This function receives a list of checkbox input choices, and orders them so that they will 
    #displayed vertically instead of horizontally when written out into a table.
    
    #Input is a 1-D list containing [A B C D E F G H I J ] which would normally be displayed
    #as: 
    #[ A B C D ]
    #[ E F G H ]
    #[ I J     ]
    
    #And this function will re-order the list to be [A D G J B E H C F I] which will be displayed
    #as (notice how data is now sorted in columns instead of horizontally):
    #[ A D G J]
    #[ B E H  ]
    #[ C F I  ]
    
    #"""
    
    #try:
        #import math
        
        #cols_per_row = constants.CHECKBOX_INPUT_COLS_PER_ROW
        
        #list_len = len(list_of_sorted_pairs)
        #idx = 0; row = 0; 
        #num_rows = int(math.ceil(float(list_len)/cols_per_row))
        #matrix_size = num_rows * cols_per_row
        #matrix_representation = []
        
        #"""
        #First, we pull out sections of the list that correspond to the height of the final matrix - 
        #for example, we will pull out sub-lists [A B C], [D E F], [G H I], [J,,] from the input list.
        #Notice that the length of each of these sub-lists is num_rows. The resulting (temporary) matrix
        #looks like the following:
        #[A B C]
        #[D E F]
        #[G H I]
        #[J    ]
        
        #Notice that the first colum corresponds to the first row of the desired matrix. 
        #"""
        #start_idx = 0
        #end_idx = num_rows         
        #while start_idx <= matrix_size - 1:
            #row_list = [None,]*num_rows  # we use this to pad the list with None in case it is not totally filled
            #row_ix = 0
            #for ix in range(start_idx, end_idx): 
                #if ix <= list_len-1:
                    #row_list[row_ix] = list_of_sorted_pairs[ix]
                    #row_ix += 1
                    
            #matrix_representation.append(row_list)
            #start_idx += num_rows
            #end_idx += num_rows
             
        ## Now, loop over the matrix, and pull out the values, column by column and copy them into new_array.  
        #column = 0
        #new_array = []
        #while column < num_rows:
            #for sub_list in matrix_representation:
                #new_array.append(sub_list[column])
            #column += 1
    
        #return new_array    

    #except:
        #error_reporting.log_exception(logging.critical)
        #return []

def generate_option_line_based_on_data_struct(fields_data_struct, options_dict):
    # has two main purposes. 
    # 1) Fills in fields_data_struct[field]['options'] with an 
    # array of strings that can be directly output inside a select dropdown/checkbox statement.
    # 2) Also, returns an "options_dict". options_dict will hold a 
    # dictionary of values for each field, in which
    # the principle key specifies the field, second field the language, and the third key specifies the
    # selection, and the output specifies the selection in the correct language.
    # ie. options_dict[smoker][english_code][prefere_no_say] = "Non Smoker". This is needed
    # for printing user settings in the user_main page.
    # - radio_or_checkbox - valid values are "radio" or "checkbox" -- allows same code to be used for both
    
    # convert all of the above lists into language-appropriate options for use in drop-down menus
    try:
        for (field, field_dict) in fields_data_struct.items():
                    
            options_dict[field]=[]
            options = []
            ordered_choices_tuples = []
            choices_tuple_list = field_dict['choices']
            input_type = field_dict['input_type']    
            
            
            for lang_idx, language_tuple in enumerate(settings.LANGUAGES):

                options.append([]) # append sub-array for current language
                
                if choices_tuple_list != None:
                    
                    ordered_choices_tuples.append([]) # append sub-array for current language
                    
                    if 'start_sorting_index' in field_dict:
                        # some part of this list should be sorted, starting after the "start_sorting_index" location in the list
                        where_to_start_sort = field_dict['start_sorting_index']
                        first_unsorted_part = \
                                      get_pairs_in_current_langauge(choices_tuple_list[:where_to_start_sort], lang_idx, do_sort = False)
                        
                        if 'stop_sorting_index' in field_dict:
                            # Leave some part of this list un-sorted
                            where_to_stop_sort = field_dict['stop_sorting_index']
                        else: 
                            # sort to the end of the list
                            where_to_stop_sort = len(choices_tuple_list)
                            
                        part_to_sort = choices_tuple_list[where_to_start_sort:where_to_stop_sort]
                        last_part_to_leave_unsorted = choices_tuple_list[where_to_stop_sort:]
                            
                        sorted_part = \
                                    get_pairs_in_current_langauge(part_to_sort, lang_idx, do_sort = True)
                        last_unsorted_part = \
                                    get_pairs_in_current_langauge(last_part_to_leave_unsorted, lang_idx, do_sort = False)       
                        list_of_sorted_pairs = first_unsorted_part + sorted_part + last_unsorted_part
                    else:
                        list_of_sorted_pairs = get_pairs_in_current_langauge(choices_tuple_list, lang_idx, do_sort = False)
                        
                        
                    #if input_type == u'checkbox':
                        #list_of_sorted_pairs = transpose_checkbox_rows_into_columns(list_of_sorted_pairs)
                        
                    ordered_choices_tuples[lang_idx] = list(list_of_sorted_pairs) # copy the list
    
                    options_dict[field].append({})
                    for choices_tuple in list_of_sorted_pairs:
                        
                        
                        # make sure the tuple is set to a valid value - due to re-ordering for checkbox display, some tuples
                        # migh be None, which will will interpret to mean that no value should be displayed. 
                        # Note, this only could happen if we enable the code to sort checkboxes by column instead of by row. 
                        if not choices_tuple:
                            assert(input_type == u'checkbox')
                            options[lang_idx].append(u'')
                        else:
                            choice_key = choices_tuple[0]
                            option_in_current_language = choices_tuple[1]
        
                            options_dict[field][lang_idx][choice_key] = option_in_current_language
                            
                            if input_type == u'select':
                                options[lang_idx].append(smart_unicode("<option value='%s'>%s\n" % (choice_key, option_in_current_language)))
                            elif input_type == u'checkbox' or input_type == u'radio':
                                options[lang_idx].append(smart_unicode("<input type = '%s' name='%s' id='id-edit-%s-%s' value='%s'> %s\n" % 
                                                            (input_type, field, field, choice_key, choice_key, option_in_current_language)))
                            else:
                                raise Exception("Unknown input type %s encountered" % input_type) 
                        
                    # This is located inside "if choices_tuple_list != None:" so that we don't need special
                    # checks for country, region, sub_region .... they never have choices defined in this data structure
                    fields_data_struct[field]['ordered_choices_tuples'] = ordered_choices_tuples

                if field != 'country':  
                    # note: country is filled in before getting into this function, and should not be over-written
                    # this was done in the populate_country_options function (located in localizations.py at the time
                    # this comment was written). Also, note tht regions and sub_regions never appeared in the signup
                    # fields and so do not have to be explicity excluded here.
                    fields_data_struct[field]['options'] = options
                
    except:
        error_reporting.log_exception(logging.critical)