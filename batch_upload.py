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

# This code will batch-upload a time-stamped version of the current code to all sites

import datetime, codecs, re
import subprocess, sys, shutil, pexpect, time, getpass
    
# Note: we add in the '' build name so that
# the settings.py will default back to the previously selected build name (see settings.py to understand
# why a '' value will cause the previously selected build name to be used). Additionally, this
# causes an additional version to be generated and written to settings.py, which ensures that we 
# will not accidentally upload over top of a previous version number. 
BUILD_NAMES_LIST = ['Discrete', 'Single' , 'Language', 'Lesbian', 'Gay', 'Swinger', 'Friend', '']

def get_version_identifier():
    # use datetime as a version identifier/timestamp - but need to remove spaces and colons    
    datetime_str = str(datetime.datetime.now())
    datetime_str = datetime_str[:16]
    datetime_str = datetime_str.replace(' ', '-')
    datetime_str = datetime_str.replace(':', '')
    return datetime_str


settings_file_name = "settings.py"
new_settings_file_name = "settings.new.py"

build_name_pattern = re.compile(r'(BATCH_BUILD_NAME.*=)(.*)')  
version_id_pattern = re.compile(r'(VERSION_ID.*=)(.*)')  

email_address = raw_input('Email: ')
password = getpass.getpass()


for build_name in BUILD_NAMES_LIST:

    settings_file_handle = codecs.open(settings_file_name, encoding='utf_8')    
    new_settings_file_handle = codecs.open(new_settings_file_name, 'w', encoding='utf_8')    
    for line in settings_file_handle:
        
        match_build_name_pattern = build_name_pattern.match(line)
        match_version_id_pattern = version_id_pattern.match(line)
    
        if match_build_name_pattern:
            line = match_build_name_pattern.group(1) + " '%s'\n" % build_name
        elif match_version_id_pattern:
            line = match_version_id_pattern.group(1) + " '%s'\n" % get_version_identifier()
        
        new_settings_file_handle.write(line)
        
    new_settings_file_handle.close()
    settings_file_handle.close()
    # copy the new settings file over the old one
    shutil.move(new_settings_file_name, settings_file_name)
    
    
    if build_name != '':
    
        print "**********************************************************************"
        print "Batch uploader uploading build: %s" % (build_name)
        print "**********************************************************************\n"
    
        pargs = ['python', './upload_code.py'] + sys.argv[1:]
        
        try:
            command = "%s" % " ".join(pargs)
            print "command = %s" % command
            child = pexpect.spawn(command)
            child.expect('Email: ')
            child.sendline(email_address)
            child.expect('Password:')
            time.sleep(0.1) # wait for 1/10th of a second so that the password echo can be turned off.
            child.sendline(password)
            child.interact()        

        except: # CalledProcessError (but we catch all errors here just in case there are others)
            sys.stderr.write("Error calling upload_code.py\n\n") 
            sys.exit(1)

    
    