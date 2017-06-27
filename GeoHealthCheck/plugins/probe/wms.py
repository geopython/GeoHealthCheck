from GeoHealthCheck.probe import Probe
from GeoHealthCheck.plugin import Plugin
from owslib.wms import WebMapService


class WmsGetMapV1(Probe):
    """
    Get WMS map image using the OGC WMS GetMap v1.1.1 Operation
    for single Layer.
    """

    NAME = 'WMS GetMap WMS v1.1.1. operation on SINGLE Layer'
    DESCRIPTION = """
    Do WMS GetMap v1.1.1 request with user-specified parameters
    for single Layer.
    """
    RESOURCE_TYPE = 'OGC:WMS'

    REQUEST_METHOD = 'GET'
    REQUEST_TEMPLATE = '?SERVICE=WMS&VERSION=1.1.1&' + \
                       'REQUEST=GetMap&LAYERS={layers}&SRS={srs}&' + \
                       'BBOX={bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}&' + \
                       'WIDTH={width}&HEIGHT={height}&FORMAT={format}' + \
                       '&STYLES={styles}&EXCEPTIONS={exceptions}'

    PARAM_DEFS = {
        'layers': {
            'type': 'stringlist',
            'description': 'The WMS Layer, select one',
            'default': [],
            'required': True,
            'range': None
        },
        'srs': {
            'type': 'string',
            'description': 'The SRS as EPSG: code',
            'default': 'EPSG:4326',
            'required': True,
            'range': None
        },
        'bbox': {
            'type': 'bbox',
            'description': 'The WMS bounding box',
            'default': ['-180', '-90', '180', '90'],
            'required': True,
            'range': None
        },
        'width': {
            'type': 'string',
            'description': 'The image width',
            'default': '256',
            'required': True
        },
        'height': {
            'type': 'string',
            'description': 'The image height',
            'default': '256',
            'required': True
        },
        'format': {
            'type': 'string',
            'description': 'The image format',
            'default': 'image/png',
            'required': True,
            'range': None
        },
        'styles': {
            'type': 'string',
            'description': 'The Styles to apply',
            'default': None,
            'required': False
        },
        'exceptions': {
            'type': 'string',
            'description': 'The Exception format to use',
            'default': 'application/vnd.ogc.se_xml',
            'required': True,
            'range': None
        }

    }
    """Param defs"""

    CHECKS_AVAIL = {
        'GeoHealthCheck.plugins.check.checks.HttpHasImageContentType': {
            'default': True
        },
        'GeoHealthCheck.plugins.check.checks.NotContainsOwsException': {
            'default': True
        }
    }
    """
    Checks for WMS GetMap Response available.
    Optionally override Check PARAM_DEFS using set_params
    e.g. with specific `value` or even `name`.
    """

    def __init__(self):
        Probe.__init__(self)
        self.layer_count = 0

    # Overridden: expand param-ranges from WMS metadata
    def expand_params(self, resource):

        # Use WMS Capabilities doc to get metadata for
        # PARAM_DEFS ranges/defaults
        try:
            wms = WebMapService(resource.url)
            layers = wms.contents
            self.layer_count = len(layers)

            # Layers to select
            self.PARAM_DEFS['layers']['range'] = list(layers.keys())

            # Image Format
            for oper in wms.operations:
                if oper.name == 'GetMap':
                    self.PARAM_DEFS['format']['range'] = \
                        oper.formatOptions
                    break

            # Take first layer to determine generic attrs
            layer_name, layer_entry = layers.popitem()

            # SRS
            srs_range = layer_entry.crsOptions
            self.PARAM_DEFS['srs']['range'] = srs_range

            # bbox list: 0-3 is bbox, 4 is SRS
            bbox = layer_entry.boundingBox
            bbox_srs = bbox[4]
            self.PARAM_DEFS['srs']['default'] = bbox_srs
            # if it is not EPSG:4326 we need to transform bbox
            # if bbox_srs != 'EPSG:4326':
            #     bbox = transform_bbox('EPSG:4326', bbox_srs, bbox[:-1])

            self.PARAM_DEFS['bbox']['default'] = \
                [str(x) for x in bbox[:-1]]

            self.PARAM_DEFS['exceptions']['range'] = wms.exceptions
        except Exception as err:
            raise err


class WmsGetMapV1All(WmsGetMapV1):
    """
    Get WMS map image for each Layer using the WMS GetMap operation.
    """

    NAME = 'WMS GetMap WMS v1.1.1. operation on ALL Layers'
    DESCRIPTION = """
    Do WMS GetMap v1.1.1 request for all Layers with
    user-specified parameters.
    """
    # Copy all PARAM_DEFS from parent to have own instance
    PARAM_DEFS = Plugin.merge(WmsGetMapV1.PARAM_DEFS, {})

    def __init__(self):
        WmsGetMapV1.__init__(self)

    # Overridden: expand param-ranges from WMS metadata
    # from single-layer GetMap parent Probe and set layers
    # fixed to *
    def expand_params(self, resource):
        WmsGetMapV1.expand_params(self, resource)
        val = 'all %d layers' % self.layer_count

        self.PARAM_DEFS['layers']['range'] = [val]
        self.PARAM_DEFS['layers']['value'] = val
        self.PARAM_DEFS['layers']['default'] = val

    def perform_request(self):
        """ Perform actual request to service, overridden from base class"""

        # Get capabilities doc to get all layers
        try:
            wms = WebMapService(self._resource.url)
            layers = wms.contents.keys()
        except Exception as err:
            self.result.set(False, str(err))
            return

        results_failed_total = []
        for layer in layers:
            self._parameters['layers'] = [layer]

            # Let the templated parent perform
            Probe.perform_request(self)
            self.run_checks()

            # Only keep failed Layer results
            # otherwise with 100s of Layers the report grows out of hand...
            results_failed = self.result.results_failed
            if len(results_failed) > 0:
                # We have a failed layer: add to result message
                for result in results_failed:
                    result.message = 'layer %s: %s' % (layer, result.message)

                results_failed_total += results_failed
                self.result.results_failed = []

            self.result.results = []

        self.result.results_failed = results_failed_total
