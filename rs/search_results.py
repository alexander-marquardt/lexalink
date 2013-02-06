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

""" This module is responsible for generating the results of user searches. 
It will generate HTML based on the criteria specified in the user-search parameters. """
import datetime, logging

from django.core.urlresolvers import reverse
from django.utils.encoding import smart_unicode
from django import http

from google.appengine.ext import ndb
from google.appengine.datastore.datastore_query import Cursor


from google.appengine.api import memcache

from rs.utils import *
from rs.forms import FormUtils
from rs import forms
from rs.models import UserModel
from rs.user_profile_main_data import UserSpec
from rs.user_profile_details import UserProfileDetails
from rs.constants import ABOUT_USER_SEARCH_DISPLAY_DESCRIPTION_LEN
from rs.localizations import *
from rs import display_profiles_summary
import store_data, utils, error_reporting
import rendering, text_fields, utils_top_level, vip_status_support
import profile_utils
from rs.import_search_engine_overrides import *

from django.utils.translation import ugettext


if settings.BUILD_NAME == "Friend":
    import friend_bazaar_specific_code

PAGESIZE = 6


#####################################
def setup_and_run_search_by_name_query(search_vals_dict, num_results_needed, paging_cursor):
    # gets the results for the current search-by-name query
      
    try:
        q = UserModel.query().order(-UserModel.last_login_string)
        
        q = q.filter(UserModel.is_real_user == True)
        q = q.filter(UserModel.user_is_marked_for_elimination == False)
        q = q.filter(UserModel.username_combinations_list == search_vals_dict['search_by_name'])
            
        if paging_cursor:
            (query_results_keys, new_cursor, more_results) = q.fetch_page(num_results_needed, start_cursor = paging_cursor, keys_only = True)
        else:
            (query_results_keys, new_cursor, more_results) = q.fetch_page(num_results_needed, keys_only = True)
        return (query_results_keys, new_cursor, more_results)
            
    except:
        error_reporting.log_exception(logging.error, error_message = 'Search query exception.')
        query_results_keys = []
        return (query_results_keys, None, False)
               



def setup_and_run_user_search_query(search_vals_dict, num_results_needed):
    """
    Purpose:
      - Sets up the query filters based on the parameters passed in. 
      - Executes the query and returns the results.
      - Note: we do a "keys only" query so that we can effectively cache the summary of each user profile as opposed
        to re-generating it every time the code is called.
    Args:
      - search_vals_dict: a dictionary containing all the values that can (and must) appear in a search.
      - search_order can be unique_last_login or last_login_string - this determines how the results will be ordered.
    Returns: 
      - Returns a list of keys that correspond to the user profiles that correspond to the search query.
    """
    
    try:
        q = UserModel.query().order(-UserModel._properties[search_vals_dict['query_order']])
        
        # the following sequence selects the location query based on the tightest 
        # (most specific) region. I.e. if the client specifies a sub-region, then
        # that is the query that will be done.  However, if the client specified 
        # a country, but did not specify any more specific search criteria, then
        # the entire country will be searched. 
        q = q.filter(UserModel.sub_region_ix_list == search_vals_dict['sub_region'])
        q = q.filter(UserModel.region_ix_list ==  search_vals_dict['region'])
        q = q.filter(UserModel.country_ix_list == search_vals_dict['country'])
        
        # if a value is set to don't care, then it will not be added to the filter dictionary, and 
        # will therefore have no effect on the query. If it is not set to don't care, it is added and 
        # the query will respect the constraint.
        q = q.filter(UserModel.sex_ix_list ==  search_vals_dict['sex'])
            
        # We set the "sex" of the current user to dont care in order to amplify the query matches.
        # 
        # --TODO: MIGHT HAVE TO DO A QUERY ON A "LIST" TO MAKE THIS WORK PROPERLY -- could allow users 
        # to select preference from a checkbox as opposed to dropdown, therefore allowing them
        # multiple values.

            
        if settings.BUILD_NAME == "Language": # setup Language
            # Note: the language_to_teach and language_to_learn are reversed. Eg. I want to learn
            # spanish (my language_to_learn = Spanish) therefore, I want to see people whose 
            # languages list contains at least Spanish.             
            # this is a query on the "languages" list to see if *any* of the values match
            q = q.filter(UserModel.languages == search_vals_dict['language_to_learn'])
            q = q.filter(UserModel.languages_to_learn == search_vals_dict['language_to_teach'])
            
        elif settings.BUILD_NAME == "Friend": # Setup Friend
            
            q = q.filter(UserModel.friend_price_ix_list == search_vals_dict['friend_price'])
            
            # we do not yet pass in the currency as a search value - therefore default it to "----"
            q = q.filter(UserModel.friend_currency_ix_list == "----")

            #for menu_name in ['for_sale', 'to_buy']:
            menu_name = "for_sale"
            if search_vals_dict['%s_sub_menu' % menu_name] != "----":
                # if the sub-menu is passed in, then try to to match the value in the sub-menu, otherwise try to match the
                # category.
                q = q.filter(UserModel._properties['%s_ix_list' % menu_name] == search_vals_dict['%s_sub_menu' % menu_name])
            elif search_vals_dict[menu_name] != "----":
                # Note: this is a very special case - if no value is passed in for the "for_sale" parameter,
                # then we completely exclude it from the search - this can only be done because the composite index 
                # for this value is completely separate from the other index values, and therefore leaving it out
                # of the query completely will result in a more efficient lookup. 
                q = q.filter(UserModel._properties['%s_ix_list' % menu_name] == search_vals_dict['%s' % menu_name])
                

                        
        else: # setup for "dating" websites
            q = q.filter(UserModel.preference_ix_list == search_vals_dict['preference'])
            q = q.filter(UserModel.relationship_status_ix_list == search_vals_dict['relationship_status'])
        
        q = q.filter(UserModel.age_ix_list ==  search_vals_dict['age'])
            
        q = q.filter(UserModel.is_real_user == True)
        q = q.filter(UserModel.user_is_marked_for_elimination == False)
    
        # DO NOT REMOVE BOOKMARKS - to replace with cursors - search engines can come back to a page 
        # that is indexed by a bookmark, but cannot load a page that requires a cursor.
        if search_vals_dict['bookmark']:
            q = q.filter(UserModel._properties[search_vals_dict['query_order']] <=  search_vals_dict['bookmark'])
        
        query_results_keys = q.fetch(num_results_needed, keys_only = True)
            
    except:
        error_reporting.log_exception(logging.error, error_message = 'Search query exception.')
        query_results_keys = []
        
    return (query_results_keys)
      
 

def generate_title_for_current_search(search_vals_dict, lang_idx, extended_results):
    # given the userobject that is passed in, generate a text string that is appropriate for display
    # in the title of the webpage. 
    generated_title = ''
    start_title = ''; location_title = '';  relationship_status_title = ''; age_title = ''; query_order_title = '';
    
    try:        
        
        (curr_lang_dict) = utils.get_fields_in_current_language(search_vals_dict, lang_idx, pluralize_sex = True, search_or_profile_fields = "search")
        
        if settings.BUILD_NAME != "Language" and settings.BUILD_NAME != 'Friend':
            if curr_lang_dict['sex'] != "----":
                sex_title = u"%s" % ugettext("generated_search_title %(sex)s") % {'sex': curr_lang_dict['sex']}
            else:
                if settings.BUILD_NAME != "Lesbian":
                    sex_title = u"%s" % ugettext("All people (feminine)")
                else:
                    sex_title = u"%s" % ugettext("All lesbian types")

            if curr_lang_dict['preference'] != "----":
                preference_title = u" %s" % ugettext("generated_search_title %(preference)s") % {'preference': curr_lang_dict['preference']}
            else:
                preference_title = u''
                
            get_additional_description = utils_top_level.get_additional_description_from_sex_and_preference(search_vals_dict['sex'], search_vals_dict['preference'], pluralize = True)
                
            start_title = u"%s%s%s. " % (sex_title, preference_title, get_additional_description)
        else: 
            if settings.BUILD_NAME == "Language":
                if curr_lang_dict['language_to_learn'] != "----":
                    languages_to_learn_title = u"%s" % ugettext("generated_search_title %(language_to_learn)s") % {
                        'language_to_learn': curr_lang_dict['language_to_learn']}
                else:
                    languages_to_learn_title = u"%s" % ugettext("All people (feminine)")            
                
                if curr_lang_dict['language_to_teach'] != "----":
                    language_title = u"%s" % ugettext("generated_search_title %(language_to_teach)s") % {'language_to_teach': curr_lang_dict['language_to_teach']}
                    start_title = u"%s %s. " % (languages_to_learn_title, language_title)
                else:
                    start_title = u"%s. " % (languages_to_learn_title)
    
                if curr_lang_dict['sex'] != "----":
                    sex_title = u'%s. ' % ugettext("Sex: %(sex)s") % {'sex': curr_lang_dict['sex']}
                else:
                    sex_title = u''
                    
            elif settings.BUILD_NAME == 'Friend':
                if curr_lang_dict['sex'] != "----":
                    sex_title = u"%s" % ugettext("generated_search_title %(sex)s") % {'sex': curr_lang_dict['sex']}
                else:
                    sex_title = u"%s" % ugettext("All people (feminine)")    
                
                if curr_lang_dict['for_sale_sub_menu'] != "----":
                    interested_in_title = u" %s." % ugettext("interested in %(for_sale_sub_menu)s") % {
                        'for_sale_sub_menu' : curr_lang_dict['for_sale_sub_menu']}
                elif curr_lang_dict['for_sale'] != "----":
                    interested_in_title = u" %s." % ugettext("interested in %(for_sale)s") % {'for_sale' : curr_lang_dict['for_sale']}
                else:
                    interested_in_title = '.'
                
                if curr_lang_dict['friend_price']  != "----":
                    if curr_lang_dict['friend_currency']  != "----":
                        available_for_price_title = u" %s." % ugettext("Price: %(friend_price)s. Currency: %(friend_currency)s") % {
                            'friend_price' : curr_lang_dict['friend_price'],
                            'friend_currency' : curr_lang_dict['friend_currency']}
                    else:
                        available_for_price_title = u" %s." % ugettext("Price: %(friend_price)s") % {
                            'friend_price' : curr_lang_dict['friend_price']}    
                else:
                    available_for_price_title = ''
                    
                start_title = u"%s%s%s " % (sex_title, interested_in_title, available_for_price_title)
            else:
                assert(0)
                
                
                
        if curr_lang_dict['location'] != "----":
            location_title = u"%s. " % ugettext("generated_search_title %(location)s") % {'location': curr_lang_dict['location']}
        else:
            location_title = u"%s. " % ugettext("In: The entire world")
            
        if curr_lang_dict['age'] != "----" and extended_results:
            age_title = u"%s. " % ugettext("generated_search_title %(age)s") % {'age' : curr_lang_dict['age']}
            
        # query order should always exist
        if extended_results:
            query_order_txt = user_profile_main_data.UserSpec.search_fields_options_dict["query_order"][lang_idx][search_vals_dict['query_order']]
            query_order_title = u"%s: %s. " % (ugettext("Ordered by"), query_order_txt)

        if settings.BUILD_NAME == "Discrete" or settings.BUILD_NAME == "Gay"  or settings.BUILD_NAME == "Swinger":
            if curr_lang_dict['relationship_status'] != "----":
                relationship_status_title += u"%s. " % ugettext("Status generated_search_title %(relationship_status)s") % {
                    'relationship_status': curr_lang_dict['relationship_status']}
        if settings.BUILD_NAME == "Single" or settings.BUILD_NAME == "Lesbian":
            if curr_lang_dict['relationship_status'] != "----":
                relationship_status_title += u"%s. " % ugettext("For generated_search_title %(relationship_status)s") % {
                    'relationship_status': curr_lang_dict['relationship_status']}
            
        if settings.BUILD_NAME != "Language" and settings.BUILD_NAME != "Friend":
            generated_title = u"%s%s%s%s%s" % (start_title, location_title, relationship_status_title, age_title, query_order_title)
        else:
            if settings.BUILD_NAME == "Language":
                generated_title = u"%s%s%s%s%s%s" % (start_title, location_title, relationship_status_title, sex_title, age_title, query_order_title)
            elif settings.BUILD_NAME == "Friend":
                generated_title = "%s%s%s%s" % (start_title, age_title, location_title, query_order_title)
    
    except:
        error_reporting.log_exception(logging.critical)       
        return '' 
    
    return generated_title


def loosen_search_criteria(search_vals_dict):
    
    break_out_of_loop = False
    
    
    if settings.BUILD_NAME != "Language" and settings.BUILD_NAME != "Friend":
        if search_vals_dict['relationship_status'] != '----' or search_vals_dict['age'] != '----' or \
           search_vals_dict['sub_region'] != '----' or search_vals_dict['preference'] != '----':
            # Temporarly change a group of search parameters -- this should be acceptable since
            # we are loosening the parameters in a somewhat arbitrary order anyway.
            if search_vals_dict['relationship_status'] != '----':
                search_vals_dict['relationship_status'] = '----'
            if search_vals_dict['age'] != '----':
                search_vals_dict['age'] = '----'
            if search_vals_dict['sub_region'] != '----':
                search_vals_dict['sub_region'] = '----'
            if search_vals_dict['preference'] != '----':
                search_vals_dict['preference'] = '----'

        elif search_vals_dict['region'] != '----':
            search_vals_dict['region'] = '----'
        elif search_vals_dict['country'] != '----':
            search_vals_dict['country'] = '----' 
        elif search_vals_dict['sex'] != '----':
            search_vals_dict['sex'] = '----'
        else:    
            # we have already loosened all search criteria -- nothing left to show
            break_out_of_loop = True
    elif settings.BUILD_NAME == "Language":
        if search_vals_dict['age'] != '----' or search_vals_dict['sub_region'] != '----' \
           or search_vals_dict['region'] != '----' or search_vals_dict['country'] != '----':
            # Temporarly change a group of search parameters -- this should be acceptable since
            # we are loosening the parameters in a somewhat arbitrary order anyway.
            search_vals_dict['age'] = '----'
            search_vals_dict['sub_region'] = '----'
            search_vals_dict['region'] = '----'
            search_vals_dict['country'] = '----' 
            
        elif search_vals_dict['sex'] != '----':
            search_vals_dict['sex'] = '----'
        elif search_vals_dict['language_to_teach'] != '----':
            search_vals_dict['language_to_teach'] = '----' #refers to the language spoken by other people
        elif search_vals_dict['language_to_learn'] != '----':
            search_vals_dict['language_to_learn'] = '----' # referes to the language that other people want to learn
        else:    
            # we have already loosened all search criteria -- nothing left to show
            break_out_of_loop = True
        
    elif settings.BUILD_NAME == "Friend":
        if search_vals_dict['friend_price'] != '----' or search_vals_dict['friend_currency'] != '----':
            search_vals_dict['friend_price'] = '----'                        
            search_vals_dict['friend_currency'] = '----'  
        elif search_vals_dict['age'] != '----' or search_vals_dict['sex'] != '----':
            search_vals_dict['sex'] = '----'                        
            search_vals_dict['age'] = '----'    
        elif search_vals_dict['for_sale_sub_menu'] != '----' or search_vals_dict['for_sale'] != '----':
            search_vals_dict['for_sale_sub_menu'] = '----'
            search_vals_dict['for_sale'] = '----'
        elif  search_vals_dict['sub_region'] != '----' \
           or search_vals_dict['region'] != '----' or search_vals_dict['country'] != '----':
            # Temporarly change a group of search parameters -- this should be acceptable since
            # we are loosening the parameters in a somewhat arbitrary order anyway.
            search_vals_dict['sub_region'] = '----'
            search_vals_dict['region'] = '----'
            search_vals_dict['country'] = '----' 
        else:    
            # we have already loosened all search criteria -- nothing left to show
            break_out_of_loop = True
        
    else: # should never enter this branch
        assert(0)
        
    return break_out_of_loop
                    

#####################################
def generate_search_results(request, type_of_search = "normal"):
    # Code that is responsible for the main part of generating search results. This includes code 
    # for keeping track of bookmarks (required in order to remember which page of search resluts 
    # we are showing), for keeping track of the number of results returned from queries, for
    # loosening search criteria if query doesn't have enough or any more results.
    #
    # type_of_search "normal" or "by_name"

    
    try:       
        generated_html_hidden_variables = ''
        generated_html_top_next_button = ''
        generated_html_bottom_next_button = ''
        
        viewer_userobject =  utils_top_level.get_userobject_from_request(request)
        viewer_uid = utils_top_level.get_uid_from_request(request)
        display_online_status = False
        if viewer_userobject:
            display_online_status = utils.do_display_online_status(viewer_uid)
    
        search_vals_dict = {}
        
        lang_idx = localizations.input_field_lang_idx[request.LANGUAGE_CODE]
        lang_idx_offset = lang_idx + 1
        
        if type_of_search == "normal":
            for search_field in UserSpec.search_fields_expected_keys:
                # we use UserSpec.search_fields as a build-independent list of fields that need to be passed in for each build
                search_vals_dict[search_field] = request.GET.get(search_field,'----')
                
                # The following will catch "dont_care" values that might be passed in (we used use "dont_care" instead of "----")
                # If this is passed in, do a re-direct. Written Sept 17 2011. At some point in the future, this can be removed (once
                # the internet/bookmarks/search engines do not contain "dont_care" values)
                if search_vals_dict[search_field] == "dont_care":
                    return permanent_search_query_redirect(request)
                
                if settings.BUILD_NAME == "Swinger":
                    if search_vals_dict[search_field] == "gay_couple" or search_vals_dict[search_field] == "lesbian_couple":
                        return permanent_search_query_redirect(request)               
                    
                
            if search_vals_dict['query_order'] == "----":
                # I don't think "----" should ever be passed in, but I will leave this code here for now... 
                search_vals_dict['query_order'] = 'last_login_string'

                
            # the following fields are written as hidden data so that the JS can quickly pull the values out and immediately
            # display them, without requiring an additional ajax request. This will be used for setting the dropdown menus to
            # the most recent query values
            search_vals_dict['available_in_html'] = 'Yes' # read by JS to check that passed in search values are written into hidden fields.
            for (search_var, search_val) in search_vals_dict.iteritems():
                generated_html_hidden_variables += \
                    u'<input type=hidden id="id-passed_in_search-%(search_var)s" name="passed_in_search-%(search_var)s" \
                    value="%(search_val)s">\n' % {'search_var': search_var, 'search_val': search_val}            
            del search_vals_dict['available_in_html']
            
            generated_title = generate_title_for_current_search(search_vals_dict, lang_idx, extended_results = False)
            
            if settings.SEO_OVERRIDES_ENABLED:
                generated_meta_description = u"%s. %s" % (search_engine_overrides.get_main_page_meta_description_common_part(), generated_title)
            else:
                generated_meta_description = u''
                
            generated_header = generate_title_for_current_search(search_vals_dict, lang_idx, extended_results = True)
            
            if settings.SEO_OVERRIDES_ENABLED:
                refined_links_html = search_engine_overrides.generate_refine_search_links_for_current_search(search_vals_dict, request.LANGUAGE_CODE)
            else:
                refined_links_html = ''

            # show the rest of the search results
            post_action = "/%s/search/" % (request.LANGUAGE_CODE)
            
                
        elif type_of_search == "by_name":
            search_vals_dict["search_by_name"] = request.GET.get("search_by_name",'').upper()
            generated_header = "%s" % search_vals_dict["search_by_name"]
            generated_title = generated_header
            generated_meta_description = u''
            refined_links_html = ''
            post_action = "/%s/search_by_name/" % (request.LANGUAGE_CODE)
            
        else:
            assert(0)


        header_html = "%s: %s" % (ugettext("Showing results for"), generated_header)
        generated_html_top = display_profiles_summary.generate_summary_html_top(header_html)
        generated_html_open_form = display_profiles_summary.generate_summary_html_open_form(post_action)
        generated_html_body =  u'<div class="cl-clear"></div>\n'
        
       
        search_vals_dict['bookmark'] = request.GET.get('bookmark','')
        # If a bookmark is  passed in, then don't store the search (preferences), because it should have been stored when the original
        # search was done.
        if type_of_search == "normal" and viewer_userobject and not search_vals_dict['bookmark']:            
            # store the search preferences for the user.
            store_data.store_search_preferences(request)        
        
        print_remainder_of_results_from_previous_page = True
        
        query_results_keys = []
        len_query_results_currently_stored = 0
        if type_of_search == "normal":
            # Need a total (minimum) of PAGESIZE+1 results in order to be able to display a "next results" button
            # If we can't get PAGESIZE+1 results (after loosening search criteria to the maximum along the way)
            # then the current page is the last results page that can be displayed.
            # Get the results from the query
            query_size = PAGESIZE + 1
        elif type_of_search == "by_name":
            # We use cursors for by_name searches, and cursors automatically index the first value *following* 
            # the values that have been returned. So, we just get PAGESIZE number of results
            query_size = PAGESIZE
            paging_cursor = None
        else:
            assert(0)
            
        
        while len_query_results_currently_stored < query_size:
            # loop which progressively loosens search criteria, so that initial results
            # returned to the user correspond to their criteria, but after those results are
            # exhausted, more, broader search results will be returned .

            if type_of_search == "normal":

                num_results_needed = query_size - len_query_results_currently_stored
                (new_query_results_keys) = setup_and_run_user_search_query(search_vals_dict, num_results_needed)
            
            elif type_of_search == "by_name":
                num_results_needed = query_size - len_query_results_currently_stored
                start_cursor = Cursor(urlsafe=search_vals_dict['bookmark'])
                (new_query_results_keys, paging_cursor, more_results) = setup_and_run_search_by_name_query(search_vals_dict, num_results_needed, start_cursor)
            
            else:
                assert(0)
    
            # count of the number of results returned
            len_new_query_results = len(new_query_results_keys)
    
            if len_new_query_results == 0:
                # no results found, we will fall-through to the "loosen_search_criteria" call or exit the loop
                # if no loosening can be done. In both cases, the bookmark must be cleared. 
                search_vals_dict['bookmark'] = ""
                
            elif  0 < len_new_query_results < num_results_needed:
                # the current query was not able to get enough results to satisfy the current query, we 
                # generate results for the results that were returned. 
                generated_html_body +=  display_profiles_summary.generate_html_for_list_of_profiles(request, viewer_userobject, new_query_results_keys, display_online_status)  
                len_query_results_currently_stored += len_new_query_results
                search_vals_dict['bookmark'] = ""
                
            else: 
                # there will be another page of results to return.
                if type_of_search == "normal":
                    # by construction, we are guaranteed that len_new_query_results >= num_results_needed.
                    # can remove this assert in the future. 
                    assert(len_new_query_results >= num_results_needed)
                    generated_html_body += display_profiles_summary.generate_html_for_list_of_profiles(request, viewer_userobject, new_query_results_keys[:-1], display_online_status)  
                    last_userobject = utils_top_level.get_object_from_string(new_query_results_keys[-1].urlsafe())
                    # get the value of last_login_string, or unique_last_login (or in the future other criteria)
                    # that is stored on the "last_userobject"
                    search_vals_dict['bookmark'] = getattr(last_userobject, search_vals_dict['query_order'])
                elif type_of_search == "by_name":
                    # cursors are used for this search, and we did not generate an extra tail value as a bookmark
                    # therefore, we pass in the entire list of keys without chopping off the last value.
                    generated_html_body += display_profiles_summary.generate_html_for_list_of_profiles(request, viewer_userobject, new_query_results_keys, display_online_status) 
                    assert(paging_cursor)
                    if more_results:
                        search_vals_dict['bookmark'] = paging_cursor.urlsafe()
                    else: 
                        search_vals_dict['bookmark'] = ""
                break
    
            if len_new_query_results < num_results_needed:
                # With the current query parameters, no more results were found. 
                
                if type_of_search == "normal":
                    break_out_of_loop = loosen_search_criteria(search_vals_dict)
                    if break_out_of_loop:
                        break
                elif type_of_search == "by_name":
                    # there are no search critera - so we cannot loosen the search. 
                    break
                else:
                    assert(0)
                    
          
                generated_html_body += u'<div class="grid_9 alpha omega cl-divider-line" ></div>'
                generated_html_body += u'<div class="grid_9 alpha omega" ><br><br><br></div>'     
                generated_html_body += u'<div class="grid_9 alpha omega cl-color-text">\n' 
                generated_html_body += u'<strong>%s</strong><br><br>' % text_fields.loosening_search_criteria
                generated_html_body += forms.print_current_search_settings(search_vals_dict, lang_idx)
                generated_html_body += u'<br><br><br></div> <!-- end grid9 -->\n'
    

        if search_vals_dict['bookmark']:
            
            # we only show the "next" buttons if there is a bookmark passed in - this indicates that there are 
            # more values that need to be displayed that did not fit on the current page.
            
            # The following loop prints out the search variables *after* all loosening criteria has been applied. This will also print
            # out the bookmark that will be used when retrieving the "next" page.
            for (search_var, search_val) in search_vals_dict.iteritems():
                generated_html_hidden_variables += \
                    u'<input type=hidden id="id-%(search_var)s" name="%(search_var)s" \
                    value="%(search_val)s">\n' % {'search_var': search_var, 'search_val': search_val}      
            

            (generated_html_top_next_button, generated_html_bottom_next_button) = display_profiles_summary.generate_next_button_html()
            
            
            
        generated_html_close_form = display_profiles_summary.generate_summary_html_close_form()
    
            
        generated_html =  generated_html_top + generated_html_open_form + generated_html_hidden_variables + \
        generated_html_top_next_button + generated_html_body + generated_html_bottom_next_button + generated_html_close_form
        
        return rendering.render_main_html(request, generated_html, viewer_userobject, page_title = generated_title, 
                                          refined_links_html = refined_links_html, show_social_buttons = True,
                                          page_meta_description = generated_meta_description)

    except:
        error_reporting.log_exception(logging.critical)
        return http_utils.redirect_to_url(request, "/%s/" % request.LANGUAGE_CODE)
        
dont_care_pattern = re.compile(r'.*dont_care.*') 
dashes_pattern = re.compile(r'.*----.*')
gay_couple_pattern = re.compile(r'.*gay_couple.*')
lesbian_couple_pattern = re.compile(r'.*lesbian_couple.*')

def permanent_search_query_redirect(request):
    # This function is responsible for re-directing old URL calls to "generate_search_results" to the new URL that 
    # just contains "search" instead. Additionally, any part of the URL that contains "dont_care" will be totally removed
    # Re-maps the  rs/generate_search_results/... to /search/... 
    
    host = request.get_host()
    path = request.path_info
    query_string = ''
    if request.META.get("QUERY_STRING", ""):
        query_string = request.META['QUERY_STRING']
        
    path = path.replace("/rs", "")
    path = path.replace("generate_search_results", "search")
    
    remaining_get_fields = []
    # completely remove any "dont_care" values from the get (query) string
    for field_declaration in query_string.split("&"):
        if not dont_care_pattern.match(field_declaration) and not dashes_pattern.match(field_declaration) and \
           not gay_couple_pattern.match(field_declaration) and not lesbian_couple_pattern.match(field_declaration):
            remaining_get_fields.append(field_declaration)
    
    query_string = "&".join(remaining_get_fields)
    redirect = "http://%s%s?%s" % (host, path, query_string)
     
    logging.warning("Redirecting from URL %s to %s" % (request.build_absolute_uri(), redirect))
    return http.HttpResponsePermanentRedirect(redirect)

