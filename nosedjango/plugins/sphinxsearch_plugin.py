from __future__ import with_statement
from __future__ import print_function

import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time

from nosedjango.plugins.base_plugin import Plugin


class SphinxSearchPlugin(Plugin):
    """
    Plugin for configuring and running a sphinx search process for djangosphinx
    that's hooked up to a django test database.
    """
    name = 'django-sphinxsearch'
    searchd_port = 45798

    def __init__(self, *args, **kwargs):
        super(SphinxSearchPlugin, self).__init__(*args, **kwargs)

        self.tmp_sphinx_dir = None
        self.sphinx_config_tpl = None
        self._searchd = None

    def options(self, parser, env=None):
        """
        Sphinx config file that can optionally take the following python
        template string arguments:

        ``database_name``
        ``database_password``
        ``database_username``
        ``database_host``
        ``database_port``
        ``sphinx_search_data_dir``
        ``searchd_log_dir``
        """
        if env is None:
            env = os.environ
        parser.add_option(
            '--sphinx-config-tpl',
            help='Path to the Sphinx configuration file template.',
        )

        super(SphinxSearchPlugin, self).options(parser, env)

    def configure(self, options, config):
        if options.sphinx_config_tpl:
            self.sphinx_config_tpl = os.path.abspath(options.sphinx_config_tpl)

            # Create a directory for storing the configs, logs and index files
            self.tmp_sphinx_dir = tempfile.mkdtemp()

        super(SphinxSearchPlugin, self).configure(options, config)

    def startTest(self, test):
        from django.conf import settings
        from django.db import connection
        if 'django.db.backends.mysql' in connection.settings_dict['ENGINE']:
            # Using startTest instead of beforeTest so that we can be sure that
            # the fixtures were already loaded with nosedjango's beforeTest
            build_sphinx_index = getattr(test, 'build_sphinx_index', False)
            run_sphinx_searchd = getattr(test, 'run_sphinx_searchd', False)

            if run_sphinx_searchd:
                # Need to build the config

                # Update the DjangoSphinx client to use the proper port and
                # index
                settings.SPHINX_PORT = self.searchd_port
                from djangosphinx import models as dj_sphinx_models
                dj_sphinx_models.SPHINX_PORT = self.searchd_port

                # Generate the sphinx configuration file from the template
                sphinx_config_path = os.path.join(
                    self.tmp_sphinx_dir,
                    'sphinx.conf',
                )

                db_dict = connection.settings_dict
                with open(self.sphinx_config_tpl, 'r') as tpl_f:
                    context = {
                        'database_name': db_dict['NAME'],
                        'database_username': db_dict['USER'],
                        'database_password': db_dict['PASSWORD'],
                        'database_host': db_dict['HOST'],
                        'database_port': db_dict['PORT'],
                        'sphinx_search_data_dir': self.tmp_sphinx_dir,
                        'searchd_log_dir': self.tmp_sphinx_dir,
                    }
                    tpl = tpl_f.read()
                    output = tpl % context

                    with open(sphinx_config_path, 'w') as sphinx_conf_f:
                        sphinx_conf_f.write(output)
                        sphinx_conf_f.flush()

            if build_sphinx_index:
                self._build_sphinx_index(sphinx_config_path)
            if run_sphinx_searchd:
                self._start_searchd(sphinx_config_path)

    def afterTest(self, test):
        from django.db import connection
        if 'django.db.backends.mysql' in connection.settings_dict['ENGINE']:
            if getattr(test.context, 'run_sphinx_searchd', False):
                self._stop_searchd()

    def finalize(self, test):
        # Delete the temporary sphinx directory
        shutil.rmtree(self.tmp_sphinx_dir, ignore_errors=True)

    def _build_sphinx_index(self, config):
        indexer = subprocess.Popen(
            [
                'indexer',
                '--config',
                config,
                '--all',
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if indexer.wait() != 0:
            print("Sphinx Indexing Problem")
            stdout, stderr = indexer.communicate()
            print("stdout: %s" % stdout)
            print("stderr: %s" % stderr)

    def _start_searchd(self, config):
        self._searchd = subprocess.Popen(
            ['searchd', '--config', config, '--console',
             '--port', str(self.searchd_port)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        returned = self._searchd.poll()
        if returned is not None:
            print("Sphinx Search unavailable. searchd exited with code: %s" % returned)  # noqa
            stdout, stderr = self._searchd.communicate()
            print("stdout: %s" % stdout)
            print("stderr: %s" % stderr)

        self._wait_for_connection(self.searchd_port)

    def _wait_for_connection(self, port):
        """
        Wait until we can make a socket connection to sphinx.
        """
        connected = False
        max_tries = 10
        num_tries = 0
        wait_time = 0.5
        while not connected or num_tries >= max_tries:
            time.sleep(wait_time)
            try:
                af = socket.AF_INET
                addr = ('127.0.0.1', port)
                sock = socket.socket(af, socket.SOCK_STREAM)
                sock.connect(addr)
            except socket.error:
                if sock:
                    sock.close()
                num_tries += 1
                continue
            connected = True

        if not connected:
            print("Error connecting to sphinx searchd", file=sys.stderr)

    def _stop_searchd(self):
        try:
            if not self._searchd.poll():
                os.kill(self._searchd.pid, signal.SIGKILL)
                self._searchd.wait()
        except AttributeError:
            print("Error stopping sphinx search daemon", file=sys.stderr)
