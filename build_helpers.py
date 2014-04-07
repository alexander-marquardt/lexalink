#!/usr/bin/python

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


import site_configuration
import codecs, shutil, re, glob, os, logging, subprocess, sys, datetime
        
        
print "Imported site_configuration from %s" % site_configuration.__file__
print "USE_COMPRESSED_STATIC_FILES = %s" % site_configuration.USE_COMPRESSED_STATIC_FILES

def check_site_configuration():
    # make sure that site_configuration file doesn't have any declarations that will cause problems when uploaded.
    # We especially want to make sure that we are uploading and accessing minimized and compressed static files.
    if not site_configuration.USE_COMPRESSED_STATIC_FILES:
        sys.stderr.write("************* Error *************\n")
        sys.stderr.write("You are attempting upload code with an incorrectly configured static directory\n")
        sys.stderr.write('Please modify site_configuration.USE_COMPRESSED_STATIC_FILES to True\n\n')
        sys.stderr.write("Upload cancelled\n")
        sys.stderr.write("************* Exit *************\n\n")
        exit(1)
        
    if site_configuration.ENABLE_APPSTATS:
        print "****\n"
        print "WARNING: APPSTATS ENABLED - This can slightly impact performance\n"
        print "****\n"        
        
        
def generate_index_files():
    # In order to support different database models, we copy the index.yaml file for the correct build. 
    
    logging.info("Generating index file")  
    src_common = "common_index.yaml"
    src_index = "%s_index.yaml" % site_configuration.BUILD_NAME
    dst = "index.yaml"
    logging.info("Generating %s based on %s and %s.\n" % (dst, src_common, src_index))
    
    destination = open(dst,'wb')
    shutil.copyfileobj(open(src_common,'rb'), destination)
    shutil.copyfileobj(open(src_index,'rb'), destination)
    destination.close()

    

def generate_app_yaml():
    # THE FOLLOWING FUNCTIONALITY IS REQUIRED BECAUSE I AM 
    # BUILDING MULTIPLE SITES FROM A single_build CODE BASE
    # Additionally, we customize the app.yaml file so that it uploads to the correct application id, and so
    # that the favicon icons are correctly defined.

    logging.info("Running setup_my_local_environment")
    
    # copy the app.yaml so that proper favicons are included
    src = "app_generic.yaml"
    dst = "app.yaml"

    src_file = codecs.open(src, encoding='ascii')
    dst_file = codecs.open(dst, 'w', encoding='ascii')
    
    
    build_name_pattern = re.compile(r'(.*)(BUILD_NAME)(.*)')    
    
    app_id_pattern = re.compile(r'application:.*')
    version_id_pattern = re.compile(r'version: yyyy-mm-dd-hhhh')
    #favicon_pattern = re.compile(r'(.+)(rs/static)(/img)(.*)(/favicon.ico)')
    static_dir_pattern = re.compile(r'(.+)(STATIC_DIR)(.*)')   
    proprietary_static_dir_pattern = re.compile(r'(.+)(PROPRIETARY_STATIC_DIR)(.*)')   
    appstat_middleware_pattern = re.compile(r'(- appstats:\s)(on|off)')
    manually_versioned_images_dir_pattern = re.compile(r'(.+)(MANUALLY_VERSIONED_IMAGES_DIR)(.*)')   
    
    
    # generate the app.yaml file, based on the current site_configuration.
    logging.info("Generating %s based on %s.\n" % (dst, src))
    dst_file.write("# DO NOT EDIT - Auto-generated from %s\n\n" % src)
    for line in src_file:
        
        match_build_name_pattern = build_name_pattern.match(line)
        if match_build_name_pattern:
            line = match_build_name_pattern.group(1) + site_configuration.BUILD_NAME + match_build_name_pattern.group(3)        
        
        match_app_id_pattern = app_id_pattern.match(line)
        match_version_pattern = version_id_pattern.match(line)
        #match_favicon_pattern = favicon_pattern.match(line)
        match_static_dir_pattern = static_dir_pattern.match(line)
        match_proprietary_static_dir_pattern = proprietary_static_dir_pattern.match(line)
        match_appstat_middleware_pattern = appstat_middleware_pattern.match(line)
        match_versioned_images_dir_pattern = manually_versioned_images_dir_pattern.match(line)
        if match_app_id_pattern:
            logging.info("Replacing appid with %s" % site_configuration.app_id_dict[site_configuration.BUILD_NAME])
            dst_file.write("application: %s\n" % site_configuration.app_id_dict[site_configuration.BUILD_NAME])
        elif match_version_pattern:
            logging.info("Replacing version with %s" % site_configuration.VERSION_ID)
            dst_file.write("version: %s\n" % site_configuration.VERSION_ID )
        elif match_proprietary_static_dir_pattern:
            line = "%s%s%s" % (match_proprietary_static_dir_pattern.group(1), site_configuration.PROPRIETARY_STATIC_DIR, match_proprietary_static_dir_pattern.group(3))
            logging.info("Writing %s" % line)
            dst_file.write("%s\n" % line)            
        elif match_static_dir_pattern:
            line = "%s%s%s" % (match_static_dir_pattern.group(1), site_configuration.STATIC_DIR, match_static_dir_pattern.group(3))
            logging.info("Writing %s" % line)
            dst_file.write("%s\n" % line)
        elif match_versioned_images_dir_pattern:
            line = "%s%s%s" % (match_versioned_images_dir_pattern.group(1), site_configuration.MANUALLY_VERSIONED_IMAGES_DIR, match_versioned_images_dir_pattern.group(3))
            logging.info("Writing %s" % line)
            dst_file.write("%s\n" % line)
        elif match_appstat_middleware_pattern:
            line = "%s%s" % (match_appstat_middleware_pattern.group(1), "on" if site_configuration.ENABLE_APPSTATS else "off")
            logging.info("Writing: %s" % line)
            dst_file.write("%s\n" % line)
        else:
            dst_file.write(line)
    
    src_file.close()
    dst_file.close()
          
    
def print_warning(txt):
    sys.stderr.write("\n************* WARNING *************\n")
    sys.stderr.write("************* WARNING *************\n")
    sys.stderr.write(txt + '\n')
    sys.stderr.write("************* END WARNING *************\n")
    sys.stderr.write("************* END WARNING *************\n\n")
    

def check_that_minimized_javascript_files_are_enabled():
    
    # makes sure that the .min.js versions of externally loaded files is used - since we sometimes
    # enable the non-minimized file during development, this will generate a warning
    # if the min file is not enabled. This is intended to be called when uploading code.
    file_names = ["jquery.min.js",  "jquery-ui.min.js"]
    input_html_src = "client/app/html/import_main_css_and_js.html"
    input_html_src_file = codecs.open(input_html_src, encoding='ascii')
    jquery_pattern = re.compile(r'.*ajax.googleapis.com/ajax/libs/jquery/.*jquery.min.js.*')
    jquery_ui_pattern = re.compile(r'.*ajax.googleapis.com/ajax/libs/jqueryui/.*jquery-ui.min.js.*')

    jquery_minimized = False
    jquery_ui_minimized = False
    
    for line in input_html_src_file:
        if jquery_pattern.match(line):
            jquery_minimized = True
        if jquery_ui_pattern.match(line):
            jquery_ui_minimized = True
    
    if not jquery_minimized:
        print_warning("Not using minimized version of Jquery")
    if not jquery_ui_minimized:
        print_warning("Not using minimized version of Jquery-ui")
     


def setup_build_settings_json():
    # We use node/grunt to minimize html/css/javascript. This function modifies the build_settigns.json file
    # that is read by Gruntfile.js in order to communicate the current build name.
    logging.info("Running setup_build_settings_json")
    # copy the app.yaml so that proper favicons are included
    dst = "client/build_settings.json"
    logging.info("Generating %s\n" % dst)
    dst_file = codecs.open(dst, 'w', encoding='ascii')
    dst_file.write('{\n')
    dst_file.write('\t\"comment" : "this build file has been auto-generated by setup_build_settings_json and will be over-written by the build scripts",\n')
    dst_file.write('\t\"build_name" : "%s",\n' %  site_configuration.BUILD_NAME)
    dst_file.write('\t\"build_name_used_for_menubar" : "%s",\n' %  site_configuration.BUILD_NAME_USED_FOR_MENUBAR)
    dst_file.write('\t\"proprietary_styles_dir" : "%s"\n' %  site_configuration.PROPRIETARY_STYLES_DIR)
    dst_file.write('}\n')
    dst_file.close()
         
     
def run_grunt(grunt_arg, subprocess_function):
    # run the node/grunt build scripts. These are responsible for minimizing/versioning/copying html/css/js files.
    setup_build_settings_json()
    
    os.chdir("client")
    pargs = ['grunt', grunt_arg]
    process = subprocess_function(pargs,  stderr=subprocess.STDOUT)    
    os.chdir("..")
    logging.info("Switched directory back to: %s" % os.getcwd())
    
    
def run_grunt_jobs():
    
    
    if site_configuration.ENABLE_GRUNT:
        
        # If the user is just running locally and not using proprietary builds, then the grunt build scripts are not necessary. 
        # Grunt can be enabled by advanced users who know what they are doing.     

        if site_configuration.USE_COMPRESSED_STATIC_FILES:
            # only run the grunt build scripts if we are currently accessing the compressed static files (ie. client/dist instead of client/app). 
            # Otherwise, we are directly accessing the source static files, and minimizing would serve no purpose.
            run_grunt('build', subprocess.call)
            
        else:
            run_grunt('clean', subprocess.call)
            # we only run the watch/livereload if this user knows what they are doing. Feel free to enable this
            # and to also enable livereload in the html template if you know how to use it. This really only makes sense
            # if we are accessing the original (non-compressed) static files as you normally would do during development.
            run_grunt('watch', subprocess.Popen)    
            
    else:
        if site_configuration.USE_COMPRESSED_STATIC_FILES:
            logging.error("cannot set flag USE_COMPRESSED_STATIC_FILES unless ENABLE_GRUNT is set")
            exit(1)
        else:
            pass
    
        
def customize_files():
    
    logging.info( "**********************************************************************"  )  
    logging.info( "Generating custom files: %s (Build: %s)" % (site_configuration.APP_NAME, site_configuration.BUILD_NAME))
    logging.info( "Current path): %s" % os.getcwd())    
    logging.info( "%s" % datetime.datetime.now())
    logging.info( "**********************************************************************")
    
    generate_app_yaml()
    check_that_minimized_javascript_files_are_enabled()
    generate_index_files()
    run_grunt_jobs()

        

if __name__ == "__main__":
    # If build_helpers.py is called as an executable file, it is likely customizing build-specific files for
    # the prepare-lexalink.py script.
    customize_files()
    
