
// idle.js (c) Alexios Chouchoulas 2009
// Released under the terms of the GNU Public License version 2.0 (or later).
// Extensive LexaLink related modifications by Alexander Marquardt 2012.


function IdleClass(idle_params) {
    // class that defines what actions will be take when the user is idle for a pre-defined period of time.
    // This must be called with the "new" declaration so that an object is instantiated
    /* idle_params is a dictionary object with the following values:

    {idle_timeout: int, away_timeout: int, onIdle: function(), onAway: function(), onBack: function() }

    Here's a simple example, using jQuery (the only jQuery-specific thing is the code inside the function() event handlers):

    idle_params.onIdle = function() {$('#div_idle').css('opacity', '1');}
    idle_params.onAway = function() {$('#div_away').css('opacity', '1');}
    idle_params.onBack = function(isIdle, isAway) {
        if (isIdle) $('#div_idle').css('opacity', '0.2');
        if (isAway) $('#div_away').css('opacity', '0.2');
    }
    */

    var _idleTimeout = idle_params.idle_timeout;
    var _awayTimeout = idle_params.away_timeout;
    
    var _idleNow = false;
    var _idleTimestamp = null;
    var _idleTimer = null;
    var _awayNow = false;
    var _awayTimestamp = null;
    var _awayTimer = null;

    setIdleTimeout(_idleTimeout);
    setAwayTimeout(_awayTimeout);
    
    function setIdleTimeout(ms)
    {
        _idleTimeout = ms;
        _idleTimestamp = new Date().getTime() + ms;
        if (_idleTimer != null) {
        clearTimeout (_idleTimer);
        }
        _idleTimer = setTimeout(_makeIdle, ms + 50);
    }


    function setAwayTimeout(ms)
    {
        _awayTimeout = ms;
        _awayTimestamp = new Date().getTime() + ms;
        if (_awayTimer != null) {
        clearTimeout (_awayTimer);
        }
        _awayTimer = setTimeout(_makeAway, ms + 50);
    }

    function _makeIdle()
    {
        var t = new Date().getTime();
        if (t < _idleTimestamp) {
        //console.log('Not idle yet. Idle in ' + (_idleTimestamp - t + 50));
        _idleTimer = setTimeout(_makeIdle, _idleTimestamp - t + 50);
        return;
        }
        _idleNow = true;

        try {
        if (idle_params.onIdle) idle_params.onIdle();
        } catch (err) {
        }
    }

    function _makeAway()
    {
        var t = new Date().getTime();
        if (t < _awayTimestamp) {
        _awayTimer = setTimeout(_makeAway, _awayTimestamp - t + 50);
        return;
        }
        _awayNow = true;

        try {
        if (idle_params.onAway) idle_params.onAway();
        } catch (err) {
        }
    }


    function _active(event)
    {
        var t = new Date().getTime();
        _idleTimestamp = t + _idleTimeout;
        _awayTimestamp = t + _awayTimeout;

        if (_idleNow) {
        setIdleTimeout(_idleTimeout);
        }

        if (_awayNow) {
        setAwayTimeout(_awayTimeout);
        }

        try {
        if ((_idleNow || _awayNow) && idle_params.onBack) idle_params.onBack(_idleNow, _awayNow);
        } catch (err) {
        }

        _idleNow = false;
        _awayNow = false;
    }



    bind_online_status_event_handlers = function()
    {
            // bind the following actions to the "_active" handler function
                $(document).mousemove(_active);
                try {
                    $(document).mouseenter(_active);
                } catch (err) { }
                try {
                    $(document).scroll(_active);
                } catch (err) { }
                try {
                    $(document).keydown(_active);
                } catch (err) { }
                try {
                    $(document).click(_active);
                } catch (err) { }
                try {
                    $(document).dblclick(_active);
                } catch (err) { }
    }

    unbind_online_status_event_handlers = function()
    {
            // bind the following actions to the "_active" handler function
                $(document).unbind('mousemove', _active);
                try {
                    $(document).unbind('mouseenter', _active);
                } catch (err) { }
                try {
                    $(document).unbind('scroll', _active);
                } catch (err) { }
                try {
                    $(document).unbind('keydown', _active);
                } catch (err) { }
                try {
                    $(document).unbind('click', _active);
                } catch (err) { }
                try {
                    $(document).unbind('dblclick', _active);
                } catch (err) { }
    }

    bind_online_status_event_handlers();
    
} // end IdleClass



