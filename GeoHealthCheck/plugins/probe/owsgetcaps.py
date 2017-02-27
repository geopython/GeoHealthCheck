from GeoHealthCheck.probe import Probe
from GeoHealthCheck.plugindecor import Parameter, UseCheck


class OwsGetCaps(Probe):
    """
    Fetch OWS capabilities doc
    """

    NAME = 'OWS GetCapabilities'

    # Abstract Base Class for OGC OWS GetCaps Probes
    RESOURCE_TYPE = 'OGC:ABC'

    REQUEST_METHOD = 'GET'
    REQUEST_TEMPLATE = '?SERVICE={service}&VERSION={version}&REQUEST=GetCapabilities'

    def __init__(self):
        Probe.__init__(self)

    #
    # Parameters for Probe as Decorators
    #

    @Parameter(ptype=str, default=None, required=True)
    def service(self):
        """
        The OWS service within resource endpoint.
        """
        pass

    @Parameter(ptype=str, default=None, required=True)
    def version(self):
        """
        The OWS service version within resource endpoint.
        """
        pass

    #
    # Checks for Probe as Decorators
    #

    @UseCheck(check_class='GeoHealthCheck.plugins.check.checks.XmlParse')
    def xml_parsable(self):
        """
        response is parsable.
        """
        pass

    @UseCheck(check_class='GeoHealthCheck.plugins.check.checks.NotContainsOwsException')
    def no_ows_exception(self):
        """
        response does not contain OWS Exception.
        Optional: False
        """
        pass

    @UseCheck(check_class='GeoHealthCheck.plugins.check.checks.ContainsStrings',
        parameters={'strings': ['Title>']})
    def has_title_element(self):
        """
        Should have title element in capabilities response doc.
        """
        pass

class WmsGetCaps(OwsGetCaps):
    """Fetch WMS capabilities doc"""
    
    NAME = 'WMS GetCapabilities'
    RESOURCE_TYPE = 'OGC:WMS'

    def __init__(self):
        OwsGetCaps.__init__(self)

    @Parameter(ptype=str, value='WMS')
    def service(self):
        """
        The OWS service within resource endpoint.
        """
        pass

    @Parameter(ptype=str, default='1.1.1', required=True, value_range=['1.1.1', '1.3.0'])
    def version(self):
        """
        The OWS service version within resource endpoint.
        """
        pass


class WfsGetCaps(OwsGetCaps):
    """WFS GetCapabilities Probe"""

    NAME = 'WFS GetCapabilities'
    RESOURCE_TYPE = 'OGC:WFS'

    def __init__(self):
        OwsGetCaps.__init__(self)

    @Parameter(ptype=str, value='WFS')
    def service(self):
        """
        The OWS service within resource endpoint.
        """
        pass

    @Parameter(ptype=str, default='1.1.0', required=True, value_range=['1.0.0', '1.1.0', '2.0.2'])
    def version(self):
        """
        The OWS service version within resource endpoint.
        """
        pass


class WcsGetCaps(OwsGetCaps):
    """WCS GetCapabilities Probe"""

    NAME = 'WCS GetCapabilities'
    RESOURCE_TYPE = 'OGC:WCS'

    def __init__(self):
        OwsGetCaps.__init__(self)

    @Parameter(ptype=str, value='WCS')
    def service(self):
        """
        The OWS service within resource endpoint.
        """
        pass

    @Parameter(ptype=str, default='1.1.0', required=True, value_range=['1.1.0', '1.1.1', '2.0.1'])
    def version(self):
        """
        The OWS service version within resource endpoint.
        """
        pass


class CswGetCaps(OwsGetCaps):
    """CSW GetCapabilities Probe"""

    NAME = 'CSW GetCapabilities'
    RESOURCE_TYPE = 'OGC:CSW'

    def __init__(self):
        OwsGetCaps.__init__(self)

    @Parameter(ptype=str, value='CSW')
    def service(self):
        """
        The OWS service within resource endpoint.
        """
        pass

    @Parameter(ptype=str, default='2.0.2', required=True, value_range=['2.0.2'])
    def version(self):
        """
        The OWS service version within resource endpoint.
        """
        pass


class WmtsGetCaps(OwsGetCaps):
    """WMTS GetCapabilities Probe"""

    NAME = 'WMTS GetCapabilities'
    RESOURCE_TYPE = 'OGC:WMTS'

    def __init__(self):
        OwsGetCaps.__init__(self)

    @Parameter(ptype=str, value='WMTS')
    def service(self):
        """
        The OWS service within resource endpoint.
        """
        pass

    @Parameter(ptype=str, default='1.0.0', required=True, value_range=['1.0.0'])
    def version(self):
        """
        The OWS service version within resource endpoint.
        """
        pass


class WpsGetCaps(OwsGetCaps):
    """WPS GetCapabilities Probe"""

    NAME = 'WPS GetCapabilities'
    RESOURCE_TYPE = 'OGC:WPS'

    def __init__(self):
        OwsGetCaps.__init__(self)

    @Parameter(ptype=str, value='WPS')
    def service(self):
        """
        The OWS service within resource endpoint.
        """
        pass

    @Parameter(ptype=str, default='1.0.0', required=True, value_range=['1.0.0', '2.0.0'])
    def version(self):
        """
        The OWS service version within resource endpoint.
        """
        pass


class SosGetCaps(OwsGetCaps):
    """SOS GetCapabilities Probe"""

    NAME = 'SOS GetCapabilities'
    RESOURCE_TYPE = 'OGC:SOS'

    def __init__(self):
        OwsGetCaps.__init__(self)

    @Parameter(ptype=str, value='SOS')
    def service(self):
        """
        The OWS service within resource endpoint.
        """
        pass

    @Parameter(ptype=str, default='1.0.0', required=True, value_range=['1.0.0'])
    def version(self):
        """
        The OWS service version within resource endpoint.
        """
        pass

