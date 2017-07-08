from GeoHealthCheck.probe import Probe
from GeoHealthCheck.plugin import Plugin
from owslib.tms import TileMapService


class TmsCaps(Probe):
    """Probe for TMS main endpoint url"""

    NAME = 'TMS Capabilities'
    DESCRIPTION = 'Perform TMS Capabilities Operation and check validity'
    RESOURCE_TYPE = 'OSGeo:TMS'

    REQUEST_METHOD = 'GET'

    def __init__(self):
        Probe.__init__(self)

    CHECKS_AVAIL = {
        'GeoHealthCheck.plugins.check.checks.XmlParse': {
            'default': True
        },
        'GeoHealthCheck.plugins.check.checks.ContainsStrings': {
            'default': True,
            'set_params': {
                'strings': {
                    'name': 'Must contain TileMap Element',
                    'value': ['<TileMap']
                }
            }
        },
    }
    """
    Checks avail for all specific Caps checks.
    Optionally override Check.PARAM_DEFS using set_params
    e.g. with specific `value` or even `name`.
    """


class TmsGetTile(Probe):
    """Fetch TMS tile and check result"""

    NAME = 'TMS GetTile Single - get SINGLE Tile Image'
    DESCRIPTION = """Fetch SINGLE TMS-tile. NB extension
                  should match last string of layer."""
    RESOURCE_TYPE = 'OSGeo:TMS'

    REQUEST_METHOD = 'GET'

    # e.g. http://geodata.nationaalgeoregister.nl/tms/1.0.0/
    # brtachtergrondkaart/1/0/0.png
    REQUEST_TEMPLATE = '/{layer}/{zoom}/{x}/{y}.{extension}'

    PARAM_DEFS = {
        'layer': {
            'type': 'string',
            'description': 'The TMS Layer within resource endpoint',
            'default': None,
            'required': True,
            'range': None
        },
        'zoom': {
            'type': 'string',
            'description': 'The tile pyramid zoomlevel',
            'default': '0',
            'required': True,
            'range': None
        },
        'x': {
            'type': 'string',
            'description': 'The tile x offset',
            'default': '0',
            'required': True,
            'range': None
        },
        'y': {
            'type': 'string',
            'description': 'The tile y offset',
            'default': '0',
            'required': True,
            'range': None
        },
        'extension': {
            'type': 'string',
            'description': 'The tile image extension',
            'default': 'png',
            'required': True,
            'range': None
        }
    }
    """Param defs"""

    CHECKS_AVAIL = {
        'GeoHealthCheck.plugins.check.checks.HttpHasImageContentType': {
            'default': True
        }
    }
    """Check for TMS GetTile"""

    def __init__(self):
        Probe.__init__(self)
        self.layer_count = 0

    # Overridden: expand param-ranges from WMS metadata
    def expand_params(self, resource):

        # Use WMS Capabilities doc to get metadata for
        # PARAM_DEFS ranges/defaults
        try:
            tms = TileMapService(resource.url, version='1.0.0')
            layers = tms.contents
            self.layer_count = len(layers)

            # Determine Layers and Extensions
            layer_list = [layer_name.split('1.0.0/')[-1]
                          for layer_name in layers]
            self.PARAM_DEFS['layer']['range'] = layer_list

            # Make a set of all extensions
            extensions = set([layer.extension
                              for layer_name, layer in layers.items()])
            self.PARAM_DEFS['extension']['range'] = list(extensions)
        except Exception as err:
            raise err


class TmsGetTileAll(TmsGetTile):
    """
    Get TMS map image for each Layer using the TMS GetTile operation.
    """

    NAME = 'TMS GetTile All - get Tile Image for ALL Layers'
    DESCRIPTION = """
    Do TMS GetTile request for each Layer.
    """
    PARAM_DEFS = Plugin.merge(TmsGetTile.PARAM_DEFS, {})

    def __init__(self):
        TmsGetTile.__init__(self)
        self.tms = None
        self.layers = None

    # Overridden: expand param-ranges from TMS metadata
    # from single-layer GetTile parent Probe and set layers
    # fixed to *
    def expand_params(self, resource):
        TmsGetTile.expand_params(self, resource)
        layer_val = 'all %d layers' % self.layer_count
        extension_val = 'all extensions'

        self.PARAM_DEFS['layer']['range'] = [layer_val]
        self.PARAM_DEFS['layer']['value'] = layer_val
        self.PARAM_DEFS['layer']['default'] = layer_val

        self.PARAM_DEFS['extension']['range'] = [extension_val]
        self.PARAM_DEFS['extension']['value'] = extension_val
        self.PARAM_DEFS['extension']['default'] = extension_val

    def before_request(self):
        """ Before request to service, overridden from base class"""

        # Get capabilities doc to get all layers
        try:
            self.tms = TileMapService(self._resource.url, version='1.0.0')
            self.layers = self.tms.contents
        except Exception as err:
            self.result.set(False, str(err))

    def perform_request(self):
        """ Perform actual request to service, overridden from base class"""

        if not self.layers:
            self.result.set(False, 'Found no TMS Layers')
            return

        self.result.start()

        results_failed_total = []
        for layer_name in self.layers.keys():
            # Layer name is last part of full URL
            self._parameters['layer'] = layer_name.split('1.0.0/')[-1]
            self._parameters['extension'] = self.layers[layer_name].extension

            # Let the templated parent perform
            Probe.perform_request(self)
            self.run_checks()

            # Only keep failed Layer results
            # otherwise with 100s of Layers the report grows out of hand...
            results_failed = self.result.results_failed
            if len(results_failed) > 0:
                # We have a failed layer: add to result message
                for result in results_failed:
                    result.message = 'layer %s: %s' % \
                                     (layer_name, result.message)

                results_failed_total += results_failed
                self.result.results_failed = []

            self.result.results = []

        self.result.results_failed = results_failed_total
        self.result.results = results_failed_total
