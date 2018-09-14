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

RESOURCE_TYPES = {
    'OGC:WMS': {
        'label': 'Web Map Service (WMS)',
        'versions': ['1.3.0'],
        'capabilities': 'service=WMS&version=1.3.0&request=GetCapabilities'
    },
    'OGC:WMTS': {
        'label': 'Web Map Tile Service (WMTS)',
        'versions': ['1.0.0'],
        'capabilities': 'service=WMTS&version=1.0.0&request=GetCapabilities'
    },
    'OSGeo:TMS': {
        'label': 'Tile Map Service (TMS)',
        'versions': ['1.0.0'],
    },
    'OGC:WFS': {
        'label': 'Web Feature Service (WFS)',
        'versions': ['1.1.0'],
        'capabilities': 'service=WFS&version=1.1.0&request=GetCapabilities'
    },
    'OGC:WCS': {
        'label': 'Web Coverage Service (WCS)',
        'versions': ['1.1.0'],
        'capabilities': 'service=WCS&version=1.1.0&request=GetCapabilities'
    },
    'OGC:WPS': {
        'label': 'Web Processing Service (WPS)',
        'versions': ['1.0.0'],
        'capabilities': 'service=WPS&version=1.0.0&request=GetCapabilities'
    },
    'OGC:CSW': {
        'label': 'Catalogue Service (CSW)',
        'versions': ['2.0.2'],
        'capabilities': 'service=CSW&version=2.0.2&request=GetCapabilities'
    },
    'OGC:SOS': {
        'label': 'Sensor Observation Service (SOS)',
        'versions': ['1.0.0'],
        'capabilities': 'service=SOS&version=1.0.0&request=GetCapabilities'
    },
    'OGC:STA': {
        'label': 'SensorThings API (STA)',
        'versions': ['1.0']
    },
    'urn:geoss:waf': {
        'label': 'Web Accessible Folder (WAF)'
    },
    'WWW:LINK': {
        'label': 'Web Address (URL)'
    },
    'FTP': {
        'label': 'File Transfer Protocol (FTP)'
    },
    'OSGeo:GeoNode': {
        'label': 'GeoNode instance'
    }
}
