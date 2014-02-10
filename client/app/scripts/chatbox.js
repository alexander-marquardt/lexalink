/*
 * Orignal Copyright 2010, Wen Pu (dexterpu at gmail dot com)
 * Dual licensed under the MIT or GPL Version 2 licenses.
 * http://jquery.org/license
 *
 * Check out http://www.cs.illinois.edu/homes/wenpu1/chatbox.html for document
 *
 * Depends on jquery.ui.core, jquery.ui.widiget, jquery.ui.effect
 * 
 * Also uses some styles for jquery.ui.dialog
 *
 * **Extensive** LexaLink related modifications made by Alexander Marquardt
 */

/*var chatbox_gobals = new function() { // new instantiates an object
    chatbox_self = this;

    chatbox_self.chatboxIdleObject = chatboxManager.trackUserActivityForOnlineStatus();

}*/






// TODO: implement destroy()
var initJqueryUiChatbox = function($){

    // This function sets up the JqueryUI functions, and is automatically executed 

    try {

        $.widget("js.chatbox", {

            options: {
                id: null, //id for the DOM element
                title: null, // title of the chatbox
                allow_elimination: true, // show the X in the top right corner - this can be over-ridden
                include_chatbox_input: true,
                type_of_conversation: '', // override with "one_on_one" or "group"
                hidden: false,
                offset: 0, // default relative to right edge of the browser window - over-ridden
                width: 0, // default width of the chatbox - over-ridden
                just_opened : false, // for newly created boxes, we temporarily ignore the "keep_open" status from the server
                messageSent: function() {}, //over-ride this
                boxClosed: function(box_id) {}, // called when the close icon is clicked - over-ridden
                minimizeBoxWasClicked: function(box_id) {}, // over-ridden
                maximizeBoxWasClicked: function(box_id) {}, // over-ridden
                boxManager: {
                    // thanks to the widget factory facility
                    // similar to http://alexsexton.com/?p=51
                    init: function(elem) {
                        try {
                            this.elem = elem;

                            // highlightLock is used for the bounce effect, to prevent it from attempting to
                            // start bouncing (or whatever highlight we use), when it is already in the middle of bouncing.
                            this.highlightLock = false;
                        } catch(err) {
                            reportTryCatchError( err, "initJqueryUiChatbox.init()");
                        }
                    },
                    getBox: function() {
                        var self = this;
                        return self;
                    },
                    addMsg: function(sender_name, msg, highlight_box_enabled) {
                        // This function will be called when a chatbox needs to be updated with additional
                        // messages, but it will not erase the history. This must be carefully coordinated
                        // with the information that we decide to send from the server.
                        try {
                            var self = this;
                            var box = self.elem.uiChatboxLog;
                            var e = document.createElement('div');
                            $(e).html("<b>" + sender_name +":</b> " + msg)
                            .addClass("ui-chatbox-msg ui-chatbox-highlight-link cl-literally-display-user-text");
                            box.append(e);
                            self._scrollToBottom();

                            if (highlight_box_enabled) {
                                if(!self.elem.uiChatboxTitlebar.hasClass("ui-state-focus")) {
                                    self.highlightBox();
                                }
                            }
                        } catch(err) {
                            reportTryCatchError( err, "initJqueryUiChatbox.addMsg()");
                        }
                    },
                    refreshBox: function(msg) {
                        try {
                            // This function will be called when a chatbox needs to be totally refreshed.
                            // This is intended for the contact list.
                            var self = this;
                            var box = self.elem.uiChatboxLog;
                            box.html(msg);
                        } catch(err) {
                            reportTryCatchError( err, "initJqueryUiChatbox.refreshBox()");
                        }
                    },
                    highlightBox: function() {
                        try {
                            //this.elem.uiChatbox.addClass("ui-state-highlight");
                            var self = this;
                            if (!self.elem.uiChatboxContent.is(":visible")) {
                                // if it is not currently visible, show it
                                self.elem.uiChatboxContent.toggle();
                            }
                            //self.elem.uiChatboxTitlebar.effect("highlight", {}, 300);

                            if (!self.highlightLock) {
                                // highlightLock - prevent call to "highlight" effect until current effect has terminated.
                                // Otherwise, bad things happen (widgets disappear etc.)
                                self.highlightLock = true;
                                self.elem.uiChatboxTitlebar.effect("highlight", {color: '#FFEEFF'}, 3000, function() {
                                    self.highlightLock = false;
                                    self._scrollToBottom();
                                });
                            }
                        } catch(err) {
                            reportTryCatchError( err, "initJqueryUiChatbox.highlightBox()");
                        }
                    },
                    resizeWidth: function(width) {
                        this.elem._setWidth(width);
                    },

                    setChatboxInputBox: function (new_value) {
                        this.elem.uiChatboxInputBox.val(new_value);
                    },
                    setBoxOffset: function(offset) {
                        this.elem._position(offset);
                    },
                    hideBox: function () {
                        // Hide the entire chatbox - ie. it is "eliminated"
                        this.elem.uiChatbox.hide();
                    },
                    chatboxLogHeight: function (new_height) {
                        // set *or* get the height of the chatbox - if blank value is passed in, will get the height
                        return this.elem.uiChatboxLog.height(new_height);
                    },
                    hideChatboxContent: function () {
                        this.elem.uiChatboxContent.hide();
                    },
                    showChatboxContent: function () {
                        this.elem.uiChatboxContent.show();
                    },
                    addCssToChatbox: function (property, new_class) {
                        this.elem.uiChatbox.css(property, new_class);
                    },
                    addIdToChatbox: function (new_id) {
                        this.elem.uiChatbox.attr('id', new_id);
                    },
                    changeBoxTitle: function(new_title) {
                        this.elem.uiChatboxTitle.html(new_title);
                    },
                    addClassToChatbox: function(class_name) {
                        this.elem.uiChatbox.addClass(class_name);
                    },
                    addClassToBoxTitle: function(class_name) {
                        this.elem.uiChatboxTitle.addClass(class_name);
                    },
                    hyperlinkWrapBoxTitle: function(hyperlink_to_profile) {
                       this.elem.uiChatboxTitle.wrap(hyperlink_to_profile);
                    },
                    toggleBox: function() {
                        this.elem.uiChatbox.toggle();
                    },
                    minimizeBox: function() {
                        this.elem.uiChatboxContent.hide();
                    },
                    maximizeBox: function() {
                        this.elem.uiChatboxContent.show();
                    },
                    addClassToUIChatboxLog: function (class_name) {
                        this.elem.uiChatboxLog.addClass(class_name);
                    },

                    _scrollToBottom: function() {
                        try {
                            var box = this.elem.uiChatboxLog;
                            if (!$(box).hasClass("cl-chatbox-log-has-focus")) {
                                // we only scroll if the user is not focused inside the chatbox - this is because we want them
                                // to be able to "pause" the scrolling at a given point (by putting the cursor in the log),
                                // irrespective of incomming messages
                                box.scrollTop(box.get(0).scrollHeight);
                            }
                        } catch(err) {
                            reportTryCatchError( err, "initJqueryUiChatbox._scrollToBottom()");
                        }
                    },

                    // Optional status selector (online/offline)
                    uiChatboxOnlineSelector: function () {
                        try {
                            var self=this;
                            var go_offline_text = $('#id-disactivate-chat-button-text').html();
                            self.elem.uiChatboxTitlebar.after($('<button class="ui-chatbox-submit-button ' +
                                    'ui-remove-corner-all"' +
                                    'id="id-go-offline-button">' + go_offline_text + '</button>'));
                            $('#id-go-offline-button').button();
                            $('#id-go-offline-button').click(function() {
                                chanUtils.executeGoOfflineOnClient();
                                $("#main").chatbox("option", "boxManager").hideChatboxContent();

                                // the following interactions occur with the server, and so should only
                                // occur once, and therefore we do not put them in the "executeGoOfflineOnClient" function
                                chanUtils.closeAllChatboxesOnServer();
                                chanUtils.updateChatBoxesStatusOnServer("chat_disabled");
                                return false;
                            });

                            var go_online_text = $('#id-activate-chat-button-text').html();
                            $('#id-go-offline-button').after($('<button class="ui-chatbox-submit-button ' +
                                    'ui-remove-corner-all"' +
                                    'id="id-go-online-button">' + go_online_text + '</button>'));
                            $('#id-go-online-button').button();
                            $('#id-go-online-button').hide();
                            $('#id-go-online-button').click(function() {
                                chanUtils.updateChatBoxesStatusOnServer("chat_enabled");
                                chanUtils.executeGoOnlineOnClient();
                                return false;
                            });

                            if (lt_ie8) {
                                $('#id-go-online-button').css('width', self.elem.options.width);
                                $('#id-go-offline-button').css('width', self.elem.options.width);
                            }
                        } catch(err) {
                            reportTryCatchError( err, "initJqueryUiChatbox.uiChatboxOnlineSelector()");
                        }
                    },

                    uiChatboxCreateGroupButton: function () {
                        try {
                            var self=this;
                            var create_group_text = $('#id-create-group-button-text').html();
                            self.elem.uiChatboxTitlebar.after($('<button class="ui-chatbox-submit-button ' +
                                    'ui-remove-corner-all"' +
                                    'id="id-create-group-button">' + create_group_text + '</button>'));
                            $('#id-create-group-button').button();
                            $('#id-create-group-button').click(function() {
                                $("#id-create-group-dialog").dialog();
                                return false;
                            });
                        } catch(err) {
                            reportTryCatchError( err, "initJqueryUiChatbox.uiChatboxCreateGroupButton()");
                        }
                    },

                    uiChatboxShowGroupMembersButton: function (group_id, box_title) {

                        try {
                            var self=this;
                            var chat_group_members_text = $('#id-chat_group_members-button-text').html();
                            self.elem.uiChatboxTitlebar.after($('<button class="ui-chatbox-submit-button ' +
                                    'ui-remove-corner-all"' +
                                    'id="id-chat_group_members-button-' + group_id + '">' + chat_group_members_text + '</button>'));
                            $('#id-chat_group_members-button-' + group_id).button();
                            $('#id-chat_group_members-button-' + group_id).click(function(event) {
                                chanUtils.openGroupMembersDialog(group_id, box_title);
                            });
                        } catch(err) {
                            reportTryCatchError( err, "initJqueryUiChatbox.uiChatboxShowGroupMembersButton()");
                        }
                    },


                    uiChatboxVideoButton: function (other_uid) {

                        // TODO - give each button a unique name - otherwise calls will be random. ie. Include the other_uid in the button id.
    //                    var self=this;
    //                    var videocall_text = $('#id-videocall-button-text').html();
    //                    self.elem.uiChatboxTitlebar.after($('<button class="ui-chatbox-submit-button ' +
    //                            'ui-remove-corner-all"' +
    //                            'id="id-videochat-button">' + videocall_text + '</button>'));
    //                    $('#id-videochat-button').button();
    //                    $('#id-videochat-button').click(function(event) {
    //                        //var otherUsername = self.elem.uiChatboxTitle.text();
    //                        var windowName = "Video Chat";
    //                        var video_window = window.open ("/videochat_window/video_phone.html?other_uid=" + other_uid + '&initiate_call=yes&time=' + rnd(), windowName,"menubar=1,resizable=1,width=520,height=440");
    //                        video_window.focus();
    //                        return false;
    //                    });

                    }
                }
            },

            widget: function() {
                try {
                    return this.uiChatbox;
                } catch(err) {
                    reportTryCatchError( err, "initJqueryUiChatbox.widget()");
                }
                return false; // prevent jslint warning
            },

            _create: function(){

                try {
                    var self = this,

                    options = self.options,

                    title = options.title || "No Title",

                    // chatbox
                    uiChatbox = (self.uiChatbox = $('<div></div>'))
                    .appendTo(document.body)
                    .addClass('ui-widget ui-corner-top ui-chatbox ')
                    .attr('outline', 0),

                    // titlebar
                    uiChatboxTitlebar = (self.uiChatboxTitlebar = $('<div></div>'))
                    .addClass('ui-chatbox-titlebar ui-widget-header ui-corner-top ui-helper-clearfix ')
                    .appendTo(uiChatbox),


                    uiChatboxTitle = (self.uiChatboxTitle = $('<span class="ui-chatbox-title"></span>'))
                    .html(title)
                    .appendTo(uiChatboxTitlebar),
                    uiChatboxTitlebarClose = (self.uiChatboxTitlebarClose =
                            self._AddEliminationToWidget()),


                    uiChatboxTitlebarMinimize = (self.uiChatboxTitlebarMinimize = $('<a href="#"></a>'))
                    .addClass('ui-corner-all ' +
                          'ui-chatbox-icon'
                         )
                    .attr('role', 'button')
                    .hover(function() {uiChatboxTitlebarMinimize.addClass('ui-state-hover');},
                           function() {uiChatboxTitlebarMinimize.removeClass('ui-state-hover');})
                    .click(function(event) {

                        try {
                            if(!self.uiChatboxContent.is(":visible")) {
                                self.uiChatboxContent.show();
                                self.options.boxManager._scrollToBottom();
                                self.options.maximizeBoxWasClicked(self.options.id);
                            } else {
                                self.uiChatboxContent.hide();
                                self.options.minimizeBoxWasClicked(self.options.id);
                            }

                            return false;
                        } catch(err) {
                            reportTryCatchError( err, "initJqueryUiChatbox._create.click()", "warning");
                        }
                        return false; // prevent jslint warning
                    })
                    .appendTo(uiChatboxTitlebar),


                    uiChatboxTitlebarMinimizeText = $('<span></span>')
                    .addClass('ui-icon ' +
                          'ui-icon-minusthick')
                    .text('minimize')
                    .appendTo(uiChatboxTitlebarMinimize),


                    // content
                    uiChatboxContent = (self.uiChatboxContent = $('<div></div>'))
                    .addClass('ui-widget-content ' +
                          'ui-chatbox-content '
                         )
                    .appendTo(uiChatbox),

                    uiChatboxLog = (self.uiChatboxLog = self.element)
                    //.show()
                    .addClass('ui-widget-content '+
                          'ui-chatbox-log'
                         )
                    .appendTo(uiChatboxContent)
                    .mouseenter(function() {
                        $(this).addClass("cl-chatbox-log-has-focus");
                    })
                    .mouseleave(function() {
                        $(this).removeClass("cl-chatbox-log-has-focus");
                    }),


                    uiChatboxInput = (self.uiChatboxInput =
                             self._AddChatboxInputToWidget(options.include_chatbox_input));

                    self._setWidth(self.options.width);
                    self._position(self.options.offset);

                    self.options.boxManager.init(self);

                    if(!self.options.hidden) {
                    uiChatbox.show();
                    }
                } catch(err) {
                    reportTryCatchError( err, "initJqueryUiChatbox._create()");
                }
            },

            _setOption: function(option, value) {
                try {
                    if(value !== null){
                        switch(option) {
                        case "hidden":
                            if(value) {
                            this.uiChatbox.hide();
                            }
                            else {
                            this.uiChatbox.show();
                            }
                            break;
                        case "offset":
                            this._position(value);
                            break;
                        case "width":
                            this._setWidth(value);
                            break;
                        default:
                            break;
                        }
                    }

                    $.Widget.prototype._setOption.apply(this, arguments);
                } catch(err) {
                    reportTryCatchError( err, "initJqueryUiChatbox._setOption()");
                }
            },

            _setWidth: function(width) {
                try {
                    this.uiChatboxTitlebar.width(width + "px");
                    this.uiChatboxLog.width(width + "px");
                    // this is a hack to subtract out the padding
                    if (this.options.include_chatbox_input) {
                        this.uiChatboxInputBox.css("width", (width - 4) + "px");
                    }
                } catch(err) {
                    reportTryCatchError( err, "initJqueryUiChatbox._setWidth()");
                }
            },

            _position: function(offset) {
                this.uiChatbox.css("right", offset);
            },


            _AddEliminationToWidget: function() {
                // This is the code that adds the "eliminate" (the X) in the top right corner
                // of the chatboxes.

                try {
                    var self = this;
                    var uiChatboxTitlebarClose = null;
                    var uiChatboxTitlebarCloseText = null;
                    if (self.options.allow_elimination) {
                        uiChatboxTitlebarClose = $('<a href="#"></a>')
                        .addClass('ui-corner-all ' + 'ui-chatbox-icon' )
                        .attr('role', 'button')
                        .hover(function() {uiChatboxTitlebarClose.addClass('ui-state-hover');},
                               function() {uiChatboxTitlebarClose.removeClass('ui-state-hover');})
                        .click(function(event) {
                            self.uiChatbox.hide();
                            self.options.boxClosed(self.options.id);
                            return false;
                        })
                        .appendTo(self.uiChatboxTitlebar);

                        uiChatboxTitlebarCloseText = $('<span></span>')
                        .addClass('ui-icon ' +
                              'ui-icon-closethick')
                        .text('close')
                        .appendTo(uiChatboxTitlebarClose);
                    }
                    return uiChatboxTitlebarClose;
                } catch(err) {
                    reportTryCatchError( err, "AddEliminationToWidget");
                }
                return false; // prevent jslint warning
            },


            _AddChatboxInputToWidget : function(include_chatbox_input) {

                // modifies uiChatboxInput to contain uiChatboxInputBox. Note: "self" is modified
                // to contain the newly created textarea "uiChatboxInputBox"

                var self = this;

                function focusin_function(self) {
                    self.uiChatboxTitlebar.addClass('ui-state-focus');
                    self.uiChatboxInputBox.addClass('ui-chatbox-input-focus');
                    self.uiChatboxLog.scrollTop(self.uiChatboxLog.get(0).scrollHeight);
                    chanUtils.setFocusinPollingDelay();
                    chanUtils.callPollServerForStatusAndNewMessages();
                }

                try {
                    var uiChatboxInput = null;
                    if (include_chatbox_input) {
                        uiChatboxInput = $('<div></div>')
                        .addClass('ui-widget-content ' + 'ui-chatbox-input')
                        .click(function(event) {
                            // anything?
                        })
                        .appendTo(self.uiChatboxContent);

                        self.uiChatboxInputBox = (self.uiChatboxInputBox = $('<textarea></textarea>'))
                        .addClass('ui-widget-content ' + 'ui-chatbox-input-box ' + 'ui-corner-all')
                        .appendTo(uiChatboxInput)
                            .keydown(function(event) {
                            if(event.keyCode && event.keyCode == $.ui.keyCode.ENTER) {
                                var msg = $.trim($(this).val());
                                if(msg.length > 0) {
                                    self.options.messageSent(self.options.id, msg, self.options.type_of_conversation);
                                }
                                return false;
                            }
                        })
                        .focusin(function() {
                            focusin_function(self);
                        })
                        .click(function() {
                            focusin_function(self);
                        })
                        .focusout(function() {
                            self.uiChatboxInputBox.removeClass('ui-chatbox-input-focus');
                            self.uiChatboxTitlebar.removeClass('ui-state-focus');
                            chanUtils.setFocusoutPollingDelay();
                        });
                    }

                    return uiChatboxInput;
                } catch (err) {
                    reportTryCatchError( err, "AddChatboxInputToWidget");
                }
                return false; // prevent jslint warning
            }


        });
    } catch(err) {
        reportTryCatchError( err, "initJqueryUiChatbox");
    }

}(jQuery);





var catchWindowResizeEvents = function () {

    try {
        $(window).resize(function() {
            chatboxManager.resize_boxes_if_necessary();
        });
    } catch(err) {
        reportTryCatchError( err, "initJqueryUiChatbox.catchWindowResizeEvents()");
    }
};

var chatboxManager = function() {


    try {
        // list of all opened boxes
        var boxList = new Array();
        // list of boxes shown on the page
        var showList = new Array();
        // type of conversation that each box_id contains

        // list of first names, for in-page demo
        var user_name = null;

        var config = {
            default_main_width: 120,
            default_chatbox_width : 250, //px
            gap : 10,
            maxBoxes : 20,
            //max_chatbox_log_height: 200, // px
            max_main_log_height: 200, //px
            border_and_padding: 6
        };

        var current_main_width = config.default_main_width;
        var current_chatbox_width = config.default_chatbox_width;

        var getNextOffset = function(current_box_number) {
            // get the offset from the right side, taking into account that the main box has a different width
            // than the normal chatboxes.
            if (current_box_number >= 2) {

                return (current_main_width + config.gap) * 2 + (current_chatbox_width + config.gap) * (current_box_number - 2);
            } else {
                // it is the main or groups box, which are placed beside each other on the right side.
                return (current_main_width + config.gap) * (current_box_number);
            }

        };


        var changeBoxtitle = function (box_id, new_title) {
            if ($("#"+ box_id).length>0) { // make sure the element exists
                // add hyperlink to allow clicking on title to view the user profile
                $("#"+ box_id).chatbox("option", "boxManager").changeBoxTitle(new_title);
            }
        };

        var hyperlinkBoxtitle = function (box_id,  nid, url_description) {
            // this should wrap the title (which can change) with an anchor and href that
            // links to the associated users profile

            if ($("#"+ box_id).length>0) { // make sure the element exists
                // add hyperlink to allow clicking on title to view the user profile
                var href = "/" + templatePresenceVars.language + "/profile/" + nid + "/" + url_description + "/";
                var hyperlink_to_profile = '<a href="' + href +'" rel="address:' + href + '"></a>';
                $("#"+ box_id).chatbox("option", "boxManager").hyperlinkWrapBoxTitle(hyperlink_to_profile);
            }
        };


        var changeOpacityOfAllBoxes = function (opacity_val) {
            // used for "graying out" boxes - to indicate for example that a user is not online
            for(var idx = 0; idx < boxList.length; idx++) {
                var box_id = boxList[idx];
                $("#"+ box_id).chatbox("option", "boxManager").addCssToChatbox('opacity', opacity_val);
            }

            var list_len = chanUtils.listOfOpenChatGroupsMembersBoxes.length;
            for (var i=0; i<list_len; i++) {
                group_id = chanUtils.listOfOpenChatGroupsMembersBoxes[i];
                $("#id-group_members-dialog-box-" + group_id ).parent().css({'opacity': opacity_val});
            }
        };

        var closeAllChatBoxes = function() {
            // we need to process the list from tail to head, since we are shortening it
            // on each pass.
            var initial_length = showList.length;
            for(var idx = initial_length - 1; idx > 0; idx--) {
                var box_id = showList[idx];
                boxClosedCallback(box_id);
            }
        };


        var closeChatboxOnClient = function(box_id) {
            // we *do not* allow closing of the *main* box, and so this code does not currently handle this situation
            var idx = $.inArray(box_id, showList);
            if(idx != -1) {
                showList.splice(idx, 1);
                $("#"+ box_id).chatbox("option", "boxManager").hideBox();
                diff = current_chatbox_width + config.gap;
                for(var i = idx; i < showList.length; i++) {
                    offset = $("#" + showList[i]).chatbox("option", "offset");
                    $("#" + showList[i]).chatbox("option", "offset", offset - diff);
                }
                resize_boxes_if_necessary();
            }
            else {
                 report_javascript_error_on_server("closeChatboxOnClient error: " + box_id);
            }


            if ($("#" + box_id).chatbox("option", 'type_of_conversation') === 'group') {
                // close the list of group members, so that we don't have people "spying" on who is in the group
                // without actually being in the group themselves
                chanUtils.closeGroupMembersDialog(box_id);
            }
        }

        var boxClosedCallback = function(box_id) {

            try{
                // close button in the titlebar is clicked
                closeChatboxOnClient(box_id);

                chanUtils.closeChatboxOnServer(box_id);

            } catch(err) {
                reportTryCatchError( err, "initJqueryUiChatbox.boxClosedCallback()");
            }
        };

        var minimizeBoxWasClickedCallback = function(box_id) {
            chanUtils.minimizeChatboxOnServer(box_id);
        };

        var maximizeBoxWasClickedCallback = function(box_id) {
            chanUtils.maximizeChatboxOnServer(box_id);
        };

        var resize_boxes_if_necessary = function() {

            try {
                var current_box_width;

                var document_width = $(window).width() - 50; // subtract out scrollbar width (approx)
                var document_height = $(window).height() - 50;
                var num_displayed_mainboxes = 2;
                var num_displayed_chatboxes = showList.length - 2;
                var chatbox_height_override = document_height / 2;

                // the following math is approximate, and needs to be investigated/written properly - it more or less works
                // but for a large number of chatboxes the scaling is not perfect.
                var normalization_width = (num_displayed_mainboxes * (config.default_main_width + config.gap + 2*config.border_and_padding)) +
                        (num_displayed_chatboxes * (config.default_chatbox_width + config.gap + 2*config.border_and_padding));
                var scaling_ratio = document_width/normalization_width;


                if (scaling_ratio >= 1) {
                    // the boxes should be made to their maximum default size
                    current_chatbox_width = config.default_chatbox_width; // subtract the padding and border
                    current_main_width = config.default_main_width;
                } else {
                    current_chatbox_width = config.default_chatbox_width * scaling_ratio;
                    current_main_width = config.default_main_width * scaling_ratio;
                }

                for(var idx = 0; idx < showList.length; idx++) {
                    var box_id = showList[idx];

                    if (box_id == "main" || box_id == "groups") { // will probably have to seperate main and groups later to get the height the same
                        if ($("#"+ box_id).chatbox("option", "boxManager").chatboxLogHeight() > config.max_main_log_height) {
                            $("#"+ box_id).chatbox("option", "boxManager").chatboxLogHeight(config.max_main_log_height);
                        }

                        current_box_width = current_main_width;

                    } else {

                        current_box_width = current_chatbox_width;
                        $("#"+ box_id).chatbox("option", "boxManager").chatboxLogHeight(chatbox_height_override);
                        // scale the bottom div so that the chatboxes don't cover over the main part of the page.
                        $('#id-height_chatbox_override').height(chatbox_height_override+75);
                    }
                    $("#"+ box_id).chatbox("option", "boxManager").resizeWidth(current_box_width);
                    $("#"+ box_id).chatbox("option", "boxManager").setBoxOffset(getNextOffset(idx));
                }

                // in IE6 AND IE7 buttons do not scale to fit within their container div. Therefore, we manually
                // resize them here.
                if (lt_ie8)  {
                    $('#id-go-online-button').css('width', current_main_width + config.border_and_padding);
                    $('#id-go-offline-button').css('width', current_main_width + config.border_and_padding);
                    $('#id-create-group-button').css('width', current_main_width + config.border_and_padding);
                    $('#id-videochat-button').css('width', current_main_width + config.border_and_padding);
                    $('button[id^=id-chat_group_members-button]').css('width', current_chatbox_width + config.border_and_padding);
                }
                
            } catch(err) {
                reportTryCatchError( err, "initJqueryUiChatbox.resize_boxes_if_necessary()", "warning");
            }
        };


        // caller should guarantee the uniqueness of box_id
        var addBox = function(box_id, box_title, allow_elimination, include_chatbox_input, highlight_box_enabled,
                              type_of_conversation, nid, url_description, just_opened) {

            try {
                var idx1 = $.inArray(box_id, showList);
                var idx2 = $.inArray(box_id, boxList);
                var open_box_on_server = false;
                var manager = undefined;
                var offset_from_right = undefined;
                if(idx1 != -1) {
                    // Chatbox already exists and is open - apply effect so the user notices it
                    manager = $("#"+ box_id).chatbox("option", "boxManager");
                    if (highlight_box_enabled) {
                        manager.highlightBox();
                    }
                }
                else if(idx2 != -1) {
                    // exists, but hidden (totally hidden, ie appears not to exist/has been "eliminated" )
                    // show it and put it back to showList
                    open_box_on_server = true;
                    offset_from_right = getNextOffset(showList.length);
                    $("#"+ box_id).chatbox("option", "offset", offset_from_right);
                    manager = $("#"+ box_id).chatbox("option", "boxManager");
                    manager.toggleBox();
                    manager._scrollToBottom();
                    $("#"+ box_id).chatbox("option", "just_opened", true );
                    showList.push(box_id);
                }
                else {
                    // not found, create a new chatbox
                    var el = document.createElement('div');
                    offset_from_right = getNextOffset(showList.length);
                    var box_width;

                    open_box_on_server = true;

                    if (box_id == 'main') {
                        box_width = current_main_width;
                    } else {
                        box_width = current_chatbox_width;
                    }
                    el.setAttribute('id', box_id);
                    $(el).chatbox({
                        id : box_id,
                        title : box_title,
                        allow_elimination: allow_elimination, // show the X in the top right corner
                        include_chatbox_input: include_chatbox_input,
                        type_of_conversation: type_of_conversation,
                        hidden : false,
                        width : box_width,
                        offset : offset_from_right,
                        just_opened : just_opened,
                        messageSent: function(box_id, msg, type_of_conversation) {
                            chanUtils.sendMessage(box_id, msg, type_of_conversation);
                        },
                        boxClosed : boxClosedCallback,
                        minimizeBoxWasClicked : minimizeBoxWasClickedCallback,
                        maximizeBoxWasClicked : maximizeBoxWasClickedCallback
                    });
                    boxList.push(box_id);
                    showList.push(box_id);

                    if (lt_ie8) { // apply hack for fixed positioning to work in IE6
                        $("#"+ box_id).chatbox("option", "boxManager").addClassToChatbox('fixed-bottom');
                    }

                    if (box_id != "main" && box_id != "groups" && open_box_on_server) {
                        if (type_of_conversation != "group") {
                            // group conversations will not have a hyperlink in the title, since there is no associated profile
                            hyperlinkBoxtitle(box_id, nid, url_description);

                            // Note: box_id for chatboxes is the uid of the other user
                            $("#" + box_id).chatbox("option", "boxManager").uiChatboxVideoButton(box_id);

                        }
                        else { // group conversation
                            $("#" + box_id).chatbox("option", "boxManager").uiChatboxShowGroupMembersButton(box_id, box_title);
                        }
                    }
                }

                resize_boxes_if_necessary();
            } catch(err) {
                reportTryCatchError( err, "initJqueryUiChatbox.addBox()");
            }
        };

        var trackUserActivityForOnlineStatus = function () {

            try {
                // setup the timers for detecting user online/idle status
                idle_params = {};
                idle_params.idle_timeout = chanUtils.presenceIdleTimeout;
                idle_params.away_timeout = chanUtils.presenceAwayTimeout;

                idle_params.onIdle = function() {
                    var new_main_title = $('#id-chat-contact-title-user_presence_idle-text').text();
                    changeOpacityOfAllBoxes(0.75);
                    changeBoxtitle("main", new_main_title);
                    chanUtils.userPresenceStatus = "user_presence_idle";
                    chanUtils.currentMessagePollingDelay = chanUtils.presenceIdlePollingDelay;
                    chanUtils.updateUserPresenceStatusOnServer(chanUtils.userPresenceStatus);

                };
                idle_params.onAway = function() {
                    var new_main_title = $('#id-chat-contact-title-user_presence_away-text').text();
                    changeOpacityOfAllBoxes(0.25);
                    changeBoxtitle("main", new_main_title);
                    chanUtils.userPresenceStatus = "user_presence_away";
                    chanUtils.currentMessagePollingDelay = chanUtils.presenceAwayPollingDelay;
                    chanUtils.updateUserPresenceStatusOnServer(chanUtils.userPresenceStatus);
                };
                idle_params.onBack = function(isIdle, isAway) {
                    var new_main_title = $('#id-chat-contact-title-text').text();
                    changeOpacityOfAllBoxes(1);
                    changeBoxtitle("main", new_main_title);
                    chanUtils.userPresenceStatus = "user_presence_active";
                    chanUtils.updateUserPresenceStatusOnServer(chanUtils.userPresenceStatus);
                    chanUtils.startPolling();
                };
                

                chatbox_idle_object = IdleClass(idle_params);
                return chatbox_idle_object;

            } catch(err) {
                reportTryCatchError( err, "trackUserActivityForOnlineStatus");
            }
        };

        return {
            addBox : addBox,
            closeAllChatBoxes: closeAllChatBoxes,
            changeOpacityOfAllBoxes: changeOpacityOfAllBoxes,
            changeBoxtitle: changeBoxtitle,
            hyperlinkBoxtitle: hyperlinkBoxtitle,
            resize_boxes_if_necessary: resize_boxes_if_necessary,
            trackUserActivityForOnlineStatus: trackUserActivityForOnlineStatus,
            closeChatboxOnClient: closeChatboxOnClient,
            showList: showList
        };
    } catch(err) {
        reportTryCatchError( err, "chatboxManager");
    }

}();


var updateChatControlBox = function (box_name, dict_to_display) {
    // used for updating the "main" and the "groups" chatboxes -- in the case of the main box, it will
    // display a list of contacts that are online. For the groups box, it will display a list of available
    // chat groups.


    try {

        var sort_ascending = undefined;
        if (box_name == "groups") {
            // we are updating the list of chat groups
            sort_ascending = false;
        } else {
            // we are updating the list of chat friends
            sort_ascending = true;
        }
        var sorted_list_of_names_with_info = chanUtils.sortUserOrGroupsByName(box_name, dict_to_display, sort_ascending);
        var display_list = chanUtils.displayAsListWithHrefs(box_name, sorted_list_of_names_with_info, false);

        $("#" + box_name).chatbox("option", "boxManager").refreshBox(display_list);


        $("#id-chatbox-" + box_name + "-list li").click(function(e){
            var anchor = $(this).find('a');
            var box_id =  anchor.data("uid"); // jquery .data() operator
            var box_title = dict_to_display[box_id]['user_or_group_name'];
            var url_description = dict_to_display[box_id]['url_description'];
            var nid = dict_to_display[box_id]['nid'];

            var type_of_conversation;
            if (box_name == "main") {
                type_of_conversation = "one_on_one";
            } else if (box_name == "groups") {
                type_of_conversation = "group";
                // They have just opened a new chat window for a group discussion, so we want to show who is in the group
                chanUtils.openGroupMembersDialog(box_id, box_title);

            } else {
                type_of_conversation = "Error in javascript - invalid box_name";
            }

            // by creating a box entry on the server, we will recieve a response that indicates that a new box is open
            // at which point we will open the box. 
            var just_opened = true;
            chatboxManager.addBox(box_id, box_title, true, true, true, type_of_conversation, nid, url_description, just_opened);
            chanUtils.createNewBoxEntryOnServer(box_id);
            return false;
        });

        // the height of the main box might have increased due to new contacts being added - scale it appropriately
        chatboxManager.resize_boxes_if_necessary();
    } catch(err) {
        reportTryCatchError( err, "updateChatControlBox");
    }
};

var updateUserChatBoxTitles = function(contacts_info_dict) {
    try {
        for (var uid in contacts_info_dict) {
            if (contacts_info_dict[uid]['userPresenceStatus'] != 'hidden_online_status') {
                // get the *translated* online status by looking it up in a div that we have defined.
                online_status = $('#id-chat-contact-title-' + contacts_info_dict[uid]['userPresenceStatus'] + '-text').html();
            } else {
                // to keep the chatboxes looking clean, by default we don't show a status for active users.
                online_status = '';
            }
            var chatbox_title = contacts_info_dict[uid]['user_or_group_name'] + online_status;
            
            chatboxManager.changeBoxtitle(uid, chatbox_title);
        }
    } catch(err) {
        reportTryCatchError( err, "updateUserChatBoxTitles");
    }
};

var updateGroupChatBoxTitles = function(chat_groups_dict) {
    try {
        for (var gid in chat_groups_dict) {
            var chatbox_name = chat_groups_dict[gid]['user_or_group_name'];
            var chatbox_title = chatbox_name + " [" + chat_groups_dict[gid]['num_group_members'] + "]";
            chatboxManager.changeBoxtitle(gid, chatbox_title);

            // check if there is an associated "group members" box open and update the title
            // on this box if it exists (note: we do not include the number of users in this box since
            // the number does not always precisely match the number of users in the group due to update delays
            // and since the number of members is already shown in other locations.
            if ($("#id-group_members-dialog-box-" + gid).length > 0) {
                $("#id-group_members-dialog-box-" + gid).dialog("option", "title", chatbox_name);
            }
        }
    } catch(err) {
        reportTryCatchError( err, "updateGroupChatBoxTitles");
    }
};

var setupContactsAndGroupsBoxes = function(chat_is_disabled) {

    try {

        var main_box_id = "main";
        var main_box_title = $('#id-chat-contact-title-text').text();
        var allow_elimination = false, include_chatbox_input = false, highlight_box_enabled = false;
        var type_of_conversation = 'Not used/Not valid'; // not used for contact and group boxes
        var just_opened = true;
        chatboxManager.addBox(main_box_id, main_box_title, allow_elimination, include_chatbox_input,
                highlight_box_enabled, type_of_conversation, '', '', just_opened);
        // Add the button that allows the user to specify if they want to go online/offline
        $("#" + main_box_id).chatbox("option", "boxManager").uiChatboxOnlineSelector();
        $("#" + main_box_id).chatbox("option", "boxManager").addClassToUIChatboxLog("ui-chatbox-log-override-height-for-main");
        $("#" + main_box_id).chatbox("option", "boxManager").minimizeBox();

        var groups_box_id = "groups";
        var groups_box_title = $("#id-chat-group-title-text").text();
        chatboxManager.addBox(groups_box_id, groups_box_title, allow_elimination, include_chatbox_input,
                highlight_box_enabled, type_of_conversation, '', '', just_opened);
        $("#" + groups_box_id).chatbox("option", "boxManager").uiChatboxCreateGroupButton();
        $("#" + groups_box_id).chatbox("option", "boxManager").addClassToUIChatboxLog("ui-chatbox-log-override-height-for-main");
        $("#" + groups_box_id).chatbox("option", "boxManager").minimizeBox();


        if (chat_is_disabled == "yes") {
            chanUtils.executeGoOfflineOnClient();
        }
        else {
            chanUtils.initializeMainAndGroupBoxesOnServer();
        }
    } catch(err) {
        reportTryCatchError( err, "setupContactsAndGroupsBoxes", "warning");
    }
};

