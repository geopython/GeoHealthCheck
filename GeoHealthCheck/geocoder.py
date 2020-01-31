from plugin import Plugin
import logging


LOGGER = logging.getLogger(__name__)


class Geocoder(Plugin):
    """
    Base class for specific Geocode plugins to locate servers by their hostname
    """

    def __init__(self):
        super().__init__()

    def init(self, geocoder_vars):
        self._geocoder_vars = geocoder_vars

    def locate(self, hostname):
        """
        Perform a locate on the host.

        :param hostname string: the hostname of the server for which we want
                                the coords.

        TOOD: return result as tuple with locatin in lat-lon like: (52.4, 21.0)
        """
        pass

    def log(self, text):
        LOGGER.info(text)
