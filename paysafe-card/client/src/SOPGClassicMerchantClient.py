
from appengine_suds import suds
from Validator import Validator

class SOPGClassicMerchantClient:

  def __init__(self, endpoint):
    self.client  = suds.client.Client(endpoint + '?wsdl')

    # The following line over-rides the location in the returned wsdl document to point to our
    # proxy server. The value that is over-written is originally
    # location="https://soatest.paysafecard.com/psc/services/PscService"/, and will become
    # location=[endpoint]
    self.client.wsdl.services[0].setlocation(endpoint)

  """ Calls the CreateDisposition web service method.
  * 
  * @param username
  *          Username to use for the web service call.
  * @param password
  *          Password to use for the web service call.
  * @param mtid
  *          Merchant transaction id to use for the web service call. It must
  *          be unique for each invocation.
  * @param subId
  *          SubId to use for the web service call. The parameter is optional
  *          and can be <code>null</code>.
  * @param amount
  *          Amount to use for the web service call.
  * @param currency
  *          Currency to use for the web service call. It must contain a 3
  *          letter ISO 4217 currency code.
  * @param okUrl
  *          OKUrl to use for the web service call.
  * @param nokUrl
  *          NOKurl to use for the web service call.
  * @param merchantClientId
  *          ID of the client to use for the web service call. This is
  *          merchant's internal id to identify the client. The parameter is
  *          optional and can be <code>null</code>.
  * @param pnUrl
  *          Payment notification URL to use for the web service call. The 
  *          parameter is optional and can be <code>null</code>.
  * @param clientIp
  *          IP address of the client to use for the web service call. This is
  *          the IP of the client when connecting to the merchant. The
  *          parameter is optional and can be <code>null</code>.
  * @return Response of the CreateDisposition web service call. The call was
  *         successful if resultCode and errorCode of the response are 0. For
  *         list of possible error codes refer to merchant documentation.
  * @throws ValueError
  *           If required parameters are null or empty.
  """
  def createDisposition(self, username, password, mtid, subId, amount, currency, okUrl, nokUrl, clientIp, merchantClientId, pnUrl):
    Validator.validateStringNotNull(username, 'username')
    Validator.validateStringNotNull(password, 'password')
    Validator.validateStringNotNull(mtid, 'mtid')
    Validator.validateStringNotNull(okUrl, 'okUrl')
    Validator.validateStringNotNull(nokUrl, 'nokUrl')
    Validator.validateCurrency(currency)
    return self.client.service.createDisposition(username, password, mtid, subId, amount, currency.upper(), okUrl, nokUrl, merchantClientId, pnUrl, clientIp)

  """
  * Calls the AssignCardToDisposition web service method.
  * 
  * @param username
  *          Username to use for the web service call.
  * @param password
  *          Password to use for the web service call.
  * @param mtid
  *          Merchant transaction id to use for the web service call. It must
  *          be unique for each invocation.
  * @param subId
  *          SubId to use for the web service call. The parameter is optional
  *          and can be <code>null</code>.
  * @param amount
  *          Amount to use for the web service call.
  * @param currency
  *          Currency to use for the web service call. It must contain a 3
  *          letter ISO 4217 currency code.
  * @param pin
  *          PIN number to use for the web service call.
  * @return Response of the AssignCardToDisposition web service call. The call
  *         was successful if resultCode and errorCode of the response are 0.
  *         For list of possible error codes refer to merchant documentation.
  * @throws ValueError
  *           If required parameters are null or empty.
  """
  def assignCardToDisposition(self, username, password, mtid, subId, amount, currency, pin):
    Validator.validateStringNotNull(username, 'username')
    Validator.validateStringNotNull(password, 'password')
    Validator.validateStringNotNull(mtid, 'mtid')
    Validator.validateStringNotNull(pin, 'pin')
    Validator.validateCurrency(currency)
    return self.client.service.assignCardToDisposition(username, password, mtid, subId, amount, currency.upper(), pin)

  """
  * Calls the AssignCardsToDisposition web service method.
  * 
  * @param username
  *          Username to use for the web service call.
  * @param password
  *          Password to use for the web service call.
  * @param mtid
  *          Merchant transaction id to use for the web service call. It must
  *          be unique for each invocation.
  * @param subId
  *          SubId to use for the web service call. The parameter is optional
  *          and can be <code>null</code>.
  * @param amount
  *          Amount to use for the web service call.
  * @param currency
  *          Currency to use for the web service call. It must contain a 3
  *          letter ISO 4217 currency code.
  * @param cards
  *          Card information (pin, password) to use for the web service call.
  *          At least one (1) card and at most ten (10) cards can be present in
  *          the request. Card passwords are optional and should be
  *          <code>null</code> if no password is specified for the given card.
  * @param locale
  *          Locale to use for the web service call. The parameter is optional
  *          and can be <code>null</code>.
  * @param acceptingTerms
  *          Integer value indicating if the user accepts Paysafecard's terms
  *          of use. Value should be 1 if user accepts terms of use.
  * @return Response of the AssignCardToDisposition web service call. The call
  *         was successful if resultCode and errorCode of the response are 0.
  *         For list of possible error codes refer to merchant documentation.
  * @throws ValueError
  *           If required parameters are null or empty.
  """
  def assignCardsToDisposition(self, username, password, mtid, subId, amount, currency, locale, acceptingTerms, cards):
    Validator.validateStringNotNull(username, 'username')
    Validator.validateStringNotNull(password, 'password')
    Validator.validateStringNotNull(mtid, 'mtid')
    Validator.validateCurrency(currency)
    Validator.validateCards(cards)
    return self.client.service.assignCardsToDisposition(username, password, mtid, subId, amount, currency.upper(), locale, acceptingTerms, cards)


  """
  * Calls the ModifyDispositionValue web service method.
  * 
  * @param username
  *          Username to use for the web service call.
  * @param password
  *          Password to use for the web service call.
  * @param mtid
  *          Merchant transaction id to use for the web service call. It must
  *          be unique for each invocation.
  * @param subId
  *          SubId to use for the web service call. The parameter is optional
  *          and can be <code>null</code>.
  * @param amount
  *          Amount to use for the web service call.
  * @param currency
  *          Currency to use for the web service call. It must contain a 3
  *          letter ISO 4217 currency code.
  * @return Response of the ModifyDispositionValue web service call. The call
  *         was successful if resultCode and errorCode of the response are 0.
  *         For list of possible error codes refer to merchant documentation.
  * @throws ValueError
  *           If required parameters are null or empty.
  """
  def modifyDispositionValue(self, username, password, mtid, subId, amount, currency):
    Validator.validateStringNotNull(username, 'username')
    Validator.validateStringNotNull(password, 'password')
    Validator.validateStringNotNull(mtid, 'mtid')
    Validator.validateCurrency(currency)
    return self.client.service.modifyDispositionValue(username, password, mtid, subId, amount, currency.upper())

  """
  * Calls the GetSerialNumbers web service method.
  * 
  * @param username
  *          Username to use for the web service call.
  * @param password
  *          Password to use for the web service call.
  * @param mtid
  *          Merchant transaction id to use for the web service call. It must
  *          be unique for each invocation.
  * @param subId
  *          SubId to use for the web service call. The parameter is optional
  *          and can be <code>null</code>.
  * @param currency
  *          Currency to use for the web service call. It must contain a 3
  *          letter ISO 4217 currency code.
  * @return Response of the GetSerialNumbers web service call. The call was
  *         successful if resultCode and errorCode of the response are 0. For
  *         list of possible error codes refer to merchant documentation.
  * @throws ValueError
  *           If required parameters are null or empty.
  """
  def getSerialNumbers(self, username, password, mtid, subId, currency):
    Validator.validateStringNotNull(username, 'username')
    Validator.validateStringNotNull(password, 'password')
    Validator.validateStringNotNull(mtid, 'mtid')
    Validator.validateCurrency(currency)
    return self.client.service.getSerialNumbers(username, password, mtid, subId, currency.upper())

  """
  * Calls GetDispositionRawState web service method.
  * 
  * @param username
  *          Username to use for the web service call.
  * @param password
  *          Password to use for the web service call.
  * @param mtid
  *          Merchant transaction id to use for the web service call. It must
  *          be unique for each invocation.
  * @param subId
  *          SubId to use for the web service call. The parameter is optional
  *          and can be <code>null</code>.
  * @param currency
  *          Currency to use for the web service call. It must contain a 3
  *          letter ISO 4217 currency code.
  * @return Response of the GetDispositionRawState web service call. The call
  *         was successful if resultCode and errorCode of the response are 0.
  *         For list of possible error codes refer to merchant documentation.
  * @throws ValueError
  *           If required parameters are null or empty.
  """
  def getDispositionRawState(self, username, password, mtid, subId, currency):
    Validator.validateStringNotNull(username, 'username')
    Validator.validateStringNotNull(password, 'password')
    Validator.validateStringNotNull(mtid, 'mtid')
    Validator.validateCurrency(currency)
    return self.client.service.getDispositionRawState(username, password, mtid, subId, currency.upper())

  """
  * Calls ExecuteDebit web service method.
  * 
  * @param username
  *          Username to use for the web service call.
  * @param password
  *          Password to use for the web service call.
  * @param mtid
  *          Merchant transaction id to use for the web service call. It must
  *          be unique for each invocation.
  * @param subId
  *          SubId to use for the web service call. The parameter is optional
  *          and can be <code>null</code>.
  * @param amount
  *          Amount to use for the web service call.
  * @param currency
  *          Currency to use for the web service call. It must contain a 3
  *          letter ISO 4217 currency code.
  * @param close
  *          Close flag indicating if further debits will be executed or not.
  *          If the close flag is 1 the disposition will be set to totally
  *          consumed and no further debits are possible.
  * @param partialDebitId
  *          PartialDebitId to use for the web service call. The parameter is
  *          optional and can be <code>null</code>.
  * @ return Response of the ExecuteDebit web service call. The call was
  *          successful if resultCode and errorCode of the response are 0. For
  *          list of possible error codes refer to merchant documentation.
  * @throws ValueError
  *           If required parameters are null or empty.
  """
  def executeDebit(self, username, password, mtid, subId, amount, currency, close, partialDebitId):
    Validator.validateStringNotNull(username, 'username')
    Validator.validateStringNotNull(password, 'password')
    Validator.validateStringNotNull(mtid, 'mtid')
    Validator.validateCurrency(currency)
    return self.client.service.executeDebit(username, password, mtid, subId, amount, currency.upper(), close, partialDebitId)

  """
  * Calls the GetMid SOPG web service method.
  * 
  * @param username
  *          Username to use for the web service call.
  * @param password
  *          Password to use for the web service call.
  * @param currency
  *          Currency to use for the web service call. It must contain a 3
  *          letter ISO 4217 currency code.
  * @return Response containing mid configured for the given currency. The call
  *         was successful if resultCode and errorCode of the response are 0.
  *         For list of possible error codes refer to merchant documentation.
  * @throws ValueError
  *           If required parameters are null or empty.
  """
  def getMid(self, username, password, currency):
    Validator.validateStringNotNull(username, 'username')
    Validator.validateStringNotNull(password, 'password')
    Validator.validateCurrency(currency)
    return self.client.service.getMid(username, password, currency.upper())


