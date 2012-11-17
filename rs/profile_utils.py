from django.core.urlresolvers import reverse
from google.appengine.api import memcache

import re, urllib

import settings
from rs import forms, utils_top_level, constants



def get_profile_url_description(lang_code, uid):
    # Returns a description of the current profile that is suitable for display in a URL (ie. Male-Seeking-Female...)
    
    # Note: if the userprofile is updated, then this memcache entry should be deleted as it could 
    # potentially be out of date. This is taken care of in the put_userobject() function. 
    # Do not change the following memcache key without also changing it in the put_userobject function.
    memcache_key_str = lang_code + constants.PROFILE_URL_DESCRIPTION_MEMCACHE_PREFIX + uid
    profile_url_description = memcache.get(memcache_key_str)
    if profile_url_description is not None:
        return profile_url_description
    else:
        userobject = utils_top_level.get_object_from_string(uid)
        profile_url_description = forms.FormUtils.get_base_userobject_title(lang_code, userobject)
        profile_url_description = re.sub('[,;()/]', '', profile_url_description)
        profile_url_description = re.sub(r'\s+' , '-', profile_url_description)        
        profile_url_description = urllib.quote(profile_url_description.encode('utf8')) # escape unicode chars for URL    
        memcache.set(memcache_key_str, profile_url_description, constants.SECONDS_PER_MONTH)
        return profile_url_description


def get_userprofile_href(lang_code, userobject, is_primary_user = False):
    
    if is_primary_user:
        userobject_href =  reverse("edit_profile_url", kwargs={'display_nid' :userobject.key().id()})           
    else:
        uid = str(userobject.key())
        profile_url_description = get_profile_url_description(lang_code, uid)
        userobject_href =  reverse("user_profile_url", kwargs={'display_nid' :userobject.key().id(),
                                              'profile_url_description' : profile_url_description})    
    return userobject_href



