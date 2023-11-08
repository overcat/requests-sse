"""Tests for `requests_sse` package."""
import json

from requests_sse import EventSource


def test_basic_usage():
    """Test basic usage."""
    messages = []
    with EventSource(
        "https://stream.wikimedia.org/v2/stream/recentchange"
    ) as event_source:
        for message in event_source:
            if len(messages) > 1:
                break
            messages.append(message)

    print(messages)
    assert messages[0].type == "message"
    assert messages[0].origin == "https://stream.wikimedia.org"
    assert messages[1].type == "message"
    assert messages[1].origin == "https://stream.wikimedia.org"
    data_0 = json.loads(messages[0].data)
    data_1 = json.loads(messages[1].data)
    assert data_0["meta"]["id"] != data_1["meta"]["id"]
