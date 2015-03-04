import urllib2
import re
import logging

from string import Template
import settings


def generate_patter_dict_for_pulling_keys_from_response(expected_keys_list):
    keys_pattern = {}
    for key in expected_keys_list:
        keys_pattern[key] = re.compile(r'.*<ns1:%(key)s>(.*)</ns1:%(key)s>' % {'key': key})

    return keys_pattern


DISPOSITION_TEMPLATE = Template("""
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
xmlns:urn="urn:pscservice">
<soapenv:Header/>
<soapenv:Body>
<urn:createDisposition>
<urn:username>$username</urn:username>
<urn:password>$password</urn:password>
<urn:mtid>$merchant_transaction_id</urn:mtid>
<!--Zero or more repetitions:-->
<urn:subId></urn:subId>
<urn:amount>$amount</urn:amount>
<urn:currency>$currency_code</urn:currency>
<urn:okUrl>$ok_url</urn:okUrl>
<urn:nokUrl>$nok_url</urn:nokUrl>
<!--Optional:-->
<urn:merchantclientid>$merchant_client_id</urn:merchantclientid>
<!--Optional:-->
<urn:pnUrl>$pn_url</urn:pnUrl>
<!--Zero or more repetitions:-->
<urn:dispositionRestrictions>
<urn:key></urn:key>
<urn:value></urn:value>
</urn:dispositionRestrictions>
<urn:dispositionRestrictions>
<urn:key></urn:key>
<urn:value></urn:value>
</urn:dispositionRestrictions>
<!--Optional:-->
<urn:shopId></urn:shopId>
<!--Optional:-->
<urn:shopLabel></urn:shopLabel>
</urn:createDisposition>
</soapenv:Body>
</soapenv:Envelope>
""")

disposition_expected_keys = ['errorCode', 'resultCode', 'mid', 'mtid']
disposition_keys_pattern = generate_patter_dict_for_pulling_keys_from_response(disposition_expected_keys)

if settings.TESTING_PAYSAFECARD:
    paysafe_endpoint = settings.PAYSAFE_TEST_ENDPOINT
else:
    paysafe_endpoint = settings.PAYSAFE_ENDPOINT

def get_soap_response(template_string, template_dict):

    logging.info('Contacting endpoint: %s' % paysafe_endpoint)
    headers = {
        'Content-Type': 'application/soap+xml; charset=utf-8'
    }
    soap_data = template_string.substitute(template_dict)
    request = urllib2.Request(paysafe_endpoint, soap_data, headers)
    response = urllib2.urlopen(request)
    soap_response = response.read()
    logging.info('soap_response is: %s' % soap_response)
    return soap_response

def parse_soap_response(soap_response, expected_keys, expected_keys_pattern):
    response_dict = {}

    for key in expected_keys:
        response_dict[key] = expected_keys_pattern[key].match(soap_response).group(1)

    return response_dict

def create_disposition(
            username,
            password,
            merchant_transaction_id,
            amount,
            currency_code,
            ok_url,
            nok_url,
            merchant_client_id,
            pn_url):

    template_dict = locals()
    soap_response = get_soap_response(DISPOSITION_TEMPLATE, template_dict)
    response_dict = parse_soap_response(soap_response, disposition_expected_keys, disposition_keys_pattern)

    return response_dict


EXECUTE_DEBIT_TEMPLATE = Template("""
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
xmlns:urn="urn:pscservice">
<soapenv:Header/>
<soapenv:Body>
<urn:executeDebit>
<urn:username>$username</urn:username>
<urn:password>$password</urn:password>
<urn:mtid>$merchant_transaction_id</urn:mtid>
<!--Zero or more repetitions:-->
<urn:subId></urn:subId>
<urn:amount>$transaction_amount</urn:amount>
<urn:currency>$transaction_currency</urn:currency>
<urn:close>$close_transaction</urn:close>
</urn:executeDebit>
</soapenv:Body>
</soapenv:Envelope>
""")

execute_debit_expected_keys = ['errorCode', 'resultCode', 'mtid']
execute_debit_keys_pattern = generate_patter_dict_for_pulling_keys_from_response(execute_debit_expected_keys)

def execute_debit(username,
                  password,
                  merchant_transaction_id,
                  transaction_amount,
                  transaction_currency,
                  close_transaction):

    template_dict = locals()
    soap_response = get_soap_response(EXECUTE_DEBIT_TEMPLATE, template_dict)
    response_dict = parse_soap_response(soap_response, execute_debit_expected_keys, execute_debit_keys_pattern)

    return response_dict

get_serial_numbers_expected_keys = ['errorCode', 'resultCode', 'mtid', 'amount', 'currency', 'dispositionState', 'serialNumbers']
get_serial_numbers_keys_pattern = generate_patter_dict_for_pulling_keys_from_response(get_serial_numbers_expected_keys)

GET_SERIAL_NUMBERS_TEMPLATE = Template("""
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
xmlns:urn="urn:pscservice">
<soapenv:Header/>
<soapenv:Body>
<urn:getSerialNumbers>
<urn:username>$username</urn:username>
<urn:password>$password</urn:password>
<urn:mtid>$merchant_transaction_id</urn:mtid>
<!--Zero or more repetitions:-->
<urn:subId></urn:subId>
<urn:currency>$transaction_currency</urn:currency>
</urn:getSerialNumbers>
</soapenv:Body>
</soapenv:Envelope>
""")

def get_serial_numbers(username,
                       password,
                       merchant_transaction_id,
                       transaction_currency):

    # Passed in arguments are copied into the template_dict by accessing locals()
    template_dict = locals() # copy all of the arguments
    soap_response = get_soap_response(GET_SERIAL_NUMBERS_TEMPLATE, template_dict)
    response_dict = parse_soap_response(soap_response, get_serial_numbers_expected_keys, get_serial_numbers_keys_pattern)

    return response_dict