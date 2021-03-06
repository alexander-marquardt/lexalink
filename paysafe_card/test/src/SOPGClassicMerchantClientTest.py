import sys
import setup_sys_path_for_testing

import site_configuration

from SOPGClassicMerchantClient import SOPGClassicMerchantClient

import unittest
import time
import urllib

from rs.proprietary import my_private_data

# The following logging and filter are used for turning on logging in suds
import logging
handler = logging.StreamHandler(sys.stderr)
logger = logging.getLogger('suds.transport.http')
logger.setLevel(logging.DEBUG), handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

class OutgoingFilter(logging.Filter):
    def filter(self, record):
        return record.msg.startswith('sending:')

handler.addFilter(OutgoingFilter())

notification_host = 'http://paysafecard.romancesapp.appspot.com'

# The following is our Google Compute Engine proxy that will handle all communications with Paysafecard's servers
# See https://console.developers.google.com/project/lexabit-proxy
endpoint = my_private_data.PAYSAFE_ENDPOINT

# We load the wsdl from our servers.
# For testing purposes we can generally load from localhost, as long as we
# are running a webserver locally. For release application, it is better to get the hostname from
# request.META.HTTP_HOST if possible.
wsdl_url = endpoint + '?wsdl'

username = 'Lexabit_Inc_test'
password = 'uOLSLoFmktH7DyB'
currency = 'EUR'
amount = 0.01
mid = '1000005878'
ok_url = urllib.quote(notification_host + '/psc/okurl/', '')
nok_url = urllib.quote(notification_host + '/psc/nokurl/', '')
pn_url = urllib.quote(notification_host + '/paysafecard/payment_notification_from_unittest/', '')
merchant_client_id = 'foobartesting-id-1'
client_ip = None # This will be set once we get farther along into the paysafe integration

class TestSOPGClassicMerchantClient(unittest.TestCase):

    def setUp(self):
        self.mtid = 'unit-testing-id-' + str(time.time())
        self.client = SOPGClassicMerchantClient(wsdl_url, endpoint)


    def test_02_CreateDisposition(self):
        response = self.createDisposition()

        self.assertEqual(response['errorCode'], 0)
        self.assertEqual(response['resultCode'], 0)


    def createDisposition(self):
        createDisposition = self.client.createDisposition
        return createDisposition(
            username,
            password,
            self.mtid,
            None,
            amount,
            currency,
            ok_url,
            nok_url,
            merchant_client_id,
            pn_url,
            client_ip,
        )


    if __name__ == '__main__':
        unittest.main()
