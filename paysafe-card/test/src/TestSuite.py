import sys
sys.path.append('.\..\..\client\src')

import unittest
from SOPGClassicMerchantClientTest import TestSOPGClassicMerchantClient
from xmlrunner import XMLTestRunner

suite1 = unittest.TestLoader().loadTestsFromTestCase(TestSOPGClassicMerchantClient)
alltests = unittest.TestSuite([suite1])

#unittest.TextTestRunner(verbosity=2).run(alltests)
XMLTestRunner().run(alltests)
#sopgSuite = unittest.TestSuite()
#sopgSuite.addTest(SOPGClassicMerchantClientTest('test_default_size'))
#sopgSuite.addTest(WidgetTestCase('test_resize'))

