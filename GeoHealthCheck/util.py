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

import io
import json
import logging
import os
import smtplib
from urllib2 import urlopen
from urlparse import urlparse
from gettext import translation

from jinja2 import Environment, FileSystemLoader

LOGGER = logging.getLogger(__name__)


def average(values):
    """calculates average from a list"""

    try:
        return float(sum(values) / len(values))
    except ZeroDivisionError:
        return 0


def percentage(number, total):
    """calculates a percentage"""

    if total == 0:  # no resources registered yet
        return 0.00

    percentage_value = float((float(float(number) / float(total))) * 100.0)
    if percentage_value in [0.0, 100.0]:
        return int(percentage_value)
    return percentage_value


def get_python_snippet(resource):
    """return sample interactive session"""

    lines = []
    if resource.resource_type.startswith('OGC:'):
        lines.append('# testing via OWSLib')
        lines.append('# test GetCapabilities')
    else:
        lines.append('# testing via urllib2 and urlparse')

    if resource.resource_type == 'OGC:WMS':
        lines.append('from owslib.wms import WebMapService')
        lines.append('myows = WebMapService(\'%s\')' % resource.url)
    elif resource.resource_type == 'OGC:WMTS':
        lines.append('from owslib.wmts import WebMapTileService')
        lines.append('myows = WebMapTileService(\'%s\')' % resource.url)
    elif resource.resource_type == 'OSGeo:TMS':
        lines.append('from owslib.tms import TileMapService')
        lines.append('myows = WebMapTileService(\'%s\')' % resource.url)
    elif resource.resource_type == 'OGC:CSW':
        lines.append('from owslib.csw import CatalogueServiceWeb')
        lines.append('myows = CatalogueServiceWeb(\'%s\')' % resource.url)
    elif resource.resource_type == 'OGC:WFS':
        lines.append('from owslib.wfs import WebFeatureService')
        lines.append('myows = WebFeatureService(\'%s\')' % resource.url)
    elif resource.resource_type == 'OGC:WPS':
        lines.append('from owslib.wfs import WebProcessingService')
        lines.append('myows = WebFeatureService(\'%s\')' % resource.url)
    elif resource.resource_type == 'OGC:SOS':
        lines.append('from owslib.wfs import SensorObservationService')
        lines.append('myows = SensorObservationService(\'%s\')' % resource.url)
    elif resource.resource_type == 'WWW:LINK':
        lines.append('import re')
        lines.append('from urllib2 import urlopen')
        lines.append('ows = urlopen(\'%s\')' % resource.url)
        lines.append('try:')
        lines.append('    title_re = re.compile("<title>(.+?)</title>")')
        lines.append('    title = title_re.search(ows.read()).group(1)')
    elif resource.resource_type == 'urn:geoss:waf':
        lines.append('from urllib2 import urlopen')
        lines.append('from urlparse import urlparse')
        lines.append('ows = urlopen(\'%s\')' % resource.url)
        lines.append('title = urlparse(url).hostname')
    elif resource.resource_type == 'FTP':
        lines.append('from urllib2 import urlopen')
        lines.append('from urlparse import urlparse')
        lines.append('ows = urlopen(\'%s\')' % resource.url)
        lines.append('title = urlparse(url).hostname')

    if resource.resource_type.startswith('OGC:'):
        lines.append('myows.identification.title\n\'%s\'' % resource.title)
    else:
        lines.append('title\n\'%s\'' % resource.title)
    return '\n>>> '.join(lines)


def render_template2(template, template_vars):
    """convenience function to render template in a non-Flask context"""

    loader_dir = os.path.join(os.path.dirname(__file__), 'templates')
    loader = FileSystemLoader(loader_dir)

    env = Environment(loader=loader, extensions=['jinja2.ext.i18n'])
    translations_dir = os.path.join(os.path.dirname(__file__), 'translations')
    translations = translation('messages', translations_dir, fallback=True)
    env.install_gettext_translations(translations)
    template_obj = env.get_template(template)

    return template_obj.render(template_vars)


def send_email(mail_config, fromaddr, toaddr, msg):
    """convenience function to send an email"""

    LOGGER.debug(mail_config)
    LOGGER.debug(msg)
    server = smtplib.SMTP('%s:%s' % (mail_config['server'],
                                     mail_config['port']))

    if mail_config['tls']:
        server.starttls()
        server.login(mail_config['username'],
                     mail_config['password'])
    server.sendmail(fromaddr, toaddr, msg)
    server.quit()

    return True


def geocode(value, spatial_keyword_type='hostname'):
    """convenience function to geocode a value"""
    lat, lon = 0.0, 0.0
    if spatial_keyword_type == 'hostname':
        try:
            hostname = urlparse(value).hostname
            url = 'http://ip-api.com/json/%s' % hostname
            LOGGER.info('Geocoding %s with %s', hostname, url)
            content = json.loads(urlopen(url).read())
            lat, lon = content['lat'], content['lon']
        except Exception as err:  # skip storage
            msg = 'Could not derive coordinates: %s' % err
            LOGGER.exception(msg)
    return lat, lon


def transform_bbox(epsg1, epsg2, bbox):
    """
    convenience function to transform a bbox array
    """

    import pyproj

    p1 = pyproj.Proj(init=epsg1)
    p2 = pyproj.Proj(init=epsg2)
    ll = pyproj.transform(p1, p2, bbox[0], bbox[1])
    ul = pyproj.transform(p1, p2, bbox[2], bbox[3])

    return list(ll) + list(ul)


def read(filename, encoding='utf-8'):
    """read file contents"""
    full_path = os.path.join(os.path.dirname(__file__), filename)
    with io.open(full_path, encoding=encoding) as fh:
        contents = fh.read().strip()
    return contents
