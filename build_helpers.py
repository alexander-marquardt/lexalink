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


import settings
import codecs, shutil, re, glob, os, logging, subprocess, sys


def create_combined_static_file(html_source, output_file_name,  static_file_type):
    
    """ Scans the html_source file for static files of the appropriate type, and generates a combined and 
        minified version of these files - this increases efficiency and speed of page download and rendering due to
        a reduction in the number of server request/response cycles (which are time-consuming)
        
        Args:
        - html_source: the html file that we are scanning for the static file names
        - output_file_name: the name of the combined output file (without including extensions such as .css or .js in the file name)
        - static_file_type: either "css" or "js" - indicates the file extension that we are looking for
        
        Notes:
        - We currently open input files as "ascii" - if we ever have unicode characters in our css or javascript, this might
          cause a problem.
    """
    
    input_html_src = "rs/templates/user_main_helpers/%s" % html_source
    input_html_src_file = codecs.open(input_html_src, encoding='ascii')
        
    # parse the file to figure out which CSS files we need to combine
    static_file_list = []
    static_file_pattern =  re.compile(r'.*/{{ live_static_dir }}/%s/(.*).%s' % (static_file_type, static_file_type))
    proprietary_static_file_pattern =  re.compile(r'.*/{{ live_proprietary_static_dir }}/%s/(.*).%s' % (static_file_type, static_file_type))
    build_name_pattern = re.compile(r'(.*)({{ build_name }})(.*)')
    default_common_pattern = re.compile(r'.*default_common\.css.*')
    
    
    for line in input_html_src_file:
        matched_file_name = None
        match_static_file_pattern = static_file_pattern.match(line)
        match_proprietary_static_file_pattern = proprietary_static_file_pattern.match(line)
        match_default_common_pattern = default_common_pattern.match(line)
        
        if match_static_file_pattern:
            matched_file_name = match_static_file_pattern.group(1)
            
            if match_default_common_pattern and settings.PROPRIETARY_STATIC_DIR_EXISTS:
                # exclude the "default_common.css" file from the combined css file, since we are using
                # customized css for each build.
                logging.info("ignoring default_common.css")
                continue
            
        elif settings.PROPRIETARY_STATIC_DIR_EXISTS and match_proprietary_static_file_pattern:
            matched_file_name = match_proprietary_static_file_pattern.group(1)
            
        if matched_file_name and matched_file_name != output_file_name + ".min" and matched_file_name != output_file_name:
            build_name_match = build_name_pattern.match(matched_file_name)
            if build_name_match:
                # we need to replace the {{ build_name }} with the actual build name
                final_file_name = build_name_match.group(1) + settings.BUILD_NAME + build_name_match.group(3)
            else:
                final_file_name = matched_file_name
            logging.info("Matched %s file %s" % (static_file_type, final_file_name))
            static_file_list.append(final_file_name)
            
    combined_static_file_name = settings.LIVE_STATIC_DIR + "/%s/%s.%s" % (static_file_type, output_file_name, static_file_type)
    combined_static_file_handle = codecs.open(combined_static_file_name, 'w', encoding='ascii')  
    
    
    
    charset_pattern = re.compile(r'(.*@charset.*)')    
    logging.info("Writing master %s file: %s" % (static_file_type, combined_static_file_name))
    if static_file_type == "css":
        combined_static_file_handle.write('@charset "utf-8";\n')
        
    for static_file in static_file_list:
        logging.info("Including: " + settings.LIVE_STATIC_DIR + "/" +static_file_type + "/" + static_file + ".%s" % static_file_type)
        input_file_handle = open(settings.LIVE_STATIC_DIR + "/" + static_file_type + "/" + static_file + ".%s" % static_file_type, 'r')
        
        if static_file_type == "js": 
            combined_static_file_handle.write(input_file_handle.read())  
        if static_file_type == "css":
            # loop over the input file and strip out the @charset "utf-8" declarations 
            for input_file_line in input_file_handle: 
                match_charset_pattern = charset_pattern.match(input_file_line)
                if not match_charset_pattern:
                    combined_static_file_handle.write(input_file_line)

        
    combined_static_file_handle.close()
    
    combined_min_static_file_name = settings.LIVE_STATIC_DIR + "/%s/%s.min.%s" % (static_file_type, output_file_name, static_file_type)
    
    if static_file_type == "css":
        logging.info("Minifying master %s file: %s" % (static_file_type, combined_min_static_file_name))    
        if not settings.IS_CYGWIN:
            pargs = ['java', '-jar', '/Users/alexandermarquardt/bin/yuicompressor-2.4.6/build/yuicompressor-2.4.6.jar', combined_static_file_name, '-o', combined_min_static_file_name]
        else:
            # in order to run the jar file in cygwin, it must have the path specified in a special manner
            pargs = ['java', '-jar', r'Z:\bin\yuicompressor-2.4.6\build\yuicompressor-2.4.6.jar', combined_static_file_name, '-o', combined_min_static_file_name]

        subprocess.Popen(pargs)
        
    if static_file_type == "js":
        logging.info("Minifying master %s file: %s" % (static_file_type, combined_min_static_file_name))    
        if not settings.IS_CYGWIN:
            pargs = ['java', '-jar', '/Users/alexandermarquardt/bin/js-compiler.jar',  '--compilation_level',  'SIMPLE_OPTIMIZATIONS', \
                     '--js',  combined_static_file_name]
        else:
            # setup path for cygwin compilation
            pargs = ['java', '-jar', r'Z:\bin\js-compiler.jar',  '--compilation_level',  'SIMPLE_OPTIMIZATIONS', \
                     '--js',  combined_static_file_name]
        
        # note that the closure compiler writes output to stdout, which requires additional processing to get the results into a file
        process = subprocess.Popen(pargs, stdout = subprocess.PIPE)
        (stdout, stderr) = process.communicate()
        minimized_file_handle = codecs.open(combined_min_static_file_name, 'w', encoding='ascii')   
        minimized_file_handle.write(stdout)
        minimized_file_handle.close()

from glob import iglob
from shutil import copy
from os.path import join

def copy_file_to_folder(src_glob, dst_folder):
    for fname in iglob(src_glob):
        copy(fname, dst_folder)
        
        
def generate_index_files():
    src = "%s_index.yaml" % settings.BUILD_NAME
    dst = "index.yaml"
    logging.info("Generating %s based on %s.\n" % (dst, src))
    shutil.copyfile(src, dst)    

def setup_my_local_environment():
    # THE FOLLOWING FUNCTIONALITY IS REQUIRED BECAUSE I AM 
    # BUILDING MULTIPLE SITES FROM A SINGLE CODE BASE
    # in order to support different database models, we copy the index.yaml file for the correct build. 
    # Additionally, we customize the app.yaml file so that it uploads to the correct application id, and so
    # that the favicon icons are correctly defined.


    
    # copy the app.yaml so that proper favicons are included
    src = "app_generic.yaml"
    dst = "app.yaml"

    src_file = codecs.open(src, encoding='ascii')
    dst_file = codecs.open(dst, 'w', encoding='ascii')
    
    
    build_name_pattern = re.compile(r'(.*)(BUILD_NAME)(.*)')    
    
    app_id_pattern = re.compile(r'application:.*')
    version_id_pattern = re.compile(r'version: yyyy-mm-dd-hhhh')
    #favicon_pattern = re.compile(r'(.+)(rs/static)(/img)(.*)(/favicon.ico)')
    static_dir_pattern = re.compile(r'(.+)(rs/versioned_static)(.*)')   
    proprietary_static_dir_pattern = re.compile(r'(.+)(rs/proprietary/proprietary_versioned_static)(.*)')   
    flash_files_dir_pattern = re.compile(r'(.*)(FLASH_FILES_DIR)(.*)')
    appstat_middleware_pattern = re.compile(r'(- appstats:\s)(on|off)')
    
    
    # generate the app.yaml file, based on the current settings.
    logging.info("Generating %s based on %s.\n" % (dst, src))
    dst_file.write("# DO NOT EDIT - Auto-generated from %s\n\n" % src)
    for line in src_file:
        
        match_build_name_pattern = build_name_pattern.match(line)
        if match_build_name_pattern:
            line = match_build_name_pattern.group(1) + settings.BUILD_NAME + match_build_name_pattern.group(3)        
        
        match_app_id_pattern = app_id_pattern.match(line)
        match_version_pattern = version_id_pattern.match(line)
        #match_favicon_pattern = favicon_pattern.match(line)
        match_static_dir_pattern = static_dir_pattern.match(line)
        match_proprietary_static_dir_pattern = proprietary_static_dir_pattern.match(line)
        match_flash_files_dir_pattern = flash_files_dir_pattern.match(line)
        match_appstat_middleware_pattern = appstat_middleware_pattern.match(line)
        if match_app_id_pattern:
            logging.info("Replacing appid with %s" % settings.app_id_dict[settings.BUILD_NAME])
            dst_file.write("application: %s\n" % settings.app_id_dict[settings.BUILD_NAME])
        elif match_version_pattern:
            logging.info("Replacing version with %s" % settings.VERSION_ID)
            dst_file.write("version: %s\n" % settings.VERSION_ID )
        elif match_static_dir_pattern:
            line = "%s%s%s\n" % (match_static_dir_pattern.group(1), settings.LIVE_STATIC_DIR, match_static_dir_pattern.group(3))
            logging.info("Writing %s" % line)
            dst_file.write(line)
        elif match_proprietary_static_dir_pattern:
            line = "%s%s%s\n" % (match_proprietary_static_dir_pattern.group(1), settings.LIVE_PROPRIETARY_STATIC_DIR, match_proprietary_static_dir_pattern.group(3))
            logging.info("Writing %s" % line)
            dst_file.write(line)            
        elif match_flash_files_dir_pattern:
            line = "%s%s%s\n" % (match_flash_files_dir_pattern.group(1), settings.FLASH_FILES_DIR, match_flash_files_dir_pattern.group(3))
            logging.info("Writing %s" % line)
            dst_file.write(line)
        elif match_appstat_middleware_pattern:
            line = "%s%s\n" % (match_appstat_middleware_pattern.group(1), "on" if settings.ENABLE_APPSTATS else "off")
            logging.info("Writing: %s" % line)
            dst_file.write(line)
        else:
            dst_file.write(line)
    
    src_file.close()
    dst_file.close()
        

    pwd = os.getcwd()
    # remove any old static "generated" directories
    previous_auto_generated_dirs = glob.glob(pwd + "/rs/static/auto-generated-*")
    for remove_dir in previous_auto_generated_dirs:
        logging.info("Removing directory %s\n" % remove_dir)
        shutil.rmtree(remove_dir)
        
    if not settings.USE_TIME_STAMPED_STATIC_FILES:
        pass
        # If we are directly accessing the static directory, then we bypass all of the following code since 
        # it is un-necessary and slows down the startup
    else: 
        
        # copy the static dir into the auto-generated static dir
        source_static_dir = pwd + "/rs/static/" 
        logging.info("Copying %s to %s" % (source_static_dir, settings.LIVE_STATIC_DIR))
        shutil.copytree(source_static_dir, settings.LIVE_STATIC_DIR)
        
        if settings.PROPRIETARY_STATIC_DIR_EXISTS:
            # copy the proprietary files into the time-stammped "live" static directory
            # This method of copying/tracking proprietary files should be re-thought at some point in the future.  
            logging.info("Copying proprietary static files into the live static directory\n")
            copy_file_to_folder(pwd + "/rs/proprietary/static/css/*",  settings.LIVE_STATIC_DIR + "/css/")
            copy_file_to_folder(pwd + "/rs/proprietary/static/img/Discrete/*", settings.LIVE_STATIC_DIR + "/img/Discrete/")
            copy_file_to_folder(pwd + "/rs/proprietary/static/img/Friend/*", settings.LIVE_STATIC_DIR + "/img/Friend/")
            copy_file_to_folder(pwd + "/rs/proprietary/static/img/Gay/*", settings.LIVE_STATIC_DIR + "/img/Gay/")
            copy_file_to_folder(pwd + "/rs/proprietary/static/img/Language/*", settings.LIVE_STATIC_DIR + "/img/Language/")
            copy_file_to_folder(pwd + "/rs/proprietary/static/img/Lesbian/*", settings.LIVE_STATIC_DIR + "/img/Lesbian/")
            copy_file_to_folder(pwd + "/rs/proprietary/static/img/Single/*", settings.LIVE_STATIC_DIR + "/img/Single/")
            copy_file_to_folder(pwd + "/rs/proprietary/static/img/Swinger/*", settings.LIVE_STATIC_DIR + "/img/Swinger/")
            copy_file_to_folder(pwd + "/rs/proprietary/static/js/*", settings.LIVE_STATIC_DIR + "/js/")
        
        # Modify the jquery.fancybox file so that AlphaImageLoader files use the correct path to the
        # image files -- this is necessary because relative paths do not work correctly inside of the AlphaImageLoader call
        alpha_image_loader_pattern = re.compile(r'(.*)(rs/static/img)(.*)')
        orig = settings.LIVE_STATIC_DIR + "/css/jquery.fancybox-1.3.4.css"
        modified = src + ".new"
        orig_file = codecs.open(orig, encoding='ascii')
        modified_file = codecs.open(modified, 'w', encoding='ascii')
        for line in orig_file:
            match_alpha_image_loader_pattern = alpha_image_loader_pattern.match(line)
            if match_alpha_image_loader_pattern:
                modified_file.write("%s%s%s\n" % (match_alpha_image_loader_pattern.group(1),
                                             settings.LIVE_STATIC_DIR + "/img", 
                                             match_alpha_image_loader_pattern.group(3)))
            else:
                modified_file.write(line)
                
        orig_file.close()
        modified_file.close()
        
        # over-write the source file since it is no longer needed, and was a copy of the original anyway
        # move the destination over the source
        shutil.move(modified, orig)
        
        
def generate_time_stamped_static_files():   
    # create the "combined" css and js files 
    if settings.USE_TIME_STAMPED_STATIC_FILES:
        create_combined_static_file("import_main_css_and_js.html", "combined_css", "css")        
        create_combined_static_file("import_main_css_and_js.html", "combined_js", "js")     
    
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
    input_html_src = "rs/templates/user_main_helpers/import_main_css_and_js.html"
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