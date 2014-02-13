"use strict";

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



/* Declare functions that are defined in other files, so that jshint doesn't complain  */
/* global chanUtils */
/* global templatePresenceVars */
/* global reportTryCatchError */
/* global reportJavascriptErrorOnServer */
/* global IdleClass */
/* global ltIE8 */


/* Exported functions */
/* exported initJqueryUiChatbox */
/* exported catchWindowResizeEvents */
/* exported updateChatControlBox */
/* exported updateUserChatBoxTitles */
/* exported updateGroupChatBoxTitles */
/* exported setupContactsAndGroupsBoxes */


// Define functions that are declared after call to the function
var chatboxManager;

// TODO: implement destroy()
var initJqueryUiChatbox = (function($){

    // This function sets up the JqueryUI functions, and is automatically executed 

    try {

        $.widget("js.chatbox", {

            options: {
                id: null, //id for the DOM element
                title: null, // title of the chatbox
                allowElimination: true, // show the X in the top right corner - this can be over-ridden
                includeChatboxInput: true,
                typeOfConversation: '', // override with 'oneOnOne' or "group"
                hidden: false,
                offset: 0, // default relative to right edge of the browser window - over-ridden
                width: 0, // default width of the chatbox - over-ridden
                justOpened : false, // for newly created boxes, we temporarily ignore the 'keepOpen' status from the server
                messageSent: function() {}, //over-ride this
                boxClosed: function() {}, // called when the close icon is clicked - over-ridden
                minimizeBoxWasClicked: function() {}, // over-ridden
                maximizeBoxWasClicked: function() {}, // over-ridden
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
                    addMsg: function(senderName, msg, highlightBoxEnabled) {
                        // This function will be called when a chatbox needs to be updated with additional
                        // messages, but it will not erase the history. This must be carefully coordinated
                        // with the information that we decide to send from the server.
                        try {
                            var self = this;
                            var box = self.elem.uiChatboxLog;
                            var e = document.createElement('div');
                            $(e).html("<b>" + senderName +":</b> " + msg)
                            .addClass("ui-chatbox-msg ui-chatbox-highlight-link cl-literally-display-user-text");
                            box.append(e);
                            self._scrollToBottom();

                            if (highlightBoxEnabled) {
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

                    setChatboxInputBox: function (newValue) {
                        this.elem.uiChatboxInputBox.val(newValue);
                    },
                    setBoxOffset: function(offset) {
                        this.elem._position(offset);
                    },
                    hideBox: function () {
                        // Hide the entire chatbox - ie. it is "eliminated"
                        this.elem.uiChatbox.hide();
                    },
                    chatboxLogHeight: function (newHeight) {
                        // set *or* get the height of the chatbox - if blank value is passed in, will get the height
                        return this.elem.uiChatboxLog.height(newHeight);
                    },
                    hideChatboxContent: function () {
                        this.elem.uiChatboxContent.hide();
                    },
                    showChatboxContent: function () {
                        this.elem.uiChatboxContent.show();
                    },
                    addCssToChatbox: function (property, newClass) {
                        this.elem.uiChatbox.css(property, newClass);
                    },
                    addIdToChatbox: function (newId) {
                        this.elem.uiChatbox.attr('id', newId);
                    },
                    changeBoxTitle: function(newTitle) {
                        this.elem.uiChatboxTitle.html(newTitle);
                    },
                    addClassToChatbox: function(className) {
                        this.elem.uiChatbox.addClass(className);
                    },
                    addClassToBoxTitle: function(className) {
                        this.elem.uiChatboxTitle.addClass(className);
                    },
                    hyperlinkWrapBoxTitle: function(hyperlinkToProfile) {
                        this.elem.uiChatboxTitle.wrap(hyperlinkToProfile);
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
                    addClassToUIChatboxLog: function (className) {
                        this.elem.uiChatboxLog.addClass(className);
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
                            var goOfflineText = $('#id-disactivate-chat-button-text').html();
                            self.elem.uiChatboxTitlebar.after($('<button class="ui-chatbox-submit-button ' +
                                    'ui-remove-corner-all"' +
                                    'id="id-go-offline-button">' + goOfflineText + '</button>'));
                            $('#id-go-offline-button').button();
                            $('#id-go-offline-button').click(function() {
                                chanUtils.executeGoOfflineOnClient();
                                $("#main").chatbox("option", "boxManager").hideChatboxContent();

                                // the following interactions occur with the server, and so should only
                                // occur once, and therefore we do not put them in the "executeGoOfflineOnClient" function
                                chanUtils.closeAllChatboxesOnServer();
                                chanUtils.updateChatBoxesStatusOnServer('chatDisabled');
                                return false;
                            });

                            var goOnlineText = $('#id-activate-chat-button-text').html();
                            $('#id-go-offline-button').after($('<button class="ui-chatbox-submit-button ' +
                                    'ui-remove-corner-all"' +
                                    'id="id-go-online-button">' + goOnlineText + '</button>'));
                            $('#id-go-online-button').button();
                            $('#id-go-online-button').hide();
                            $('#id-go-online-button').click(function() {
                                chanUtils.updateChatBoxesStatusOnServer('chatEnabled');
                                chanUtils.executeGoOnlineOnClient();
                                return false;
                            });

                            if (ltIE8) {
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
                            var createGroupText = $('#id-create-group-button-text').html();
                            self.elem.uiChatboxTitlebar.after($('<button class="ui-chatbox-submit-button ' +
                                    'ui-remove-corner-all"' +
                                    'id="id-create-group-button">' + createGroupText + '</button>'));
                            $('#id-create-group-button').button();
                            $('#id-create-group-button').click(function() {
                                $("#id-create-group-dialog").dialog();
                                return false;
                            });
                        } catch(err) {
                            reportTryCatchError( err, "initJqueryUiChatbox.uiChatboxCreateGroupButton()");
                        }
                    },

                    uiChatboxShowGroupMembersButton: function (groupId, boxTitle) {

                        try {
                            var self=this;
                            var chatGroupMembersText = $('#id-chat_group_members-button-text').html();
                            self.elem.uiChatboxTitlebar.after($('<button class="ui-chatbox-submit-button ' +
                                    'ui-remove-corner-all"' +
                                    'id="id-chat_group_members-button-' + groupId + '">' + chatGroupMembersText + '</button>'));
                            $('#id-chat_group_members-button-' + groupId).button();
                            $('#id-chat_group_members-button-' + groupId).click(function() {
                                chanUtils.openGroupMembersDialog(groupId, boxTitle);
                            });
                        } catch(err) {
                            reportTryCatchError( err, "initJqueryUiChatbox.uiChatboxShowGroupMembersButton()");
                        }
                    }


    //                uiChatboxVideoButton: function (other_uid) {
    //
    //                    // TODO - give each button a unique name - otherwise calls will be random. ie. Include the other_uid in the button id.
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
    //
    //                }
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
                    var self = this;
                    var options = self.options;
                    var title = options.title || "No Title";

                    // chatbox
                    var uiChatbox = (self.uiChatbox = $('<div></div>'))
                    .appendTo(document.body)
                    .addClass('ui-widget ui-corner-top ui-chatbox ')
                    .attr('outline', 0);

                    // titlebar
                    var uiChatboxTitlebar = (self.uiChatboxTitlebar = $('<div></div>'))
                    .addClass('ui-chatbox-titlebar ui-widget-header ui-corner-top ui-helper-clearfix ');
                    uiChatboxTitlebar.appendTo(uiChatbox);


                    var uiChatboxTitle = (self.uiChatboxTitle = $('<span class="ui-chatbox-title"></span>'))
                    .html(title);
                    uiChatboxTitle.appendTo(uiChatboxTitlebar);
                    self.uiChatboxTitlebarClose =  self._AddEliminationToWidget();


                    var uiChatboxTitlebarMinimize = (self.uiChatboxTitlebarMinimize = $('<a href="#"></a>'))
                    .addClass('ui-corner-all ' +
                          'ui-chatbox-icon'
                         )
                    .attr('role', 'button')
                    .hover(function() {uiChatboxTitlebarMinimize.addClass('ui-state-hover');},
                           function() {uiChatboxTitlebarMinimize.removeClass('ui-state-hover');})
                    .click(function() {

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
                    });
                    uiChatboxTitlebarMinimize.appendTo(uiChatboxTitlebar);


                    var uiChatboxTitlebarMinimizeText = $('<span></span>')
                    .addClass('ui-icon ' +
                          'ui-icon-minusthick')
                    .text('minimize');
                    uiChatboxTitlebarMinimizeText.appendTo(uiChatboxTitlebarMinimize);


                    // content
                    var uiChatboxContent = (self.uiChatboxContent = $('<div></div>'))
                    .addClass('ui-widget-content ' +
                          'ui-chatbox-content '
                         )
                    .appendTo(uiChatbox);

                    self.uiChatboxLog = self.element;
                    self.uiChatboxLog.addClass('ui-widget-content '+
                          'ui-chatbox-log'
                         )
                    .appendTo(uiChatboxContent)
                    .mouseenter(function() {
                        $(this).addClass("cl-chatbox-log-has-focus");
                    })
                    .mouseleave(function() {
                        $(this).removeClass("cl-chatbox-log-has-focus");
                    });


                    self.uiChatboxInput = self._AddChatboxInputToWidget(options.includeChatboxInput);

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
                    if (this.options.includeChatboxInput) {
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
                    if (self.options.allowElimination) {
                        uiChatboxTitlebarClose = $('<a href="#"></a>')
                        .addClass('ui-corner-all ' + 'ui-chatbox-icon' )
                        .attr('role', 'button')
                        .hover(function() {uiChatboxTitlebarClose.addClass('ui-state-hover');},
                               function() {uiChatboxTitlebarClose.removeClass('ui-state-hover');})
                        .click(function() {
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


            _AddChatboxInputToWidget : function(includeChatboxInput) {

                // modifies uiChatboxInput to contain uiChatboxInputBox. Note: "self" is modified
                // to contain the newly created textarea "uiChatboxInputBox"

                var self = this;

                function focusinFunction(self) {
                    self.uiChatboxTitlebar.addClass('ui-state-focus');
                    self.uiChatboxInputBox.addClass('ui-chatbox-input-focus');
                    self.uiChatboxLog.scrollTop(self.uiChatboxLog.get(0).scrollHeight);
                    chanUtils.setFocusinPollingDelay();
                    chanUtils.callPollServerForStatusAndNewMessages();
                }

                try {
                    var uiChatboxInput = null;
                    if (includeChatboxInput) {
                        uiChatboxInput = $('<div></div>')
                        .addClass('ui-widget-content ' + 'ui-chatbox-input')
                        .click(function() {
                            // anything?
                        })
                        .appendTo(self.uiChatboxContent);

                        self.uiChatboxInputBox = (self.uiChatboxInputBox = $('<textarea></textarea>'))
                        .addClass('ui-widget-content ' + 'ui-chatbox-input-box ' + 'ui-corner-all')
                        .appendTo(uiChatboxInput)
                            .keydown(function(event) {
                            if(event.keyCode && event.keyCode === $.ui.keyCode.ENTER) {
                                var msg = $.trim($(this).val());
                                if(msg.length > 0) {
                                    self.options.messageSent(self.options.id, msg, self.options.typeOfConversation);
                                }
                                return false;
                            }
                        })
                        .focusin(function() {
                            focusinFunction(self);
                        })
                        .click(function() {
                            focusinFunction(self);
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

}(jQuery));





var catchWindowResizeEvents = function () {

    try {
        $(window).resize(function() {
            chatboxManager.resizeBoxesIfNecessary();
        });
    } catch(err) {
        reportTryCatchError( err, "initJqueryUiChatbox.catchWindowResizeEvents()");
    }
};

chatboxManager = (function() {


    try {
        // list of all opened boxes
        var boxList = [];
        // list of boxes shown on the page
        var showList = [];
        // type of conversation that each box_id contains

        var config = {
            defaultMainWidth: 120,
            defaultChatboxWidth : 250, //px
            gap : 10,
            maxBoxes : 20,
            //max_chatbox_log_height: 200, // px
            maxMainLogHeight: 200, //px
            borderAndPadding: 6
        };

        var currentMainWidth = config.defaultMainWidth;
        var currentChatboxWidth = config.defaultChatboxWidth;

        var getNextOffset = function(currentBoxNumber) {
            // get the offset from the right side, taking into account that the main box has a different width
            // than the normal chatboxes.
            if (currentBoxNumber >= 2) {

                return (currentMainWidth + config.gap) * 2 + (currentChatboxWidth + config.gap) * (currentBoxNumber - 2);
            } else {
                // it is the main or groups box, which are placed beside each other on the right side.
                return (currentMainWidth + config.gap) * (currentBoxNumber);
            }

        };


        var changeBoxtitle = function (boxId, newTitle) {
            if ($("#"+ boxId).length>0) { // make sure the element exists
                // add hyperlink to allow clicking on title to view the user profile
                $("#"+ boxId).chatbox("option", "boxManager").changeBoxTitle(newTitle);
            }
        };

        var hyperlinkBoxtitle = function (boxId,  nid, urlDescription) {
            // this should wrap the title (which can change) with an anchor and href that
            // links to the associated users profile

            if ($("#"+ boxId).length>0) { // make sure the element exists
                // add hyperlink to allow clicking on title to view the user profile
                var href = "/" + templatePresenceVars.language + "/profile/" + nid + "/" + urlDescription + "/";
                var hyperlinkToProfile = '<a href="' + href +'" rel="address:' + href + '"></a>';
                $("#"+ boxId).chatbox("option", "boxManager").hyperlinkWrapBoxTitle(hyperlinkToProfile);
            }
        };


        var changeOpacityOfAllBoxes = function (opacityVal) {
            // used for "graying out" boxes - to indicate for example that a user is not online
            for(var idx = 0; idx < boxList.length; idx++) {
                var boxId = boxList[idx];
                $("#"+ boxId).chatbox("option", "boxManager").addCssToChatbox('opacity', opacityVal);
            }

            var listLen = chanUtils.listOfOpenChatGroupsMembersBoxes.length;
            for (var i=0; i<listLen; i++) {
                var groupId = chanUtils.listOfOpenChatGroupsMembersBoxes[i];
                $("#id-group_members-dialog-box-" + groupId ).parent().css({'opacity': opacityVal});
            }
        };

        var closeAllChatBoxes = function() {
            // we need to process the list from tail to head, since we are shortening it
            // on each pass.
            var initialLength = showList.length;
            for(var idx = initialLength - 1; idx > 0; idx--) {
                var boxId = showList[idx];
                boxClosedCallback(boxId);
            }
        };


        var closeChatboxOnClient = function(boxId) {
            // we *do not* allow closing of the *main* box, and so this code does not currently handle this situation
            var idx = $.inArray(boxId, showList);
            if(idx !== -1) {
                showList.splice(idx, 1);
                $("#"+ boxId).chatbox("option", "boxManager").hideBox();
                var diff = currentChatboxWidth + config.gap;
                for(var i = idx; i < showList.length; i++) {
                    var offset = $("#" + showList[i]).chatbox("option", "offset");
                    $("#" + showList[i]).chatbox("option", "offset", offset - diff);
                }
                resizeBoxesIfNecessary();
            }
            else {
                reportJavascriptErrorOnServer("closeChatboxOnClient error: " + boxId);
            }


            if ($("#" + boxId).chatbox("option", 'typeOfConversation') === 'group') {
                // close the list of group members, so that we don't have people "spying" on who is in the group
                // without actually being in the group themselves
                chanUtils.closeGroupMembersDialog(boxId);
            }
        };

        var boxClosedCallback = function(boxId) {

            try{
                // close button in the titlebar is clicked
                closeChatboxOnClient(boxId);

                chanUtils.closeChatboxOnServer(boxId);

            } catch(err) {
                reportTryCatchError( err, "initJqueryUiChatbox.boxClosedCallback()");
            }
        };

        var minimizeBoxWasClickedCallback = function(boxId) {
            chanUtils.minimizeChatboxOnServer(boxId);
        };

        var maximizeBoxWasClickedCallback = function(boxId) {
            chanUtils.maximizeChatboxOnServer(boxId);
        };


        var resizeBoxesIfNecessary = function() {

            try {
                var currentBoxWidth;

                var documentWidth = $(window).width() - 50; // subtract out scrollbar width (approx)
                var documentHeight = $(window).height() - 50;
                var numDisplayedMainboxes = 2;
                var numDisplayedChatboxes = showList.length - 2;
                var chatboxHeightOverride = documentHeight / 2;

                // the following math is approximate, and needs to be investigated/written properly - it more or less works
                // but for a large number of chatboxes the scaling is not perfect.
                var normalizationWidth = (numDisplayedMainboxes * (config.defaultMainWidth + config.gap + 2*config.borderAndPadding)) +
                        (numDisplayedChatboxes * (config.defaultChatboxWidth + config.gap + 2*config.borderAndPadding));
                var scalingRatio = documentWidth/normalizationWidth;


                if (scalingRatio >= 1) {
                    // the boxes should be made to their maximum default size
                    currentChatboxWidth = config.defaultChatboxWidth; // subtract the padding and border
                    currentMainWidth = config.defaultMainWidth;
                } else {
                    currentChatboxWidth = config.defaultChatboxWidth * scalingRatio;
                    currentMainWidth = config.defaultMainWidth * scalingRatio;
                }

                for(var idx = 0; idx < showList.length; idx++) {
                    var boxId = showList[idx];

                    if (boxId === "main" || boxId === "groups") { // will probably have to seperate main and groups later to get the height the same
                        if ($("#"+ boxId).chatbox("option", "boxManager").chatboxLogHeight() > config.maxMainLogHeight) {
                            $("#"+ boxId).chatbox("option", "boxManager").chatboxLogHeight(config.maxMainLogHeight);
                        }

                        currentBoxWidth = currentMainWidth;

                    } else {

                        currentBoxWidth = currentChatboxWidth;
                        $("#"+ boxId).chatbox("option", "boxManager").chatboxLogHeight(chatboxHeightOverride);
                        // scale the bottom div so that the chatboxes don't cover over the main part of the page.
                        $('#id-height_chatbox_override').height(chatboxHeightOverride+75);
                    }
                    $("#"+ boxId).chatbox("option", "boxManager").resizeWidth(currentBoxWidth);
                    $("#"+ boxId).chatbox("option", "boxManager").setBoxOffset(getNextOffset(idx));
                }

                // in IE6 AND IE7 buttons do not scale to fit within their container div. Therefore, we manually
                // resize them here.
                if (ltIE8)  {
                    $('#id-go-online-button').css('width', currentMainWidth + config.borderAndPadding);
                    $('#id-go-offline-button').css('width', currentMainWidth + config.borderAndPadding);
                    $('#id-create-group-button').css('width', currentMainWidth + config.borderAndPadding);
                    $('#id-videochat-button').css('width', currentMainWidth + config.borderAndPadding);
                    $('button[id^=id-chat_group_members-button]').css('width', currentChatboxWidth + config.borderAndPadding);
                }
                
            } catch(err) {
                reportTryCatchError( err, "initJqueryUiChatbox.resizeBoxesIfNecessary()", "warning");
            }
        };


        // caller should guarantee the uniqueness of box_id
        var addBox = function(boxId, boxTitle, allowElimination, includeChatboxInput, highlightBoxEnabled,
                              typeOfConversation, nid, urlDescription, justOpened) {

            try {
                var idx1 = $.inArray(boxId, showList);
                var idx2 = $.inArray(boxId, boxList);
                var openBoxOnServer = false;
                var manager;
                var offsetFromRight;
                if(idx1 !== -1) {
                    // Chatbox already exists and is open - apply effect so the user notices it
                    manager = $("#"+ boxId).chatbox("option", "boxManager");
                    if (highlightBoxEnabled) {
                        manager.highlightBox();
                    }
                }
                else if(idx2 !== -1) {
                    // exists, but hidden (totally hidden, ie appears not to exist/has been "eliminated" )
                    // show it and put it back to showList
                    openBoxOnServer = true;
                    offsetFromRight = getNextOffset(showList.length);
                    $("#"+ boxId).chatbox("option", "offset", offsetFromRight);
                    manager = $("#"+ boxId).chatbox("option", "boxManager");
                    manager.toggleBox();
                    manager._scrollToBottom();
                    $("#"+ boxId).chatbox("option", "justOpened", true );
                    showList.push(boxId);
                }
                else {
                    // not found, create a new chatbox
                    var el = document.createElement('div');
                    offsetFromRight = getNextOffset(showList.length);
                    var boxWidth;

                    openBoxOnServer = true;

                    if (boxId === 'main') {
                        boxWidth = currentMainWidth;
                    } else {
                        boxWidth = currentChatboxWidth;
                    }
                    el.setAttribute('id', boxId);
                    $(el).chatbox({
                        id : boxId,
                        title : boxTitle,
                        allowElimination: allowElimination, // show the X in the top right corner
                        includeChatboxInput: includeChatboxInput,
                        typeOfConversation: typeOfConversation,
                        hidden : false,
                        width : boxWidth,
                        offset : offsetFromRight,
                        justOpened : justOpened,
                        messageSent: function(boxId, msg, typeOfConversation) {
                            chanUtils.sendMessage(boxId, msg, typeOfConversation);
                        },
                        boxClosed : boxClosedCallback,
                        minimizeBoxWasClicked : minimizeBoxWasClickedCallback,
                        maximizeBoxWasClicked : maximizeBoxWasClickedCallback
                    });
                    boxList.push(boxId);
                    showList.push(boxId);

                    if (ltIE8) { // apply hack for fixed positioning to work in IE6
                        $("#"+ boxId).chatbox("option", "boxManager").addClassToChatbox('fixed-bottom');
                    }

                    if (boxId !== "main" && boxId !== "groups" && openBoxOnServer) {
                        if (typeOfConversation !== "group") {
                            // group conversations will not have a hyperlink in the title, since there is no associated profile
                            hyperlinkBoxtitle(boxId, nid, urlDescription);

                            // Note: boxId for chatboxes is the uid of the other user
                            //$("#" + boxId).chatbox("option", "boxManager").uiChatboxVideoButton(boxId);

                        }
                        else { // group conversation
                            $("#" + boxId).chatbox("option", "boxManager").uiChatboxShowGroupMembersButton(boxId, boxTitle);
                        }
                    }
                }

                resizeBoxesIfNecessary();
            } catch(err) {
                reportTryCatchError( err, "initJqueryUiChatbox.addBox()");
            }
        };

        var trackUserActivityForOnlineStatus = function () {

            try {
                // setup the timers for detecting user online/idle status
                var idleParams = {};
                idleParams.idleTimeout = chanUtils.presenceIdleTimeout;
                idleParams.awayTimeout = chanUtils.presenceAwayTimeout;

                idleParams.onIdle = function() {
                    var newMainTitle = $('#id-chat-contact-title-user_presence_idle-text').text();
                    changeOpacityOfAllBoxes(0.75);
                    changeBoxtitle("main", newMainTitle);
                    chanUtils.userPresenceStatus = 'userPresenceIdle';
                    chanUtils.currentMessagePollingDelay = chanUtils.presenceIdlePollingDelay;
                    chanUtils.updateUserPresenceStatusOnServer(chanUtils.userPresenceStatus);

                };
                idleParams.onAway = function() {
                    var newMainTitle = $('#id-chat-contact-title-user_presence_away-text').text();
                    changeOpacityOfAllBoxes(0.25);
                    changeBoxtitle("main", newMainTitle);
                    chanUtils.userPresenceStatus = 'userPresenceAway';
                    chanUtils.currentMessagePollingDelay = chanUtils.presenceAwayPollingDelay;
                    chanUtils.updateUserPresenceStatusOnServer(chanUtils.userPresenceStatus);
                };
                idleParams.onBack = function() {
                    var newMainTitle = $('#id-chat-contact-title-text').text();
                    changeOpacityOfAllBoxes(1);
                    changeBoxtitle("main", newMainTitle);
                    chanUtils.userPresenceStatus = 'userPresenceActive';
                    chanUtils.updateUserPresenceStatusOnServer(chanUtils.userPresenceStatus);
                    chanUtils.startPolling();
                };
                

                var chatboxIdleObject = new IdleClass(idleParams);
                return chatboxIdleObject;

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
            resizeBoxesIfNecessary: resizeBoxesIfNecessary,
            trackUserActivityForOnlineStatus: trackUserActivityForOnlineStatus,
            closeChatboxOnClient: closeChatboxOnClient,
            showList: showList
        };
    } catch(err) {
        reportTryCatchError( err, "chatboxManager");
    }

}());


var updateChatControlBox = function (boxName, dictToDisplay) {
    // used for updating the "main" and the "groups" chatboxes -- in the case of the main box, it will
    // display a list of contacts that are online. For the groups box, it will display a list of available
    // chat groups.


    try {

        var sortAscending;
        if (boxName === "groups") {
            // we are updating the list of chat groups
            sortAscending = false;
        } else {
            // we are updating the list of chat friends
            sortAscending = true;
        }
        var sortedListOfNamesWithInfo = chanUtils.sortUserOrGroupsByName(boxName, dictToDisplay, sortAscending);
        var displayList = chanUtils.displayAsListWithHrefs(boxName, sortedListOfNamesWithInfo, false);

        $("#" + boxName).chatbox("option", "boxManager").refreshBox(displayList);


        $("#id-chatbox-" + boxName + "-list li").click(function(){
            var anchor = $(this).find('a');
            var boxId =  anchor.data("uid"); // jquery .data() operator
            var boxTitle = dictToDisplay[boxId]['userOrGroupName'];
            var urlDescription = dictToDisplay[boxId]['urlDescription'];
            var nid = dictToDisplay[boxId]['nid'];

            var typeOfConversation;
            if (boxName === "main") {
                typeOfConversation = 'oneOnOne';
            } else if (boxName === "groups") {
                typeOfConversation = "group";
                // They have just opened a new chat window for a group discussion, so we want to show who is in the group
                chanUtils.openGroupMembersDialog(boxId, boxTitle);

            } else {
                typeOfConversation = "Error in javascript - invalid boxName";
            }

            // by creating a box entry on the server, we will recieve a response that indicates that a new box is open
            // at which point we will open the box. 
            var justOpened = true;
            chatboxManager.addBox(boxId, boxTitle, true, true, true, typeOfConversation, nid, urlDescription, justOpened);
            chanUtils.createNewBoxEntryOnServer(boxId);
            return false;
        });

        // the height of the main box might have increased due to new contacts being added - scale it appropriately
        chatboxManager.resizeBoxesIfNecessary();
    } catch(err) {
        reportTryCatchError( err, "updateChatControlBox");
    }
};

var updateUserChatBoxTitles = function(contactsInfoDict) {
    try {
        var onlineStatus;
        for (var uid in contactsInfoDict) {
            if (contactsInfoDict[uid]['userPresenceStatus'] !== 'hidden_online_status') {
                // get the *translated* online status by looking it up in a div that we have defined.
                onlineStatus = $('#id-chat-contact-title-' + contactsInfoDict[uid]['userPresenceStatus'] + '-text').html();
            } else {
                // to keep the chatboxes looking clean, by default we don't show a status for active users.
                onlineStatus = '';
            }
            var chatboxTitle = contactsInfoDict[uid]['userOrGroupName'] + onlineStatus;
            
            chatboxManager.changeBoxtitle(uid, chatboxTitle);
        }
    } catch(err) {
        reportTryCatchError( err, "updateUserChatBoxTitles");
    }
};

var updateGroupChatBoxTitles = function(chatGroupsDict) {
    try {
        for (var gid in chatGroupsDict) {
            var chatboxName = chatGroupsDict[gid]['userOrGroupName'];
            var chatboxTitle = chatboxName + " [" + chatGroupsDict[gid]['numGroupMembers'] + "]";
            chatboxManager.changeBoxtitle(gid, chatboxTitle);

            // check if there is an associated "group members" box open and update the title
            // on this box if it exists (note: we do not include the number of users in this box since
            // the number does not always precisely match the number of users in the group due to update delays
            // and since the number of members is already shown in other locations.
            if ($("#id-group_members-dialog-box-" + gid).length > 0) {
                $("#id-group_members-dialog-box-" + gid).dialog("option", "title", chatboxName);
            }
        }
    } catch(err) {
        reportTryCatchError( err, "updateGroupChatBoxTitles");
    }
};


var setupContactsAndGroupsBoxes = function(chatIsDisabled) {

    try {

        var mainBoxId = "main";
        var mainBoxTitle = $('#id-chat-contact-title-text').text();
        var allowElimination = false, includeChatboxInput = false, highlightBoxEnabled = false;
        var typeOfConversation = 'Not used/Not valid'; // not used for contact and group boxes
        var justOpened = true;
        chatboxManager.addBox(mainBoxId, mainBoxTitle, allowElimination, includeChatboxInput,
                highlightBoxEnabled, typeOfConversation, '', '', justOpened);
        // Add the button that allows the user to specify if they want to go online/offline
        $("#" + mainBoxId).chatbox("option", "boxManager").uiChatboxOnlineSelector();
        $("#" + mainBoxId).chatbox("option", "boxManager").addClassToUIChatboxLog("ui-chatbox-log-override-height-for-main");
        $("#" + mainBoxId).chatbox("option", "boxManager").minimizeBox();

        var groupsBoxId = "groups";
        var groupsBoxTitle = $("#id-chat-group-title-text").text();
        chatboxManager.addBox(groupsBoxId, groupsBoxTitle, allowElimination, includeChatboxInput,
                highlightBoxEnabled, typeOfConversation, '', '', justOpened);
        $("#" + groupsBoxId).chatbox("option", "boxManager").uiChatboxCreateGroupButton();
        $("#" + groupsBoxId).chatbox("option", "boxManager").addClassToUIChatboxLog("ui-chatbox-log-override-height-for-main");
        $("#" + groupsBoxId).chatbox("option", "boxManager").minimizeBox();


        if (chatIsDisabled === "yes") {
            chanUtils.executeGoOfflineOnClient();
        }
        else {
            chanUtils.initializeMainAndGroupBoxesOnServer();
        }
    } catch(err) {
        reportTryCatchError( err, "setupContactsAndGroupsBoxes", "warning");
    }
};

