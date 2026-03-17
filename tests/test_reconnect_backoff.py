from datetime import timedelta
from unittest.mock import Mock, call, patch

import requests

from requests_sse import EventSource


def make_mock_response(lines, status_code=200, content_type="text/event-stream"):
    response = Mock(spec=requests.Response)
    response.status_code = status_code
    response.headers = {"Content-Type": content_type}
    response.history = []
    response.url = "http://example.com/sse"
    response.iter_lines.return_value = iter(lines)
    response.close = Mock()
    return response


@patch("requests_sse.client.time.sleep")
def test_retry_values_persist_across_reconnects(mock_sleep):
    session = Mock(spec=requests.Session)
    session.request.side_effect = [
        make_mock_response([b"retry:2000", b"data:one", b""]),
        make_mock_response([b"data:two", b""]),
    ]
    source = EventSource("http://example.com/sse", session=session)
    source.connect()

    assert next(source).data == "one"
    assert next(source).data == "two"
    assert mock_sleep.call_args_list == [call(2.0)]

    source.close()


@patch("requests_sse.client.time.sleep")
def test_connect_uses_fixed_delay_after_request_exceptions(mock_sleep):
    session = Mock(spec=requests.Session)
    session.request.side_effect = [
        requests.RequestException("boom"),
        make_mock_response([b"data:ok", b""]),
    ]
    source = EventSource(
        "http://example.com/sse",
        reconnection_time=timedelta(seconds=3),
        session=session,
    )

    source.connect(retry=1)

    assert session.request.call_count == 2
    mock_sleep.assert_called_once_with(3.0)
    source.close()


@patch("requests_sse.client.time.sleep")
def test_reconnect_delay_does_not_grow_between_cycles(mock_sleep):
    session = Mock(spec=requests.Session)
    session.request.side_effect = [
        make_mock_response([b"data:one", b""]),
        make_mock_response([b"data:two", b""]),
        make_mock_response([b"data:three", b""]),
    ]
    source = EventSource(
        "http://example.com/sse",
        reconnection_time=timedelta(seconds=4),
        session=session,
    )
    source.connect()

    assert next(source).data == "one"
    assert next(source).data == "two"
    assert next(source).data == "three"
    assert mock_sleep.call_args_list == [call(4.0), call(4.0)]

    source.close()
