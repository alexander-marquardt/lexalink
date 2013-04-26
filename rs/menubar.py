

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext
import utils, constants, error_reporting, logging

def generate_num_received_html(num_received):
    
    if num_received: 
        num_received_html = '[%s %s]' % (num_received, ugettext("new"))
    else: num_received_html = ''    
    
    return num_received_html

def generate_menu_item(contact_type, new_contact_counter_obj):
    
    try:
        html_list = []
                    
        html_list.append("<li>")
        
        num_received_contact_type_since_last_reset = getattr(new_contact_counter_obj, 'num_received_' + contact_type + "_since_last_reset") 
        
        if contact_type == "chat_friend":
            # we need to add in extra html to show the "connected" friends
            num_friend_connected_since_last_reset = getattr(new_contact_counter_obj, "num_connected_chat_friend_since_last_reset")
            combined_num_friends_since_last_reset =  num_friend_connected_since_last_reset +\
                num_received_contact_type_since_last_reset     
            combined_num_html = generate_num_received_html(combined_num_friends_since_last_reset)   
            
            num_confirmed_friends_html = generate_num_received_html(num_friend_connected_since_last_reset)
            
            additional_li_and_anchor_html = """
            <li><a href="%(connected_url)s">%(connected_txt)s %(num_confirmed_friends_html)s
            </a></li>            
            """ % {'connected_url': reverse("show_contacts", kwargs={'contact_type': contact_type,  
                                                                  'sent_or_received' : 'connected'}),
                   'connected_txt': ugettext("Confirmed"),
                   'num_confirmed_friends_html' : num_confirmed_friends_html,
                   }
        else:
            additional_li_and_anchor_html = ''
            combined_num_html = generate_num_received_html(num_received_contact_type_since_last_reset)  
            
        num_received_html = generate_num_received_html(num_received_contact_type_since_last_reset)            
            
        html_list.append(u"""
        <a href="#" class="fly">%(plural_contact_type)s
        %(combined_num_html)s
        </a>
        <ul class="sub">
        <li><a href="%(received_url)s">%(received_txt)s
        %(num_received_html)s
        </a></li>
        <li><a href="%(sent_url)s">%(sent_txt)s
        </a></li>
        %(additional_li_and_anchor_html)s
                
        </ul>
        """ % {'plural_contact_type' : constants.ContactIconText.plural_icon_name[contact_type],
               'combined_num_html' : combined_num_html,
                'num_received_html' : num_received_html, 
                'received_url' : reverse("show_contacts", kwargs={'contact_type': contact_type,  
                                                                  'sent_or_received' : 'received'}),
                'sent_url' : reverse("show_contacts", kwargs={'contact_type': contact_type,  
                                                              'sent_or_received' : 'sent'}),
                'received_txt' : ugettext("Received"),
                'sent_txt' : ugettext("Sent"),
                'additional_li_and_anchor_html' : additional_li_and_anchor_html,
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
                <a href="%(show_favorite_url)s">%(favorite_profile_txt)s</a>
            </li>
            <li>
                <a href="%(show_blocked_url)s">%(blocked_profile_txt)s</a>
            </li>        
            """ % {
                    'show_favorite_url' : reverse("show_contacts", kwargs={'contact_type': 'favorite',  
                                                                           'sent_or_received' : 'sent',},),
                    'show_blocked_url' : reverse("show_contacts", kwargs={'contact_type': 'blocked',  
                                                                          'sent_or_received' : 'sent',}),
                    'favorite_profile_txt' : ugettext("Favorite profiles"),
                    'blocked_profile_txt' : ugettext("Blocked profiles"), 
                })
            
        html_list.append('</ul>')
        html_list.append("</li>")
        
        
        generated_html = ''.join(html for html in html_list)
        return generated_html
    except: 
        error_reporting.log_exception(logging.critical)
        return ''    
    