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


# Wrapper for "appcfg.py update ." that ensures that all static directories are correctly 
# configured for the current build configuration. We should generally call this script instead
# of directly using appcfg.py in order to ensure that everything is setup ok.

import subprocess, sys, build_helpers, logging, datetime, time
import build_helpers
# import pexpect # http://www.noah.org/wiki/Pexpect - you must install this
import getpass
import site_configuration

def check_site_configuration():
    # make sure that site_configuration file doesn't have any declarations that will cause problems when uploaded.
    
    if not site_configuration.USE_TIME_STAMPED_STATIC_FILES:
        sys.stderr.write("************* Error *************\n")
        sys.stderr.write("You are attempting upload code with an incorrectly configured static directory\n")
        sys.stderr.write('Please modify site_configuration.USE_TIME_STAMPED_STATIC_FILES to True\n\n')
        sys.stderr.write("Upload cancelled\n")
        sys.stderr.write("************* Exit *************\n\n")
        exit(1)
    
    if site_configuration.FLASH_FILES_DIR == "bin-debug": 
        sys.stderr.write("************* Error *************\n")
        sys.stderr.write("You are attempting upload code with FLASH_FILES_DIR set to bin-debug\n")
        sys.stderr.write("Upload cancelled\n")
        sys.stderr.write("************* Exit *************\n\n")
        sys.exit(1)
        
    if site_configuration.ENABLE_APPSTATS:
        print "****\n"
        print "WARNING: APPSTATS ENABLED - This can slightly impact performance\n"
        print "****\n"        
        

logging.getLogger().setLevel(logging.DEBUG)

print "**********************************************************************"
print "Starting upload_code script %s (Build: %s)" % (site_configuration.APP_NAME, site_configuration.BUILD_NAME)
print "%s" % datetime.datetime.now()
print "**********************************************************************\n"

check_site_configuration()

#email_address = raw_input('Email: ')
#password = getpass.getpass()
    
# Build all the dependent files etc. 
build_helpers.customize_files()

print "**********************************************************************"
print "Beginning upload: %s (Build: %s)" % (site_configuration.APP_NAME, site_configuration.BUILD_NAME)
print "Version: %s" % site_configuration.VERSION_ID
print "%s" % datetime.datetime.now()
print "**********************************************************************\n"

additional_args = sys.argv[1:]
if not additional_args:
    pargs = ['appcfg.py', '--oauth2', 'update'] + ['.']
else:
    pargs = ['appcfg.py', '--oauth2'] + additional_args + ['.']

print "Process args = %s" % pargs

process = subprocess.call(pargs,  stderr=subprocess.STDOUT)
#command = "%s" % " ".join(pargs)
#child = pexpect.spawn(command)
#child.expect('Email: ')
#child.sendline(email_address)
#child.expect('Password for .+:')
#time.sleep(0.1) # wait for 1/10th of a second so that the password echo can be turned off.
#child.sendline(password)
#child.interact()

print "**********************************************************************"
print "Finisehd upload %s (Build: %s)" % (site_configuration.APP_NAME, site_configuration.BUILD_NAME)
print "%s" % datetime.datetime.now()
print "**********************************************************************\n"

sys.exit(0)

