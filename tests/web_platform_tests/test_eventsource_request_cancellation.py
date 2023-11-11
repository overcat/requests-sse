import time

from requests_sse import EventSource, ReadyState

from .const import WPT_SERVER


def test_eventsource_request_cancellation():
    """Test EventSource: reconnection event.

    ..seealso: https://github.com/web-platform-tests/wpt/blob/master/
    eventsource/eventsource-request-cancellation.htm
    """
    closed = False

    def on_open():
        if closed:
            assert False

    def on_error():
        assert source.ready_state == ReadyState.CLOSED

    try:
        with EventSource(
            WPT_SERVER
            + "resources/message.py?sleep=1000&message="
            + "retry:1000\ndata:abc\n\n",
            on_open=on_open,
            on_error=on_error,
        ) as source:
            raise ConnectionAbortedError
    except ConnectionAbortedError:
        closed = True
        time.sleep(1)
        assert source.ready_state == ReadyState.CLOSED
