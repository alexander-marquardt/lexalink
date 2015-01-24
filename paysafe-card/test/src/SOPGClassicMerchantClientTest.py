import sys
import setup_sys_path_for_testing

from SOPGClassicMerchantClient import SOPGClassicMerchantClient

import unittest
import time


class TestSOPGClassicMerchantClient(unittest.TestCase):



  def setUp(self):
    self.mtid = time.time()

  def testSOPGClassicMerchantClient(self):
    try:
      client = SOPGClassicMerchantClient(self.params['endpoint'])
    except Exception as e:
      print ('Error creating SOAP client: ', e)
      self.assertTrue(False)
    else:
      self.assertTrue(True)

  def testCreateDisposition(self):
    client = SOPGClassicMerchantClient(self.params['endpoint'])
    response = self.createDisposition(client)

    self.assertEqual(response['errorCode'], 0)
    self.assertEqual(response['resultCode'], 0)

  def testAssignCardToDisposition(self):
    client = SOPGClassicMerchantClient(self.params['endpoint'])
    self.createDisposition(client)
    response = self.assignCardToDisposition(client)

    self.assertEqual(response['errorCode'], 0)  
    self.assertEqual(response['resultCode'], 0)

  def testAssignCardsToDisposition(self):
    client = SOPGClassicMerchantClient(self.params['endpoint'])
    self.createDisposition(client)
    
    response = self.assignCardsToDisposition(client)
    
    self.assertEqual(response['errorCode'], 0)  
    self.assertEqual(response['resultCode'], 0)

  def testModifyDispositionValue(self):
    client = SOPGClassicMerchantClient(self.params['endpoint'])
    self.createDisposition(client)
    self.assignCardToDisposition(client)
    response = client.modifyDispositionValue(
                                 self.params['username'],
                                 self.params['password'], 
                                 self.mtid, 
                                 None, 
                                 self.params['amount'],
                                 self.params['currency'],
         )
    self.assertEqual(response['errorCode'], 0)
    self.assertEqual(response['resultCode'], 0)

  def testGetSerialNumbers(self):
    client = SOPGClassicMerchantClient(self.params['endpoint'])
    self.createDisposition(client)
    response = client.getSerialNumbers(
                                 self.params['username'],
                                 self.params['password'], 
                                 self.mtid, 
                                 None, 
                                 self.params['currency'],
         )
    self.assertEqual(response['errorCode'], 0)
    self.assertEqual(response['resultCode'], 0)

  def testGetDispositionRawState(self):
    client = SOPGClassicMerchantClient(self.params['endpoint'])
    self.createDisposition(client)
    response = client.getDispositionRawState(
                                 self.params['username'],
                                 self.params['password'], 
                                 self.mtid, 
                                 None, 
                                 self.params['currency'],
         )
    self.assertEqual(response['errorCode'], 0)
    self.assertEqual(response['resultCode'], 0)

  def testExecuteDebit(self):
    client = SOPGClassicMerchantClient(self.params['endpoint'])
    self.createDisposition(client)
    self.assignCardToDisposition(client)
    response = client.executeDebit(
                                 self.params['username'],
                                 self.params['password'], 
                                 self.mtid, 
                                 None, 
                                 self.params['amount'],
                                 self.params['currency'],
                                 1,
                                 None
         )
    self.assertEqual(response['errorCode'], 0)
    self.assertEqual(response['resultCode'], 0)
  
  def testGetMid(self):
    client = SOPGClassicMerchantClient(self.params['endpoint'])
    response = client.getMid(
                                 self.params['username'],
                                 self.params['password'], 
                                 self.params['currency'],
         )
    self.assertEqual(response['errorCode'], 0)
    self.assertEqual(response['resultCode'], 0)

  def createDisposition(self, client):
    return client.createDisposition(
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

  def assignCardToDisposition(self, client):
    return client.assignCardToDisposition(
                                 self.params['username'],
                                 self.params['password'], 
                                 self.mtid, 
                                 None, 
                                 self.params['amount'],
                                 self.params['currency'],
                                 self.params['pin'],
         )

  def assignCardsToDisposition(self, client):
    return client.assignCardsToDisposition(
                                self.params['username'],
                                self.params['password'],
                                self.mtid,
                                None,
                                self.params['amount'],
                                self.params['currency'],
                                None,
                                1,
                                self.cards)

  params = {
                'endpoint' : 'https://soatest.paysafecard.com/psc/services/PscService?wsdl', 
                'username' : 'USER_CLASSIC',
                'password' : 'PASS',
                'currency' : 'EUR',
                'amount' : 0.01,
                'okUrl' : 'http://okurl',
                'nokUrl' : 'http://nokurl',
                'pin' : '5000000000002517',
                'mid' : '1000001243',
                'serialNumber' : '5000000000002517;0.01',
                'dispositionState' : 'S',
        }
  
  card1 = {}
  card1['pin']='5000000000002517'
  card2 = {}
  card2['pin']='5000000000002511'
  cards = [card1, card2]

  if __name__ == '__main__':
    unittest.main()
