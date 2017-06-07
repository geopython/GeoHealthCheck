from GeoHealthCheck.probe import Probe
from GeoHealthCheck.result import Result
from owslib.wms import WebMapService


class MyWMSProbe(Probe):
    """
    Example Probe for WMS Probe user plugin. This is a free-form Probe
    that overrides perform_request with custom checks.
    
    To configure a probe, use Docker Container ENV 
    GHC_USER_PLUGINS='GeoHealthCheck.plugins.user.mywmsprobe,...'.
    Note that GeoHealthCheck.plugins package prefix is required as
    Plugins are placed in GHC app tree there.
    """

    NAME = 'MyWMSProbe'
    DESCRIPTION = 'Example User Probe, gets WMS Capabilities'
    RESOURCE_TYPE = 'OGC:WMS'

    REQUEST_METHOD = 'GET'

    PARAM_DEFS = {
        'probing_level': {
            'type': 'string',
            'description': 'How heavy the Probe should be.',
            'default': 'minor',
            'required': True,
            'range': ['minor', 'moderate', 'full']
        }
    }
    """Param defs"""

    def __init__(self):
        Probe.__init__(self)

    def perform_request(self):
        """
        Perform the request.
        See https://github.com/geopython/OWSLib/blob/
        master/tests/doctests/wms_GeoServerCapabilities.txt
        """

        # Test capabilities doc
        result = Result(True, 'Test Capabilities')
        result.start()
        try:
            wms = WebMapService(self._resource.url)
            title = wms.identification.title
            self.log('response: title=%s' % title)
        except Exception as err:
            result.set(False, str(err))

        # Do more rigorous stuff here below
        result.stop()

        self.result.add_result(result)
