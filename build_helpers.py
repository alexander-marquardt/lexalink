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


import site_configuration
import codecs, shutil, re, glob, os, logging, subprocess, sys, datetime
        
        
def generate_index_files():
    logging.info("Generating index file")  
    src_common = "common_index.yaml"
    src_index = "%s_index.yaml" % site_configuration.BUILD_NAME
    dst = "index.yaml"
    logging.info("Generating %s based on %s and %s.\n" % (dst, src_common, src_index))
    
    destination = open(dst,'wb')
    shutil.copyfileobj(open(src_common,'rb'), destination)
    shutil.copyfileobj(open(src_index,'rb'), destination)
    destination.close()


def setup_my_local_environment():
    # THE FOLLOWING FUNCTIONALITY IS REQUIRED BECAUSE I AM 
    # BUILDING MULTIPLE SITES FROM A single_build CODE BASE
    # in order to support different database models, we copy the index.yaml file for the correct build. 
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
    static_dir_pattern = re.compile(r'(.+)(client/app)(.*)')   
    proprietary_static_dir_pattern = re.compile(r'(.+)(client/app/proprietary)(.*)')   
    appstat_middleware_pattern = re.compile(r'(- appstats:\s)(on|off)')
    
    
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
        if match_app_id_pattern:
            logging.info("Replacing appid with %s" % site_configuration.app_id_dict[site_configuration.BUILD_NAME])
            dst_file.write("application: %s\n" % site_configuration.app_id_dict[site_configuration.BUILD_NAME])
        elif match_version_pattern:
            logging.info("Replacing version with %s" % site_configuration.VERSION_ID)
            dst_file.write("version: %s\n" % site_configuration.VERSION_ID )
        elif match_static_dir_pattern:
            line = "%s%s%s" % (match_static_dir_pattern.group(1), site_configuration.LIVE_STATIC_DIR, match_static_dir_pattern.group(3))
            logging.info("Writing %s" % line)
            dst_file.write("%s\n" % line)
        elif match_proprietary_static_dir_pattern:
            line = "%s%s%s" % (match_proprietary_static_dir_pattern.group(1), site_configuration.LIVE_PROPRIETARY_STATIC_DIR, match_proprietary_static_dir_pattern.group(3))
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
        
        
def customize_files():
    
    logging.info( "**********************************************************************"  )  
    logging.info( "Generating custom files: %s (Build: %s)" % (site_configuration.APP_NAME, site_configuration.BUILD_NAME))
    logging.info( "%s" % datetime.datetime.now())
    logging.info( "**********************************************************************")
    
    
    setup_my_local_environment()
    check_that_minimized_javascript_files_are_enabled()
    generate_index_files()

