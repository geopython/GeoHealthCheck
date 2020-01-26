from plugin import Plugin
import logging


LOGGER = logging.getLogger(__name__)


class Geocoder(Plugin):
    """
    Base class for specifiv Geocode plugin to locate servers by their hostname
    """

    def __init__(self):
        Plugin.__init__(self)

    def init(self, geocoder_vars):
        self._geocoder_vars = geocoder_vars

    def locate(self, host):
        """
        Perform a locate on the host.

        TOOD: return result tuple like (52.4, 21.0)
        """
        pass

    def log(self, text):
        LOGGER.info(text)

