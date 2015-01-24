This is a reference implementation of SOPG web service clients. There are separate clients for different kinds of users:
- SOPGClassicMerchantClient - supports all classic merchant functionallity with following methods
  - createDisposition
  - assignCardToDisposition
  - assignCardsToDisposition
  - modifyDispositionValue
  - getSerialNumbers
  - getDispositionRawState
  - executeDebit
  - getMid

All methods contain basic verification of required parameters and do not execute a web service call if the required parameters are not valid (for detailed information refer to in code comments).

To build and run the code Python version 2.7.1 is required. To execute web service calls suds (https://fedorahosted.org/suds/) library must be present. To execute the provided unit tests pyAnt tasks (http://code.google.com/p/pyanttasks/) is required. For displaying results of the tests in browser XmlTestRunner (http://pypi.python.org/pypi/XmlTestRunner/0.1) is required.

The provided ant script is capable of building the client, as well as building and running the provided unit tests (results are stored in 'results' folder).