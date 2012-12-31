#!/Users/alexandermarquardt/venv2.7/bin/python

import sys, subprocess, datetime
import build_helpers, settings

build_helpers.customize_files()

print "\n**********************************************************************"    
print "Executing: %s (Build: %s)" % (settings.APP_NAME, settings.BUILD_NAME)
print "%s" % datetime.datetime.now()
print "**********************************************************************\n"

additional_args = sys.argv[1:]
pargs = ['./manage.py', 'runserver'] + additional_args
print "Process args = %s" % pargs

process = subprocess.call(pargs,  stderr=subprocess.STDOUT)

sys.exit(0)