#!/usr/bin/python

# Before executing the original manage.py code, we first setup the customized app.yaml file,
# and generate the custom static directories, as well as the minimized javascript and css files. 
import build_helpers
import sys, logging, datetime
import site_configuration

logging.getLogger().setLevel(logging.DEBUG)

if "skip_build" in sys.argv:
    # In some very limited cases, we may wish to skip the building of the css/javascript/etc.
    # This was originally (and perhaps only ever) used for debugging the build scripts.
    print  "Found skip_build"
    sys.argv = filter(lambda a: a != "skip_build", sys.argv) # remove the skip_build from the argv
    print "new argv = %s" % sys.argv
    
else:
    build_helpers.customize_files()
    
    logging.info( "**********************************************************************"    )
    logging.info( "Executing: %s (Build: %s)" % (site_configuration.APP_NAME, site_configuration.BUILD_NAME))
    logging.info( "%s" % datetime.datetime.now() )
    logging.info( "**********************************************************************")


# Original manage.py code starts here
try:
    import settings # Assumed to be in the same directory.
except ImportError:
    import sys
    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
    sys.exit(1)

from django.core.management import execute_manager

if __name__ == "__main__":
    # Execute the program
    execute_manager(settings)

        