import logging

from django.template import loader, Context

from rs import constants
from rs import error_reporting
from rs import vip_paypal_payments
from rs import vip_paysafecard_payments

def render_payment_options(request, username, owner_nid):
    # Generates the radio buttons/submit buttons that will allow the user purchase a vip membership.

    # Note: do not pull the owner_nid from the request, since this page may be shown on the logout when then user has
    # already closed their session. Doing this gives us one last chance to get them to signup for a VIP membership.

    try:

        if constants.THIS_BUILD_ALLOWS_VIP_UPGRADES:
            # only show payment options/buttons to users that are logged-in.

            paypal_data = vip_paypal_payments.generate_paypal_data(request, username, owner_nid)
            paysafecard_data = vip_paysafecard_payments.generate_paysafecard_data(request, owner_nid)
            template = loader.get_template("user_main_helpers/vip_payment_options.html")
            context = Context (dict({
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
