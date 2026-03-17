from unittest.mock import Mock, call, patch

import pytest
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
def test_connect_stops_after_retry_exhaustion(mock_sleep):
    session = Mock(spec=requests.Session)
    session.request.side_effect = requests.RequestException("boom")
    source = EventSource("http://example.com/sse", session=session)

    with pytest.raises(requests.RequestException):
        source.connect(retry=2)

    assert session.request.call_count == 3
    assert mock_sleep.call_args_list == [call(5.0), call(5.0)]


@patch("requests_sse.client.time.sleep")
def test_connect_returns_when_retry_succeeds(mock_sleep):
    session = Mock(spec=requests.Session)
    session.request.side_effect = [
        requests.RequestException("boom"),
        make_mock_response([b"data:ok", b""]),
    ]
    source = EventSource("http://example.com/sse", session=session)

    source.connect(retry=1)

    assert session.request.call_count == 2
    mock_sleep.assert_called_once_with(5.0)
    source.close()


@patch("requests_sse.client.time.sleep")
def test_connect_stops_when_on_error_closes_source(mock_sleep):
    session = Mock(spec=requests.Session)
    session.request.side_effect = requests.RequestException("boom")
    source = EventSource("http://example.com/sse", session=session)

    def on_error():
        source.close()

    source._on_error = on_error

    with pytest.raises(requests.RequestException):
        source.connect(retry=1)

    assert session.request.call_count == 1
    mock_sleep.assert_not_called()


@patch("requests_sse.client.time.sleep")
def test_connect_stops_when_closed_during_sleep(mock_sleep):
    session = Mock(spec=requests.Session)
    session.request.side_effect = [
        requests.RequestException("boom"),
        AssertionError("connect retried after close"),
    ]
    source = EventSource("http://example.com/sse", session=session)

    def close_during_sleep(_seconds):
        source.close()

    mock_sleep.side_effect = close_during_sleep

    with pytest.raises(requests.RequestException):
        source.connect(retry=1)

    assert session.request.call_count == 1
