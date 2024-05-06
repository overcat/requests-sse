import copy
import logging
import time
from dataclasses import dataclass
from datetime import timedelta
from enum import IntEnum
from typing import Callable, Iterator, Optional

import requests
from urllib3.util import Url, parse_url

__all__ = [
    "ReadyState",
    "EventSource",
    "MessageEvent",
    "InvalidStatusCodeError",
    "InvalidContentTypeError",
]

DEFAULT_RECONNECTION_TIME = timedelta(seconds=5)
DEFAULT_MAX_CONNECT_RETRY = 5
_CONTENT_TYPE_EVENT_STREAM = "text/event-stream"
_CONTENT_TYPE_EVENT_STREAM_UTF_8 = "text/event-stream;charset=utf-8"
_LOGGER = logging.getLogger(__name__)


class InvalidStatusCodeError(requests.RequestException):
    """Invalid status code error."""

    def __init__(self, status_code: int, *args, **kwargs):
        self.status_code = status_code
        requests.RequestException.__init__(self, *args, **kwargs)


class InvalidContentTypeError(requests.RequestException):
    """Invalid content type error."""

    def __init__(self, content_type: Optional[str], *args, **kwargs):
        self.content_type = content_type
        requests.RequestException.__init__(self, *args, **kwargs)


class ReadyState(IntEnum):
    """Represents the state of the connection.

    See `MDN - EventSource: readyState property <https://developer.mozilla.org/en-US/docs/Web/API/EventSource/readyState>`__ for more information.
    """

    CONNECTING = 0
    OPEN = 1
    CLOSED = 2


@dataclass
class MessageEvent:
    """Represents MessageEvent Interface.

    See `MDN - EventSource: instance properties <https://developer.mozilla.org/en-US/docs/Web/API/MessageEvent#instance_properties>`__ for more information.
    See `Event types <https://javascript.info/server-sent-events#event-types>` for more information.
    """

    type: Optional[str]
    """A string representing the type of event."""
    data: Optional[str]
    """The data sent by the message emitter."""
    origin: str
    """A string representing the message emitter."""
    last_event_id: str
    """A string representing a unique ID for the event."""


class EventSource:
    """Represents EventSource Interface as a context manager.

    An example::

        import requests
        from requests_sse import EventSource, InvalidStatusCodeError, InvalidContentTypeError

        with EventSource("https://stream.wikimedia.org/v2/stream/recentchange", timeout=30) as event_source:
            try:
                for event in event_source:
                    print(event)
            except InvalidStatusCodeError:
                pass
            except InvalidContentTypeError:
                pass
            except requests.RequestException:
                pass

    See `MDN - EventSource <https://developer.mozilla.org/en-US/docs/Web/API/EventSource>`__ for more information.

    :param url: specifies the URL to which to connect
    :param method: specifies the HTTP method with which connection should be established
    :param reconnection_time: wait time before try to reconnect in case
        connection broken
    :param max_connect_retry: maximum number of retries to connect
    :param timeout: how long to wait for the server to send data before giving up,
        I recommend that you set a reasonable value based on actual needs, which will improve stability,
        see https://docs.python-requests.org/en/latest/user/quickstart/#timeouts for more information
    :param session: specifies a requests.Session, if not, create
        a default requests.Session
    :param on_open: event handler for open event
    :param on_message: event handler for message event
    :param on_error: event handler for error event
    :param kwargs: keyword arguments will pass to underlying requests.request() method.

    :raises InvalidStatusCodeError: if status code is not 200
    :raises InvalidContentTypeError: if content type is not 'text/event-stream' or 'text/event-stream;charset=utf-8'
    :raises requests.RequestException: if connection failed
    """

    def __init__(
        self,
        url: str,
        method: str = "GET",
        reconnection_time: timedelta = DEFAULT_RECONNECTION_TIME,
        max_connect_retry: int = DEFAULT_MAX_CONNECT_RETRY,
        timeout: Optional[float] = None,
        session: Optional[requests.Session] = None,
        on_open: Optional[Callable[[], None]] = None,
        on_message: Optional[Callable[[MessageEvent], None]] = None,
        on_error: Optional[Callable[[], None]] = None,
        **kwargs,
    ):
        self._url = url
        self._ready_state = ReadyState.CONNECTING

        if session is not None:
            self._session = session
            self._need_close_session = False
        else:
            self._session = requests.Session()
            self._need_close_session = True

        self._on_open = on_open
        self._on_message = on_message
        self._on_error = on_error

        self._reconnection_time = reconnection_time
        self._orginal_reconnection_time = reconnection_time
        self._max_connect_retry = max_connect_retry
        self._timeout = timeout
        self._last_event_id = ""
        self._kwargs = copy.deepcopy(kwargs)

        if "headers" not in self._kwargs:
            self._kwargs["headers"] = dict()
        self._kwargs["headers"]["Accept"] = _CONTENT_TYPE_EVENT_STREAM
        self._kwargs["headers"]["Cache-Control"] = "no-cache"

        self._event_id = ""
        self._event_type = None
        self._event_data = None

        self._origin: Optional[str] = None
        self._response: Optional[requests.Response] = None
        self._data_generator: Optional[Iterator] = None

        self._method = method

    def __enter__(self):
        """Connect and listen Server-Sent Event."""
        self.connect(self._max_connect_retry)
        return self

    def __exit__(self, *exc):
        """Close connection and session if needed."""
        self.close()
        if self._need_close_session:
            self._session.close()

    @property
    def url(self) -> str:
        """Return URL to which to connect."""
        return self._url

    @property
    def ready_state(self) -> ReadyState:
        """Return ready state."""
        return self._ready_state

    def __iter__(self):
        return self

    def __next__(self) -> MessageEvent:
        """Process events"""
        if not self._response:
            raise ValueError("response is None")

        if not self._data_generator:
            raise ValueError("data_generator is None")

        while True:
            while True:
                try:
                    line_in_bytes = next(self._data_generator)
                except StopIteration:
                    self._event_type = None
                    self._event_data = None
                    break
                except requests.RequestException as e:
                    _LOGGER.error("requests exception", exc_info=e)
                    self._event_type = None
                    self._event_data = None
                    break

                line: str = line_in_bytes.decode("utf8")
                line = line.rstrip("\n").rstrip("\r")

                if line == "":
                    # empty line
                    event = self._dispatch_event()
                    if event is not None:
                        return event
                    continue

                if line[0] == ":":
                    # comment line, ignore
                    continue

                if ":" in line:
                    # contains ':'
                    fields = line.split(":", 1)
                    field_name = fields[0]
                    field_value = fields[1].lstrip(" ")
                    self._process_field(field_name, field_value)
                else:
                    self._process_field(line, "")
            self._ready_state = ReadyState.CONNECTING
            if self._on_error:
                self._on_error()
            self._reconnection_time *= 2
            _LOGGER.debug(
                "wait %s seconds for reconnect", self._reconnection_time.total_seconds()
            )
            time.sleep(self._reconnection_time.total_seconds())
            self.connect(self._max_connect_retry)

    def connect(self, retry: int = 0) -> None:
        """Connect to resource."""
        _LOGGER.debug(f"connect, retry={retry}")

        if self._last_event_id != "":
            self._kwargs["headers"]["Last-Event-Id"] = self._last_event_id

        try:
            response = self._session.request(
                method=self._method,
                url=self.url,
                stream=True,
                timeout=self._timeout,
                **self._kwargs,
            )
        except requests.RequestException:
            if retry <= 0 or self._ready_state == ReadyState.CLOSED:
                self._fail_connect()
                raise
            else:
                self._ready_state = ReadyState.CONNECTING
                if self._on_error:
                    self._on_error()
                self._reconnection_time *= 2
                _LOGGER.debug(
                    "wait %s seconds for retry", self._reconnection_time.total_seconds()
                )
                time.sleep(self._reconnection_time.total_seconds())
                self.connect(retry - 1)
            return

        if response.status_code != 200:
            error_message = "fetch {} failed with wrong response status: {}".format(
                self._url, response.status_code
            )
            _LOGGER.error(error_message)
            self._fail_connect()
            raise InvalidStatusCodeError(
                response.status_code, error_message, response=response
            )

        content_type = response.headers.get("Content-Type")
        if not content_type or content_type.lower().replace(" ", "") not in (
            _CONTENT_TYPE_EVENT_STREAM,
            _CONTENT_TYPE_EVENT_STREAM_UTF_8,
        ):
            error_message = "fetch {} failed with wrong Content-Type: {}".format(
                self._url, response.headers.get("Content-Type")
            )
            _LOGGER.error(error_message)
            self._fail_connect()
            raise InvalidContentTypeError(
                content_type, error_message, response=response
            )
        # only status == 200 and content_type is 'text/event-stream' or 'text/event-stream;charset=utf-8' can reach here
        self._connected()
        self._response = response
        self._data_generator = response.iter_lines()
        self._origin = self._get_origin(response)

    def close(self) -> None:
        """Close connection."""
        _LOGGER.debug("close")
        self._ready_state = ReadyState.CLOSED
        if self._response is not None:
            self._response.close()
            self._response = None
            self._data_generator = None

    def _connected(self):
        """Announce the connection is made."""
        if self._ready_state != ReadyState.CLOSED:
            self._ready_state = ReadyState.OPEN
            if self._on_open:
                self._on_open()
        self._reconnection_time = self._orginal_reconnection_time

    def _fail_connect(self):
        """Announce the connection is failed."""
        if self._ready_state != ReadyState.CLOSED:
            self._ready_state = ReadyState.CLOSED
            if self._on_error:
                self._on_error()

    def _dispatch_event(self):
        """Dispatch event."""
        self._last_event_id = self._event_id

        if self._event_data is None:
            self._event_type = None
            return

        self._event_data = self._event_data.rstrip("\n")

        message = MessageEvent(
            type=self._event_type,
            data=self._event_data,
            origin=self._origin,
            last_event_id=self._last_event_id,
        )
        _LOGGER.debug(message)
        if self._on_message and self._event_type == "message":
            self._on_message(message)

        self._event_type = None
        self._event_data = None
        return message

    def _process_field(self, field_name, field_value):
        """Process field."""
        if field_name == "event":
            self._event_type = field_value

        elif field_name == "data":
            # by default, the event type is "message"
            if self._event_type is None:
                self._event_type = "message"

            if self._event_data is None:
                self._event_data = field_value
            else:
                self._event_data += field_value
            self._event_data += "\n"

        elif field_name == "id" and field_value not in ("\u0000", "\x00\x00"):
            self._event_id = field_value

        elif field_name == "retry":
            try:
                retry_in_ms = int(field_value)
                self._reconnection_time = timedelta(milliseconds=retry_in_ms)
            except ValueError:
                _LOGGER.warning(
                    "Received invalid retry value %s, ignore it", field_value
                )

    @staticmethod
    def _get_origin(response: requests.Response) -> str:
        """Get origin from response."""
        url = response.history[0].url if response.history else response.url
        parsed_url = parse_url(url)
        return Url(
            scheme=parsed_url.scheme, host=parsed_url.host, port=parsed_url.port
        ).url
