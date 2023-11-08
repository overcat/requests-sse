from requests_sse import EventSource

from .const import WPT_SERVER


def test_eventsource_onmessage():
    """Test EventSource: onmessage.

    ..seealso: https://github.com/web-platform-tests/wpt/blob/master/
    eventsource/eventsource-onmessage.htm
    """

    def on_message(event):
        """Callback for message event."""
        assert event.data == "data"

    source = EventSource(WPT_SERVER + "resources/message.py", on_message=on_message)
    source.connect()
    for e in source:
        assert e.data == "data"
        break
    source.close()
