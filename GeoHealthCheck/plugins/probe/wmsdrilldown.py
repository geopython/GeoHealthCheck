import random

from GeoHealthCheck.probe import Probe
from GeoHealthCheck.result import Result
from owslib.wms import WebMapService


class WmsDrilldown(Probe):
    """
    Probe for WMS endpoint "drilldown": starting
    with GetCapabilities doc: get Layers and do
    GetMap on them etc. Using OWSLib.WebMapService.

    TODO: needs finalization.
    """

    NAME = 'WMS Drilldown'
    DESCRIPTION = 'Traverses a WMS endpoint by drilling down from Capabilities'
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
        Perform the drilldown.
        See https://github.com/geopython/OWSLib/blob/
        master/tests/doctests/wms_GeoServerCapabilities.txt
        """
        wms = None

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

        # 2. Test layers
        # TODO: use parameters to work on less/more drilling
        # "full" could be all layers.
        result = Result(True, 'Test Layers')
        result.start()
        try:
            # Pick a random layer
            layer_name = random.sample(wms.contents.keys(), 1)[0]
            layer = wms[layer_name]

            # TODO Only use EPSG:4326, later random CRS
            if 'EPSG:4326' in layer.crsOptions \
                    and layer.boundingBoxWGS84:

                # Search GetMap operation
                get_map_oper = None
                for oper in wms.operations:
                    if oper.name == 'GetMap':
                        get_map_oper = oper
                        break

                format = None
                for format in get_map_oper.formatOptions:
                    if format.startswith('image/'):
                        break

                # format = random.sample(get_map_oper.formatOptions, 1)[0]

                self.log('testing layer: %s' % layer_name)
                layer_bbox = layer.boundingBoxWGS84
                wms.getmap(layers=[layer_name],
                           styles=[''],
                           srs='EPSG:4326',
                           bbox=(layer_bbox[0],
                                 layer_bbox[1],
                                 layer_bbox[2],
                                 layer_bbox[3]),
                           size=(256, 256),
                           format=format,
                           transparent=False)

                self.log('WMS GetMap: format=%s' % format)
                # Etc, to be finalized

        except Exception as err:
            result.set(False, str(err))

        result.stop()

        # Add to overall Probe result
        self.result.add_result(result)
