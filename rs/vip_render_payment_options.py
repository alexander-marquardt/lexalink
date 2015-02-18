import logging

from django.template import loader, Context

from rs import constants
from rs import error_reporting
from rs import utils
from rs import vip_payments_common
from rs import vip_paypal_payments
from rs import vip_paysafecard_payments

def render_payment_options(request, userobject):
    # Generates the radio buttons/submit buttons that will allow the user purchase a vip membership.

    # Note: do not pull the owner_nid from the request, since this page may be shown on the logout when then user has
    # already closed their session. Doing this gives us one last chance to get them to signup for a VIP membership.

    try:

        if constants.THIS_BUILD_ALLOWS_VIP_UPGRADES:
            # only show payment options/buttons to users that are logged-in.

            # Get the ISO 3155-1 alpha-2 (2 Letter) country code, which we then use for a lookup of the
            # appropriate currency to display. If country code is missing, then we will display
            # prices for the value defined in vip_paypal_structures.DEFAULT_CURRENCY
            if not vip_payments_common.TESTING_COUNTRY:
                http_country_code = request.META.get('HTTP_X_APPENGINE_COUNTRY', None)
                country_override = False
            else:
                error_reporting.log_exception(logging.error, error_message = "TESTING_COUNTRY is over-riding HTTP_X_APPENGINE_COUNTRY")
                http_country_code = vip_payments_common.TESTING_COUNTRY
                country_override = True

            # If user is VIP, then they will be offered a discounted price
            user_has_discount = utils.get_client_vip_status(userobject)
            user_has_discount_flag = vip_payments_common.USER_HAS_DISCOUNT_STRING if user_has_discount else vip_payments_common.USER_NO_DISCOUNT_STRING

            payments_common_data = {}
            payments_common_data['country_override'] = country_override
            payments_common_data['country_code'] = http_country_code
            payments_common_data['language'] = request.LANGUAGE_CODE
            payments_common_data['owner_nid'] = userobject.key.integer_id()
            payments_common_data['username'] = userobject.username
            payments_common_data['user_has_discount_flag'] = user_has_discount_flag
            paypal_data = vip_paypal_payments.generate_paypal_data(request, userobject, http_country_code, user_has_discount)
            paysafecard_data = vip_paysafecard_payments.generate_paysafecard_data(http_country_code, user_has_discount)
            template = loader.get_template("user_main_helpers/vip_payment_options.html")
            context = Context (dict({
                'payments_common_data': payments_common_data,
                'paypal_data': paypal_data,
                'paysafecard_data' : paysafecard_data,
                'request' : request,
                }, **constants.template_common_fields))
            return template.render(context)

        else:
            error_reporting.log_exception(logging.error, error_message="Why is render_payment_options called for a build that doesn't support VIP memberships?")
            return ''

    except:
        error_reporting.log_exception(logging.error)
        return ''
