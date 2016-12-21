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
SQLALCHEMY_DATABASE_URI = 'sqlite:///data.db'

# Replace None with 'your secret key string' in quotes
SECRET_KEY = None

GHC_RETENTION_DAYS = 30
GHC_RUN_FREQUENCY = 'hourly'
GHC_SELF_REGISTER = False
GHC_NOTIFICATIONS = False
GHC_NOTIFICATIONS_VERBOSITY = True
GHC_ADMIN_EMAIL = 'you@example.com'
GHC_SITE_TITLE = 'GeoHealthCheck Demonstration'
GHC_SITE_URL = 'http://host'

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
