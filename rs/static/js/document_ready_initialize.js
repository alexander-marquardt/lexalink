/* This file contains javascript code that will be called automatically once the document has been loaded.
   It is envisioned as a "container" for code that executes on the $(document).ready() trigger.
   This is specifically intended for pieces of code that may be imported multiple times - but we don't want to
   place the javascript multiple times in the html code, so we put it here.
   This code will only be executed a single time.
 */


$(document).ready(function() {

    $('#id-show_online_status_menu_element').click(function() {
        return show_online_status_main_dialog();
    });


    $('#id-show_online_status_button').button();
    $('#id-show_online_status_button').click(function(){
        show_online_status_button_click_dialog();
    });


    $(document).on("click",'.cl-see_all_vip_benefits', function(e) {
        show_all_vip_benefits_dialog();
        e.preventDefault();
    });

    $('.cl-paypal-purchase').button();
    
    $(document).on("click",'#id-paypal_logo_button', function(e) {
        $(".cl-show_paypal_purchase_options").show();
        e.preventDefault();
    });
    
});
