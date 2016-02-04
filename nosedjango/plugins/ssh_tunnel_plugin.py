import os
import subprocess
import sys
import signal
from __future__ import print_function

from nosedjango.plugins.base_plugin import Plugin


class SshTunnelPlugin(Plugin):
    name = 'sshtunnel'

    def options(self, parser, env=None):
        if env is None:
            env = os.environ
        parser.add_option(
            '--remote-server',
            help='Use a remote server to run the tests, must pass in the server address',  # noqa
        )
        parser.add_option(
            '--to-from-ports',
            help=(
                'Should be of the form x:y where x is the port that needs to '
                'be forwarded to the server and y is the port that the server '
                'needs forwarded back to the localhost'
            ),
            default='4444:8001',
        )
        parser.add_option(
            '--username',
            help='The username with which to create the ssh tunnel to the remote server',  # noqa
            default=None,
        )
        Plugin.options(self, parser, env)

    def configure(self, options, config):
        # This is only checked since this plugin is configured regardless if
        # the sshtunnel flag is used, and we only want this info here if the
        # --remote-server flag is used
        if options.remote_server:
            try:
                to_port, from_port = options.to_from_ports.split(':', 1)
            except:
                raise RuntimeError("--to_from_ports should be of the form x:y")
            else:
                self._to_port = to_port
                self._from_port = from_port
            self._remote_server = options.remote_server
            self._username = options.username
        Plugin.configure(self, options, config)

    def begin(self):
        # If we are using a remote connection we want to create two tunnels,
        # one to forward from local to server for the port that selenium is
        # listening to, and another from server to local on the port runserver
        # is running on
        if getattr(self, '_remote_server', False):
            params = {
                'username': self._username,
                'host': self._remote_server,
                'to_port': self._to_port,
                'from_port': self._from_port,
            }
            host_str = self._remote_server
            if self._username:
                host_str = '%(username)s@%(host)s' % params,
            self.tunnel_command = [
                'ssh',
                host_str,
                '-L',
                '%(to_port)s:%(host)s:%(to_port)s' % params,
                '-N',
            ]
            self.reverse_tunnel_command = [
                'ssh',
                '-nNT',
                '-R',
                '%(from_port)s:localhost:%(from_port)s' % params,
                host_str,
            ]
            self._tunnel = subprocess.Popen(
                self.tunnel_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self._reverse_tunnel = subprocess.Popen(
                self.reverse_tunnel_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

    def finalize(self, result):
        # Clean up all ssh tunnels
        if not self._tunnel.poll():
            os.kill(self._tunnel.pid, signal.SIGKILL)
            self._tunnel.wait()
        if not self._reverse_tunnel.poll():
            os.kill(self._reverse_tunnel.pid, signal.SIGKILL)
            self._reverse_tunnel.wait()

            print("Error killing ssh tunnel", file=sys.stderr)
