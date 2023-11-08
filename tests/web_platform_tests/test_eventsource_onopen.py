from requests_sse import EventSource, ReadyState

from .const import WPT_SERVER


def test_eventsource_onopen():
    """Test EventSource: open (announcing the connection).

    ..seealso: https://github.com/web-platform-tests/wpt/blob/master/
    eventsource/eventsource-onopen.htm
    """

    def on_open():
        """Callback for open event."""
        assert source.ready_state == ReadyState.OPEN

    source = EventSource(WPT_SERVER + "resources/message.py", on_open=on_open)
    assert source.ready_state == ReadyState.CONNECTING
    source.connect()
    assert source.ready_state == ReadyState.OPEN
    source.close()
