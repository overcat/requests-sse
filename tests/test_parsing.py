from unittest.mock import Mock

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
