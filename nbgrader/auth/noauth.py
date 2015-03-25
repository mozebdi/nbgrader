"""No authentication authenticator."""
import socket
import os
import subprocess as sp
import time
from IPython.utils.traitlets import Bool, Integer

from .base import BaseAuth


def random_port():
    """Get a single random port"""
    sock = socket.socket()
    sock.bind(('', 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


class NoAuth(BaseAuth):
    """Pass through authenticator."""

    start_nbserver = Bool(True, config=True, help=""""Start a single notebook
        server that allows submissions to be viewed.""")
    nbserver_port = Integer(config=True, help="Port for the notebook server")

    def _nbserver_port_default(self):
        return random_port()

    def __init__(self, *args, **kwargs):
        super(NoAuth, self).__init__(*args, **kwargs)

        # first launch a notebook server
        if self.start_nbserver:
            self._notebook_server_ip = self._ip
            self._notebook_server_port = str(self.nbserver_port)
            self._notebook_server = sp.Popen(
                [
                    "python", os.path.join(os.path.dirname(__file__), "..", "apps", "notebookapp.py"),
                    "--ip", self._notebook_server_ip,
                    "--port", self._notebook_server_port
                ],
                cwd=self._base_directory)
            self._notebook_server_exists = True
        else:
            self._notebook_server_exists = False

    def notebook_server_exists(self):
        """Does the notebook server exist?"""
        return self._notebook_server_exists

    def get_notebook_url(self, relative_path):
        """Gets the notebook's url."""
        return "http://{}:{}/notebooks/{}".format(
            self._notebook_server_ip,
            self._notebook_server_port,
            relative_path)

    def stop(self, sig):
        """Stops the notebook server."""
        if self.notebook_server_exists():
            self._notebook_server.send_signal(sig)
            for i in range(10):
                retcode = self._notebook_server.poll()
                if retcode is not None:
                    self._notebook_server_exists = False
                    break
                time.sleep(0.1)

            if retcode is None:
                self.log.critical("couldn't shutdown notebook server, force killing it")
                self._notebook_server.kill()
