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
from functools import partial

from owslib.wms import WebMapService
from owslib.wmts import WebMapTileService
from owslib.tms import TileMapService
from owslib.wfs import WebFeatureService
from owslib.wcs import WebCoverageService
from owslib.wps import WebProcessingService
from owslib.csw import CatalogueServiceWeb
from owslib.sos import SensorObservationService

from flask_babel import gettext
from enums import RESOURCE_TYPES
from probe import Probe
from result import ResourceResult
from plugins.probe.geonode import (get_ows_endpoints as geonode_get_ows,
                                   make_default_tags as geonode_make_tags,
                                   )

LOGGER = logging.getLogger(__name__)


def run_test_resource(resource):
    """tests a service and provides run metrics"""

    result = ResourceResult(resource)
    if not resource.active:
        result.message = 'Skipped'
        return result
    result.start()
    probes = resource.probe_vars
    for probe in probes:
        result.add_result(Probe.run(resource, probe))

    result.stop()

    return result


def sniff_test_resource(config, resource_type, url):
    """tests a Resource endpoint for general compliance"""

    out = []
    tag_list = []
    if resource_type not in RESOURCE_TYPES.keys():
        msg = gettext('Invalid resource type')
        msg2 = '%s: %s' % (msg, resource_type)
        LOGGER.error(msg2)
        raise RuntimeError(msg2)

    title = None
    start_time = datetime.datetime.utcnow()
    message = None
    resource_type_map = {'OGC:WMS': [partial(WebMapService, version='1.3.0'),
                                     partial(WebMapService, version='1.1.1')],
                         'OGC:WMTS': [WebMapTileService],
                         'OSGeo:TMS': [TileMapService],
                         'OGC:WFS': [WebFeatureService],
                         'OGC:WCS': [WebCoverageService],
                         'OGC:WPS': [WebProcessingService],
                         'OGC:CSW': [CatalogueServiceWeb],
                         'OGC:SOS': [SensorObservationService],
                         'OGC:STA': [urlopen],
                         'WWW:LINK': [urlopen],
                         'FTP': [urlopen],
                         'OSGeo:GeoNode': [geonode_get_ows],
                         }
    try:
        ows = None
        try:
            ows_handlers = resource_type_map[resource_type]
        except KeyError:
            LOGGER.error("No hanlder for %s type", resource_type)
            raise
        for ows_handler in ows_handlers:
            try:
                ows = ows_handler(url)
                break
            except Exception, err:
                LOGGER.warning("Cannot use %s on %s: %s",
                               ows_handler, url, err, exc_info=err)
        if ows is None:
            msg = "Cannot get {} service instance for {}".format(resource_type,
                                                                 url)
            raise ValueError(msg)

        if resource_type == 'WWW:LINK':
            content_type = ows.info().getheader('Content-Type')

            # Check content if the response is not an image
            if 'image/' not in content_type:
                content = ows.read()
                import re
                try:
                    title_re = re.compile("<title>(.+?)</title>")
                    title = title_re.search(content).group(1)
                except Exception:
                    title = url

                # Optional check for any OGC-Exceptions in Response
                if config and config['GHC_WWW_LINK_EXCEPTION_CHECK']:
                    exception_text = None
                    try:
                        except_re = re.compile(
                            "ServiceException>|ExceptionReport>")
                        exception_text = except_re.search(content).group(0)
                    except Exception:
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
            title = urlparse(url).hostname
        elif resource_type == 'OSGeo:GeoNode':
            endpoints = ows
            end_time = datetime.datetime.utcnow()
            delta = end_time - start_time
            response_time = '%s.%s' % (delta.seconds, delta.microseconds)
            base_tags = geonode_make_tags(url)

            for epoint in endpoints:
                row = sniff_test_resource(config,
                                          epoint['type'],
                                          epoint['url'])
                if row:
                    _tags = row[0][-1]
                    _tags.extend(base_tags)
                    row[0][-1] = _tags
                    out.append(row[0])

        success = True
        if resource_type.startswith(('OGC:', 'OSGeo')):
            if resource_type == 'OGC:STA':
                title = 'OGC STA'
            else:
                title = ows.identification.title
        if title is None:
            title = '%s %s %s' % (resource_type, gettext('for'), url)

        title = title.decode('utf-8')
    except Exception as err:
        title = 'Untitled'
        msg = 'Getting metadata failed: %s' % str(err)
        LOGGER.error(msg, exc_info=err)
        message = msg
        success = False

    end_time = datetime.datetime.utcnow()

    delta = end_time - start_time
    response_time = '%s.%s' % (delta.seconds, delta.microseconds)
    # if out is not populated yet, that means it should be populated now
    if not out:
        out.append([resource_type,
                    url,
                    title,
                    success,
                    response_time,
                    message,
                    start_time,
                    tag_list])
    return out


if __name__ == '__main__':
    import sys
    from init import App
    if len(sys.argv) < 3:
        print('Usage: %s <resource_type> <url>' % sys.argv[0])
        sys.exit(1)

    # TODO: need APP.config here, None for now
    print(sniff_test_resource(App.get_config(), sys.argv[1], sys.argv[2]))
