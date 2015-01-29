import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), './../../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), './../../../appengine_suds/')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), './../../client/src')))
sys.path.insert(0, '/usr/local/google_appengine/')
import dev_appserver
dev_appserver.fix_sys_path()
