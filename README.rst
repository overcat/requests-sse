============
requests-sse
============

A Server-Sent Event python client based on requests, provides a simple interface to process `Server-Sent Event <https://www.w3.org/TR/eventsource>`_.

Installation
------------
.. code-block:: bash

    pip install requests-sse

Usage
-----
.. code-block:: python

    from requests_sse import EventSource

    with EventSource("https://stream.wikimedia.org/v2/stream/recentchange") as event_source:
        try:
            for event in event_source:
                print(event)
        except ConnectionError:
            pass

Credits
-------

This project was inspired by `aiohttp-sse-client <https://github.com/rtfol/aiohttp-sse-client>`_, `aiosseclient <https://github.com/ebraminio/aiosseclient>`_,
`sseclient <https://github.com/btubbs/sseclient>`_, and `sseclient-py <https://github.com/mpetazzoni/sseclient>`_.