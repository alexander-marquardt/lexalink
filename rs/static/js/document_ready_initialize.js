/* This file contains javascript code that will be called automatically once the document has been loaded.
   It is envisioned as a "container" for all code that executes on the $(document).ready() trigger.
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
    })


    $(document).on("click",'.cl-paypal_logo_button', function(e) {
        debugger;
        show_paypal_purchase_dialog();
        e.preventDefault();
    })
});
