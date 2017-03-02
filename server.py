#!/usr/bin/env python3

import json
import logging
import os
import signal

import tornado
from tornado import gen, web
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop, PeriodicCallback
from tornado.iostream import StreamClosedError
from tornado.options import options
from tornado.wsgi import WSGIContainer

from faker import Factory
from flask_server import app as flaskapp

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

fake = Factory.create()

"""

Main server!

Tornado sends SSE

Rerouts other calls to FLASK

"""


def random_string():
    '''
    Random dict 
    '''
    out = {"name": fake.name(),
           "address": fake.address()}
    return json.dumps(out)


class DataSource(object):
    """
    Generic object for producing data to feed to clients.
    """

    def __init__(self, initial_data=None):
        self._data = initial_data

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        self._data = data


class EventSource(web.RequestHandler):
    """
    Basic handler for server-sent events.
    """

    def initialize(self, source):
        """
        The ``source`` parameter is a string that is updated with
        new data. The :class:`EventSouce` instance will continuously
        check if it is updated and publish to clients when it is.
        """
        self.source = source
        self._last = None
        self.set_header('content-type', 'text/event-stream')
        self.set_header('cache-control', 'no-cache')

    @gen.coroutine
    def publish(self, data):
        """
        Pushes data to a listener.
        """
        try:
            self.write('data: {}\n\n'.format(data))
            yield self.flush()
        except StreamClosedError as exception:
            logger.exception(exception)

    @gen.coroutine
    def get(self):
        while True:
            if self.source.data != self._last:
                yield self.publish(self.source.data)
                self._last = self.source.data
            else:
                yield gen.sleep(0.005)


class MainHandler(web.RequestHandler):

    def get(self):
        self.redirect("/static/index.html")

if __name__ == "__main__":

    options.parse_command_line()

    publisher = DataSource(random_string())

    def get_next():
        publisher.data = random_string()
        logger.debug("Publisher: %s", publisher.data)

    checker = PeriodicCallback(lambda: get_next(), 1000.)
    checker.start()

    flask_handler = WSGIContainer(flaskapp)

    app = web.Application(
        [
            (r'/', MainHandler),
            (r'/events', EventSource, {'source': publisher}),
            (r'/static/(.*)', web.StaticFileHandler, {'path': "./static"}),
            (r".*", web.FallbackHandler, {'fallback': flask_handler}),
        ],
        debug=True
    )
    server = HTTPServer(app)
    server.listen(8000)
    signal.signal(signal.SIGINT, lambda x, y: IOLoop.instance().stop())
    IOLoop.instance().start()
