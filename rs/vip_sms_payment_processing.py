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


""" Setup the structures that will be used in processing SMS payments. 
    Currently we are using fortumo.com as our payment processor.
    
    
    Currently we are offering SMS payment in Argentina, Chile, Colombia, Mexico, and Spain"""


# We  detect that an SMS payment has come from a given country, and verify that it is 
# of the expected amount. Once these two conditions are met, then the following number of VIP days
# will be awarded to the member.
payment_days_awarded = { 
    # for each country, specify a dictionary of the form {price : days awarded}
    'AR' : {"9.99" : 1},    # $1.75 USD
    'CL' : {"900.00" : 1},  # $1.70 USD
    'CO' : {"6960.00" : 3}, # $3.46 USD
    'MX' : {"30.26" : 2},   # $2.16 USD
    'ES' : {"7.26" : 5},    # $9.18 USD 
}


