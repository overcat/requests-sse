============
requests-sse
============

.. image:: https://img.shields.io/github/actions/workflow/status/overcat/requests-sse/test-deploy.yml?branch=main
    :alt: GitHub Workflow Status
    :target: https://github.com/overcat/requests-sse/actions
.. image:: https://img.shields.io/pypi/v/requests-sse.svg
    :alt: PyPI
    :target: https://pypi.python.org/pypi/requests-sse
.. image:: https://img.shields.io/badge/python-%3E%3D3.8-blue
    :alt: Python - Version
    :target: https://pypi.python.org/pypi/stellar-sdk

A Server-Sent Events python client based on requests, provides a simple interface to process `Server-Sent Event <https://www.w3.org/TR/eventsource>`_.

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