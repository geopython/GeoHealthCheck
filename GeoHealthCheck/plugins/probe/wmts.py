from GeoHealthCheck.probe import Probe
from owslib.wmts import WebMapTileService
from pyproj import CRS, Transformer
import math


class WmtsGetTile(Probe):
    """
    Get WMTS map tile for specific layers.
    """

    NAME = 'WMTS GetTile operation on specific layers'
    DESCRIPTION = """
    Do WMTS GetTile request on user-specified layers.
    """

    RESOURCE_TYPE = 'OGC:WMTS'

    REQUEST_METHOD = 'GET'
    REQUEST_TEMPLATE = {
        'KVP':
            '?SERVICE=WMTS&VERSION=1.0.0&' +
            'REQUEST=GetTile&LAYER={layers}&' +
            'TILEMATRIXSET={tilematrixset}&' +
            'TILEMATRIX={tilematrix}&TILEROW={tilerow}&' +
            'TILECOL={tilecol}&FORMAT={format}&' +
            'EXCEPTIONS={exceptions}&STYLE={style}',
        'REST':
            '/{layers}/{tilematrixset}' +
            '/{tilematrix}/{tilecol}/{tilerow}.{format}'
    }

    PARAM_DEFS = {
        'layers': {
            'type': 'stringlist',
            'description': 'The WMTS Layer, select one',
            'default': [],
            'required': True,
            'range': None,
        },
        'tilematrixset': {
            'type': 'string',
            'description': 'tilematrixset',
            'value': 'All tilematrixsets',
        },
        'tilematrix': {
            'type': 'string',
            'description': 'tilematrix',
            'value': 'All tilematrices',
        },
        'tilerow': {
            'type': 'string',
            'description': 'tilerow',
            'value': 'Center of the image',
        },
        'tilecol': {
            'type': 'string',
            'description': 'tilecol',
            'value': 'Center of the image',
        },
        'format': {
            'type': 'string',
            'description': 'The image format',
            'required': True,
            'range': None,
        },
        'exceptions': {
            'type': 'string',
            'description': 'The Exception format to use',
            'value': 'application/vnd.ogc.se_xml',
        },
        'style': {
            'type': 'string',
            'description': 'The Styles to apply',
            'value': 'default',
        },
        'kvprest': {
            'type': 'string',
            'description': 'Request the endpoint through KVP or REST',
            'required': True,
            'range': [],
        },
    }
    """Param defs"""

    CHECKS_AVAIL = {
        'GeoHealthCheck.plugins.check.checks.HttpStatusNoError': {
            'default': True
        },
        'GeoHealthCheck.plugins.check.checks.NotContainsOwsException': {
            'default': True
        },
        'GeoHealthCheck.plugins.check.checks.HttpHasImageContentType': {
            'default': True
        }
    }
    """
    Checks for WMTS GetTile Response available.
    Optionally override Check PARAM_DEFS using set_params
    e.g. with specific `value` or even `name`.
    """

    def __init__(self):
        Probe.__init__(self)
        self.layer_count = 0

    def get_metadata(self, resource, version='1.0.0'):
        """
        Get metadata, specific per Resource type.
        :param resource:
        :param version:
        :return: Metadata object
        """
        return WebMapTileService(resource.url, version=version,
                                 headers=self.get_request_headers())

    def expand_params(self, resource):

        # Use WMTS Capabilities doc to get metadata for
        # PARAM_DEFS ranges/defaults
        try:
            wmts = self.get_metadata_cached(resource, version='1.0.0')

            self.PARAM_DEFS['kvprest']['range'] = self.test_kvp_rest()

            layers = wmts.contents
            self.PARAM_DEFS['layers']['range'] = list(layers.keys())

            # Take random layer to determine generic attrs
            for layer_name in layers:
                layer_entry = layers[layer_name]
                break

            # Determine image format
            self.PARAM_DEFS['format']['range'] = list(layer_entry.formats)

        except Exception as err:
            raise err

    def test_kvp_rest(self):
        restenc = False
        kvpenc = False

        url = self._resource.url

        # If url ends with wmtscapabilities.xml it is REST only
        if url.endswith('WMTSCapabilities.xml'):
            return ['REST']

        elif '?' in url:
            return ['KVP']

        else:
            print('rest:', url + '/1.0.0/WMTSCapabilities.xml')
            if self.check_capabilities(url + '/1.0.0/WMTSCapabilities.xml'):
                restenc = True

            url + '?service=WMTS&version=1.0.0&request=GetCapabilities'
            if self.check_capabilities(url +
                                       '?service=WMTS&version=1.0.0' +
                                       '&request=GetCapabilities'):
                kvpenc = True

        print('url:', url, 'rest:', restenc, 'kvp:', kvpenc)

        return [x for (x, remove) in zip(['KVP', 'REST'], [kvpenc, restenc])
                if remove]

    def check_capabilities(self, url):
        response = Probe.perform_get_request(self, url)
        return (response.status_code == 200 and
                '<ServiceException>' not in response.text)

    def before_request(self):
        """ Before request to service, overridden from base class"""

        # Get capabilities doc to get all layers
        try:
            self.wmts = self.get_metadata_cached(self._resource,
                                                 version='1.0.0')
            self.layers = self._parameters['layers']

            if self._resource.url.endswith('/1.0.0/WMTSCapabilities.xml'):
                self._resource.url = self._resource.url.split(
                    '/1.0.0/WMTSCapabilities.xml')[0]

            self.REQUEST_TEMPLATE = self.REQUEST_TEMPLATE[
                self._parameters['kvprest']]

        except Exception as err:
            self.result.set(False, str(err))

    def perform_request(self):
        """ Perform actual request to service, overridden from base class"""

        if not self.layers:
            self.result.set(False, 'Found no WMTS Layers')
            return

        self.result.start()

        results_failed_total = []

        for layer in self.layers:
            self._parameters['layers'] = [layer]

            layer_object = self.wmts.contents[layer]

            # Get the boundingbox from capabilities to get
            # the center coordinate
            bbox84 = layer_object.boundingBoxWGS84
            center_coord_84 = [(bbox84[0] + bbox84[2]) / 2,
                               (bbox84[1] + bbox84[3]) / 2]

            tilematrixsets = layer_object.tilematrixsetlinks

            if self._parameters['kvprest'] == 'REST':
                format = layer_object.formats[0]
                self._parameters['format'] = format.split('/')[1]

            for set in tilematrixsets:
                self._parameters['tilematrixset'] = set

                tilematrixset_object = self.wmts.tilematrixsets[set]

                # Get projection from capabilities and transform
                # the center coordinate
                set_crs = CRS(tilematrixset_object.crs)
                transformer = Transformer.from_crs(CRS('EPSG:4326'),
                                                   set_crs,
                                                   always_xy=False)
                center_coord = transformer.transform(center_coord_84[1],
                                                     center_coord_84[0])

                # print(center_coord, center_coord_84)

                tilematrices = tilematrixset_object.tilematrix
                for zoom in tilematrices:
                    self._parameters['tilematrix'] = zoom

                    tilecol, tilerow = self.calculate_center_tile(
                        center_coord,
                        tilematrices[zoom], set_crs)
                    self._parameters['tilecol'] = tilecol
                    self._parameters['tilerow'] = tilerow

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

    def calculate_center_tile(self, center_coord, tilematrix, crs):
        scale = tilematrix.scaledenominator
        topleftcorner = list(tilematrix.topleftcorner)
        center_coord = list(center_coord)

        first_axis = crs.axis_info[0].direction
        unit = crs.axis_info[0].unit_name

        if first_axis == 'north':
            center_coord.reverse()
            topleftcorner.reverse()

        corr = {
            'metre': [1, 1],
            'degree': [(1 / (40075000 * math.cos(center_coord[0]) / 360)),
                       (1 / 111320)],
            'feet': [0.3048, 0.3048]
        }

        # Calculate tile size
        tilewidth = 0.00028 * scale * tilematrix.tilewidth * corr[unit][0]
        tileheight = 0.00028 * scale * tilematrix.tileheight * corr[unit][1]

        # Calculate tile index of center tile in the right projection
        tilecol = int((center_coord[0] - topleftcorner[0]) / tilewidth)
        tilerow = int((topleftcorner[1] - center_coord[1]) / tileheight)

        return tilecol, tilerow


class WmtsGetTileAll(WmtsGetTile):
    """
    Get WMTS GetTile for all layers.
    """

    NAME = 'Get WMTS GetTile for all layers.'
    DESCRIPTION = """
    Get WMTS GetTile for all layers.
    """

    PARAM_DEFS = WmtsGetTile.PARAM_DEFS
    """Param defs"""

    # Overridden: expand param-ranges from WMTS metadata
    def expand_params(self, resource):
        # Use WMTS Capabilities doc to get metadata for
        # PARAM_DEFS ranges/defaults
        try:
            wmts = self.get_metadata_cached(resource, version='1.0.0')

            try:
                if wmts.restonly:
                    self.PARAM_DEFS['kvprest']['range'] = ['REST']
            except AttributeError:
                self.PARAM_DEFS['kvprest']['range'] = ['KVP', 'REST']

            self.PARAM_DEFS['layers'] = {
                'type': 'stringlist',
                'description': 'The WMTS layer, select one',
                'value': ['All layers']
            }

            layers = wmts.contents

            # Take random layer to determine generic attrs
            for layer_name in layers:
                layer_entry = layers[layer_name]
                break

            # Determine image format
            self.PARAM_DEFS['format']['range'] = list(layer_entry.formats)

        except Exception as err:
            raise err

    def before_request(self):
        """ Before request to service, overridden from base class"""

        # Get capabilities doc to get all layers
        WmtsGetTile.before_request(self)
        try:
            self.wmts = self.get_metadata_cached(self._resource,
                                                 version='1.0.0')
            self.layers = self.wmts.contents

        except Exception as err:
            self.result.set(False, str(err))
