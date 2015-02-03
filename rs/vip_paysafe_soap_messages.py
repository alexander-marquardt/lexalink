import urllib2
import re
import logging

from string import Template
import settings


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

disposition_keys_pattern = {}
for key in disposition_expected_keys:
    disposition_keys_pattern[key] = re.compile(r'.*<ns1:%(key)s>(.*)</ns1:%(key)s>' % {'key': key})

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
    headers = {
        'Content-Type': 'application/soap+xml; charset=utf-8'
    }
    soap_data = DISPOSITION_TEMPLATE.substitute(template_dict)
    request = urllib2.Request(settings.PAYSAFE_ENDPOINT, soap_data, headers)
    response = urllib2.urlopen(request)
    soap_response = response.read()

    response_dict = {}

    for key in disposition_expected_keys:
        response_dict[key] = disposition_keys_pattern[key].match(soap_response).group(1)

    return response_dict