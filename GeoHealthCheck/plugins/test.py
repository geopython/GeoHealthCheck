from GeoHealthCheck.probe import Probe
from GeoHealthCheck.models import *

## NB this test doesn't work anymore, see HOME/tests for "real" unit tests!

"""Test for Probe plugins
Run python GeoHealthCheck/plugins/test.py from root GitHub dir.
"""

def healthcheck(requests):
    for request in requests:
        result = Probe.run(request)

if __name__ == '__main__':
    """ Some data, should come from Models later"""

    resource1 = {
        'url': 'https://geodata.nationaalgeoregister.nl/bag/wms?',
        'resource_type': 'OWS:WMS'
    }

    checks1 = [
        {
            'function': 'GeoHealthCheck.checks.xml_parse',
            'parameters': {}
        },
        {
            'function': 'GeoHealthCheck.checks.not_contains_exception',
            'parameters': {}
        },
        {
            'function': 'GeoHealthCheck.checks.contains_string',
            'parameters': {
                'text': 'Title'
            }
        }
    ]


    request1 = {
        'resource': resource1,
        'request_identifier': 'GeoHealthCheck.plugins.owsgetcaps.WmsGetCaps',
        'parameters': {
            'service': 'WMS',
            'version': '1.0.0'
        },
        'checks': checks1
    }

    ###########
    resource2 = {
        'url': 'https://geodata.nationaalgeoregister.nl/bag/wfs?',
        'resource_type': 'OWS:WFS'
    }

    checks21 = [
        {
            'function': 'GeoHealthCheck.checks.xml_parse',
            'parameters': {}
        },
        {
            'function': 'GeoHealthCheck.checks.contains_string',
            'parameters': {
                'text': 'Title'
            }
        }
    ]
    checks22 = [
        {
            'function': 'GeoHealthCheck.checks.xml_parse',
            'parameters': {}
        },
        {
            'function': 'GeoHealthCheck.checks.not_contains_exception',
            'parameters': {}
        },
        {
            'function': 'GeoHealthCheck.checks.contains_string',
            'parameters': {
                'text': 'FeatureCollection>'
            }
        }
    ]

    request21 = {
        'resource': resource2,
        'request_identifier': 'GeoHealthCheck.plugins.owsgetcaps.WfsGetCaps',
        'parameters': {
            'service': 'WFS',
            'version': '1.1.0'
        },
        'checks': checks21
    }

    request22 = {
        'resource': resource2,
        'request_identifier': 'GeoHealthCheck.plugins.wfsgetfeature.WfsGetFeatBbox',
        'parameters': {

            'typename': 'verblijfsobject:verblijfsobject',

            'typename_ns': 'verblijfsobject',

            'typename_ns_url': 'http://bag.geonovum.nl',

            'geom_property_name': 'geometrie',

            'srs': 'EPSG:28992',

            'lower_x': '180635',

            'lower_y': '455870',

            'upper_x': '180961',

            'upper_y': '456050'

        },
        'checks': checks22
    }

    requests = [request1, request21, request22]

    healthcheck(requests)
