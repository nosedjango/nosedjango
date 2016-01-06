import os
import time

from django.core.handlers.wsgi import WSGIHandler
from nosedjango.plugins.base_plugin import Plugin

# Next 3 plugins taken from django-sane-testing:
# http://github.com/Almad/django-sane-testing
# By: Lukas "Almad" Linhart http://almad.net/
#####
# It was a nice try with Django server being threaded.
# It still sucks for some cases (did I mentioned urllib2?),
# so provide cherrypy as working alternative.
# Do imports in method to avoid CP as dependency
# Code originally written by Mikeal Rogers under Apache License.
#####

DEFAULT_LIVE_SERVER_ADDRESS = '0.0.0.0'
DEFAULT_LIVE_SERVER_PORT = '8000'


class CherryPyLiveServerPlugin(Plugin):
    name = 'cherrypyliveserver'
    activation_parameter = '--with-cherrypyliveserver'
    nosedjango = True

    def __init__(self):
        Plugin.__init__(self)
        self.server_started = False
        self.server_thread = None

    def options(self, parser, env=os.environ):
        Plugin.options(self, parser, env)

    def configure(self, options, config):
        Plugin.configure(self, options, config)

    def startTest(self, test):
        from django.conf import settings

        if not self.server_started and \
           getattr(test, 'start_live_server', False):

            self.start_server(
                address=getattr(
                    settings,
                    "LIVE_SERVER_ADDRESS",
                    DEFAULT_LIVE_SERVER_ADDRESS,
                ),
                port=int(getattr(
                    settings,
                    "LIVE_SERVER_PORT",
                    DEFAULT_LIVE_SERVER_PORT,
                ))
            )
            self.server_started = True

    def finalize(self, result):
        self.stop_test_server()

    def start_server(self, address='0.0.0.0', port=8000):
        from django.contrib.staticfiles.handlers import StaticFilesHandler
        _application = StaticFilesHandler(WSGIHandler())

        def application(environ, start_response):
            environ['PATH_INFO'] = environ['SCRIPT_NAME'] + environ['PATH_INFO']  # noqa
            return _application(environ, start_response)

        from cherrypy.wsgiserver import CherryPyWSGIServer
        from threading import Thread
        self.httpd = CherryPyWSGIServer(
            (address, port),
            application,
            server_name='django-test-http',
        )
        self.httpd_thread = Thread(target=self.httpd.start)
        self.httpd_thread.start()
        # FIXME: This could be avoided by passing self to thread class starting
        # django and waiting for Event lock
        time.sleep(.5)

    def stop_test_server(self):
        if self.server_started:
            self.httpd.stop()
            self.server_started = False
