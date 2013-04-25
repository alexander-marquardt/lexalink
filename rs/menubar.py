

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext
import utils, constants, error_reporting, logging


def generate_menu_item(contact_type, new_contact_counter_obj):
    
    try:
        html_list = []
        
        if contact_type == "chat_friend":
            # minor hack due to the inconsistency in the naming convention used for chat friends
            fixed_contact_type = "friend_request"
        else:
            fixed_contact_type = contact_type
            
        html_list.append("<li>")
        num_received_contact_type_since_last_reset = getattr(new_contact_counter_obj, 'num_received_' + fixed_contact_type + "_since_last_reset")

        if num_received_contact_type_since_last_reset: 
            num_received_html = '[%s %s]' % (num_received_contact_type_since_last_reset, ugettext("new"))
        else: num_received_html = ''
        
        
        html_list.append(u"""
        <a href="#" class="fly">%(plural_contact_type)s
        %(num_received_html)s
        </a>
        <ul class="sub">
        <li><a href="%(received_url)s">%(received_txt)s
        %(num_received_html)s
        </a></li>
        <li><a href="%(sent_url)s">%(sent_txt)s
        
        </a></li>
                
        </ul>
        """ % {'plural_contact_type' : constants.ContactIconText.plural_icon_name[contact_type],
                'num_received_html' : num_received_html, 
                'received_url' : reverse("show_contacts", kwargs={'contact_type': contact_type,  'sent_or_received' : 'received'}),
                'sent_url' : reverse("show_contacts", kwargs={'contact_type': contact_type,  'sent_or_received' : 'sent'}),
                'received_txt' : ugettext("Received"),
                'sent_txt' : ugettext("Sent")
                })
        
        html_list.append("</li>")
        
        generated_html = ''.join(html for html in html_list)
        return generated_html    
    
    except: 
        error_reporting.log_exception(logging.critical)
        return ''      
    
def generate_contacts_dropdown_html(new_contact_counter_obj):
    
    try:
        html_list = []
        html_list.append('<li class="top">')
        
        new_contact_count_sum = utils.get_new_contact_count_sum(new_contact_counter_obj)
        if new_contact_count_sum:
            new_contact_count_html = "[%s %s]" % (new_contact_count_sum, ugettext("new"))
        else: new_contact_count_html = ''

        
        html_list.append(u"""
            <a href="#" class="top_link">
                <span class="down">%(contacts)s
                    %(new_contact_count_html)s
                </span>
            </a>    
        """ % {'contacts' : ugettext("Contacts"),
                'new_contact_count_html' : new_contact_count_html,
                })
        
        html_list.append('<ul class="sub">')
        
        menu_items_list = ['wink', 'kiss', 'key', 'chat_friend']
        for contact_type in menu_items_list:
            html_list.append(generate_menu_item(contact_type, new_contact_counter_obj))
                             
        
        
        html_list.append(
            """
            <li>
                <a href="#">Favorite Profiles</a>
            </li>
            <li>
                <a href="#">Blocked Profiles</a>
            </li>        
            """)
            
        html_list.append('</ul>')
        html_list.append("</li>")
        
        
        generated_html = ''.join(html for html in html_list)
        return generated_html
    except: 
        error_reporting.log_exception(logging.critical)
        return ''    
    