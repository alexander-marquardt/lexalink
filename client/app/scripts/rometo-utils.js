"use strict";

/*
################################################################################
# LexaLink Copyright information - do not remove this copyright notice
# Copyright (C) 2012
#
# Lexalink - a free social network and dating website platform for the Google App Engine.
#
# Original author: Alexander Marquardt
# Documentation and additional information: http://www.LexaLink.com
# Git source code repository: https://github.com/alexander-marquardt/lexalink
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

/* Declare imported functions so that jshint doesn't complain */
/* global printStackTrace */
/* global MANUALLY_VERSIONED_IMAGES_DIR */
/* global Recaptcha */
/* global loginErrorsDict */
/* global registrationErrorsDict */

/* Declare exported functions */
/* exported reportTryCatchError */
/* exported confirmDecision */
/* exported checkIfJavascriptVersionIdHasChanged */
/* exported sufficientTimeHasPassedSinceLastSearch */
/* exported loadForSaleToBuyOnChange */
/* exported setDropdownOptionsAndSettings */
/* exported fancyboxSetup */
/* exported handleLinkForEdit */
/* exported undoFuncMouseoverButtonHandler */
/* exported handleSubmitAndCancelButtons */
/* exported handleClickOnContactIcon */
/* exported handleDialogPopupCloseButton */
/* exported handleSubmitSendMailButton */
/* exported showRegistrationDialogOnClick */
/* exported handleClickOnUpdateMessageActionIcon */
/* exported handlePostButtonWithConfirmationOfResult */
/* exported formatNumberLength */
/* exported clearBothRegistrationAndLoginFieldsErrors */
/* exported showFieldsErrors */
/* exported closeDialogBoxForUserFeedback */



// gnerate "random" string for unique URL -- required for IE caching bug
function rnd() {
    return String((new Date()).getTime());
}

function confirmDecision(message, url) {
    if (window.confirm(message)) {
        location.href = url;
    }
}


function reportJavascriptErrorOnServer(statusText, warningLevel) {
    // This function will POST the given errorText to the server, which will write the message
    // to the error logs.
    // warningLevel: [info, warning, error, critical]

    var printTrace = printStackTrace().join("\n\n");
    statusText = statusText + "\n\n" + printTrace;
    $.ajax({
        type: 'post',
        url:  "/rs/ajax/report_javascript_error/" + warningLevel + "/",
        data: {'statusText' : statusText},
        success: function() {
        }
    });


    //if (debugging_enabled)
        // Disable this alert - is annoying and not currently needed
        //alert("Error: " + statusText);
}

function reportTryCatchError(err, callingFunctionName, warningLevel) {
    // make sure warningLevel is set to a default value of "error"
    warningLevel = warningLevel || "warning";

    // callingFunctionName is necessary because these names might be minimized and therefore we cannot extract them automatically

    var errorText = "\nTry/Catch Error\nCalling function: " + callingFunctionName + "\nError message: " + err.message +  "\n\n" ;
    reportJavascriptErrorOnServer(errorText, warningLevel);
}

var unloadFuncs = []; // this will be filled with various functions that will clean-up event handlers that need to be de-allocated
                      // Note: each element in this array is actually an array, with the first value beign the function to call, and
                      // the remaining values being the parameters to pass in to the function.
                      // eg. load it with the following: unloadFuncs.push([function_name, arg0, arg1 ...])


function checkIfJavascriptVersionIdHasChanged(newVersionId) {
    if (typeof window.newVersionId === 'undefined') {
        window.newVersionId = newVersionId;
    }
    else if (window.newVersionId !== newVersionId) {
        // Yes, has changed - force a reload of the current page so that we get the most
        // recent javascript code.
        window.location.reload();
    }
}


function sufficientTimeHasPassedSinceLastSearch(millisecondsToPass) {

    // this function is designed to put a limit on how often the user can press the "search" button, so that
    // we don't re-submit on double clicks.

    var currentTime = (new Date()).getTime();
    var returnval;

    if (typeof window.previousTimeInMilliseconds === 'undefined') {
        returnval = true;
    }
    else {
        returnval =  (currentTime - millisecondsToPass > window.previousTimeInMilliseconds);
    }

    window.previousTimeInMilliseconds = currentTime;
    return returnval;
}




function rsSetSelectorToValue(selectorId, selectedValue) {
    // hack that deals with instability in IE6 when selecting values from select menu (dropdown)
    // Note: we try to set selectors that are members of the class cl-primary-option before attempting
    // "general" selector. This is primarily for the country drop-down menus, which contain duplicates
    // of some countries (in the short-list at the top, and in the complete list).

    try {
        /* the following code will ensure that the top/first appearance of a value will be selected */
        var firstSelector = $(selectorId + " option[value='" + selectedValue + "']:first");
        if (firstSelector.length) { // check that the selector was found
            firstSelector[0].selected = true;
        }
        else {
            $(selectorId).val(selectedValue);
            /*this is the old way of doing it - and seems to work even if selectedValue not found*/
        }

        $(selectorId).change(); // trigger a change event so that sub-menus will be loaded
    }
    catch(ex) {
        /* this is primarily intended for ie6 */
        setTimeout("$('" + selectorId + "').val('" + selectedValue + "')", 1);
    }
}


function reportAjaxError(textStatus, errorThrown, callingFunctionName, warningLevel) {
    // make sure warningLevel is set to a default value of "error"
    warningLevel = warningLevel || "warning";
    // callingFunctionName is necessary because these names might be minimized and therefore we cannot extract them automatically

    var errorText = "\nAjax Error\nCalling function: " + callingFunctionName + "\ntextStatus: " + textStatus + "\nerrorThrown: " + errorThrown +  "\n\n";
    reportJavascriptErrorOnServer(errorText, warningLevel);
}

function showSpinner(objectToSet, objectName) {
    // for dynamically loaded dropdown menus, while loading the values we shrink the width and show a spinner beside the menu

    try{
        var spinnerImage = MANUALLY_VERSIONED_IMAGES_DIR + "/small-ajax-loader.gif";
        objectToSet.after(' <img src= "' + spinnerImage  + '" align="right "  id="id-' + objectName +  '-show-small-ajax-loader">');
        objectToSet.removeClass('cl-standard-dropdown-width-px');
        objectToSet.addClass('cl-spinner-dropdown-width-px');
    } catch (err) {
        reportTryCatchError( err, "showSpinner");
    }

}

function hideSpinner(objectToSet, objectName) {

    try {
        $('#id-' + objectName + '-show-small-ajax-loader').remove();
        objectToSet.removeClass('cl-spinner-dropdown-width-px');
        objectToSet.addClass('cl-standard-dropdown-width-px');
    } catch (err) {
        reportTryCatchError( err, "hideSpinner");
    }

}



function loadSelectorOptions(childFeldId, parentFieldVal, defaultOptionText, hideFieldIfNotDefined, selectedValue,
                               notAvailableOptionText, ajaxBaseUrl) {

    // when the selector (drop-down menu) indicated by parent_field_id is modified, then load the child
    // selector based on the value selected
    // "selectedValue" refers to the value that we initially assign to the child dropdown.

    try {
        if (parentFieldVal === "----") {
            // If the parent has not been set, then don't try to obtain selector options for the child
            // This is actually an error condition that should never occur -- but since this is on the client side I do not
            // want to cause a "hard" crash if this condition is triggered (in any case, as the code is currently written
            // this is unlikely to happen).
            return '';
        }

        var optUrl = ajaxBaseUrl + parentFieldVal + "/";


        $(childFeldId).html('');

        // remove the spinner, just in case the user tries multiple times and the server is really slow at responding
        $('#id-child-show-small-ajax-loader').remove();

        // show spinning icon while data is being loaded from server.
        showSpinner( $(childFeldId), "child");

        $.ajax({
            url: optUrl,
            success: function(html) {
                // if it is left "unselected" then the child field should have ---- value
                if (html !== '' && html !== "----") {
                    $(childFeldId).html('<option selected value="----">' + defaultOptionText);
                    $(childFeldId).append(html);
                    $(childFeldId).show();
                    if (selectedValue !== '----') {
                        rsSetSelectorToValue(childFeldId, selectedValue);
                    }
                }
                else { // html is empty, which means that it is not defined
                    $(childFeldId).html('<option selected value="----">' + notAvailableOptionText);
                    if (hideFieldIfNotDefined === true) {
                        $(childFeldId).hide();
                    }
                }

                hideSpinner($(childFeldId), "child");
            },
            error: function(jqXHR, textStatus, errorThrown) {
                reportAjaxError(textStatus, errorThrown, "loadSelectorOptions");
            }
        });
    } catch(err) {
        reportTryCatchError( err, "loadSelectorOptions");
    }
}


function handleChangeOnForSaleToBuy(menuId, subMenuId, defaultText) {

    try {
        $(menuId).change(function() {
            var currMenuVal = $(menuId).val();
            if (currMenuVal === "----") {
                $(subMenuId).html('<option value="----">' + defaultText);
            } else {
                loadSelectorOptions(subMenuId, currMenuVal, defaultText, false, "----",
                        "Not defined (this should never appear)", "/rs/ajax/get_for_sale_to_buy_options/");
            }
        });
    } catch(err) {
        reportTryCatchError( err, "handleChangeOnForSaleToBuy");
    }
}

function loadForSaleToBuyOnChange(idPrefix, defaultText) {

    try {
        var forSaleId = idPrefix + "-for_sale";
        var forSaleSubMenuId = idPrefix + "-for_sale_sub_menu";
        var toBuyId = idPrefix + "-to_buy";
        var toBuySubMenuId = idPrefix + "-to_buy_sub_menu";

        handleChangeOnForSaleToBuy(forSaleId, forSaleSubMenuId, defaultText['for_sale_sub_menu']);
        handleChangeOnForSaleToBuy(toBuyId, toBuySubMenuId, defaultText['to_buy_sub_menu']);
    } catch(err) {
        reportTryCatchError( err, "loadForSaleToBuyOnChange");
    }
}



function undoFuncLoadLocationSettingsOnChange(idPrefix) {
    // make sure that the change handlers are removed - otherwise leaks in IE6
    var countryId = idPrefix + "-country";
    var regionId = idPrefix + "-region";

    $(countryId).off();
    $(regionId).off();

}

function loadLocationSettingsOnChange(idPrefix, defaultText, hideFieldIfNotDefined) {

    // loads drop-down location menu values when the parent location is changed


    try {
        var countryId = idPrefix + "-country";
        var regionId = idPrefix + "-region";
        var subRegionId = idPrefix + "-sub_region";


        // the following logic ensure that sub-menus are cleared and that the default value
        // will have a value that the server can handle. ie. if region is don't care, then
        // we have to return the value of the country as the value for the don't care selection.

        $(countryId).on("change.location_settings_on_change", function() {

            var countryVal = $(countryId).val();

            if (!countryVal || countryVal === "----") {
                $(regionId).html('<option value="----">' + defaultText['region']);

            } else {
                // set the default value of the region selector to be the currently selected country.
                loadSelectorOptions(regionId, countryVal, defaultText['region'], hideFieldIfNotDefined, "----",
                        defaultText['not_available'], "/rs/ajax/get_location_options/");
            }

            // since the country just changed, and the region was just modified, overwrite the sub_region dropdown to ensure
            // that it does not contain stale data
            $(subRegionId).html('<option value="----">' + defaultText['sub_region']);

            // if country value is changed, then we know that the region has not been selected yet -- therefore, hide sub_regions
            // if this is the specifed behaviour.
            if (hideFieldIfNotDefined === true) {
                $(subRegionId).hide();
            }
        });

        $(regionId).on("change.location_settings_on_change", function() {
            var regionVal = $(regionId).val();

            if (regionVal && regionVal !== '----') {
                // if the region has been selected, load sub-regions
                loadSelectorOptions(subRegionId, regionVal, defaultText['sub_region'], hideFieldIfNotDefined, "----",
                        defaultText['not_available'], "/rs/ajax/get_location_options/");

            }
            else {
                // if the region has not been selected, we don't load sub-regions, and we just set the
                // default value to be the currently selected country, or hide the sub_regions (if this is spefied)
                $(subRegionId).html('<option selected value="----">' + defaultText['sub_region']);
                if (hideFieldIfNotDefined === true) {
                    $(subRegionId).hide();
                }
            }
        });
    } catch(err) {
        reportTryCatchError( err, "loadLocationSettingsOnChange");
    }

    unloadFuncs.push([undoFuncLoadLocationSettingsOnChange, idPrefix]);
}



function getJsonHandler(action, idPrefix, fieldType) {

    // - action -  is the path to execut the script which will return JSON data
    // - idPrefix - is a section-specific identifier that ensure that all JSON data returned for 
    // a given section will have an identifier that will only be matched in the target section.
    // - fieldType - either "dropdown", or "checkbox"
    //

    try {
        $.getJSON(action,
            // pull the current settings out of the data-structure on the server, and set the
            // dropdown menus to reflect the correct value
            function(data) {
                var idName;
                if (fieldType !== "email_address" && fieldType !== "textarea" && fieldType !== "current_status" &&
                    fieldType !== "about_user" && fieldType !== "about_user_dialog_popup") {
                    for (var field in data) {

                        // hasOwnProperty just makes sure that the field is not an inherited property, ie. it ensures
                        // that it is defined directly on the data object (this check is a bit paranoid actually)
                        if (data.hasOwnProperty(field)) {

                            if (fieldType === "dropdown") {
                                idName = idPrefix + field;
                                //$(idName).val(data[field]);
                                rsSetSelectorToValue(idName, data[field]);
                            }
                            if (fieldType === "checkbox") {
                                idName = idPrefix + data[field];
                                $(idName).attr('checked', true);
                            }
                        }
                    }
                }
                else {
                    // it is a email-address text-box input or a textarea.
                    idName = idPrefix + fieldType;
                    $(idName).val(data);
                }
            }
        );
    } catch(err) {
        reportTryCatchError( err, "getJsonHandler");
    }
}



function setSubMenu(objectToSet, objectName, optionsHtml, defaultUnselectedText, listOfObjectsToHideIfNotSelected, hideFieldIfNotSelected) {

    try {
        if (hideFieldIfNotSelected === true && optionsHtml === '') {
            for (var idx = 0; idx < listOfObjectsToHideIfNotSelected.length; idx ++) {
                listOfObjectsToHideIfNotSelected[idx].hide();
            }
        } else {
            objectToSet.html('<option selected value="----">' + defaultUnselectedText);
            objectToSet.append(optionsHtml);
            objectToSet.show();
        }

        hideSpinner(objectToSet, objectName);
    } catch (err) {
        reportTryCatchError( err, "setSubMenu");
    }
}

function setSearchValuesToData(data, idPrefix, defaultText, hideFieldIfNotSelected) {
    // pull the current settings out of the data-structure on the server, and set the 
    // dropdown menus to reflect the correct value

    try {
        var fieldsToSetup = ['region', 'sub_region', 'for_sale_sub_menu', 'to_buy_sub_menu'];
        var fieldId = {};
        var fieldObject = {};
        var optionsHtmlName = {};
        var idx, fieldName;

        for (idx in fieldsToSetup) {
            fieldName = fieldsToSetup[idx];
            fieldId[fieldName] = idPrefix + "-" + fieldName;
            fieldObject[fieldName] = $(fieldId[fieldName]);
            optionsHtmlName[fieldName] = fieldName + "_options_html";
        }

        var matrixOfObjectsToHideIfNotSelected = {};
        matrixOfObjectsToHideIfNotSelected['region'] = [fieldObject['region'], fieldObject['sub_region']]; // this is used on the login screen to hide dropdowns until they are needed/defined
        matrixOfObjectsToHideIfNotSelected['sub_region'] = [fieldObject['sub_region']];
        matrixOfObjectsToHideIfNotSelected['for_sale_sub_menu'] = []; // no reason to hide the for_sale/to_buy fields for the moment
        matrixOfObjectsToHideIfNotSelected['to_buy_sub_menu'] = [];


        for (idx in fieldsToSetup) {
            fieldName = fieldsToSetup[idx];
            var optionsHtml = data[optionsHtmlName[fieldName]];
            var listOfObjectsToHideIfNotSelected = matrixOfObjectsToHideIfNotSelected[fieldName];
            setSubMenu(fieldObject[fieldName], fieldName, optionsHtml, defaultText[fieldName], listOfObjectsToHideIfNotSelected, hideFieldIfNotSelected);
        }

        // load the value that is selected for all dropdown data fields (note that the "_options_html" data is not a data field, it is a value
        // (containing the dropdown menu contents) that we have loaded into a data field.
        for (var field in data) {
            if (field !== 'region_options_html' && field !== 'sub_region_options_html' && field !== 'for_sale_sub_menu_options_html' && field !== 'to_buy_sub_menu_options_html') {
                var idName = idPrefix + "-" + field;
                if (data[field] !== "----") {
                    rsSetSelectorToValue(idName, data[field]);
                }
            }
        }
    } catch(err) {
        reportTryCatchError( err, "setSearchValuesToData");
    }
}

function showMenusAsLoading(menuName, idPrefix) {

    // helper function taht just modifies a dropdown menu to show a spinner beside it (for use while it is
    // being loaded for example)
    try {
        var menuId = idPrefix + '-' + menuName;
        var $menuObj = $(menuId);
        // clear menu contents while it is loading
        $menuObj.html('');
        // show spinner beside menu while it is being loaded
        showSpinner($menuObj, menuName);
    } catch(err) {
        reportTryCatchError( err, "showMenusAsLoading");
    }
}

function jsonSetDropdownOptionsAndSettings(action, idPrefix, defaultText, hideFieldIfNotDefined) {

    //
    // - action -  is the path to execute the script which will return JSON data
    // - idPrefix - is a section-specific identifier that ensure that all JSON data returned for 
    // a given section will have an identifier that will only be matched in the target section.
    // 
    //


    try {
        showMenusAsLoading('region', idPrefix);
        showMenusAsLoading('sub_region', idPrefix);
        showMenusAsLoading('for_sale_sub_menu', idPrefix);
        showMenusAsLoading('to_buy_sub_menu', idPrefix);


        $.getJSON(action, function(data) {
            // set the dropdown menus to correct values, and remove the spinners after dynamically loaded menus are setup
            setSearchValuesToData(data, idPrefix, defaultText, hideFieldIfNotDefined);
        });
    } catch(err) {
        reportTryCatchError( err, "jsonSetDropdownOptionsAndSettings");
    }
}


function setValuesOnDataObjectToUndefined(dataObject, fieldsList) {

    // simple helper function that just copies "----" (undefined) values into the "dataObject" that will be passed around
    // for setting dropdown menus.

    try{
        for (var idx=0; idx < fieldsList.length; idx ++) {

            var fieldName = fieldsList[idx];
            dataObject[fieldName] = "----";
        }
    } catch(err) {
        reportTryCatchError( err, "setValuesOnDataObjectToUndefined");
    }
}

function setValuesOnDataObject(dataObject, fieldsList) {

    // simple helper function that just copies the values that have (possibly) been passed in the html as hidden
    // id fields, and copies these values onto "dataObject" that will be passed around for setting dropdown menu values.

    try {
        for (var idx=0; idx < fieldsList.length; idx ++) {

            var fieldName = fieldsList[idx];
            dataObject[fieldName] = $("#id-passed_in_search-" + fieldName).val();
        }
    } catch(err) {
        reportTryCatchError( err, "setValuesOnDataObject");
    }
}

function setDropdownOptionsAndSettings(action, idPrefix, defaultText, hideFieldIfNotDefined, isRegisteredUser) {

    var fieldsList = ['sex', 'age', 'preference', 'relationship_status', 'language_to_learn', 'language_to_teach',
    'country', 'region', 'sub_region', 'for_sale', 'to_buy',
    'for_sale_sub_menu', 'to_buy_sub_menu', 'query_order',
    'sub_region_options_html', 'region_options_html',
    'for_sale_sub_menu_options_html', 'to_buy_sub_menu_options_html'];

    var dataObject = {};

    try {

        if ($('#id-passed_in_search-available_in_html').length) {
            // If the data is defined inside the html, this means that we can just pull the search settings from the hidden
            // values that were passed in the html
            // Note: we don't bother showing the spinners and other stuff that we need to do if we were to retrieve JSON data
            // because this data will be instantly loaded once the page has loaded.

            setValuesOnDataObject(dataObject, fieldsList);
            setSearchValuesToData(dataObject, idPrefix, defaultText, hideFieldIfNotDefined);
        }
        else {
            // Otherwise, we default back to an ajax call to the server to find the data - this happens if we load a page other than
            // a search results page (ie. click on "My profile"). Eventually, we should try to pass all search settings data directly in
            // the HTML as opposed to ajax calls.
            if (isRegisteredUser) {
                jsonSetDropdownOptionsAndSettings(action, idPrefix, defaultText, hideFieldIfNotDefined);
            } else {
                setValuesOnDataObjectToUndefined(dataObject, fieldsList);
                setSearchValuesToData(dataObject, idPrefix, defaultText, hideFieldIfNotDefined);
            }
        }
    } catch(err) {
        reportTryCatchError( err, "setDropdownOptionsAndSettings");
    }
}


function fancyboxSetup(jqueryObj) {
    // fancybox is the jquery module that displays photos in a fancy way, and allows user
    // interaction such as scrolling throug a gallery. This function simply does some
    // initialization of fancybox.
    jqueryObj.fancybox({
        'SpeedIn'                :        500,
        'SpeedOut'                :        500,
        'onComplete'              :   function() {
            $('#fancybox-img').bind("contextmenu", function(){ return false; });
        }
    });

    // since we are always disabling the context menu at the same time that we are setting up the fancybox
    // just disable it here.
    $('img').bind("contextmenu", function(){ return false; });
}

function handleLinkForEdit(sectionName, inputType, uid) {
    // this code is responsible for re-loading the current section with input fields for
    // edit. this is in response to the user clicking on the edit button. the code here is highly coupled
    // to the server-side code that generates the html. any modifications must be done in both server and client side.
    // - sectionName - the name of the piece of html which contains an independent form -- examples could be
    //                  an input section for user languages, hobbies, physical features.
    // - inputType - we currently support "checkbox" and "dropdown" input types with this code
    // - region_defaultText - is the the header that will say "Select region" in whatever language the user is using
    // - sub_region_defaultText - same as region_defaultText

    // for this function to work, the corresponding css/html divs must follow exactly
    // the naming conventions specified here. this is necessary to allow us to programmatically
    // send data from the server, and to allow us to re-use this code. .. also it keeps the code
    // consistent in the naming conventions.


    try{

        // we need to treat the location information as a special case, since it is dynamically loaded depending on
        // the selection of the current country and region.
        if (sectionName === "signup_fields") {
            var signupFieldsUrl;
            var defaultText = {};
            defaultText['region'] = "Select region";
            defaultText['sub_region'] = "Select sub-region";
            defaultText['not_available'] = "Not defined yet";
            var idPrefix = "#id-edit-signup_fields";
        }


        $("#id-edit-" + sectionName + "-section").hide(); // keep menus hidden until user clicks on edit

        // for some (unknown) reason we need to unbind the click handler before binding it , or it will fire twice for a single click.
        $(document).off('click', ".cl-edit-" + sectionName + "-anchor").on('click', ".cl-edit-" + sectionName + "-anchor", function() {
            $("#id-edit-" + sectionName + "-place-holder").load("/rs/ajax/load_" + sectionName + "_for_edit/", function() {
                $("#id-display-" + sectionName + "-section").hide();
                $("#id-edit-" + sectionName + "-section").show();
                if (sectionName !== "signup_fields") {
                    getJsonHandler("/rs/ajax/get_" + sectionName + "_settings/" + uid + "/" + rnd() + "/", "#id-edit-" + sectionName + "-", inputType);
                }
                else { // signup_fields are treated specially since the location requires dynamically loaded drop-down menus
                    // note - DO NOT combine the following line with the var declaration, or the rnd value will never change
                    signupFieldsUrl = "/rs/ajax/get_signup_fields_settings/" + uid + "/" + rnd() + "/";
                    jsonSetDropdownOptionsAndSettings(signupFieldsUrl, idPrefix, defaultText, true);
                    loadLocationSettingsOnChange(idPrefix, defaultText, true);

                }
            });
            return false; // ensure that browser doesn't navigate to the href page!
        });
    } catch(err) {
        reportTryCatchError( err, "handleLinkForEdit");
    }
}

function mouseoverButtonHandler(buttonObject) {
    // defines changes in button appearance when mouse is over   
    buttonObject.button();
}

function undoFuncMouseoverButtonHandler(buttonObject) {
    buttonObject.off();
}


function submitPost(sectionName, uid) {

    try {
        $.post("/rs/store_" + sectionName + "/" + uid + "/", $("form#id-" + sectionName + "-form").serialize(), function () {
            // put the load inside the callback, since we must ensure that the data has been
            // loaded
            $("#id-display-" + sectionName + "-section").load("/rs/ajax/load_" + sectionName + "/" + rnd() + "/", function() {
                $("#id-highlight-div").effect("highlight", {color:'#FFEEFF'}, 3000);
            });


            $("#id-display-" + sectionName + "-section").show();
            $("#id-edit-" + sectionName + "-section").hide();
        });
    } catch(err) {
        reportTryCatchError( err, "submitPost");
    }
}

function undoFuncHandleSubmitButton(submitButtonObj, editSectionObj) {
    submitButtonObj.off();
    editSectionObj.off();
}

function handleSubmitButton(sectionName, uid, disableSubmitOnEnter) {
    // setup submit button and associate the action when clicked


    try {
        var submitButtonId = "#id-submit-" + sectionName;
        var editSectionId = "#id-edit-" + sectionName + "-section";
        var submitButtonObj = $(submitButtonId);
        var editSectionObj = $(editSectionId);

        submitButtonObj.off("click.handleSubmitButton").on("click.handleSubmitButton", function() {
            submitPost(sectionName, uid);
        });

        // Check to see if the enter key has been pressed inside the section -- treat this this same
        // as if the user had pressed the submit button
        disableSubmitOnEnter = typeof disableSubmitOnEnter !== 'undefined' ? disableSubmitOnEnter  : false;
        if (!disableSubmitOnEnter) {
            editSectionObj.on("keydown.handleSubmitButton", function(e) {
                if (e.keyCode === 13) {
                    submitPost(sectionName, uid);
                    e.stopImmediatePropagation();
                    e.stopPropagation();
                    return false;
                }
            });
        }

        unloadFuncs.push([undoFuncHandleSubmitButton, submitButtonObj, editSectionObj]);

        mouseoverButtonHandler(submitButtonObj);
    } catch(err) {
        reportTryCatchError( err, "handleSubmitButton");
    }
}

function undoFuncHandleCancelButton(cancelButtonObj) {
    cancelButtonObj.off();
}


function handleCancelButton(sectionName) {

    // setup cancel button

    try {
        var cancelButtonId = "#id-cancel-" + sectionName;
        var cancelButtonObj = $(cancelButtonId);
        cancelButtonObj.on("click.handleCancelButton", function() {
            $("#id-display-" + sectionName + "-section").show();
            $("#id-edit-" + sectionName + "-section").hide();
        });
        unloadFuncs.push([undoFuncHandleCancelButton, cancelButtonObj]);
        mouseoverButtonHandler($(cancelButtonId));
    } catch(err) {
        reportTryCatchError( err, "handleCancelButton");
    }
}


function handleSubmitAndCancelButtons(sectionName, uid) {
    handleSubmitButton(sectionName, uid);
    handleCancelButton(sectionName);
}


function getJsonInitiateContactSettings(uid) {
    // requests settings for the "contact" objects from the server, and sets their values to the values returned from the server

    try {
        var url = "/rs/ajax/get_initiate_contact_settings/" + uid + "/" + rnd() + "/";
        $.getJSON(url, function(data) {
            for (var dictKey in data) {
                if (data.hasOwnProperty(dictKey)) {
                    var selector = "span#id-" + dictKey;
                    $(selector).html(data[dictKey]);
                }
            }
        });
    } catch(err) {
        reportTryCatchError( err, "getJsonInitiateContactSettings");
    }
}


function showRegistrationAndLogin(additionalText, optionalPassedInUsername) {

    // prevent double clicks from being processed
    if (showRegistrationAndLogin.alreadyClicked === 'undefined' || !showRegistrationAndLogin.alreadyClicked) {
        showRegistrationAndLogin.alreadyClicked = true;
    } else {
        // we have already clicked and waiting for the dialog to be loaded before allowing another click
        // to be processed
        return;
    }


    $('#id-show-loading-spinner').show();
    $.ajax({
        type: 'get',
        url:  '/rs/get_registration_html/',
        dataType: 'json', // response type
        success: function(jsonResponse) {

            $('#id-show-registration-and-login').html("<div class='cl-center-text'><span style='display:inline-block;'>" +
                "<div id='id-inner-registration-and-login' class='grid_6 cl-text-14pt-format'>" +
                "</div></span></div>");

            if ("login_html" in jsonResponse && jsonResponse["login_html"]) {
                $('#id-show-registration-and-login').append(jsonResponse["login_html"]);
            }

            if (additionalText) {
                $('#id-show-registration-and-login').append("<div class='cl-center-text'><span style='display:inline-block;'>" +
                    "<div id='id-inner-registration-and-login' class='grid_6 cl-text-14pt-format'>" +
                    additionalText + "<br><br></div></span></div>");
            }

            if ("signup_html" in jsonResponse && jsonResponse["signup_html"]) {
                $('#id-show-registration-and-login').append("<div class='cl-center-text'><span style='display:inline-block;'>" +
                    jsonResponse["signup_html"] + "</span></div>");
            }

            $('#id-show-registration-and-login').find(".cl-registration_html-additionalText").html(additionalText);
            $('#id-show-registration-and-login').dialog({
                modal: true,
                show: {effect: 'fade',
                       duration: 300},
                position: {
                    my: "center",
                    at: "center"
                },
                width: 'auto',
                height: 'auto'
            });


            $('#id-show-registration-and-login').dialog('open');



            // set the background image on the dialog titlebar to be the same as the navigation bar
            $('#id-show-registration-and-login').parent().find('.ui-widget-header').css({'background-image': 'none' });
            // hide the background color of the titlebar and remove the border - basically we are over-riding the default
            // jquery UI default values to match the color scheme of the current site.
            $('#id-show-registration-and-login').parent().find('.ui-widget-header').css({'background-color': '#FFF' });
            $('#id-show-registration-and-login').parent().find('.ui-widget-header').css({'border': '0px' });
        },
        error: function(jqXHR, textStatus, errorThrown) {
            reportAjaxError(textStatus, errorThrown, "showRegistrationAndLogin", "error");
            $('#id-show-registration-and-login').html($("#id-unknown-error-reload-page").html());
            $('#id-show-registration-and-login').dialog();
        },
        complete: function() {
            showRegistrationAndLogin.alreadyClicked = false;
            $('#id-show-loading-spinner').hide();

            if (optionalPassedInUsername !== "undefined" && optionalPassedInUsername) {
                $('#id-login_fields-username_email').val(optionalPassedInUsername);
                $('#id-login_fields-username_email').focus();
            }
        }
    });
}

function handleClickOnContactIcon(sectionName, uid, showRegistrationDialogWhenClicked, registrationPromptText) {

    try {
        var submitButtonId = "#id-submit-" + sectionName;


        $(submitButtonId).click(function() {
            if (!showRegistrationDialogWhenClicked) {
                $.ajax({
                    type: 'post',
                    url:  "/rs/store_initiate_contact/" + uid + "/",
                    data: { 'section_name' : sectionName},
                    success: function(data) {
                        if (data === "OK") {
                            getJsonInitiateContactSettings(uid);
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
                showRegistrationAndLogin(registrationPromptText);
                return false;
            }
        });
    } catch (err) {
        reportTryCatchError( err, "handleClickOnContactIcon");
    }
}

function hideSpinnerAndShowSubmit(submitButtonId, ajaxSpinnerId, captchaDivId) {
    $(submitButtonId).show();
    $(ajaxSpinnerId).hide();
    $(captchaDivId).show();
}

function reloadSubmitAndRecaptcha(submitButtonId, ajaxSpinnerId, captchaDivId, captchaBypassString) {

    try {
        if (captchaBypassString === "no_bypass") {
            Recaptcha.reload();
        }
        hideSpinnerAndShowSubmit(submitButtonId, ajaxSpinnerId, captchaDivId);
    } catch(err) {
        reportTryCatchError( err, "reloadSubmitAndRecaptcha");
    }
}



function showDialogPopup(popupBoxId, height, width, showXCloseIcon) {

    $(popupBoxId).dialog({
        modal: true,
        title: "",
        show: 'clip',
        hide: 'clip',
        width: width,
        height: height,
        position: 'center'
    });

    if (showXCloseIcon === false) {
        $(popupBoxId).dialog('option', 'dialogClass',  'hide-x-close');
    } else {
        // remove the hide-x-close class - this is a bit complicated because there is not built-in functionality for removing a class
        // Get the existing class string
        var dlgClass = $(popupBoxId).dialog("option", "dialogClass");
        // remove the offending class
        dlgClass = dlgClass.replace('hide-x-close', "");
        // reset the dialog class
        $(popupBoxId).dialog("option", "dialogClass", dlgClass);
    }
}

function handleDialogPopupCloseButton(popupBoxId, closeButtonId) {

    $(popupBoxId).ready(function(){
        $(closeButtonId).button();
        $(closeButtonId).on('click', function() {
            $(popupBoxId).dialog("close");
        });
    });
}

function submitSendMail(sectionName, submitButtonId, captchaDivId, toUid, captchaBypassString, haveSentMessagesString,
                          successStatusString, errorStatusString) {

    try {
        // hide the submit button, to prevent double-click
        var ajaxSpinnerId = "#id-show-ajax-spinner-captcha";
        var myurl = "/rs/store_" + sectionName + "/" + toUid + "/" + captchaBypassString + "/" + haveSentMessagesString + "/";
        var mydata = $("form#id-" + sectionName + "-form").serialize();
        $(submitButtonId).hide();
        $(ajaxSpinnerId).show();
        $(captchaDivId).hide();

        // remove error message if previous submission failed
        $('#id-submit_send_mail-status').remove();

        $.ajax({
            type: 'post',
            url: myurl,
            data: (mydata),
            timeout: 15000, // 15 second timeout
            success: function (htmlResponse) {
                // success means that the server has responded with a valid response - does not necessarily mean that
                // the message was successfully sent. The value in the htmlResponse lets us know the sent status.
                //
                // put the load inside the callback, since we must ensure that the data has been
                // loaded
                //
                // load the message summary
                if (htmlResponse === "OK") {
                    $(submitButtonId).after('<div id="id-submit_send_mail-status" class="cl-color-text"><br>' + successStatusString + '!<br></div>');

                    $("#id-num_messages_sent_feedback_and_count").hide();

                    $("#id-display-" + sectionName + "-section").load("/rs/ajax/load_" + sectionName + "/" + toUid + "/" + rnd() + "/", function() {
                        $("#id-highlight-div").effect("highlight", {color:'#FFEEFF'}, 3000);
                    });

                    if (sectionName !== "send_mail") {
                        // reload the textarea -- but not for the "send_mail" section, since for this section textarea was already
                        // reloaded in the load_send_mail ajax call
                        $("#id-edit-" + sectionName + "-section").load("/rs/ajax/load_mail_textarea/" + toUid + "/" + sectionName + "/");
                    }

                    $(ajaxSpinnerId).hide();
                } else if (htmlResponse === "user_is_missing_profile_description") {
                    // we must get the user to fill in more information in their profile before they will be permitted to send a message.
                    // pop-up a dialog box that allows them to enter in the appropriate information into their profile, at which point they
                    // should be able to re-submit their message.
                    showDialogPopup("#id-about_user_is_empty_popup", 500, 800, true);
                    hideSpinnerAndShowSubmit(submitButtonId, ajaxSpinnerId, captchaDivId);

                } else if (htmlResponse === "captcha_is_incorrect") {
                    var badCaptchaMessage = $('#id-common_translations-incorrect_captcha').text();
                    $(submitButtonId).before('<div id="id-submit_send_mail-status" class="cl-warning-text cl-text-24pt-format"><br>' + badCaptchaMessage + '<br></div>');
                    reloadSubmitAndRecaptcha(submitButtonId, ajaxSpinnerId, captchaDivId, captchaBypassString);

                } else if (htmlResponse === "empty_send_message") {
                    var emptyMessageMessage = $('#id-common_translations-empty_send_message').text();
                    $(submitButtonId).before('<div id="id-submit_send_mail-status" class="cl-warning-text cl-text-24pt-format"><br>' + emptyMessageMessage + '<br></div>');
                    hideSpinnerAndShowSubmit(submitButtonId, ajaxSpinnerId, captchaDivId);

                } else {
                    // unknown status returned.
                    $(submitButtonId).before('<div id="id-submit_send_mail-status"><br>' + htmlResponse + '<br></div>');
                    reloadSubmitAndRecaptcha(submitButtonId, ajaxSpinnerId, captchaDivId, captchaBypassString);
                    reportAjaxError('', '', "submit_send_mail - unknown html response: " + htmlResponse);
                }

            },
            error: function(jqXHR, textStatus, errorThrown) {
                var errorString;
                if (jqXHR.responseText !== undefined) {
                    errorString = jqXHR.responseText;
                } else {
                    errorString = errorStatusString;
                }
                $(submitButtonId).before('<div id="id-submit_send_mail-status" class="cl-warning-text cl-text-24pt-format"><br>' + errorString + '!<br></div>');
                reloadSubmitAndRecaptcha(submitButtonId, ajaxSpinnerId, captchaDivId, captchaBypassString);
                var warningLevel;
                if (errorThrown === "timeout") {
                    warningLevel = "warning";
                } else {
                    warningLevel = "error";
                }
                reportAjaxError(textStatus, errorThrown, "submit_send_mail", warningLevel);
            }
        });
    } catch(err) {
        reportTryCatchError( err, "submit_send_mail");
    }
}


function handleSubmitSendMailButton(sectionName, toUid, captchaBypassString, haveSentMessagesString, successStatusString, errorStatusString) {
    // setup submit button and associate the action when clicked
    // sectionName is either "send_mail_from_profile_checkbox_[yes|no]" or "send_mail" -- 
    // if the event is "send_mail_from_profile", then only a small
    // summary will be loaded -- if it is a "send_mail", then the entire chain of mail messages will be reloaded.

    try {
        var submitButtonId = "#id-submit-" + sectionName;
        var captchaDivId = "#id-" + sectionName + "-captcha";

        $(submitButtonId).click(function() {
            submitSendMail(sectionName, submitButtonId, captchaDivId, toUid, captchaBypassString, haveSentMessagesString, successStatusString, errorStatusString);
        });
        // if enter key is pressed inside the captcha, this should trigger a sumbit
        // Note: IE6 requires that the trigger is on keydown..
        $(captchaDivId).keydown(function(e) {
            if (e.keyCode === 13) {
                submitSendMail(sectionName, submitButtonId, captchaDivId, toUid, captchaBypassString, haveSentMessagesString, successStatusString, errorStatusString);
                e.stopImmediatePropagation();
                e.stopPropagation();
                return false;
            }
        });
        mouseoverButtonHandler($(submitButtonId));
    } catch(err) {
        reportTryCatchError( err, "handleSubmitSendMailButton");
    }
}


function showRegistrationDialogOnClick(sectionName, registrationPromptText) {
    var submitButtonId = "#id-submit-" + sectionName;
    $(submitButtonId).click(function() {
        showRegistrationAndLogin(registrationPromptText);
    });
}

//function submitVerifyCaptcha(sectionName, submitButtonId, captchaDivId) {
//
//    try {
//        // hide the submit button, to prevent double-click
//        var ajaxSpinnerId = "#id-show-ajax-spinner-captcha";
//        var myurl = "/rs/store_" + sectionName + "/";
//        var mydata = $("form#id-" + sectionName + "-form").serialize();
//        var captchaStatusId = "#id-" + sectionName + "-status";
//        $(submitButtonId).hide();
//        $(ajaxSpinnerId).show();
//        $(captchaDivId).hide();
//
//        $.ajax({
//            type: 'post',
//            url: myurl,
//            data: (mydata),
//            timeout: 15000, // 15 second timeout
//            success: function (htmlResponse) {
//                // if successful, reload the entire page so that all buttons are
//                // enables, and the user can edit their profile
//                if (htmlResponse === "Fail") {
//                    $(captchaStatusId).html('<strong>Captcha incorrecto, intentalo de nuevo</strong>');
//                    reloadSubmitAndRecaptcha(submitButtonId, ajaxSpinnerId, captchaDivId, "no_bypass");
//                } else {
//                    window.location.href = htmlResponse; // re-direct to user profile
//                }
//
//            },
//            error: function(jqXHR, textStatus, errorThrown) {
//                $(captchaStatusId).html('<strong>Error, intentalo de nuevo</strong>');
//                reloadSubmitAndRecaptcha(submitButtonId, ajaxSpinnerId, captchaDivId, "no_bypass");
//                reportAjaxError(textStatus, errorThrown, "submitVerifyCaptcha");
//            }
//        });
//    } catch(err) {
//        reportTryCatchError( err, "submitVerifyCaptcha");
//    }
//}
//
//
//function handleVerifyCaptcha(sectionName) {
//    // setup submit button and associate the action when clicked
//
//    try {
//        var submitButtonId = "#id-submit-" + sectionName;
//        var captchaDivId = "#id-" + sectionName + "-captcha";
//
//        $(submitButtonId).click(function() {
//            submitVerifyCaptcha(sectionName, submitButtonId, captchaDivId);
//        });
//
//        // if enter key is pressed inside the captcha, this should trigger a sumbit
//        $(captchaDivId).keydown(function(e) {
//            if (e.keyCode === 13) {
//                submitVerifyCaptcha(sectionName, submitButtonId, captchaDivId);
//                e.stopImmediatePropagation();
//                e.stopPropagation();
//                return false;
//            }
//        });
//
//        mouseoverButtonHandler($(submitButtonId));
//    } catch(err) {
//        reportTryCatchError( err, "handleVerifyCaptcha");
//    }
//}


function handleClickOnUpdateMessageActionIcon(haveSentMessagesId, toUid, action, withCheckbox) {
    // this function handles a click on the icon beside the message, and refreshes the message
    // to reflect the updated status
    // withCheckbox: "yes" or "no"

    try {
        var iconId = "#id-" + action + "-have_sent_messages-" + haveSentMessagesId;
        var sectionId = "#id-have_sent_messages-" + haveSentMessagesId;

        $(iconId).click(function() {
            var postUrl = "/rs/ajax/" + action + "_message/";
            $.post(postUrl + haveSentMessagesId + "/", function() {
                // we call "load_send_mail_from_profile, because this function returns just a summary of the converstion
                $(sectionId).load("/rs/ajax/load_send_mail_from_profile_checkbox_" + withCheckbox + "/" + toUid + "/" + rnd() + "/");

                // prevent link from being followed
                return false;
            });

            // prevent scrolling to the top of the page when html is updated
            return false;
        });
    } catch (err) {
        reportTryCatchError( err, "handleClickOnUpdateMessageActionIcon");
    }
}




function handlePostButtonWithConfirmationOfResult(sectionName, uid) {

    try {
        var submissionStatusId = "#id-" + sectionName + "-status";
        var submitButtonId = "#id-submit-" + sectionName;

        $(submitButtonId).click(function() {
            $(submissionStatusId).html('Processing .....');

            $.ajax({
                type: 'post',
                url: "/rs/store_" + sectionName + "/" + uid + "/",
                data: $("form#id-" + sectionName + "-form").serialize(),
                timeout: 15000, // 15 second timeout
                // html_response contains the result of the action -- ie. success, failur, etc.
                success: function (htmlResponse) {
                    $(submissionStatusId).html(htmlResponse);
                    $(submitButtonId).hide();
                },
                error: function (jqXHR, textStatus, errorThrown) {
                    $(submissionStatusId).html('<strong>Error posting to the server, please try again</strong>');
                    reportAjaxError(textStatus, errorThrown, "handlePostButtonWithConfirmationOfResult");
                }

            });
        });
        mouseoverButtonHandler($(submitButtonId));
    } catch(err) {
        reportTryCatchError( err, "handlePostButtonWithConfirmationOfResult");
    }
}

function formatNumberLength(num, length) {
    // funtion that takes a number, and a length, and prints out a string representation of that number
    // with leading blanks to ensure that the string is the desired length
    var r = "" + num;
    while (r.length < length) {
        r = " " + r;
    }
    return r;
}



function clearFieldsErrors(fieldsType, errorsDict) {
    // fieldsType is either signup_fields or login_fields

    for (var key in errorsDict) {
        var inputFieldIdSelector = "#id-"+ fieldsType + "-" + key;
        $(inputFieldIdSelector).removeClass("cl-highlight_border");
    }
}

function clearBothRegistrationAndLoginFieldsErrors() {
    clearFieldsErrors("login_fields", loginErrorsDict);
    $("#id-password-prompt").removeClass("cl-highlight_border");
    $("#id-password-input").removeClass("cl-highlight_border");

    clearFieldsErrors("signup_fields" , registrationErrorsDict);
}

function showFieldsErrors(fieldsType, errorsDict, extraHtml, whereToPlaceDialog) {
    // fieldsType is either signup_fields or login_fields

    // dummy input to take the autofocus away from the "have you forgot password" link, otherwise it
    // automatically follows the link on enter
    var errorHtml = '<input type="hidden" autofocus="autofocus" />';
    errorHtml += '<ul>';

    // loop over the objects in the errorsDict
    for (var key in errorsDict) {
        var inputFieldIdSelector = "#id-" + fieldsType + "-" + key;
        $(inputFieldIdSelector).addClass("cl-highlight_border");
        if (errorsDict[key]) {
            errorHtml += '<li class="cl-indent">'+ errorsDict[key];
        }
    }
    errorHtml += '</ul>';
    errorHtml += extraHtml;
    $('#id-dialog_box_for_user_feedback').html(errorHtml);
    $('#id-dialog_box_for_user_feedback').dialog({
        width: 400,
        modal: false,
        position: {
            my: "center",
            at: "center",
            of: whereToPlaceDialog
        }
    }).dialog('close').dialog('open');
}

function closeDialogBoxForUserFeedback(){
    if ($('#id-dialog_box_for_user_feedback').is(':data(dialog)')) {
        $('#id-dialog_box_for_user_feedback').dialog('close');
    }
}