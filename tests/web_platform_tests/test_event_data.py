#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from requests_sse import EventSource, ReadyState
from .const import WPT_SERVER


def test_event_data():
    """Test EventSource: lines and data parsing.

    ..seealso: https://github.com/web-platform-tests/wpt/blob/master/
    eventsource/event-data.html
    """
    counter = 0
    source = EventSource(WPT_SERVER + "resources/message2.py")
    source.connect()
    for e in source:
        if counter == 0:
            assert e.data == "msg\nmsg"
        elif counter == 1:
            assert e.data == ""
        elif counter == 2:
            assert e.data == "end"
            source.close()
            break
        else:
            assert False
        counter += 1


def test_eventsource_close():
    """Test EventSource: close.

    ..seealso: https://github.com/web-platform-tests/wpt/blob/master/
    eventsource/eventsource-close.htm
    """
    source = EventSource(WPT_SERVER + "resources/message.py")
    assert source.ready_state == ReadyState.CONNECTING
    source.connect()
    assert source.ready_state == ReadyState.OPEN
    source.close()
    assert source.ready_state == ReadyState.CLOSED

    count = 0
    reconnected = False

    def on_error():
        nonlocal count, reconnected
        if count == 1:
            assert source.ready_state == ReadyState.CONNECTING
            reconnected = True
        elif count == 2:
            assert source.ready_state == ReadyState.CONNECTING
            count += 1
        elif count == 3:
            assert source.ready_state == ReadyState.CLOSED
        else:
            assert False

    with EventSource(
        WPT_SERVER
        + "resources/reconnect-fail.py?id="
        + str(datetime.utcnow().timestamp()),
        reconnection_time=timedelta(milliseconds=2),
        on_error=on_error,
    ) as source:
        try:
            for e in source:
                if count == 0:
                    assert reconnected is False
                    assert e.data == "opened"
                elif count == 1:
                    assert reconnected is True
                    assert e.data == "reconnected"
                else:
                    assert False
                count += 1
        except ConnectionError:
            pass
