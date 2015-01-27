import sys
import setup_sys_path_for_testing

import site_configuration

from SOPGClassicMerchantClient import SOPGClassicMerchantClient

import unittest
import time
import urllib

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

# The following is our Google Compute Engine proxy that will handle all communications with Paysafecard's servers
# See https://console.developers.google.com/project/lexabit-proxy
endpoint = 'https://130.211.134.3/psc/services/PscService'

# We load the wsdl from our servers.
# For testing purposes we can generally load from localhost, as long as we
# are running a webserver locally. For release application, it is better to get the hostname from
# request.META.HTTP_HOST if possible.
wsdl_url = 'http://localhost:8000/paysafecard/sopg_wsdl.xml'

username = 'Lexabit_Inc_test'
password = 'uOLSLoFmktH7DyB'
currency = 'EUR'
mid = '1000005878'
ok_url = urllib.quote('http://www.%s/psc/okurl/' % site_configuration.DOMAIN_NAME, '')
nok_url = urllib.quote('http://www.%s/psc/nokurl/' % site_configuration.DOMAIN_NAME, '')
pn_url = urllib.quote('http://www.%s/paysafe/ipn/' % site_configuration.DOMAIN_NAME, '')
client_ip = None # This will be set once we get farther along into the paysafe integration

card_pin = '8691159531990439'
card_serial_number = '8691159531990439'



class TestSOPGClassicMerchantClient(unittest.TestCase):



    def setUp(self):
        self.mtid = 'temporary-testing-id-' + str(time.time())
        self.client = SOPGClassicMerchantClient(wsdl_url, self.params['endpoint'])

    # def test_01_SOPGClassicMerchantClient(self):
    #     try:
    #         pass
    #     except Exception as e:
    #         print ('Error creating SOAP client: ', e)
    #         self.assertTrue(False)
    #     else:
    #         self.assertTrue(True)

    def test_02_CreateDisposition(self):
        response = self.createDisposition()

        self.assertEqual(response['errorCode'], 0)
        self.assertEqual(response['resultCode'], 0)

    # def test_03_AssignCardToDisposition(self):
    #     self.createDisposition()
    #     response = self.assignCardToDisposition()
    #
    #     self.assertEqual(response['errorCode'], 0)
    #     self.assertEqual(response['resultCode'], 0)
    #
    # def test_04_AssignCardsToDisposition(self):
    #     self.createDisposition()
    #
    #     response = self.assignCardsToDisposition()
    #
    #     self.assertEqual(response['errorCode'], 0)
    #     self.assertEqual(response['resultCode'], 0)
    #
    # def test_05_ModifyDispositionValue(self):
    #     self.createDisposition()
    #     self.assignCardToDisposition()
    #     response = self.client.modifyDispositionValue(
    #         self.params['username'],
    #         self.params['password'],
    #         self.mtid,
    #         None,
    #         self.params['amount'],
    #         self.params['currency'],
    #         )
    #     self.assertEqual(response['errorCode'], 0)
    #     self.assertEqual(response['resultCode'], 0)
    #
    # def test_06_GetSerialNumbers(self):
    #     self.createDisposition()
    #     response = self.client.getSerialNumbers(
    #         self.params['username'],
    #         self.params['password'],
    #         self.mtid,
    #         None,
    #         self.params['currency'],
    #         )
    #     self.assertEqual(response['errorCode'], 0)
    #     self.assertEqual(response['resultCode'], 0)
    #
    # def test_07_GetDispositionRawState(self):
    #     self.createDisposition()
    #     response = self.client.getDispositionRawState(
    #         self.params['username'],
    #         self.params['password'],
    #         self.mtid,
    #         None,
    #         self.params['currency'],
    #         )
    #     self.assertEqual(response['errorCode'], 0)
    #     self.assertEqual(response['resultCode'], 0)
    #
    # def test_08_ExecuteDebit(self):
    #     self.createDisposition()
    #     self.assignCardToDisposition()
    #     response = self.client.executeDebit(
    #         self.params['username'],
    #         self.params['password'],
    #         self.mtid,
    #         None,
    #         self.params['amount'],
    #         self.params['currency'],
    #         1,
    #         None
    #     )
    #     self.assertEqual(response['errorCode'], 0)
    #     self.assertEqual(response['resultCode'], 0)
    #
    # def test_09_GetMid(self):
    #     response = self.client.getMid(
    #         self.params['username'],
    #         self.params['password'],
    #         self.params['currency'],
    #         )
    #     self.assertEqual(response['errorCode'], 0)
    #     self.assertEqual(response['resultCode'], 0)

    def createDisposition(self):
        createDisposition = self.client.createDisposition
        return createDisposition(
            self.params['username'],
            self.params['password'],
            self.mtid,
            None,
            self.params['amount'],
            self.params['currency'],
            self.params['okUrl'],
            self.params['nokUrl'],
            None,None,None
        )

    def assignCardToDisposition(self):
        assignCardToDisposition = self.client.assignCardToDisposition
        return assignCardToDisposition(
            self.params['username'],
            self.params['password'],
            self.mtid,
            None,
            self.params['amount'],
            self.params['currency'],
            self.params['pin'],
            )

    def assignCardsToDisposition(self):
        return self.client.assignCardsToDisposition(
            self.params['username'],
            self.params['password'],
            self.mtid,
            None,
            self.params['amount'],
            self.params['currency'],
            None,
            1,
            self.cards)

    # params = {
    #               'endpoint' : 'https://soatest.paysafecard.com/psc/services/PscService?wsdl',
    #               'username' : 'USER_CLASSIC',
    #               'password' : 'PASS',
    #               'currency' : 'EUR',
    #               'amount' : 0.01,
    #               'okUrl' : 'http://okurl',
    #               'nokUrl' : 'http://nokurl',
    #               'pin' : '5000000000002517',
    #               'mid' : '1000001243',
    #               'serialNumber' : '5000000000002517;0.01',
    #               'dispositionState' : 'S',
    #       }

    params = {
        'endpoint' : endpoint,
        'username' : username,
        'password' : password,
        'currency' : currency,
        'amount' : 0.01,
        'okUrl' : ok_url,
        'nokUrl' : nok_url,
        'pin' : card_pin,
        'mid' : mid,
        'serialNumber' : '%s;0.01' % card_serial_number,
        'dispositionState' : 'S',
        }

    card1 = {}
    card1['pin']= card_pin
    card2 = {}
    card2['pin']='5000000000002511'
    cards = [card1, card2]

    if __name__ == '__main__':
        unittest.main()
