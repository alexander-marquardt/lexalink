from django.core.urlresolvers import reverse
from rs import forms

def get_userprofile_href(lang_code, userobject, is_primary_user = False):
    
    if is_primary_user:
        userobject_href =  reverse("edit_profile_url", kwargs={'display_nid' :userobject.key().id()})           
    else:
        profile_url_description = forms.FormUtils.get_profile_url_description(lang_code, userobject)
        userobject_href =  reverse("user_profile_url", kwargs={'display_nid' :userobject.key().id(),
                                              'profile_url_description' : profile_url_description})    
    return userobject_href