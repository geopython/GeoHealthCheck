from GeoHealthCheck.proberunner import ProbeRunner

class OwsGetCaps(ProbeRunner):
    """Abstract Base Class for OWS GetCapabilities Probes"""

    NAME = 'OWS GetCapabilities'
    DESCRIPTION = 'fetch capabilities'
    RESOURCE_TYPE = 'OGC:*'

    REQUEST_METHOD = 'GET'
    REQUEST_TEMPLATE = '?SERVICE={service}&VERSION={version}&REQUEST=GetCapabilities'
    REQUEST_PARAMETERS = [
        {
            'name': 'service',
            'type': 'string'
        },
        {
            'name': 'version',
            'type': 'string'
        }
    ]

    RESPONSE_CHECKS = [
        {
            'name': 'parse_response',
            'description': 'response is parsable',
            'function': 'GeoHealthCheck.checks.xml_parse'
        },
        {
            'name': 'no OWS Exception',
            'description': 'response does not contain OWS Exception',
            'function': 'GeoHealthCheck.checks.not_contains_exception'
        },
        {
            'name': 'capabilities_title',
            'description': 'find title element in capabilities response doc',
            'function': 'GeoHealthCheck.checks.contains_string',
            'parameters': [
                {
                    'name': 'text',
                    'type': 'string',
                    'value': 'Title>'
                }
            ]
        }
    ]


class WmsGetCaps(OwsGetCaps):
    """WMS GetCapabilities ProbeRunner"""
    
    NAME = 'WMS GetCapabilities'
    RESOURCE_TYPE = 'OGC:WMS'

    REQUEST_PARAMETERS = [
        {
            'name': 'service',
            'type': 'string',
            'value': 'WMS'
        },
        {
            'name': 'version',
            'type': 'string',
            'range': ['1.1.1', '1.3.0']
        }
    ]

class WfsGetCaps(OwsGetCaps):
    """WFS GetCapabilities ProbeRunner"""

    NAME = 'WFS GetCapabilities'
    RESOURCE_TYPE = 'OGC:WFS'

    REQUEST_PARAMETERS = [
        {
            'name': 'service',
            'type': 'string',
            'value': 'WFS'
        },
        {
            'name': 'version',
            'type': 'string',
            'range': ['1.0.0', '1.1.0', '2.0.2']
        }
    ]

class WcsGetCaps(OwsGetCaps):
    """WCS GetCapabilities ProbeRunner"""

    NAME = 'WCS GetCapabilities'
    RESOURCE_TYPE = 'OGC:WCS'

    REQUEST_PARAMETERS = [
        {
            'name': 'service',
            'type': 'string',
            'value': 'WCS'
        },
        {
            'name': 'version',
            'type': 'string',
            'range': ['1.1.0', '1.1.1', '2.0.1']
        }
    ]

class CswGetCaps(OwsGetCaps):
    """CSW GetCapabilities ProbeRunner"""

    NAME = 'WCS GetCapabilities'
    RESOURCE_TYPE = 'OGC:CSW'

    REQUEST_PARAMETERS = [
        {
            'name': 'service',
            'type': 'string',
            'value': 'CSW'
        },
        {
            'name': 'version',
            'type': 'string',
            'range': ['2.0.2']      # only 2.0.2?
        }
    ]

class WmtsGetCaps(OwsGetCaps):
    """WMTS GetCapabilities ProbeRunner"""

    NAME = 'WMTS GetCapabilities'
    RESOURCE_TYPE = 'OGC:WMTS'

    REQUEST_PARAMETERS = [
        {
            'name': 'service',
            'type': 'string',
            'value': 'WMTS'
        },
        {
            'name': 'version',
            'type': 'string',
            'range': ['1.0.0']
        }
    ]

class SosGetCaps(OwsGetCaps):
    """SOS GetCapabilities ProbeRunner"""

    NAME = 'SOS GetCapabilities'
    RESOURCE_TYPE = 'OGC:SOS'

    REQUEST_PARAMETERS = [
        {
            'name': 'service',
            'type': 'string',
            'value': 'SOS'
        },
        {
            'name': 'version',
            'type': 'string',
            'range': ['1.0.0']
        }
    ]

