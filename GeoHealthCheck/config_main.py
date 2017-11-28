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

DEBUG = False
SQLALCHEMY_ECHO = False
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_DATABASE_URI = 'sqlite:///data.db'
# Alternative configuration for PostgreSQL database
# SQLALCHEMY_DATABASE_URI = 'postgresql://user:password@host:port/database'

# Replace None with 'your secret key string' in quotes
SECRET_KEY = None

# days, seconds, microseconds, milliseconds, minutes, hours, weeks
GHC_RETENTION_DAYS = (30, 0, 0, 0, 0, 0, 0) 
GHC_RUN_FREQUENCY = 'hourly'
GHC_SELF_REGISTER = False
GHC_NOTIFICATIONS = False
GHC_NOTIFICATIONS_VERBOSITY = True
GHC_WWW_LINK_EXCEPTION_CHECK = False
GHC_ADMIN_EMAIL = 'you@example.com'
GHC_NOTIFICATIONS_EMAIL = ['you2@example.com']
GHC_SITE_TITLE = 'GeoHealthCheck Demonstration'
GHC_SITE_URL = 'http://host'

# Some GetCaps docs are huge. This allows
# caching them for N seconds. Set to -1 to
# disable caching.
GHC_METADATA_CACHE_SECS = 900

GHC_SMTP = {
    'server': None,
    'port': None,
    'tls': False,
    'ssl': False,
    'username': None,
    'password': None
}

GHC_RELIABILITY_MATRIX = {
    'red': {
        'min': 0,
        'max': 49
    },
    'orange': {
        'min': 50,
        'max': 79
    },
    'green': {
        'min': 80,
        'max': 100
    }
}

GHC_MAP = {
    'url': 'http://tile.osm.org/{z}/{x}/{y}.png',
    'centre_lat': 42.3626,
    'centre_long': -71.0843,
    'maxzoom': 18,
    'subdomains': 1234,
}

# GHC Core Plugins
# Each GHC Plugin should derive from GeoHealthCheck.plugin.Plugin,
# and should be findable in sys/PYTHONPATH.
# An entry may be a Python classname or module.
# The latter will include all classes derived from GeoHealthCheck.plugin.Plugin
# in the module file.
GHC_PLUGINS = [
    # Probes
    'GeoHealthCheck.plugins.probe.owsgetcaps',
    'GeoHealthCheck.plugins.probe.wms',
    'GeoHealthCheck.plugins.probe.wfs',
    'GeoHealthCheck.plugins.probe.tms',
    'GeoHealthCheck.plugins.probe.http',
    'GeoHealthCheck.plugins.probe.sta',
    'GeoHealthCheck.plugins.probe.wmsdrilldown',

    # Checkers
    'GeoHealthCheck.plugins.check.checks',
]

# Entry for User Plugins: will be added to default core GHC_PLUGINS
# This makes it easier for users to just configure their Plugins
# and always get the latest core GHC_PLUGINS without having to upgrade
# their config.
GHC_USER_PLUGINS = []

# Default Probe to assign on "add" per Resource-type
GHC_PROBE_DEFAULTS = {
    'OGC:WMS': {
        'probe_class': 'GeoHealthCheck.plugins.probe.owsgetcaps.WmsGetCaps'
    },
    'OGC:WMTS': {
        'probe_class': 'GeoHealthCheck.plugins.probe.owsgetcaps.WmtsGetCaps'
    },
    'OSGeo:TMS': {
        'probe_class': 'GeoHealthCheck.plugins.probe.tms.TmsCaps'
    },
    'OGC:WFS': {
        'probe_class': 'GeoHealthCheck.plugins.probe.owsgetcaps.WfsGetCaps'
    },
    'OGC:WCS': {
        'probe_class': 'GeoHealthCheck.plugins.probe.owsgetcaps.WcsGetCaps'
    },
    'OGC:WPS': {
        'probe_class': 'GeoHealthCheck.plugins.probe.owsgetcaps.WpsGetCaps'
    },
    'OGC:CSW': {
        'probe_class': 'GeoHealthCheck.plugins.probe.owsgetcaps.CswGetCaps'
    },
    'OGC:SOS': {
        'probe_class': 'GeoHealthCheck.plugins.probe.owsgetcaps.SosGetCaps'
    },
    'OGC:STA': {
        'probe_class': 'GeoHealthCheck.plugins.probe.sta.StaCaps'
    },
    'urn:geoss:waf': {
        'probe_class': 'GeoHealthCheck.plugins.probe.http.HttpGet'
    },
    'WWW:LINK': {
        'probe_class': 'GeoHealthCheck.plugins.probe.http.HttpGet'
    },
    'FTP': {
        'probe_class': None
    }
}
