# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2014 Tom Kralidis
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

import datetime
import logging
from urllib2 import urlopen
from urlparse import urlparse

from owslib.wms import WebMapService
from owslib.wmts import WebMapTileService
from owslib.tms import TileMapService
from owslib.wfs import WebFeatureService
from owslib.wcs import WebCoverageService
from owslib.wps import WebProcessingService
from owslib.csw import CatalogueServiceWeb
from owslib.sos import SensorObservationService

from flask.ext.babel import gettext
from enums import RESOURCE_TYPES
from probe import Probe
from result import ResourceResult

LOGGER = logging.getLogger(__name__)


def run_test_resource(resource):
    """tests a service and provides run metrics"""

    result = ResourceResult(resource)
    result.start()
    probes = resource.probe_vars
    for probe in probes:
        result.add_result(Probe.run(resource, probe))

    result.stop()

    return result


def sniff_test_resource(config, resource_type, url):
    """tests a service and provides run metrics"""

    if resource_type not in RESOURCE_TYPES.keys():
        msg = gettext('Invalid resource type')
        msg2 = '%s: %s' % (msg, resource_type)
        LOGGER.error(msg2)
        raise RuntimeError(msg2)

    title = None
    start_time = datetime.datetime.utcnow()
    message = None

    try:
        if resource_type == 'OGC:WMS':
            ows = WebMapService(url)
        elif resource_type == 'OGC:WMTS':
            ows = WebMapTileService(url)
        elif resource_type == 'OSGeo:TMS':
            ows = TileMapService(url)
        elif resource_type == 'OGC:WFS':
            ows = WebFeatureService(url)
        elif resource_type == 'OGC:WCS':
            ows = WebCoverageService(url, version='1.0.0')
        elif resource_type == 'OGC:WPS':
            ows = WebProcessingService(url)
        elif resource_type == 'OGC:CSW':
            ows = CatalogueServiceWeb(url)
        elif resource_type == 'OGC:SOS':
            ows = SensorObservationService(url)
        elif resource_type == 'OGC:STA':
            ows = urlopen(url)
        elif resource_type in ['WWW:LINK', 'urn:geoss:waf']:
            ows = urlopen(url)
            if resource_type == 'WWW:LINK':
                content_type = ows.info().getheader('Content-Type')

                # Check content if the response is not an image
                if 'image/' not in content_type:
                    content = ows.read()
                    import re
                    try:
                        title_re = re.compile("<title>(.+?)</title>")
                        title = title_re.search(content).group(1)
                    except:
                        title = url

                    # Optional check for any OGC-Exceptions in Response
                    if config and config['GHC_WWW_LINK_EXCEPTION_CHECK']:
                        exception_text = None
                        try:
                            except_re = re.compile(
                                "ServiceException>|ExceptionReport>")
                            exception_text = except_re.search(content).group(0)
                        except:
                            # No Exception in Response text
                            pass

                        if exception_text:
                            # Found OGC-Exception in Response text
                            raise Exception(
                                "Exception in response: %s" % exception_text)

                    del content

            elif resource_type == 'urn:geoss:waf':
                title = 'WAF %s %s' % (gettext('for'), urlparse(url).hostname)
        elif resource_type == 'FTP':
            ows = urlopen(url)
            title = urlparse(url).hostname
        success = True
        if resource_type.startswith(('OGC:', 'OSGeo')):
            if resource_type == 'OGC:STA':
                title = 'OGC STA'
            else:
                title = ows.identification.title
        if title is None:
            title = '%s %s %s' % (resource_type, gettext('for'), url)
    except Exception as err:
        msg = str(err)
        LOGGER.exception(msg)
        message = msg
        success = False

    end_time = datetime.datetime.utcnow()

    delta = end_time - start_time
    response_time = '%s.%s' % (delta.seconds, delta.microseconds)

    return [title, success, response_time, message, start_time]


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print('Usage: %s <resource_type> <url>' % sys.argv[0])
        sys.exit(1)

    # TODO: need APP.config here, None for now
    print(sniff_test_resource(None, sys.argv[1], sys.argv[2]))
