
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


// This file contains the routines that handle when the hash part of the URL is modified. Note that
// in the common_wrapper.html file, we re-direct any URLs that do not have /ajax/#!.... to a /ajax/#!...
// URL. This generally should only be necessary once per user session since afterwards all URLs are hashbanged.


if (!disable_jquery_address) {
// we don't use jquery address for IE versions less than 8.0 - they have too many memory leaks for good ajax performance

// Simple log
var log = function(msg) {
// ensure that the .page div is not hidden (display:none;) before expecting to see the log data.
    
//        if (!$('.log').size()) {
//            $('<div class="log" />').appendTo('.page');
//        }
//        $('.log').append(msg + "<br>");
    };




function ChangeLocationSucess(data, textStatus, div_id) {

    // clear old data from the dive that we are over-writing - this is needed to prevent memory leaks

    try {
        var div = $(div_id);
        div.off('click.jquery_address');  //unwire the jquery.address bindings
        div.off('submit.jquery_address');  //unwire the jquery.address bindings
        DoUnload(); // call custom functions for freeing up memory/event handlers
        div.empty();
        div.html(data); // HTML replacement

        // sometimes the code that is required for renderingthe buttons is not fully loaded before these calls are made
        // therefore we ignore errors if they occur.
        try {FB.XFBML.parse();} catch(err) {} //re-render FB like button
        try {gapi.plusone.go();} catch(err) {}  // render google +1 buttons
    } catch(err) {
        report_try_catch_error( err, "ChangeLocationSucess()") ;
    }
}


// Event handlers
$.address.init(function(event) {

    $(document)
    .off('click.address_handler', 'a.cl-setlang')
    .on('click.address_handler', 'a.cl-setlang', function() {
        // Note: the ajax re-direct takes place directly in the setlang link, this part of the code
        // only sets the users language preferences on the server (and ignore the return value).
        var setlang_path = this.href;
        $.ajax({
            url: setlang_path,
            data: {'is_ajax_call': 'yes'},
            cache: false,
            success: function () {
                // do nothing - ignore the returned result- it is just a redirect
            },
            error: function (jqXHR, textStatus, errorThrown) {
                report_ajax_error(textStatus, errorThrown, "$address.init().function(event)");
            }
        });
    });   
}).change(function(event) {
    //log('change: "' + event.value + '"');
    try {

        if (location.search.match(/_escaped_fragment_/)) {
            return;
        }

        var hashed_path = event.value;

        if (!hashed_path) hashed_path = "/"; // if it is empty, display the home page

        $('div#id-show_spinner_while_loading:hidden').stop(true, true).fadeIn(5000);
        // ********* if page loading does weird stuff, look here first ***********
        // ** the following line is where the page actually gets re-loaded
        //report_javascript_debugging_info_on_server("Calling URL " + hashed_path + " directly as an ajax call" );
        var jqXHR = $.ajax({
            type: 'get',
            data: {'is_ajax_call' : 'yes'},
            url:   hashed_path,
            timeout: 15000,
            cache: false,
            dataType: 'json' // response type
        });
        
        jqXHR.done(function(json_response, textStatus) {
            try {
                if (json_response.redirect_url) {
                    //report_javascript_debugging_info_on_server("Redirecting to: " + json_response.redirect_url + " event.value: " + event.value);
                    // This function will POST the given error_text
                    //window.location.replace(json_response.redirect_url);
                    $.address.value(json_response.redirect_url);
                }
                else {
                    // Clear and overwrite the HTML in the body - this is where the actual page load is done
                    ChangeLocationSucess(json_response.html, textStatus, "#id-body_main_html");


                    //report_javascript_debugging_info_on_server("Got html response on hashed_path: " + hashed_path + " event.value: " + event.value);
                    window.scroll(0,0); // since it is a new page, scroll to the top
                }
                
            } catch(err) {
                report_try_catch_error( err, "$address.init().change() inner try/catch - success: ");
            }
        }).fail(function (jqXHR, textStatus, errorThrown) {
            report_ajax_error(textStatus, errorThrown, "$address.init().change() hashed_path:" + hashed_path + " event.value: " + event.value);

            if (textStatus == "timeout") {
                // force a hard re-load - re-direct back to the non-hashed URL which should cause
                // a "hard" reload (javascript and html)
                window.location.replace(hashed_path);
            }
            else {
                log("error");
                window.location.replace("/"); // error occured - re-direct back to login
            }

        }).always(function () {
            $('div#id-show_spinner_while_loading').hide();
            $("#id-simple-search-form").find(':disabled').removeAttr("disabled");
        });

        jqXHR = null;

//        if (event.value != "/en/" && event.value != "/es/")
//        {
//            setTimeout(function(){
//                    $.address.update()
//                }
//                ,2000);
//        }

    } catch(err) {
        report_try_catch_error( err, "$address.init().change() - outer try/catch");
    }

}).internalChange(function(event) {

}).bind('externalChange', {msg: 'The value of the event is "{value}".'}, function(event) {

});

}