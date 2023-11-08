from datetime import timedelta

from requests_sse import EventSource, ReadyState
from .const import WPT_SERVER


def test_eventsource_reconnect():
    """Test EventSource: reconnection.

    ..seealso: https://github.com/web-platform-tests/wpt/blob/master/
    eventsource/eventsource-reconnect.htm
    """
    source = EventSource(WPT_SERVER + "resources/status-reconnect.py?status=200")
    source.connect()
    for e in source:
        assert e.data == "data"
        break
    source.close()


def test_eventsource_reconnect_event():
    """Test EventSource: reconnection event.

    ..seealso: https://github.com/web-platform-tests/wpt/blob/master/
    eventsource/eventsource-reconnect.htm
    """
    opened = False
    reconnected = False

    def on_error():
        nonlocal reconnected
        assert source.ready_state == ReadyState.CONNECTING
        assert opened is True
        reconnected = True

    with EventSource(
        WPT_SERVER + "resources/status-reconnect.py?status=200&ok_first&id=2",
        reconnection_time=timedelta(milliseconds=2),
        on_error=on_error,
    ) as source:
        for e in source:
            if not opened:
                opened = True
                assert reconnected is False
                assert e.data == "ok"
            else:
                assert reconnected is True
                assert e.data == "data"
                break
