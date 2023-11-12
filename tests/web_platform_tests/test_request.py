import pytest

from requests_sse import EventSource, InvalidStatusCodeError, ReadyState

from .const import WPT_SERVER


def test_request_accept():
    """Test EventSource: Accept header.

    ..seealso: https://github.com/web-platform-tests/wpt/blob/master/
    eventsource/request-accept.htm
    """
    source = EventSource(WPT_SERVER + "resources/accept.event_stream?pipe=sub")
    source.connect()
    for e in source:
        assert e.data == "text/event-stream"
        break
    source.close()


def test_request_cache_control():
    """Test EventSource: Cache-Control.

    ..seealso: https://github.com/web-platform-tests/wpt/blob/master/
    eventsource/request-cache-control.htm
    """
    source = EventSource(WPT_SERVER + "resources/cache-control.event_stream?pipe=sub")
    source.connect()
    for e in source:
        assert e.data == "no-cache"
        break
    source.close()


def test_request_redirect():
    """Test EventSource: redirect.

    ..seealso: https://github.com/web-platform-tests/wpt/blob/master/
    eventsource/request-redirect.htm
    """

    def test(status):
        def on_error():
            assert False

        def on_open():
            assert source.ready_state == ReadyState.OPEN

        source = EventSource(
            WPT_SERVER.replace(
                "eventsource",
                "common/redirect.py?"
                "location=/eventsource/resources/message.py&status=" + str(status),
            ),
            on_open=on_open,
            on_error=on_error,
        )
        source.connect()
        source.close()

    test(301)
    test(302)
    test(303)
    test(307)


def test_request_status_error():
    """Test EventSource: redirect.

    ..seealso: https://github.com/web-platform-tests/wpt/blob/master/
    eventsource/request-status-error.htm
    """

    def test(status):
        def on_error():
            assert source.ready_state == ReadyState.CLOSED

        def on_message():
            assert source.ready_state == ReadyState.OPEN

        source = EventSource(
            WPT_SERVER + "resources/status-error.py?status=" + str(status),
            on_message=on_message,
            on_error=on_error,
        )
        with pytest.raises(InvalidStatusCodeError) as e:
            source.connect()
        assert e.value.status_code == status

    test(204)
    test(205)
    test(210)
    test(299)
    test(404)
    test(410)
    test(503)


def test_request_post_to_connect():
    """Test EventSource post method for connection."""
    source = EventSource(WPT_SERVER + "resources/message.py", method="POST")
    source.connect()
    for e in source:
        assert e.data == "data"
        break
    source.close()
