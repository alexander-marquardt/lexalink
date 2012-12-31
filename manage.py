#!/usr/bin/env python
from django.core.management import execute_manager
import sys, logging

try:
    import settings # Assumed to be in the same directory.
except ImportError:
    import sys
    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
    sys.exit(1)


    
import build_helpers
    
if __name__ == "__main__":
    
    do_setup = True
    if "-no_setup" in sys.argv:
        
        if not settings.USE_TIME_STAMPED_STATIC_FILES:
            sys.stderr.write("*** -no_setup is not compatible with USE_TIME_STAMPED_STATIC_FILES=False ***\n")
            exit(1)
            
        do_setup = False
        sys.stderr.write("*** Not running setup *****\n")
        # remove the "-no_setup" from the argv
        del sys.argv[sys.argv.index("-no_setup")]
        
        
    logging.info("Calling setup_my_local_environment")
    build_helpers.setup_my_local_environment()
    
    build_helpers.check_that_minimized_javascript_files_are_enabled()
    
    logging.info("Copying index file")    
    build_helpers.generate_index_files()

    if do_setup:
        logging.info("Calling generate_time_stamped_static_files")        
        # This is a call that I have added in, which will set up static files, time-stamped static directories, etc.
        build_helpers.generate_time_stamped_static_files()
    
    if  sys.argv[1] == "-setup_only":
        # Do not run the program - this call was for setting up environment and nothing more
        pass
    else:
        # Execute the program
        execute_manager(settings)

        