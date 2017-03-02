#!/usr/bin/env python3

import json
import logging
import signal

from faker import Factory
from tornado import gen, web
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop, PeriodicCallback
from tornado.iostream import StreamClosedError
from tornado.options import options
from tornado.wsgi import WSGIContainer

from flask_server import app as flaskapp

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

fake = Factory.create()

"""

Main server!

Tornado sends SSE

Rerouts other calls to FLASK

"""


class DataSource(object):
    """
    Generic object for producing data to feed to clients.
    Next generates random dictionary data
    """

    def __init__(self, initial_data=None):
        if initial_data is None:
            self.next()
        else:
            self._data = initial_data

    @property
    def data(self):
        return json.dumps(self._data)

    def next(self):
        '''
        Gets some random data
        '''
        self._data = {
            "name": fake.name(),
            "address": fake.address()
        }
        logger.debug(self._data)


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
            logger.warning(str(exception))
            
    @gen.coroutine
    def get(self):
        while True:
            if self.source.data != self._last:
                yield self.publish(self.source.data)
                self._last = self.source.data
            else:
                yield gen.sleep(0.005)


class MainHandler(web.RequestHandler):
    '''
    Main HTTP handler
    '''

    def get(self):
        '''
        It just forwards to IndexError
        '''
        self.redirect("/static/index.html")

if __name__ == "__main__":
    # Tornado options
    options.parse_command_line()
    # publisher for SSE
    publisher = DataSource()
    checker = PeriodicCallback(lambda: publisher.next(), 1000.)
    checker.start()
    # All the requests handled by flask
    flask_handler = WSGIContainer(flaskapp)
    # Router
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
