import socket
from unittest.mock import Mock, patch

import pytest
import requests
from urllib3.exceptions import ReadTimeoutError

from requests_sse import EventSource, ReadyState
from requests_sse.client import _is_read_timeout_error


class ExceptionIterator:
    def __init__(self, exc):
        self._exc = exc

    def __iter__(self):
        return self

    def __next__(self):
        raise self._exc


def test_is_read_timeout_error_recognizes_wrapped_variants():
    wrapped_by_args = requests.exceptions.ConnectionError(
        ReadTimeoutError(None, None, "timed out")
    )
    wrapped_by_socket = requests.exceptions.ConnectionError(socket.timeout("timed out"))
    wrapped_by_context = requests.exceptions.ConnectionError("timed out")
    wrapped_by_context.__context__ = ReadTimeoutError(None, None, "timed out")

    assert _is_read_timeout_error(requests.exceptions.ReadTimeout("timed out"))
    assert _is_read_timeout_error(requests.exceptions.Timeout("timed out"))
    assert _is_read_timeout_error(wrapped_by_args)
    assert _is_read_timeout_error(wrapped_by_socket)
    assert _is_read_timeout_error(wrapped_by_context)
    assert not _is_read_timeout_error(requests.exceptions.ConnectionError("boom"))


@patch("requests_sse.client.time.sleep")
def test_next_raises_read_timeout_instead_of_reconnecting(mock_sleep):
    timeout_exc = requests.exceptions.ConnectionError(
        ReadTimeoutError(None, None, "timed out")
    )
    response = Mock()
    source = EventSource("http://example.com/sse")
    source._ready_state = ReadyState.OPEN
    source._response = response
    source._data_generator = ExceptionIterator(timeout_exc)
    source.connect = Mock()

    with pytest.raises(requests.exceptions.ConnectionError) as caught:
        next(source)

    assert caught.value is timeout_exc
    assert source.ready_state == ReadyState.CONNECTING
    response.close.assert_called_once()
    assert source._response is None
    assert source._data_generator is None
    source.connect.assert_not_called()
    mock_sleep.assert_not_called()


@patch("requests_sse.client.time.sleep")
def test_next_raises_direct_read_timeout(mock_sleep):
    timeout_exc = requests.exceptions.ReadTimeout("timed out")
    response = Mock()
    source = EventSource("http://example.com/sse")
    source._ready_state = ReadyState.OPEN
    source._response = response
    source._data_generator = ExceptionIterator(timeout_exc)
    source.connect = Mock()

    with pytest.raises(requests.exceptions.ReadTimeout) as caught:
        next(source)

    assert caught.value is timeout_exc
    assert source.ready_state == ReadyState.CONNECTING
    response.close.assert_called_once()
    source.connect.assert_not_called()
    mock_sleep.assert_not_called()


@patch("requests_sse.client.time.sleep")
def test_source_can_reconnect_after_read_timeout(mock_sleep):
    timeout_exc = requests.exceptions.ConnectionError(
        ReadTimeoutError(None, None, "timed out")
    )
    first_response = Mock()
    second_response = Mock(spec=requests.Response)
    second_response.status_code = 200
    second_response.headers = {"Content-Type": "text/event-stream"}
    second_response.history = []
    second_response.url = "http://example.com/sse"
    second_response.iter_lines.return_value = iter([b"data:ok", b""])
    second_response.close = Mock()
    session = Mock(spec=requests.Session)
    session.request.return_value = second_response
    source = EventSource("http://example.com/sse", session=session)
    source._ready_state = ReadyState.OPEN
    source._response = first_response
    source._data_generator = ExceptionIterator(timeout_exc)

    with pytest.raises(requests.exceptions.ConnectionError):
        next(source)

    source.connect()

    event = next(source)

    assert event.data == "ok"
    mock_sleep.assert_not_called()
    source.close()


@patch("requests_sse.client.time.sleep")
def test_next_still_reconnects_after_non_timeout_connection_errors(mock_sleep):
    response = Mock()
    source = EventSource("http://example.com/sse")
    source._ready_state = ReadyState.OPEN
    source._response = response
    source._data_generator = ExceptionIterator(requests.exceptions.ConnectionError("boom"))
    source.connect = Mock(side_effect=RuntimeError("reconnect attempted"))

    with pytest.raises(RuntimeError, match="reconnect attempted"):
        next(source)

    source.connect.assert_called_once_with(source._max_connect_retry)
    mock_sleep.assert_called_once_with(5.0)
