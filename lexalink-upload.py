#!/usr/bin/python
################################################################################
# This is an upload script for lexalink. It should be run *after* prepare-lexalink.py
# has already setup lexalink-upload (grunt etc.) folders for each website.
#
# This fils should be run from within each build's customized directory.
################################################################################

import datetime, sys, subprocess, os, datetime, traceback

print "importing site_configuration and build_helpers from %s" % os.getcwd()
sys.path.insert(0, os.getcwd())
# import site_configuration and build_helpers from the local "lexalink-uploads" build's directory.
try:
    import site_configuration, build_helpers

except Exception, e:
    print "Error: %s\n%s\n" % (str(e), traceback.format_exc())
    print "If you are trying to upload multiple builds, make sure that you have first run build-lexalink.py, and then use batch-upload-lexalink.py to upload"
    sys.exit(1)

UPLOAD_DONE_SEMAPHORE_FILE = "./upload_done.txt"

if "--force" in sys.argv:
    force_upload = True
    sys.argv = filter(lambda a: a != "--force", sys.argv)
else:
    force_upload = False
    

# check that the lexalink-uploads current build is configured correctly for running on the server.
build_helpers.check_site_configuration()

if os.path.isfile(UPLOAD_DONE_SEMAPHORE_FILE) and not force_upload:
    # Do not upload again
    print "This build has already been uploaded. "
    print "Remove %s before uploading again." % UPLOAD_DONE_SEMAPHORE_FILE
    print "Or run with --force argument if you want re-upload the same build"

else:
        
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
    
    print "**********************************************************************"
    print "Finisehd upload %s (Build: %s)" % (site_configuration.APP_NAME, site_configuration.BUILD_NAME)
    print "%s" % datetime.datetime.now()
    print "**********************************************************************\n"
    
    print "Writing %s" % UPLOAD_DONE_SEMAPHORE_FILE
    f = open(UPLOAD_DONE_SEMAPHORE_FILE, "w")
    f.write("Last upload completed: %s" % datetime.datetime.now())
    f.close()
    

sys.exit(0)

