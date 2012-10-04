#!/usr/bin/python

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
# configured for the current build configuration. We should always call this script instead
# of appcfg.py

import subprocess, sys, settings, build_helpers, logging, datetime

# Ensure that the environment is consistent with the settings.py configuration



logging.getLogger().setLevel(logging.DEBUG)



print "**********************************************************************"
print "RE-BUILDING ENVIRONMENT AND STATIC DIRS TO ENSURE CONSISTENCY"
print "%s" % datetime.datetime.now()
print "**********************************************************************\n"

  

""" 
Ensure that we never accidently upload a version that is not setup to have all the static directories replaced
with time-stamped version.
"""
do_setup = True
if "-no_setup" in sys.argv:
    do_setup = False
    sys.stderr.write("*** Not running setup *****\n")
    # remove the "-no_setup" from the argv
    del sys.argv[sys.argv.index("-no_setup")]


if settings.FLASH_FILES_DIR == "bin-debug": 
    sys.stderr.write("************* Error *************\n")
    sys.stderr.write("You are attempting upload code with FLASH_FILES_DIR set to bin-debug\n")
    sys.stderr.write("Now cancelling upload\n")
    sys.stderr.write("************* Exit *************\n\n")
    sys.exit(1)    

    
if do_setup:
    # ensure that static dirs are setup to be copied correctly
    if not settings.USE_TIME_STAMPED_STATIC_FILES:
        sys.stderr.write("************* Error *************\n")
        sys.stderr.write("You are attempting upload code with an incorrectly configured static directory\n")
        sys.stderr.write('Please modify settings.USE_TIME_STAMPED_STATIC_FILES to True\n\n')
        sys.stderr.write("Now cancelling upload\n")
        sys.stderr.write("************* Exit *************\n\n")
        sys.exit(1)
        
        
build_helpers.check_that_minimized_javascript_files_are_enabled();

    
build_helpers.generate_index_files()    
build_helpers.setup_my_local_environment()

if do_setup:
    build_helpers.generate_time_stamped_static_files()
    

print "**********************************************************************"
print "BEGINNING UPLOAD OF CURRENT BUILD"
print "%s" % datetime.datetime.now()
print "**********************************************************************\n"

additional_args = sys.argv[1:]
if not additional_args:
    pargs = ['appcfg.py', 'update'] + ['.']
else:
    if additional_args[0] != '-setup_only':
        pargs = ['appcfg.py'] + additional_args + ['.']

print "Process args = %s" % pargs

process = subprocess.call(pargs,  stderr=subprocess.STDOUT)

print "**********************************************************************"
print "FINISHED UPLOAD OF CURRENT BUILD"
print "%s" % datetime.datetime.now()
print "**********************************************************************\n"

if settings.ENABLE_APPSTATS:
    print "****\n"
    print "WARNING: APPSTATS ENABLED - This can slightly impact performance\n"
    print "****\n"
    

sys.exit(0)

