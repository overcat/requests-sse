from datetime import timedelta
from unittest.mock import Mock, patch

import requests

from requests_sse import EventSource


def make_mock_response(lines, status_code=200, content_type="text/event-stream"):
    """Create a mock response. `lines` must be a list of bytes."""
    response = Mock(spec=requests.Response)
    response.status_code = status_code
    response.headers = {"Content-Type": content_type}
    response.history = []
    response.url = "http://example.com/sse"
    response.iter_lines.return_value = iter(lines)
    response.close = Mock()
    return response


def make_connected_source(lines):
    session = Mock(spec=requests.Session)
    session.request.return_value = make_mock_response(lines)

    source = EventSource("http://example.com/sse", session=session)
    source.connect()
    return source


def test_strip_only_one_leading_space_from_field_value():
    source = make_connected_source([b"data:  two spaces", b""])

    event = next(source)

    assert event.data == " two spaces"
    source.close()


def test_retry_field_only_accepts_ascii_digits():
    source = EventSource("http://example.com/sse")
    source._reconnection_time = timedelta(seconds=5)

    for field_value in ("-1", "+5", "abc"):
        source._process_field("retry", field_value)
        assert source._reconnection_time == timedelta(seconds=5)

    source._process_field("retry", "3000")

    assert source._reconnection_time == timedelta(seconds=3)


def test_id_field_rejects_values_containing_null():
    source = EventSource("http://example.com/sse")
    source._event_id = "existing-id"

    source._process_field("id", "abc\x00def")

    assert source._event_id == "existing-id"


def test_bom_is_ignored_at_start_of_stream():
    source = make_connected_source([b"\xef\xbb\xbfdata:hello", b""])

    event = next(source)

    assert event.data == "hello"
    source.close()


@patch("requests_sse.client.time.sleep")
def test_bom_is_ignored_after_reconnect(mock_sleep):
    session = Mock(spec=requests.Session)
    session.request.side_effect = [
        make_mock_response([b"data:first", b""]),
        make_mock_response([b"\xef\xbb\xbfdata:second", b""]),
        make_mock_response([b"data:third", b""]),
    ]
    source = EventSource("http://example.com/sse", session=session)
    source.connect()

    assert next(source).data == "first"
    assert next(source).data == "second"
    mock_sleep.assert_called_once_with(5.0)


def test_default_event_type_is_message_when_dispatching():
    source = make_connected_source([b"data:hello", b""])

    event = next(source)

    assert event.type == "message"
    source.close()
