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


from django.utils import translation

import settings

def translate_text(lang_code, original_text):
    # translate original text into the given language. Translate text to language of your choice,
    # but remember to switch back to original language, as activating a translation catalog is done 
    # on per-thread basis and such change will affect code running in the same thread.
    
    previous_language = translation.get_language()# remember the original language, so we can set it back when we finish 
    try:
        translation.activate(lang_code)
        text = translation.ugettext(original_text)
       
    finally:
        translation.activate(previous_language)
    return text


def ugettext_tuple(original_text):
    # get the original text, and return it in an array for all languages that are
    # currently specified as valid. If a context is passed in, then we use this context 
    # for disambiguation. Eg. the word "may" can mean either might, or the month May. In this
    # case, we would pass in a context string to help disambiguate. 
    
    return_array = []
    for language_array in settings.LANGUAGES:
        lang_code = language_array[0]
        return_array.append(translate_text(lang_code, original_text))
    
    return tuple(return_array)
