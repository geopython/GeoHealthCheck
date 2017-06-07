from GeoHealthCheck.probe import Probe
from GeoHealthCheck.result import Result
from owslib.wms import WebMapService


class MyWMSProbe(Probe):
    """
    Example Probe for WMS Probe user plugin.

    Add the module GeoHealthCheck.plugins.user.mywmsprobe.py.
    """

    NAME = 'MyWMSProbe'
    DESCRIPTION = 'Simple example for Probe, gets WMS Capabilities'
    RESOURCE_TYPE = 'OGC:WMS'

    REQUEST_METHOD = 'GET'

    PARAM_DEFS = {
        'drilldown_level': {
            'type': 'string',
            'description': 'How heavy the drilldown should be.',
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

        # 1. Test capabilities doc, parses
        result = Result(True, 'Test Capabilities')
        result.start()
        try:
            wms = WebMapService(self._resource.url)
            title = wms.identification.title
            self.log('response: title=%s' % title)
        except Exception as err:
            result.set(False, str(err))

        result.stop()

        self.result.add_result(result)
