
/*
################################################################################
# LexaLink Copyright information - do not remove this copyright notice
# Copyright (C) 2012
#
# Lexalink - a free social network and dating website platform for the Google App Engine.
#
# Original author: Alexander Marquardt
# Documentation and additional information: http://www.LexaLink.com
# Git source code repository: https://github.com/lexalink/LexaLink.git
#
# Please consider contributing your enhancements and modifications to the LexaLink community,
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
################################################################################
*/


// this section defines local utility functions that are called from various positions
// within this code.


// gnerate "random" string for unique URL -- required for IE caching bug
function rnd() {
    return String((new Date()).getTime());
}

function confirm_decision(message, url) {
    if (confirm(message)) {
        location.href = url;
    }
}


var unloadFuncs = []; // this will be filled with various functions that will clean-up event handlers that need to be de-allocated
                      // Note: each element in this array is actually an array, with the first value beign the function to call, and
                      // the remaining values being the parameters to pass in to the function.
                      // eg. load it with the following: unloadFuncs.push([function_name, arg0, arg1 ...])
function DoUnload() {
// loop over all of the functions that we have defined for freeing-up event handlers and memory
    try {
        while (unloadFuncs.length > 0) {
            var func_and_args = unloadFuncs.pop();
            var f = func_and_args.shift();
            var args = func_and_args;
            f.apply(f, func_and_args);
            f = null;
        }
    } catch(err) {
        report_try_catch_error( err, "DoUnload");  
    }
}

function check_if_javascript_version_id_has_changed(new_version_id) {
    if (typeof this.new_version_id == 'undefined')
       this.new_version_id = new_version_id;

    else {
        if (this.new_version_id != new_version_id) {
            // Yes, has changed - force a reload of the current page so that we get the most
            // recent javascript code.
            window.location.reload();
        }
    }
}


function sufficient_time_has_passed_since_last_search(milliseconds_to_pass) {

    // this function is designed to put a limit on how often the user can press the "search" button, so that
    // we don't re-submit on double clicks.

    var current_time = (new Date()).getTime();
    var returnval;

    if (typeof this.previous_time_in_milliseconds == 'undefined') {
        returnval = true;
    }
    else {
        if (current_time - milliseconds_to_pass > this.previous_time_in_milliseconds)
            returnval = true;
        else
            returnval = false;

    }
    this.previous_time_in_milliseconds = current_time;
    return returnval;
}


function report_javascript_error_on_server(status_text, warning_level) {
    // This function will POST the given error_text to the server, which will write the message
    // to the error logs.
    // warning_level: [info, warning, error, critical]

    var printTrace = printStackTrace().join("\n\n");
    status_text = status_text + "\n\n" + printTrace;
    $.ajax({
        type: 'post',
        url:  "/rs/ajax/report_javascript_error/" + warning_level + "/",
        data: {'status_text' : status_text},
        success: function(response) {
        }
    });


    //if (debugging_enabled)
        // Disable this alert - is annoying and not currently needed
        //alert("Error: " + status_text);
}


function rs_set_selector_to_value(selector_id, selected_value) {
    // hack that deals with instability in IE6 when selecting values from select menu (dropdown)
    // Note: we try to set selectors that are members of the class cl-primary-option before attempting
    // "general" selector. This is primarily for the country drop-down menus, which contain duplicates
    // of some countries (in the short-list at the top, and in the complete list).

    try {
        /* the following code will ensure that the top/first appearance of a value will be selected */
        first_selector = $(selector_id + " option[value='" + selected_value + "']:first");
        if (first_selector.length) { // check that the selector was found
            first_selector[0].selected = true;
        }
        else {
            $(selector_id).val(selected_value);
            /*this is the old way of doing it - and seems to work even if selected_value not found*/
        }

        // in case other menu items need to be reset when we change the value of this dropdown, we trigger
        // a "change" event.
        //$(selector_id).trigger('change');
    }
    catch(ex) {
        /* this is primarily intended for ie6 */
        setTimeout("$('" + selector_id + "').val('" + selected_value + "')", 1);
    }
}

function report_try_catch_error(err, calling_function_name, warning_level) {
    // make sure warning_level is set to a default value of "error"
    warning_level = warning_level || "warning";

    // calling_function_name is necessary because these names might be minimized and therefore we cannot extract them automatically

    var error_text = "\nTry/Catch Error\nCalling function: " + calling_function_name + "\nError message: " + err.message +  "\n\n" ;
    report_javascript_error_on_server(error_text, warning_level);
}

function report_ajax_error(textStatus, errorThrown, calling_function_name, warning_level) {
    // make sure warning_level is set to a default value of "error"
    warning_level = warning_level || "warning";
    // calling_function_name is necessary because these names might be minimized and therefore we cannot extract them automatically

    var error_text = "\nAjax Error\nCalling function: " + calling_function_name + "\ntextStatus: " + textStatus + "\nerrorThrown: " + errorThrown +  "\n\n";
    report_javascript_error_on_server(error_text, warning_level);
}

function show_spinner(object_to_set, object_name, live_static_dir) {
    // for dynamically loaded dropdown menus, while loading the values we shrink the width and show a spinner beside the menu

    try{
        object_to_set.after(' <img src="/' + live_static_dir + '/img/small-ajax-loader.gif" align="right "  id="id-' + object_name +  '-show-small-ajax-loader">');
        object_to_set.removeClass('cl-standard-dropdown-width-px');
        object_to_set.addClass('cl-spinner-dropdown-width-px');
    } catch (err) {
        report_try_catch_error( err, "show_spinner");
    }

}

function hide_spinner(object_to_set, object_name) {

    try {
        $('#id-' + object_name + '-show-small-ajax-loader').remove();
        object_to_set.removeClass('cl-spinner-dropdown-width-px');
        object_to_set.addClass('cl-standard-dropdown-width-px');
    } catch (err) {
        report_try_catch_error( err, "hide_spinner");        
    }

}



function load_selector_options(child_field_id, parent_field_val, default_option_text, hide_field_if_not_defined, selected_value,
                               not_available_option_text, live_static_dir, ajax_base_url) {

    // when the selector (drop-down menu) indicated by parent_field_id is modified, then load the child
    // selector based on the value selected
    // "selected_value" refers to the value that we initially assign to the child dropdown.

    try {
        if (parent_field_val == "----") {
            // If the parent has not been set, then don't try to obtain selector options for the child
            // This is actually an error condition that should never occur -- but since this is on the client side I do not
            // want to cause a "hard" crash if this condition is triggered (in any case, as the code is currently written
            // this is unlikely to happen).
            return '';
        }

        var opt_url = ajax_base_url + parent_field_val + "/";


        $(child_field_id).html('');

        // remove the spinner, just in case the user tries multiple times and the server is really slow at responding
        $('#id-child-show-small-ajax-loader').remove();

        // show spinning icon while data is being loaded from server.
        show_spinner( $(child_field_id), "child", live_static_dir);

        $.ajax({
            url: opt_url,
            success: function(html) {
                // if it is left "unselected" then the child field should have ---- value
                if (html != '' && html != "----") {
                    $(child_field_id).html('<option selected value="----">' + default_option_text);
                    $(child_field_id).append(html);
                    $(child_field_id).show();
                    if (selected_value != '----') {
                        rs_set_selector_to_value(child_field_id, selected_value);
                    }
                }
                else { // html is empty, which means that it is not defined
                    $(child_field_id).html('<option selected value="----">' + not_available_option_text);
                    if (hide_field_if_not_defined == true) {
                        $(child_field_id).hide();
                    }
                }

                hide_spinner($(child_field_id), "child");
            },
            error: function(jqXHR, textStatus, errorThrown) {
                report_ajax_error(textStatus, errorThrown, "load_selector_options");
            }
        });
    } catch(err) {
        report_try_catch_error( err, "load_selector_options");      
    }
}


function handle_change_on_for_sale_to_buy(menu_id, sub_menu_id, default_text, live_static_dir) {

    try {
        $(menu_id).change(function() {
            var curr_menu_val = $(menu_id).val();
            if (curr_menu_val == "----") {
                $(sub_menu_id).html('<option value="----">' + default_text);
            } else {
                load_selector_options(sub_menu_id, curr_menu_val, default_text, false, "----",
                        "Not defined (this should never appear)", live_static_dir, "/rs/ajax/get_for_sale_to_buy_options/");
            }
        });
    } catch(err) {
        report_try_catch_error( err, "handle_change_on_for_sale_to_buy");
    }
}

function load_for_sale_to_buy_on_change(id_prefix, default_text, live_static_dir) {

    try {
        var for_sale_id = id_prefix + "-for_sale";
        var for_sale_sub_menu_id = id_prefix + "-for_sale_sub_menu";
        var to_buy_id = id_prefix + "-to_buy";
        var to_buy_sub_menu_id = id_prefix + "-to_buy_sub_menu";

        handle_change_on_for_sale_to_buy(for_sale_id, for_sale_sub_menu_id, default_text['for_sale_sub_menu'], live_static_dir);
        handle_change_on_for_sale_to_buy(to_buy_id, to_buy_sub_menu_id, default_text['to_buy_sub_menu'], live_static_dir);
    } catch(err) {
        report_try_catch_error( err, "load_for_sale_to_buy_on_change");
    }
}




function load_location_settings_on_change(id_prefix, default_text, hide_field_if_not_defined, live_static_dir) {

    // loads drop-down location menu values when the parent location is changed


    try {
        var country_id = id_prefix + "-country";
        var region_id = id_prefix + "-region";
        var sub_region_id = id_prefix + "-sub_region";


        // the following logic ensure that sub-menus are cleared and that the default value
        // will have a value that the server can handle. ie. if region is don't care, then
        // we have to return the value of the country as the value for the don't care selection.

        $(country_id).on("change.location_settings_on_change", function() {

            var country_val = $(country_id).val();

            if (country_val == "----") {
                $(region_id).html('<option value="----">' + default_text['region']);

            } else {
                // set the default value of the region selector to be the currently selected country.
                load_selector_options(region_id, country_val, default_text['region'], hide_field_if_not_defined, "----",
                        default_text['not_available'], live_static_dir, "/rs/ajax/get_location_options/");
            }

            // since the country just changed, and the region was just modified, overwrite the sub_region dropdown to ensure
            // that it does not contain stale data
            $(sub_region_id).html('<option value="----">' + default_text['sub_region']);

            // if country value is changed, then we know that the region has not been selected yet -- therefore, hide sub_regions
            // if this is the specifed behaviour.
            if (hide_field_if_not_defined == true) {
                $(sub_region_id).hide();
            }
        });

        $(region_id).on("change.location_settings_on_change", function() {
            var country_val = $(country_id).val();
            var region_val = $(region_id).val();

            if (region_val != '----') {
                // if the region has been selected, load sub-regions
                load_selector_options(sub_region_id, region_val, default_text['sub_region'], hide_field_if_not_defined, "----",
                        default_text['not_available'], live_static_dir, "/rs/ajax/get_location_options/");

            }
            else {
                // if the region has not been selected, we don't load sub-regions, and we just set the
                // default value to be the currently selected country, or hide the sub_regions (if this is spefied)
                $(sub_region_id).html('<option selected value="----">' + default_text['sub_region']);
                if (hide_field_if_not_defined == true) {
                    $(sub_region_id).hide();
                }
            }
        });
    } catch(err) {
        report_try_catch_error( err, "load_location_settings_on_change");
    }

    unloadFuncs.push([undo_func_load_location_settings_on_change, id_prefix]);
}

function undo_func_load_location_settings_on_change(id_prefix) {
    // make sure that the change handlers are removed - otherwise leaks in IE6
    var country_id = id_prefix + "-country";
    var region_id = id_prefix + "-region";

    $(country_id).off();
    $(region_id).off();
    
}


function getJSON_handler(action, id_prefix, field_type) {

    // - action -  is the path to execut the script which will return JSON data
    // - id_prefix - is a section-specific identifier that ensure that all JSON data returned for 
    // a given section will have an identifier that will only be matched in the target section.
    // - field_type - either "dropdown", or "checkbox"
    //

    try {
        $.getJSON(action,
            // pull the current settings out of the data-structure on the server, and set the
            // dropdown menus to reflect the correct value
            function(data) {
                var id_name;
                if (field_type != "email_address" && field_type != "textarea" && field_type != "current_status"
                        && field_type != "about_user" && field_type != "about_user_dialog_popup") {
                    for (var field in data) {

                        // hasOwnProperty just makes sure that the field is not an inherited property, ie. it ensures
                        // that it is defined directly on the data object (this check is a bit paranoid actually)
                        if (data.hasOwnProperty(field)) {

                            if (field_type == "dropdown") {
                                id_name = id_prefix + field;
                                //$(id_name).val(data[field]);
                                rs_set_selector_to_value(id_name, data[field]);
                            }
                            if (field_type == "checkbox") {
                                id_name = id_prefix + data[field];
                                $(id_name).attr('checked', true);
                            }
                        }
                    }
                }
                else {
                    // it is a email-address text-box input or a textarea.
                    id_name = id_prefix + field_type;
                    $(id_name).val(data);
                }
            }
        );
    } catch(err) {
        report_try_catch_error( err, "getJSON_handler");  
    }
}



function set_sub_menu(object_to_set, object_name, options_html, default_unselected_text, list_of_objects_to_hide_if_not_selected, hide_field_if_not_selected) {

    try {
        if (hide_field_if_not_selected == true && options_html == '') {
            for (var idx = 0; idx < list_of_objects_to_hide_if_not_selected.length; idx ++)
                list_of_objects_to_hide_if_not_selected[idx].hide();
        } else {
            object_to_set.html('<option selected value="----">' + default_unselected_text);
            object_to_set.append(options_html);
            object_to_set.show();
        }

        hide_spinner(object_to_set, object_name);
    } catch (err) {
        report_try_catch_error( err, "set_sub_menu");
    }
}

function set_search_values_to_data(data, id_prefix, default_text, hide_field_if_not_selected) {
    // pull the current settings out of the data-structure on the server, and set the 
    // dropdown menus to reflect the correct value

    try {
        var fields_to_setup = ['region', 'sub_region', 'for_sale_sub_menu', 'to_buy_sub_menu'];
        var field_id = new Object();
        var field_object = new Object();
        var options_html_name = new Object();
        var idx, field_name;

        for (idx in fields_to_setup) {
            field_name = fields_to_setup[idx];
            field_id[field_name] = id_prefix + "-" + field_name;
            field_object[field_name] = $(field_id[field_name]);
            options_html_name[field_name] = field_name + "_options_html";
        }

        var matrix_of_objects_to_hide_if_not_selected = new Object();
        matrix_of_objects_to_hide_if_not_selected['region'] = [field_object['region'], field_object['sub_region']]; // this is used on the login screen to hide dropdowns until they are needed/defined
        matrix_of_objects_to_hide_if_not_selected['sub_region'] = [field_object['sub_region']];
        matrix_of_objects_to_hide_if_not_selected['for_sale_sub_menu'] = []; // no reason to hide the for_sale/to_buy fields for the moment
        matrix_of_objects_to_hide_if_not_selected['to_buy_sub_menu'] = [];


        for (idx in fields_to_setup) {
            field_name = fields_to_setup[idx];
            var options_html = data[options_html_name[field_name]];
            var list_of_objects_to_hide_if_not_selected = matrix_of_objects_to_hide_if_not_selected[field_name];
            set_sub_menu(field_object[field_name], field_name, options_html, default_text[field_name], list_of_objects_to_hide_if_not_selected, hide_field_if_not_selected);
        }

        // load the value that is selected for all dropdown data fields (note that the "_options_html" data is not a data field, it is a value
        // (containing the dropdown menu contents) that we have loaded into a data field.
        for (var field in data) {
            if (field != 'region_options_html' && field != 'sub_region_options_html' && field != 'for_sale_sub_menu_options_html' && field != 'to_buy_sub_menu_options_html') {
                var id_name = id_prefix + "-" + field;
                rs_set_selector_to_value(id_name, data[field]);
            }
        }
    } catch(err) {
        report_try_catch_error( err, "set_search_values_to_data");
    }
}

function show_menus_as_loading(menu_name, id_prefix, live_static_dir) {

    // helper function taht just modifies a dropdown menu to show a spinner beside it (for use while it is
    // being loaded for example)
    try {
        var menu_id = id_prefix + '-' + menu_name;
        var $menu_obj = $(menu_id);
        // clear menu contents while it is loading
        $menu_obj.html('');
        // show spinner beside menu while it is being loaded
        show_spinner($menu_obj, menu_name, live_static_dir);
    } catch(err) {
        report_try_catch_error( err, "show_menus_as_loading");
    }
}

function JSON_set_dropdown_options_and_settings(action, id_prefix, default_text, hide_field_if_not_defined, live_static_dir) {

    //
    // - action -  is the path to execute the script which will return JSON data
    // - id_prefix - is a section-specific identifier that ensure that all JSON data returned for 
    // a given section will have an identifier that will only be matched in the target section.
    // 
    //


    try {
        show_menus_as_loading('region', id_prefix, live_static_dir);
        show_menus_as_loading('sub_region', id_prefix, live_static_dir);
        show_menus_as_loading('for_sale_sub_menu', id_prefix, live_static_dir);
        show_menus_as_loading('to_buy_sub_menu', id_prefix, live_static_dir);


        $.getJSON(action, function(data) {
            // set the dropdown menus to correct values, and remove the spinners after dynamically loaded menus are setup
            set_search_values_to_data(data, id_prefix, default_text, hide_field_if_not_defined);
        });
    } catch(err) {
        report_try_catch_error( err, "JSON_set_dropdown_options_and_settings");  
    }
}


function set_values_on_data_object_to_undefined(data_object, fields_list) {

    // simple helper function that just copies "----" (undefined) values into the "data_object" that will be passed around
    // for setting dropdown menus.

    try{
        for (var idx=0; idx < fields_list.length; idx ++) {

            var field_name = fields_list[idx];
            data_object[field_name] = "----";
        }
    } catch(err) {
        report_try_catch_error( err, "set_values_on_data_object_to_undefined");  
    }
}

function set_values_on_data_object(data_object, fields_list) {

    // simple helper function that just copies the values that have (possibly) been passed in the html as hidden
    // id fields, and copies these values onto "data_object" that will be passed around for setting dropdown menu values. 

    try {
        for (var idx=0; idx < fields_list.length; idx ++) {

            var field_name = fields_list[idx];
            data_object[field_name] = $("#id-passed_in_search-" + field_name).val();
        }
    } catch(err) {
        report_try_catch_error( err, "set_values_on_data_object");
    }
}

function set_dropdown_options_and_settings(action, id_prefix, default_text, hide_field_if_not_defined, live_static_dir, is_registered_user) {

    var fields_list = ['sex', 'age', 'preference', 'relationship_status', 'language_to_learn', 'language_to_teach',
    'country', 'region', 'sub_region', 'for_sale', 'to_buy',
    'for_sale_sub_menu', 'to_buy_sub_menu', 'query_order',
    'sub_region_options_html', 'region_options_html',
    'for_sale_sub_menu_options_html', 'to_buy_sub_menu_options_html'];

    var data_object = new Object();

    try {

        if ($('#id-passed_in_search-available_in_html').length) {
            // If the data is defined inside the html, this means that we can just pull the search settings from the hidden
            // values that were passed in the html
            // Note: we don't bother showing the spinners and other stuff that we need to do if we were to retrieve JSON data
            // because this data will be instantly loaded once the page has loaded.

            set_values_on_data_object(data_object, fields_list);
            set_search_values_to_data(data_object, id_prefix, default_text, hide_field_if_not_defined);
        }
        else {
            // Otherwise, we default back to an ajax call to the server to find the data - this happens if we load a page other than
            // a search results page (ie. click on "My profile"). Eventually, we should try to pass all search settings data directly in
            // the HTML as opposed to ajax calls.
            if (is_registered_user) {
                JSON_set_dropdown_options_and_settings(action, id_prefix, default_text, hide_field_if_not_defined, live_static_dir);
            } else {
                set_values_on_data_object_to_undefined(data_object, fields_list);
                set_search_values_to_data(data_object, id_prefix, default_text, hide_field_if_not_defined);
            }
        }
    } catch(err) {
        report_try_catch_error( err, "set_dropdown_options_and_settings");  
    }
}


function fancybox_setup(jquery_obj) {
    // fancybox is the jquery module that displays photos in a fancy way, and allows user
    // interaction such as scrolling throug a gallery. This function simply does some
    // initialization of fancybox.
    jquery_obj.fancybox({
        'SpeedIn'                :        500,
        'SpeedOut'                :        500,
        'onComplete'              :   function() {
            $('#fancybox-img').bind("contextmenu", function(e){ return false; });
        }
    });

    // since we are always disabling the context menu at the same time that we are setting up the fancybox
    // just disable it here.
    $('img').bind("contextmenu", function(e){ return false; });
}

function handle_link_for_edit(section_name, input_type, uid, live_static_dir) {
    // this code is responsible for re-loading the current section with input fields for
    // edit. this is in response to the user clicking on the edit button. the code here is highly coupled
    // to the server-side code that generates the html. any modifications must be done in both server and client side.
    // - section_name - the name of the piece of html which contains an independent form -- examples could be
    //                  an input section for user languages, hobbies, physical features.
    // - input_type - we currently support "checkbox" and "dropdown" input types with this code
    // - region_default_text - is the the header that will say "Select region" in whatever language the user is using
    // - sub_region_default_text - same as region_default_text

    // for this function to work, the corresponding css/html divs must follow exactly
    // the naming conventions specified here. this is necessary to allow us to programmatically
    // send data from the server, and to allow us to re-use this code. .. also it keeps the code
    // consistent in the naming conventions.


    try{

        // we need to treat the location information as a special case, since it is dynamically loaded depending on
        // the selection of the current country and region.
        if (section_name == "signup_fields") {
            var signup_fields_url;
            var country_default_text = '';
            var default_text = new Object();
            default_text['region'] = "Select region";
            default_text['sub_region'] = "Select sub-region";
            default_text['not_available'] = "Not defined yet";
            var id_prefix = "#id-edit-signup_fields";
        }


        $("#id-edit-" + section_name + "-section").hide(); // keep menus hidden until user clicks on edit

        // for some (unknown) reason we need to unbind the click handler before binding it , or it will fire twice for a single click.
        $(document).off('click', ".cl-edit-" + section_name + "-anchor").on('click', ".cl-edit-" + section_name + "-anchor", function() {
            $("#id-edit-" + section_name + "-place-holder").load("/rs/ajax/load_" + section_name + "_for_edit/", function() {
                $("#id-display-" + section_name + "-section").hide();
                $("#id-edit-" + section_name + "-section").show();
                if (section_name != "signup_fields") {
                    getJSON_handler("/rs/ajax/get_" + section_name + "_settings/" + uid + "/" + rnd() + "/", "#id-edit-" + section_name + "-", input_type);
                }
                else { // signup_fields are treated specially since the location requires dynamically loaded drop-down menus
                    // note - DO NOT combine the following line with the var declaration, or the rnd value will never change
                    signup_fields_url = "/rs/ajax/get_signup_fields_settings/" + uid + "/" + rnd() + "/";
                    JSON_set_dropdown_options_and_settings(signup_fields_url, id_prefix, default_text, true, live_static_dir);
                    load_location_settings_on_change(id_prefix, default_text, true, live_static_dir);

                }
            });
            return false; // ensure that browser doesn't navigate to the href page!
        });
    } catch(err) {
        report_try_catch_error( err, "handle_link_for_edit");
    }
}

function mouseover_button_handler(button_object) {
    // defines changes in button appearance when mouse is over
    button_object.button();
}

function undo_func_mouseover_button_handler(button_object) {
    button_object.off();
}


function submit_post(section_name, uid) {

    try {
        $.post("/rs/store_" + section_name + "/" + uid + "/", $("form#id-" + section_name + "-form").serialize(), function () {
            // put the load inside the callback, since we must ensure that the data has been
            // loaded
            $("#id-display-" + section_name + "-section").load("/rs/ajax/load_" + section_name + "/" + rnd() + "/", function() {
                $("#id-highlight-div").effect("highlight", {color:'#FFEEFF'}, 3000);
            });


            $("#id-display-" + section_name + "-section").show();
            $("#id-edit-" + section_name + "-section").hide();
        });
    } catch(err) {
        report_try_catch_error( err, "submit_post");  
    }
}

function handle_submit_button(section_name, uid, disable_submit_on_enter) {
    // setup submit button and associate the action when clicked


    try {
        var submit_button_id = "#id-submit-" + section_name;
        var edit_section_id = "#id-edit-" + section_name + "-section";
        var submit_button_obj = $(submit_button_id);
        var edit_section_obj = $(edit_section_id);

        submit_button_obj.off("click.handle_submit_button").on("click.handle_submit_button", function() {
            submit_post(section_name, uid);
        });

        // Check to see if the enter key has been pressed inside the section -- treat this this same
        // as if the user had pressed the submit button
        disable_submit_on_enter = typeof disable_submit_on_enter !== 'undefined' ? disable_submit_on_enter  : false;
        if (!disable_submit_on_enter) {
            edit_section_obj.on("keydown.handle_submit_button", function(e) {
                if (e.keyCode == 13) {
                    submit_post(section_name, uid);
                    e.stopImmediatePropagation();
                    e.stopPropagation();
                    return false;
                }
            });
        }

        unloadFuncs.push([undo_func_handle_submit_button, submit_button_obj, edit_section_obj]);

        mouseover_button_handler(submit_button_obj);
    } catch(err) {
        report_try_catch_error( err, "handle_submit_button");
    }
}

function undo_func_handle_submit_button(submit_button_obj, edit_section_obj) {
    submit_button_obj.off();
    edit_section_obj.off();
}

function handle_cancel_button(section_name, uid) {

    // setup cancel button

    try {
        var cancel_button_id = "#id-cancel-" + section_name;
        var cancel_button_obj = $(cancel_button_id);
        cancel_button_obj.on("click.handle_cancel_button", function() {
            $("#id-display-" + section_name + "-section").show();
            $("#id-edit-" + section_name + "-section").hide();
        });
        unloadFuncs.push([undo_func_handle_cancel_button, cancel_button_obj]);
        mouseover_button_handler($(cancel_button_id));
    } catch(err) {
        report_try_catch_error( err, "handle_cancel_button");
    }
}

function undo_func_handle_cancel_button(cancel_button_obj) {
    cancel_button_obj.off();
}

function handle_submit_and_cancel_buttons(section_name, uid) {
    handle_submit_button(section_name, uid);
    handle_cancel_button(section_name, uid);
}


function getJSON_initiate_contact_settings(uid) {
    // requests settings for the "contact" objects from the server, and sets their values to the values returned from the server

    try {
        var url = "/rs/ajax/get_initiate_contact_settings/" + uid + "/" + rnd() + "/";
        $.getJSON(url, function(data) {
            for (var dict_key in data) {
                if (data.hasOwnProperty(dict_key)) {
                    selector = "span#id-" + dict_key;
                    $(selector).html(data[dict_key]);
                }
            }
        });
    } catch(err) {
        report_try_catch_error( err, "getJSON_initiate_contact_settings");
    }
}


function  show_registration_and_login() {
    $.ajax({
        type: 'get',
        url:  '/rs/get_registration_html/',
        success: function(html_response) {
            $('#id-show-registration-and-login').html(html_response);
            $('#id-show-registration-and-login').dialog({
                modal: true,
                width: 'auto',
                position: {
                    my: "center",
                    at: "center"
                },
                show: ('fade', 500)
            });


            $('#id-show-registration-and-login').css({'padding' : "0px"});
            $('#id-show-registration-and-login').dialog('open');

            var background_img = $('#rs-nav').css('background-image');
            var background_color = $("<h1>foo</h1>").hide().appendTo("body").css('color');
            // set the background image on the dialog titlebar to be the same as the navigation bar
            $('#id-show-registration-and-login').parent().find('.ui-widget-header').css({'background-image': background_img });
            // hide the background color of the titlebar and remove the border - basically we are over-riding the default
            // jquery UI default values to match the color scheme of the current site.
            $('#id-show-registration-and-login').parent().find('.ui-widget-header').css({'background-color': '#FFF' });
            $('#id-show-registration-and-login').parent().find('.ui-widget-header').css({'border': '0px' });
        },
        error: function () {

        },
        complete: function() {

        }
    });
}

function handle_click_on_contact_icon(section_name, uid, show_registration_dialog_when_clicked) {

    try {
        var submit_button_id = "#id-submit-" + section_name;


        $(submit_button_id).click(function() {
            if (!show_registration_dialog_when_clicked) {
                $.ajax({
                    type: 'post',
                    url:  "/rs/store_initiate_contact/" + uid + "/",
                    data: { 'section_name' : section_name},
                    success: function(data) {
                        if (data == "OK") {
                            getJSON_initiate_contact_settings(uid);
                        } else {
                            $("#id-contact_icon").html(data);
                            $("#id-contact_icon").dialog();
                        }
                    },
                    complete: function () {}
                });

                // prevent scrolling to the top of the page when html is updated
                return false;
            }
            else {
                show_registration_and_login();
                return false;
            }
        });
    } catch (err) {
        report_try_catch_error( err, "handle_click_on_contact_icon");
    }
}

function hide_spinner_and_show_submit(submit_button_id, ajax_spinner_id, captcha_div_id) {
    $(submit_button_id).show();
    $(ajax_spinner_id).hide();
    $(captcha_div_id).show();
}

function reload_submit_and_recaptcha(submit_button_id, ajax_spinner_id, captcha_div_id, captcha_bypass_string) {

    try {
        if (captcha_bypass_string == "no_bypass") {
            Recaptcha.reload();
        }
        hide_spinner_and_show_submit(submit_button_id, ajax_spinner_id, captcha_div_id);
    } catch(err) {
        report_try_catch_error( err, "reload_submit_and_recaptcha");
    }
}



function show_dialog_popup(popup_box_id, height, width, show_x_close_icon) {

    $(popup_box_id).dialog({
        modal: true,
        title: "",
        show: 'clip',
        hide: 'clip',
        width: width,
        height: height,
        position: 'center'
    });

    if (show_x_close_icon == false) {
        $(popup_box_id).dialog('option', 'dialogClass',  'hide-x-close');
    } else {
        // remove the hide-x-close class - this is a bit complicated because there is not built-in functionality for removing a class
        // Get the existing class string
        var dlgClass = $(popup_box_id).dialog("option", "dialogClass");
        // remove the offending class
        dlgClass = dlgClass.replace('hide-x-close', "");
        // reset the dialog class
        $(popup_box_id).dialog("option", "dialogClass", dlgClass);
    }
}

function handle_dialog_popup_close_button(popup_box_id, close_button_id) {

    $(popup_box_id).ready(function(){
        $(close_button_id).button();
        $(close_button_id).on('click', function() {
           $(popup_box_id).dialog("close");
        });
    });
}

function submit_send_mail(section_name, submit_button_id, captcha_div_id, to_uid, captcha_bypass_string, have_sent_messages_string,
                          success_status_string, error_status_string) {

    try {
        // hide the submit button, to prevent double-click
        var ajax_spinner_id = "#id-show-ajax-spinner-captcha";
        var myurl = "/rs/store_" + section_name + "/" + to_uid + "/" + captcha_bypass_string + "/" + have_sent_messages_string + "/";
        var mydata = $("form#id-" + section_name + "-form").serialize();
        $(submit_button_id).hide();
        $(ajax_spinner_id).show();
        $(captcha_div_id).hide();

        // remove error message if previous submission failed
        $('#id-submit_send_mail-status').remove();

        $.ajax({
            type: 'post',
            url: myurl,
            data: (mydata),
            timeout: 15000, // 15 second timeout
            success: function (html_response) {
                // success means that the server has responded with a valid response - does not necessarily mean that
                // the message was successfully sent. The value in the html_response lets us know the sent status. 
                //
                // put the load inside the callback, since we must ensure that the data has been
                // loaded
                //
                // load the message summary
                if (html_response == "OK") {
                    $(submit_button_id).after('<div id="id-submit_send_mail-status" class="cl-color-text"><br>' + success_status_string + '!<br></div>');

                    $("#id-num_messages_sent_feedback_and_count").hide();

                    $("#id-display-" + section_name + "-section").load("/rs/ajax/load_" + section_name + "/" + to_uid + "/" + rnd() + "/", function() {
                        $("#id-highlight-div").effect("highlight", {color:'#FFEEFF'}, 3000);
                    });

                    if (section_name != "send_mail") {
                        // reload the textarea -- but not for the "send_mail" section, since for this section textarea was already
                        // reloaded in the load_send_mail ajax call
                        $("#id-edit-" + section_name + "-section").load("/rs/ajax/load_mail_textarea/" + to_uid + "/" + section_name + "/");
                    }

                    $(ajax_spinner_id).hide();
                } else if (html_response == "user_is_missing_profile_description") {
                    // we must get the user to fill in more information in their profile before they will be permitted to send a message.
                    // pop-up a dialog box that allows them to enter in the appropriate information into their profile, at which point they
                    // should be able to re-submit their message.
                    show_dialog_popup("#id-about_user_is_empty_popup", 500, 800, true);
                    hide_spinner_and_show_submit(submit_button_id, ajax_spinner_id, captcha_div_id);

                } else if (html_response == "captcha_is_incorrect") {
                    var bad_captcha_message = $('#id-common_translations-incorrect_captcha').text();
                    $(submit_button_id).before('<div id="id-submit_send_mail-status" class="cl-warning-text cl-text-24pt-format"><br>' + bad_captcha_message + '<br></div>');
                    reload_submit_and_recaptcha(submit_button_id, ajax_spinner_id, captcha_div_id, captcha_bypass_string);

                } else if (html_response == "empty_send_message") {
                    var empty_message_message = $('#id-common_translations-empty_send_message').text();
                    $(submit_button_id).before('<div id="id-submit_send_mail-status" class="cl-warning-text cl-text-24pt-format"><br>' + empty_message_message + '<br></div>');                    
                    hide_spinner_and_show_submit(submit_button_id, ajax_spinner_id, captcha_div_id);

                } else {
                    // unknown status returned.
                    $(submit_button_id).before('<div id="id-submit_send_mail-status"><br>' + html_response + '<br></div>');
                    reload_submit_and_recaptcha(submit_button_id, ajax_spinner_id, captcha_div_id, captcha_bypass_string);
                    report_ajax_error('', '', "submit_send_mail - unknown html response: " + html_response);
                }

            },
            error: function(jqXHR, textStatus, errorThrown) {
                if (jqXHR.responseText != undefined) {
                    error_string = jqXHR.responseText;
                } else {
                    error_string = error_status_string;
                }
                $(submit_button_id).before('<div id="id-submit_send_mail-status" class="cl-warning-text cl-text-24pt-format"><br>' + error_string + '!<br></div>');
                reload_submit_and_recaptcha(submit_button_id, ajax_spinner_id, captcha_div_id, captcha_bypass_string);
                var warning_level;
                if (errorThrown == "timeout") {
                    warning_level = "warning"
                } else {
                    warning_level = "error"
                }
                report_ajax_error(textStatus, errorThrown, "submit_send_mail", warning_level);
            }
        });
    } catch(err) {
        report_try_catch_error( err, "submit_send_mail");
    }
}


function handle_submit_send_mail_button(section_name, to_uid, captcha_bypass_string, have_sent_messages_string, success_status_string, error_status_string) {
    // setup submit button and associate the action when clicked
    // section_name is either "send_mail_from_profile_checkbox_[yes|no]" or "send_mail" -- 
    // if the event is "send_mail_from_profile", then only a small
    // summary will be loaded -- if it is a "send_mail", then the entire chain of mail messages will be reloaded.

    try {
        var submit_button_id = "#id-submit-" + section_name;
        var captcha_div_id = "#id-" + section_name + "-captcha";

        $(submit_button_id).click(function() {
            submit_send_mail(section_name, submit_button_id, captcha_div_id, to_uid, captcha_bypass_string, have_sent_messages_string, success_status_string, error_status_string);
        });
        // if enter key is pressed inside the captcha, this should trigger a sumbit
        // Note: IE6 requires that the trigger is on keydown..
        $(captcha_div_id).keydown(function(e) {
            if (e.keyCode == 13) {
                submit_send_mail(section_name, submit_button_id, captcha_div_id, to_uid, captcha_bypass_string, have_sent_messages_string, success_status_string, error_status_string);
                e.stopImmediatePropagation();
                e.stopPropagation();
                return false;
            }
        });
        mouseover_button_handler($(submit_button_id));
    } catch(err) {
        report_try_catch_error( err, "handle_submit_send_mail_button");
    }
}


function show_registration_dialog_on_click(section_name) {
    var submit_button_id = "#id-submit-" + section_name;
    $(submit_button_id).click(function() {
        show_registration_and_login();
    });
}

function submit_verify_captcha(section_name, submit_button_id, captcha_div_id) {

    try {
        // hide the submit button, to prevent double-click
        var ajax_spinner_id = "#id-show-ajax-spinner-captcha";
        var myurl = "/rs/store_" + section_name + "/";
        var mydata = $("form#id-" + section_name + "-form").serialize();
        var captcha_status_id = "#id-" + section_name + "-status";
        $(submit_button_id).hide();
        $(ajax_spinner_id).show();
        $(captcha_div_id).hide();

        $.ajax({
            type: 'post',
            url: myurl,
            data: (mydata),
            timeout: 15000, // 15 second timeout
            success: function (html_response) {
                // if successful, reload the entire page so that all buttons are
                // enables, and the user can edit their profile
                if (html_response == "Fail") {
                    $(captcha_status_id).html('<strong>Captcha incorrecto, intentalo de nuevo</strong>');
                    reload_submit_and_recaptcha(submit_button_id, ajax_spinner_id, captcha_div_id, "no_bypass");
                } else {
                    self.location = html_response; // re-direct to user profile
                }

            },
            error: function(jqXHR, textStatus, errorThrown) {
                $(captcha_status_id).html('<strong>Error, intentalo de nuevo</strong>');
                reload_submit_and_recaptcha(submit_button_id, ajax_spinner_id, captcha_div_id, "no_bypass");
                report_ajax_error(textStatus, errorThrown, "submit_verify_captcha");
            }
        });
    } catch(err) {
        report_try_catch_error( err, "submit_verify_captcha");
    }
}


function handle_verify_captcha(section_name) {
    // setup submit button and associate the action when clicked

    try {
        var submit_button_id = "#id-submit-" + section_name;
        var captcha_div_id = "#id-" + section_name + "-captcha";

        $(submit_button_id).click(function() {
            submit_verify_captcha(section_name, submit_button_id, captcha_div_id);
        });

        // if enter key is pressed inside the captcha, this should trigger a sumbit
        $(captcha_div_id).keydown(function(e) {
            if (e.keyCode == 13) {
                submit_verify_captcha(section_name, submit_button_id, captcha_div_id);
                e.stopImmediatePropagation();
                e.stopPropagation();
                return false;
            }
        });

        mouseover_button_handler($(submit_button_id));
    } catch(err) {
        report_try_catch_error( err, "handle_verify_captcha");
    }
}


function handle_click_on_update_message_action_icon(have_sent_messages_id, to_uid, action, with_checkbox) {
    // this function handles a click on the icon beside the message, and refreshes the message
    // to reflect the updated status
    // with_checkbox: "yes" or "no"

    try{
        var icon_id = "#id-" + action + "-have_sent_messages-" + have_sent_messages_id;
        var section_id = "#id-have_sent_messages-" + have_sent_messages_id;

        $(icon_id).click(function(event) {
            var post_url = "/rs/ajax/" + action + "_message/";
            $.post(post_url + have_sent_messages_id + "/", function() {
                // we call "load_send_mail_from_profile, because this function returns just a summary of the converstion
                $(section_id).load("/rs/ajax/load_send_mail_from_profile_checkbox_" + with_checkbox + "/" + to_uid + "/" + rnd() + "/");

                // prevent link from being followed
                return false;
            });

            // prevent scrolling to the top of the page when html is updated
            return false;
        });
    } catch (err) {
        report_try_catch_error( err, "handle_click_on_update_message_action_icon");
    }
}




function handle_post_button_with_confirmation_of_result(section_name, uid) {

    try {
        var submission_status_id = "#id-" + section_name + "-status";
        var submit_button_id = "#id-submit-" + section_name;

        $(submit_button_id).click(function() {
            $(submission_status_id).html('Processing .....');

            $.ajax({
                type: 'post',
                url: "/rs/store_" + section_name + "/" + uid + "/",
                data: $("form#id-" + section_name + "-form").serialize(),
                timeout: 15000, // 15 second timeout
                // html_response contains the result of the action -- ie. success, failur, etc.
                success: function (html_response) {
                    $(submission_status_id).html(html_response);
                    $(submit_button_id).hide();
                },
                error: function (jqXHR, textStatus, errorThrown) {
                    $(submission_status_id).html('<strong>Error posting to the server, please try again</strong>');
                    report_ajax_error(textStatus, errorThrown, "handle_post_button_with_confirmation_of_result");
                }

            });
        });
        mouseover_button_handler($(submit_button_id));
    } catch(err) {
        report_try_catch_error( err, "handle_post_button_with_confirmation_of_result");
    }
}

function FormatNumberLength(num, length) {
    // funtion that takes a number, and a length, and prints out a string representation of that number
    // with leading blanks to ensure that the string is the desired length
    var r = "" + num;
    while (r.length < length) {
        r = " " + r;
    }
    return r;
}



function clear_fields_errors(fields_type, errors_dict) {
    // fields_type is either signup_fields or login_fields

    for (key in errors_dict) {
        var input_field_id_selector = "#id-"+ fields_type + "-" + key;
        $(input_field_id_selector).removeClass("cl-highlight_border");
    }
}

function clear_both_registration_and_login_fields_errors() {
        clear_fields_errors("login_fields", login_errors_dict);
        $("#id-password-prompt").removeClass("cl-highlight_border");
        $("#id-password-input").removeClass("cl-highlight_border");

        clear_fields_errors("signup_fields" , registration_errors_dict);
}

function show_fields_errors(fields_type, errors_dict, extra_html, where_to_place_dialog) {
    // fields_type is either signup_fields or login_fields

    var error_html = '<ul>';
    // loop over the objects in the errors_dict
    for (key in errors_dict) {
        var input_field_id_selector = "#id-" + fields_type + "-" + key;
        $(input_field_id_selector).addClass("cl-highlight_border");
        if (errors_dict[key]) {
            error_html += '<li class="cl-indent">'+ errors_dict[key];
        }
    }
    error_html += '</ul>';
    error_html += extra_html;
    $('#id-dialog_box_for_user_feedback').html(error_html);
    $('#id-dialog_box_for_user_feedback').dialog({
        width: 400,
        modal: false,
        position: {
            my: "center",
            at: "center",
            of: where_to_place_dialog
        }
    }).dialog('close').dialog('open');
}

function close_dialog_box_for_user_feedback(){
    if ($('#id-dialog_box_for_user_feedback').is(':data(dialog)')) {
        $('#id-dialog_box_for_user_feedback').dialog('close');
    }
}