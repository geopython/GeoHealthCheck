import random

from GeoHealthCheck.probe import Probe
from GeoHealthCheck.result import Result
from owslib.wfs import WebFeatureService


class WfsDrilldown(Probe):
    """
    Probe for Wfs endpoint "drilldown": starting
    with GetCapabilities doc: get Layers and do
    GetMap on them etc. Using OWSLib.WebMapService.

    TODO: needs finalization.
    """

    NAME = 'WFS Drilldown'
    DESCRIPTION = 'Traverses a WFS endpoint by drilling down from Capabilities'
    RESOURCE_TYPE = 'OGC:WFS'

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
        Perform the drilldown.
        See https://github.com/geopython/OWSLib/blob/
        master/tests/doctests/Wfs_GeoServerCapabilities.txt
        """
        Wfs = None

        # 1. Test capabilities doc, parses
        result = Result(True, 'Test WFS Capabilities')
        result.start()
        try:
            Wfs = WebFeatureService(self._resource.url, version='2.0.0',
                                headers=self.get_request_headers())
            title = Wfs.identification.title
            self.log('response: title=%s' % title)
        except Exception as err:
            result.set(False, str(err))

        result.stop()
        self.result.add_result(result)

        # 2. Test layers
        # TODO: use parameters to work on less/more drilling
        # "full" could be all layers.
        result = Result(True, 'Test a Featuretype')
        result.start()
        try:
            # Pick a random layer
            layer_name = random.sample(Wfs.contents.keys(), 1)[0]
            layer = Wfs[layer_name]
            self.log('Fetching schema of layer: %s' % layer_name)
            schemaResponse = Wfs.get_schema(layer_name)
            self.log('Properties: %s' % schemaResponse.get('properties',''))

            self.log('testing layer: %s' % layer_name)
            gmlResponse = Wfs.getfeature(typename=layer_name, maxfeatures=1)
            self.log('Wfs GetFeature: gml=%s' % gmlResponse.getvalue())
            # Etc, to be finalized

        except Exception as err:
            result.set(False, str(err))

        result.stop()

        # Add to overall Probe result
        self.result.add_result(result)
