
from django.utils.translation import ugettext
import settings

def get_additional_description_from_sex_and_preference(sex_key_val, preference_key_val):
    additional_description = ''    
    
    if sex_key_val == "male" and preference_key_val == "male":
        additional_description = " (%s)" % ugettext("Gay men")
    elif sex_key_val == "female" and preference_key_val == "female":
        additional_description = " (%s)" % ugettext("Lesbian")
        
    if settings.BUILD_NAME == "Swinger":
        if sex_key_val == "couple" or preference_key_val == "couple":
            additional_description = ". %s" % ugettext("Contacts for swingers")
        
    return additional_description