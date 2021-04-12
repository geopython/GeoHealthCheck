# =================================================================
#
# Authors: Rob van Loon <borrob@me.com>
#
# Copyright (c) 2021 Rob van Loon
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# =================================================================

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
