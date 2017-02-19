from GeoHealthCheck.proberunner import ProbeRunner
from GeoHealthCheck.plugin import Parameter

class OwsGetCaps(ProbeRunner):
    """Abstract Base Class for OWS GetCapabilities Probes"""

    NAME = 'OWS GetCapabilities'
    DESCRIPTION = 'fetch capabilities'
    RESOURCE_TYPE = 'OGC:*'

    REQUEST_METHOD = 'GET'
    REQUEST_TEMPLATE = '?SERVICE={service}&VERSION={version}&REQUEST=GetCapabilities'

    @Parameter(ptype=str, default=None, required=True)
    def service(self):
        """
        The OWS service within resource endpoint.
        Required: True
        Default: None
        """
        pass

    @Parameter(ptype=str, default=None, required=True)
    def version(self):
        """
        The OWS service version within resource endpoint.
        Required: True
        Default: None
        """
        pass

    RESPONSE_CHECKS = [
        {
            'name': 'parse_response',
            'description': 'response is parsable',
            'class': 'GeoHealthCheck.plugins.check.checkers.XmlParse'
        },
        {
            'name': 'no OWS Exception',
            'description': 'response does not contain OWS Exception',
            'class': 'GeoHealthCheck.plugins.check.checkers.NotContainsOwsException'
        },
        {
            'name': 'capabilities_title',
            'description': 'find title element in capabilities response doc',
            'class': 'GeoHealthCheck.plugins.check.checkers.ContainsStrings',
            'parameters': [
                {
                    'name': 'strings',
                    'value': ['Title>']
                }
            ]
        }
    ]


class WmsGetCaps(OwsGetCaps):
    """WMS GetCapabilities ProbeRunner"""
    
    NAME = 'WMS GetCapabilities'
    RESOURCE_TYPE = 'OGC:WMS'

    @Parameter(ptype=str, value='WMS')
    def service(self):
        """
        The OWS service within resource endpoint.
        Required: True
        Default: None
        """
        pass

    @Parameter(ptype=str, default=None, required=True, value_range=['1.1.1', '1.3.0'])
    def version(self):
        """
        The OWS service version within resource endpoint.
        Required: True
        Default: None
        """
        pass


class WfsGetCaps(OwsGetCaps):
    """WFS GetCapabilities ProbeRunner"""

    NAME = 'WFS GetCapabilities'
    RESOURCE_TYPE = 'OGC:WFS'

    @Parameter(ptype=str, value='WFS')
    def service(self):
        """
        The OWS service within resource endpoint.
        Required: True
        Default: None
        """
        pass

    @Parameter(ptype=str, default=None, required=True, value_range=['1.0.0', '1.1.0', '2.0.2'])
    def version(self):
        """
        The OWS service version within resource endpoint.
        Required: True
        Default: None
        """
        pass

class WcsGetCaps(OwsGetCaps):
    """WCS GetCapabilities ProbeRunner"""

    NAME = 'WCS GetCapabilities'
    RESOURCE_TYPE = 'OGC:WCS'

    @Parameter(ptype=str, value='WCS')
    def service(self):
        """
        The OWS service within resource endpoint.
        Required: True
        Default: None
        """
        pass

    @Parameter(ptype=str, default=None, required=True, value_range=['1.1.0', '1.1.1', '2.0.1'])
    def version(self):
        """
        The OWS service version within resource endpoint.
        Required: True
        Default: None
        """
        pass

class CswGetCaps(OwsGetCaps):
    """CSW GetCapabilities ProbeRunner"""

    NAME = 'WCS GetCapabilities'
    RESOURCE_TYPE = 'OGC:CSW'

    @Parameter(ptype=str, value='CSW')
    def service(self):
        """
        The OWS service within resource endpoint.
        Required: True
        Default: None
        """
        pass

    @Parameter(ptype=str, default=None, required=True, value_range=['2.0.2'])
    def version(self):
        """
        The OWS service version within resource endpoint.
        Required: True
        Default: None
        """
        pass

class WmtsGetCaps(OwsGetCaps):
    """WMTS GetCapabilities ProbeRunner"""

    NAME = 'WMTS GetCapabilities'
    RESOURCE_TYPE = 'OGC:WMTS'


    @Parameter(ptype=str, value='WMTS')
    def service(self):
        """
        The OWS service within resource endpoint.
        Required: True
        Default: None
        """
        pass

    @Parameter(ptype=str, default=None, required=True, value_range=['1.0.0'])
    def version(self):
        """
        The OWS service version within resource endpoint.
        Required: True
        Default: None
        """
        pass

class SosGetCaps(OwsGetCaps):
    """SOS GetCapabilities ProbeRunner"""

    NAME = 'SOS GetCapabilities'
    RESOURCE_TYPE = 'OGC:SOS'

    @Parameter(ptype=str, value='SOS')
    def service(self):
        """
        The OWS service within resource endpoint.
        Required: True
        Default: None
        """
        pass

    @Parameter(ptype=str, default=None, required=True, value_range=['1.0.0'])
    def version(self):
        """
        The OWS service version within resource endpoint.
        Required: True
        Default: None
        """
        pass

