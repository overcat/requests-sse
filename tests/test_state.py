from unittest.mock import Mock, patch

import pytest

from requests_sse import EventSource, ReadyState


def test_next_raises_stop_iteration_after_close():
    source = EventSource("http://example.com/sse")
    source.close()

    with pytest.raises(StopIteration):
        next(source)


@patch("requests_sse.client.time.sleep")
def test_next_stops_when_on_error_closes_source(mock_sleep):
    source = EventSource("http://example.com/sse")
    source._ready_state = ReadyState.OPEN
    source._response = Mock()
    source._data_generator = iter(())
    source.connect = Mock()

    def on_error():
        source.close()

    source._on_error = on_error

    with pytest.raises(StopIteration):
        next(source)

    source.connect.assert_not_called()
    mock_sleep.assert_not_called()
