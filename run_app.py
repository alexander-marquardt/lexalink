#!/usr/bin/python

from subprocess import call
call(['python', './manage.py', 'runserver', 'localhost:8000']) 

# Where localhost:8000 is optional, and simply defines the name/IP address and port that you will be running your local server at - if you do not enter a value, then the default is localhost:8000.

# Browse to http://localhost:8000 (or the value that you have defined) to view your website running on the local/development server.

