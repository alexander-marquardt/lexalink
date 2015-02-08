import settings
import logging
import re

from django import http

main_domain_pattern = re.compile(r'.*?\.*([^\.]*)\.appspot\.com$')

class RedirectAppspotURLs(object):
    """
    Middleware that redirects anyone attempting to access our site at appspot.com to the real domain that
    they should be using. If this needs to be disabled, then have a look at the settings.py file to see
    how this middleware is being included and set REDIRECT_APPSPOT_URL to True or False.
    """
    def __init__(self):
        pass

    def process_request(self, request):
        host = request.META['HTTP_HOST']
        if 'appspot' in host:
            # if we running are on appspot, then redirect to the real domain
            try:
                appid = main_domain_pattern.match(host).group(1)
                logging.info('appid is %s' % appid)
                if request.META.get("QUERY_STRING", ""):
                    path = "%s?%s" % (request.path_info,
                            request.META['QUERY_STRING'])
                else:
                    path = request.path_info

                build_name = settings.redirect_app_id_dict[appid]
                domain_name = settings.domain_name_dict[build_name]

                redirect_address = 'http://www.' + domain_name + path
                logging.info('redirecting to %s' % redirect_address)
                return http.HttpResponsePermanentRedirect(redirect_address)

            except:
                logging.error('unable to redirect URL from host %s' % host)