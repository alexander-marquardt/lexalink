import logging

from django.template import loader, Context

from rs import constants
from rs import error_reporting
from rs import vip_paypal_payments

def render_purchase_buttons(request, username, owner_nid):

    try:

        if constants.SHOW_VIP_UPGRADE_OPTION:
            if request.session.__contains__('userobject_str'):
                # only show payment options/buttons to users that are logged-in.

                paypal_data = vip_paypal_payments.generate_paypal_data(request, username, owner_nid)
                #fortumo_data = generate_fortumo_data(request, username, owner_nid)
                template = loader.get_template("user_main_helpers/purchase_buttons.html")
                context = Context (dict({
                    'paypal_data': paypal_data,
                    #'fortumo_data' : fortumo_data,
                    'request' : request,
                    }, **constants.template_common_fields))
                return template.render(context)
            else:
                return ''
        else:
            return ''

    except:
        error_reporting.log_exception(logging.error)
        return ''
