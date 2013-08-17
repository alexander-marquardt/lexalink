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
    

    // The following is a hack to deal with the fact that we have multiple payment buttons imported into the document.
    // We therefore need to remember which value the user has checked, otherwise we might pull the value from the wrong
    // radio button. We need to fix this by only importing the payment buttons a single time.
    // This creates a small bug - if the user changes their payment option in one part of the document, and then pays
    // in a different part of the document, only the most recently selected option will be remembered, as opposed to
    // what the user may see as the selected option. 
    var fortumo_selected_payment_url = $("input:radio[name=fortumo_price_point]").val();
    $("input:radio[name=fortumo_price_point]").click(function(){
        fortumo_selected_payment_url = $(this).val();
    });
    $(document).on("click", ".cl-fortumo_purchase", function() {
        // open the url in a new window
        window.open(fortumo_selected_payment_url);
        return false;
    });
});
