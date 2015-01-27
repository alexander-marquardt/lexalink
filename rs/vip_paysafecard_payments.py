import logging

from django.shortcuts import render_to_response
from django import http

from rs import error_reporting

def paysafecard_sopg_wsdl(request):
    try:
        http_response = render_to_response("paysafecard_wsdl.xml", {})

        return http_response
    except:
        error_reporting.log_exception(logging.critical)
        return http.HttpResponseServerError('Error accessing paysafecard_wsdl.xml document')