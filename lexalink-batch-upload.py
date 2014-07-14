#!/usr/bin/python

# This code will batch-upload a time-stamped version of the current code to all sites
# Please ensure that you have already ran prepare-lexalink.py before attempting to run this code.

import os, subprocess, sys #, pexpect, time, getpass

SRC_DIR = "/Users/alexandermarquardt/Lexabit/lexalink"
sys.path.insert(0, SRC_DIR)
import batch_build_config # import from the lexalink directory


argc = len(sys.argv)

if argc == 1:
    # build all of the websites
    BUILD_NAMES_LIST = batch_build_config.BUILD_NAMES_LIST
else:
    BUILD_NAMES_LIST = sys.argv[1:]
    

TARGET_DIR = batch_build_config.TARGET_DIR

for build_name in BUILD_NAMES_LIST:

    dest_dir = TARGET_DIR + "/" + build_name        
        
    print "**********************************************************************"
    
    print "Changing working directory to: %s" % (dest_dir)
    os.chdir(dest_dir)        
    
    print "Batch uploader uploading build: %s" % (build_name)
    print "**********************************************************************\n"
    
    pargs = ['python', '/cygdrive/z/bin/lexalink-upload.py']
    process = subprocess.call(pargs,  stderr=subprocess.STDOUT)
    
        
