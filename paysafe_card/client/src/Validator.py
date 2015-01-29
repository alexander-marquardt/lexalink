
class Validator(object):
  # Returns OK if result code and error code are both 0, ERROR otherwise.
  def checkResult(result):
    return 'OK' if result['resultCode'] == 0 and result['errorCode'] == 0 else 'ERROR'

  # Raises ValueError if parameter is null or empty
  def validateStringNotNull(param, paramName):
    if param == None or param == '':
      raise ValueError(paramName + ' is a required parameter.')

  # Raises ValueError if currency is null or not 3 chars
  def validateCurrency(currency):
    if currency == None or len(currency) != 3:
      raise ValueError('currency is a required parameter. It must contain a 3 letter ISO 4217 currency code.')
  
  # Raises ValueError if no cards are specified, or if cards contain null values
  def validateCards(cards):
    if cards == None or len(cards) < 1:
      raise ValueError('At least one card is required.')
    for card in cards:
      if card == None:
        raise ValueError('Cards is a required parameter and should not contain null values.')
      pin = card['pin']
      if pin == None or pin == '':
        raise ValueError('pin is a required parameter')

  checkResult = staticmethod(checkResult)
  validateStringNotNull = staticmethod(validateStringNotNull)
  validateCurrency = staticmethod(validateCurrency)
  validateCards = staticmethod(validateCards)
