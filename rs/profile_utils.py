from django.core.urlresolvers import reverse
from google.appengine.api import memcache

import re, urllib, logging
from django.utils.translation import ugettext

import settings
from rs import  utils_top_level, utils, constants, error_reporting, localizations
from rs.user_profile_main_data import UserSpec
fields_for_title_generation   = []

# define which fields can be used in generating titles for profiles and search results. 
if settings.BUILD_NAME != "Language" and settings.BUILD_NAME != "Friend":
    fields_for_title_generation = UserSpec.principal_user_data + ['region', 'sub_region']
elif settings.BUILD_NAME == "Language":
    fields_for_title_generation = UserSpec.principal_user_data + ['region', 'sub_region', 'languages', 'languages_to_learn']    
elif settings.BUILD_NAME == "Friend":
    fields_for_title_generation = UserSpec.principal_user_data + ['region', 'sub_region',]
else:
    assert(0)


def get_profile_url_description(lang_code, uid):
    # Returns a description of the current profile that is suitable for display in a URL (ie. Male-Seeking-Female...)
    
    # Note: if the userprofile is updated, then this memcache entry should be deleted as it could 
    # potentially be out of date. This is taken care of in the put_userobject() function. 
    # Do not change the following memcache key without also changing it in the put_userobject function.
    memcache_key_str = lang_code + constants.PROFILE_URL_DESCRIPTION_MEMCACHE_PREFIX + uid
    profile_url_description = memcache.get(memcache_key_str)
    if profile_url_description is None:
        profile_url_description = get_base_userobject_title(lang_code, uid)
        profile_url_description = re.sub('[,;()/:]', ' ', profile_url_description) # replace all non-letter with blanks
        profile_url_description = re.sub(r'\s+' , '-', profile_url_description)    # replace all series of one or more blanks with a single dash
        profile_url_description = urllib.quote(profile_url_description.encode('utf8')) # escape unicode chars for URL    
        memcache.set(memcache_key_str, profile_url_description, constants.SECONDS_PER_MONTH)
                
    return profile_url_description


def get_userprofile_href(lang_code, userobject, is_primary_user = False):
    
    if is_primary_user:
        userobject_href =  reverse("edit_profile_url", kwargs={'display_nid' :userobject.key.integer_id()})           
    else:
        uid = userobject.key.urlsafe()
        profile_url_description = get_profile_url_description(lang_code, uid)
        
        if not profile_url_description:
            # For some unknown reason the profile_url_description is either blank or None. This should never happen, but
            # it has happenend in the past. It is not critical, but should be investigated and therefore we report as error as opposed to a warning.
            profile_url_description = "Internal-Error-Has-Been-Logged-And-Will-Be-Investigated"
            error_reporting.log_exception(logging.error, error_message = "user_profile_url not correctly generated for user %s" % userobject.key.integer_id())   
            
        userobject_href =  reverse("user_profile_url", kwargs={'display_nid' :userobject.key.integer_id(),
                                                         'profile_url_description' : profile_url_description})               
            
    return userobject_href


def replace_value(val_to_replace, val_to_check, default_value, replacement_string):
    if val_to_check == val_to_replace:
        return replacement_string
    else:
        return default_value       


def get_base_userobject_title(lang_code, uid):
    # Gets the main part of the user profile title (before adding in SEO optimizations
    # and anything else -- which we currently are not doing)
    
    
    try:
        # Use memcache to reduce server loading - once the title for the current profile is made
        # it will not change unless the user changes their profile. 
        # Every time the user profile is written, this memcache will be invalidated (this is 
        # taken care of in put_userobject)
        memcache_key_str = lang_code + constants.PROFILE_TITLE_MEMCACHE_PREFIX + uid
        base_title = memcache.get(memcache_key_str)
        if base_title is not None:
            # memcache hit!
            return base_title
        
        else:
            userobject = utils_top_level.get_object_from_string(uid)
            lang_idx = localizations.input_field_lang_idx[lang_code]        
            field_vals_dict = {}
    
            for field_name in fields_for_title_generation:
                field_vals_dict[field_name] = getattr(userobject, field_name)
                                 
            vals_in_curr_language_dict = utils.get_fields_in_current_language(field_vals_dict, lang_idx, pluralize_sex = False, search_or_profile_fields = "profile")
                             
            if settings.BUILD_NAME == "Discrete" or settings.BUILD_NAME == "Gay" or settings.BUILD_NAME == "Swinger":
                # check if this profile is gay (male seeking male) or lesbian .. if so, add the appropriate
                # word to the profile description.
                extra_detail = utils_top_level.get_additional_description_from_sex_and_preference(field_vals_dict['sex'], field_vals_dict['preference'], pluralize = False)
                
                relationship_status = replace_value('prefer_no_say', field_vals_dict['relationship_status'], "%s " % vals_in_curr_language_dict['relationship_status'], '')
                preference = replace_value('other', field_vals_dict['preference'], vals_in_curr_language_dict['preference'], ugettext("Contacts"))
                if settings.BUILD_NAME == "Gay":
                    sex = replace_value('other', field_vals_dict['sex'], vals_in_curr_language_dict['sex'], "Gay")
                elif settings.BUILD_NAME == "Swinger":
                    sex = replace_value('other', field_vals_dict['sex'], vals_in_curr_language_dict['sex'], "Swinger")                    
                else:
                    sex = vals_in_curr_language_dict['sex']

                base_title = u"%s" % (ugettext("%(relationship_status)s%(sex)sSeeking%(extra_detail)s%(preference)sIn%(location)s") % {
                    'relationship_status' : relationship_status,
                    'sex': "%s " % sex, 
                    'location': " %s" % vals_in_curr_language_dict['location'], 
                    'preference' : " %s " % preference,
                    'extra_detail' :  extra_detail})
                
            elif settings.BUILD_NAME == "Single" or settings.BUILD_NAME == "Lesbian":
                sex = replace_value('prefer_no_say', field_vals_dict['sex'], "%s " % vals_in_curr_language_dict['sex'], "%s " % ugettext("Lesbian"))
                preference = replace_value('prefer_no_say', field_vals_dict['preference'], " %s " % vals_in_curr_language_dict['preference'], " %s " % ugettext("Lesbian"))

                    
                extra_detail = utils_top_level.get_additional_description_from_sex_and_preference(field_vals_dict['sex'], \
                            field_vals_dict['preference'], pluralize = False)            
                base_title = u"%s" % (ugettext("%(sex)sSeeking%(extra_detail)s%(preference)sFor %(relationship_status)s In %(location)s") % {
                    'relationship_status' : vals_in_curr_language_dict['relationship_status'],                
                    'sex': sex, 
                    'location': vals_in_curr_language_dict['location'], 
                    'extra_detail' : extra_detail,
                    'preference' : preference})
                
            elif settings.BUILD_NAME == "Language":
                base_title = u"%s" % ugettext("Speaker Of %(languages)s Seeking Speakers Of %(languages_to_learn)s In %(location)s") % {
                'languages': vals_in_curr_language_dict['languages'], 'location': vals_in_curr_language_dict['location'], 
                'languages_to_learn' : vals_in_curr_language_dict['languages_to_learn']} 
                
            elif settings.BUILD_NAME == 'Friend':
                activity_summary = utils.get_friend_bazaar_specific_interests_in_current_language(userobject, lang_idx)
                base_title = u"%s" % (ugettext("%(sex)s In %(location)s") % {
                    'sex': vals_in_curr_language_dict['sex'],
                    'location' : vals_in_curr_language_dict['location'],
                })
                base_title += u"%s" % activity_summary
            else:
                assert(0)        
        
            return base_title
    except:
        error_reporting.log_exception(logging.critical)       
        return ''                