#!/usr/bin/python

################################################################################
# This is a build script that will generate unique directories for each website. 
# Once these directories are built, they can be retained for posterity, and they
# can also be used by scripts to be directly uploaded to the servers
# as each directory contains a totally server-ready website that is configured for
# a particular build.
################################################################################

# This code will prepare a lexalink-uploads directory that has a "pre-compiled" 
# (grunt already ran, etc.) directory for each build/website.


import os, datetime, codecs, re
import subprocess, sys, shutil, subprocess

SRC_DIR = "/Users/alexandermarquardt/Lexabit/lexalink"
sys.path.insert(0, SRC_DIR)
import batch_build_config # from lexalink directory (not from the lexalink-uploads directory)


argc = len(sys.argv)

if argc == 1:
    # build all of the websites
    BUILD_NAMES_LIST = batch_build_config.BUILD_NAMES_LIST
else:
    BUILD_NAMES_LIST = sys.argv[1:]
    
print "building %s" % BUILD_NAMES_LIST

TARGET_DIR = batch_build_config.TARGET_DIR

def get_version_identifier():
    # use datetime as a version identifier/timestamp - but need to remove spaces and colons    
    datetime_str = str(datetime.datetime.now())
    datetime_str = datetime_str[:16]
    datetime_str = datetime_str.replace(' ', '-')
    datetime_str = datetime_str.replace(':', '')
    return datetime_str

VERSION_ID = get_version_identifier()


def check_if_dirs_exist():
    # make sure that the SRC_DIR and TARGET_DIR exist
    if not os.path.isdir(SRC_DIR) or not os.path.isdir(TARGET_DIR):
        print "Error: This program is intended to be run from OSX"
        sys.exit()    

def copy_lexalink_to_uploads_dir(dest_dir):  
    
    try:
        print "removing %s" % dest_dir
        shutil.rmtree(dest_dir)
    except:
        print "%s not found - therefore not removed" % dest_dir
        
    ignore_patterns = shutil.ignore_patterns(".git", "*.pyc", "*.pyo", "upload_done.txt")
    print "copying %s to %s" % (SRC_DIR, dest_dir)
    shutil.copytree(SRC_DIR, dest_dir, ignore = ignore_patterns)
        

def update_site_configuration():
    site_configuration_file_name = "site_configuration.py"
    new_site_configuration_file_name = "site_configuration.new.py"
    
    
    replacement_patterns_array = [(re.compile(r'(BATCH_BUILD_NAME.*=)(.*)'), build_name),   
                                  (re.compile(r'(VERSION_ID.*=)(.*)'),  get_version_identifier()),
                                  (re.compile(r'(USE_COMPRESSED_STATIC_FILES.*=)(.*)'), True),
                                  (re.compile(r'(ENABLE_GRUNT.*=)(.*)'), True)]
    
    site_configuration_file_handle = codecs.open(site_configuration_file_name, encoding='utf_8')    
    new_site_configuration_file_handle = codecs.open(new_site_configuration_file_name, 'w', encoding='utf_8')    
    for line in site_configuration_file_handle:
        
        for pattern_tuple in replacement_patterns_array:
            match_pattern = pattern_tuple[0].match(line)
            if match_pattern:
                line = match_pattern.group(1) + " '%s'\n" % pattern_tuple[1]
                
      
        new_site_configuration_file_handle.write(line)
        
    new_site_configuration_file_handle.close()
    site_configuration_file_handle.close()
    # copy the new site_configuration file over the old one
    shutil.move(new_site_configuration_file_name, site_configuration_file_name)    
    

print "**********************************************************************"    
print "running build-lexalink.py"

check_if_dirs_exist()

import imp

for build_name in BUILD_NAMES_LIST:
    print "building %s" % build_name
    
    dest_dir = TARGET_DIR + "/" + build_name   + "/"
    copy_lexalink_to_uploads_dir(dest_dir)
    
    print "chdir to %s" % dest_dir
    os.chdir(dest_dir)
    
    update_site_configuration()    
    
    os.chmod(dest_dir + "build_helpers.py", 0777)

    pargs = ['./build_helpers.py']
    print "Process args = %s" % pargs
    process = subprocess.call(pargs,  stderr=subprocess.STDOUT)
    
    print "finished building %s" % build_name    



print "finished prepare-lexalink.py"
print "**********************************************************************\n"
