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

from datetime import datetime
import logging
import json
from urllib.request import urlopen
from urllib.parse import urlparse
from functools import partial
from flask_babel import gettext

from owslib.wms import WebMapService
from owslib.wmts import WebMapTileService
from owslib.tms import TileMapService
from owslib.wfs import WebFeatureService
from owslib.wcs import WebCoverageService
from owslib.wps import WebProcessingService
from owslib.csw import CatalogueServiceWeb
from owslib.sos import SensorObservationService

from init import App
from enums import RESOURCE_TYPES
from models import Resource, Run
from probe import Probe
from result import ResourceResult
from notifications import notify

LOGGER = logging.getLogger(__name__)
APP = App.get_app()
DB = App.get_db()


# commit or rollback shorthand
def db_commit():
    err = None
    try:
        DB.session.commit()
    except Exception as err:
        LOGGER.warning('Cannot commit to database {}'.format(err))
        DB.session.rollback()
    # finally:
    #     DB.session.close()
    return err


def run_resources():
    for resource in Resource.query.all():  # run all tests
        LOGGER.info('Testing %s %s' %
                    (resource.resource_type, resource.url))

        run_resource(resource.identifier)


# complete handle of resource test
def run_resource(resourceid):
    resource = Resource.query.filter_by(identifier=resourceid).first()

    if not resource.active:
        # Exit test of resource if it's not active
        return

    # Get the status of the last run,
    # assume success if there is none
    last_run_success = True
    last_run = resource.last_run
    if last_run:
        last_run_success = last_run.success

    # Run test
    result = run_test_resource(resource)

    run1 = Run(resource, result, datetime.utcnow())

    DB.session.add(run1)

    # commit or rollback each run to avoid long-lived transactions
    # see https://github.com/geopython/GeoHealthCheck/issues/14
    db_commit()

    if APP.config['GHC_NOTIFICATIONS']:
        # Attempt notification
        try:
            notify(APP.config, resource, run1, last_run_success)
        except Exception as err:
            # Don't bail out on failure in order to commit the Run
            msg = str(err)
            logging.warn('error notifying: %s' % msg)
    if not __name__ == '__main__':
        DB.session.remove()


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
    start_time = datetime.utcnow()
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
                         'OGC:WFS3': [urlopen],
                         'OGC:3DTiles': [urlopen],
                         'ESRI:FS': [urlopen],
                         'OGC:STA': [urlopen],
                         'WWW:LINK': [urlopen],
                         'FTP': [urlopen],
                         'GHC:Report': [urlopen],
                         'OSGeo:GeoNode': [geonode_get_ows],
                         'Mapbox:TileJSON': [urlopen]
                         }
    try:
        ows = None
        try:
            ows_handlers = resource_type_map[resource_type]
        except KeyError:
            LOGGER.error("No handler for %s type", resource_type)
            raise
        for ows_handler in ows_handlers:
            try:
                ows = ows_handler(url)
                break
            except Exception as err:
                LOGGER.warning("Cannot use %s on %s: %s",
                               ows_handler, url, err, exc_info=err)
        if ows is None:
            message = ("Cannot get {} service instance "
                       "for {}".format(resource_type, url))
            raise ValueError(message)

        if resource_type == 'WWW:LINK':
            content_type = ows.info().get('Content-Type')

            # When response is not an image try parse out Title and
            # any Exceptions
            if 'image/' not in content_type:
                content = ows.read()
                import re
                try:
                    title_re = re.compile('<title>(.+?)</title>'.encode())
                    title = title_re.search(content).group(1).decode()
                except Exception:
                    title = url

                # Optional check for any OGC-Exceptions in Response
                if config and config['GHC_WWW_LINK_EXCEPTION_CHECK']:
                    exception_text = None
                    try:
                        except_re = re.compile(
                            'ServiceException>|ExceptionReport>'.encode())
                        exception_text = except_re.search(content).\
                            group(0).decode()
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
            end_time = datetime.utcnow()
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

        elif resource_type.startswith(('OGC:', 'OSGeo', 'ESRI')):
            if resource_type == 'OGC:STA':
                title = 'OGC STA'
            elif resource_type == 'OGC:WFS3':
                title = 'OGC API Features (OAFeat)'
            elif resource_type == 'ESRI:FS':
                title = 'ESRI ArcGIS FS'
            elif resource_type == 'OGC:3DTiles':
                title = 'OGC 3D Tiles'
            else:
                title = ows.identification.title
        if title is None:
            title = '%s %s %s' % (resource_type, gettext('for'), url)
        success = True
    except Exception as err:
        title = 'Untitled'
        msg = 'Getting metadata failed: %s' % str(err)
        LOGGER.error(msg, exc_info=err)
        message = msg
        success = False

    end_time = datetime.utcnow()

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


GEONODE_OWS_API = '/api/ows_endpoints/'


def geonode_get_ows(base_url):
    r = urlopen('{}{}'.format(base_url.rstrip('/'), GEONODE_OWS_API))
    url = urlparse(base_url)
    base_name = 'GeoNode {}: {{}}'.format(url.hostname)
    status_code = r.getcode()
    if status_code != 200:
        msg = "Error response from GeoNode at {}: {}".format(
                                                    base_url, r.text)
        raise ValueError(msg)

    try:
        data = json.load(r)
    except (TypeError, ValueError,) as err:
        msg = "Cannot decode response from GeoNode at {}: {}".format(base_url,
                                                                     err)
        raise ValueError(msg)

    def update(val):
        val['title'] = base_name.format(val['type'])
        return val

    return [update(d) for d in data['data']]


def geonode_make_tags(base_url):
    url = urlparse(base_url)
    tag_name = 'GeoNode: {}'.format(url.hostname)
    return [tag_name]


if __name__ == '__main__':
    print('START - Running health check tests on %s'
          % datetime.utcnow().isoformat())
    run_resources()
    print('END - Running health check tests on %s'
          % datetime.utcnow().isoformat())
    # from init import App
    # if len(sys.argv) < 3:
    #     print('Usage: %s <resource_type> <url>' % sys.argv[0])
    #     sys.exit(1)
    #
    # # TODO: need APP.config here, None for now
    # pprint(sniff_test_resource(App.get_config(), sys.argv[1], sys.argv[2]))
