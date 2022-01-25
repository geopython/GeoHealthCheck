from GeoHealthCheck.probe import Probe
from GeoHealthCheck.plugin import Plugin
from owslib.wmts import WebMapTileService
from pyproj import CRS, Transformer
from pyproj.crs import coordinate_system
import math
import requests
from random import choice, shuffle


class WmtsGetTile(Probe):
    """
    Get WMTS map tile for specific layers.
    There are 2 possible request templates to support both KVP and REST
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
            'TILEMATRIX={tilematrix}&TILEROW={latitude_4326}&' +
            'TILECOL={longitude_4326}&FORMAT={format}&' +
            'EXCEPTIONS={exceptions}&STYLE={style}',
        'REST':
            '/{layers}/{tilematrixset}' +
            '/{tilematrix}/{longitude_4326}/{latitude_4326}.{format}'
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
            'description': 'Projection with its own set of zoom level indices',
            'range': ['all', 'sample'],
            'default': 'all'
        },
        'tilematrix': {
            'type': 'string',
            'description': 'Zoom level index',
            'range': ['all', 'sample'],
            'default': 'sample'
        },
        'latitude_4326': {
            'type': 'string',
            'description': 'latitude of tile to request'
        },
        'longitude_4326': {
            'type': 'string',
            'description': 'longitude of tile to request'
        },
        'format': {
            'type': 'string',
            'description': 'The image format',
            'range': ['sample'],
            'default': 'sample'
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
        url = Plugin.copy(resource.url)

        # If endpoint can only be accessed through REST, owslib cannot
        # get metadata, as GetCapabilities request is done through KVP.
        # Added '/1.0.0/WMTSCapabilities.xml' to omit this problem.
        if not self.check_capabilities(url +
                                       '?service=WMTS&version=1.0.0' +
                                       '&request=GetCapabilities'):
            url = url + '/1.0.0/WMTSCapabilities.xml'

        return WebMapTileService(url, version=version,
                                 headers=self.get_request_headers())

    def expand_params(self, resource):
        # Use WMTS Capabilities doc to get metadata for
        # PARAM_DEFS ranges/defaults
        try:
            self.PARAM_DEFS['kvprest']['range'] = self.test_kvp_rest()

            wmts = self.get_metadata_cached(resource, version='1.0.0')

            layers = wmts.contents
            self.PARAM_DEFS['layers']['range'] = list(layers.keys())
            
            for layer in layers:
                layer_object = layers[layer]
                break

            bbox84 = layer_object.boundingBoxWGS84
            center_coord_84 = [(bbox84[0] + bbox84[2]) / 2,
                               (bbox84[1] + bbox84[3]) / 2]

            self.PARAM_DEFS['latitude_4326']['default'] = center_coord_84[1]
            self.PARAM_DEFS['longitude_4326']['default'] = center_coord_84[0]

        except Exception as err:
            raise err

    def test_kvp_rest(self):
        """
        Make requests on some variations of the url to test
        if KVP and/or REST is possible.
        """

        encodings = []
        url = self._resource.url

        # If url ends with wmtscapabilities.xml it is REST only
        if url.endswith('WMTSCapabilities.xml'):
            return ['REST']

        if '?' in url:
            return ['KVP']

        if self.check_capabilities(url +
                                   '?service=WMTS&version=1.0.0' +
                                   '&request=GetCapabilities'):
            encodings.append('KVP')

        if self.check_capabilities(url + '/1.0.0/WMTSCapabilities.xml'):
            encodings.append('REST')

        return encodings

    def check_capabilities(self, url):
        """ Check for exception in GetCapabilities response"""

        try:
            response = Probe.perform_get_request(self, url)
        except Exception:
            return False
        return (response.status_code == 200 and
                '<ServiceException' not in response.text)

    def before_request(self):
        """ Before request to service, overridden from base class"""

        # Get capabilities doc to get all layers
        try:
            self.wmts = self.get_metadata_cached(self._resource,
                                                 version='1.0.0')

        except Exception as err:
            self.result.set(False, str(err))

        self.layers = self._parameters['layers']

        self.REQUEST_TEMPLATE = self.REQUEST_TEMPLATE[
            self._parameters['kvprest']]

    def perform_request(self):
        """ Perform actual request to service, overridden from base class"""

        if not self.layers:
            self.result.set(False, 'Found no WMTS Layers')
            return

        self.result.start()

        results_failed_total = []

        self.parameters_copy = Plugin.copy(self._parameters)

        for layer in self.layers:
            self.parameters_copy['layers'] = [layer]

            layer_object = self.wmts.contents[layer]

            # # Get the boundingbox from capabilities to get
            # # the center coordinate
            # bbox84 = layer_object.boundingBoxWGS84
            # center_coord_84 = [(bbox84[0] + bbox84[2]) / 2,
            #                    (bbox84[1] + bbox84[3]) / 2]

            if self._parameters['kvprest'] == 'KVP':
                format = choice(layer_object.formats)
                self.parameters_copy['format'] = format

            elif self._parameters['kvprest'] == 'REST':
                format_list = Plugin.copy(layer_object.formats)
                shuffle(format_list)

                format_success = False
                for format in format_list:
                    if ('image/png' in format or 'image/jpeg' in format):
                        self.parameters_copy['format'] = format.split('/')[1]
                        format_success = True
                        break
                    else:
                        continue

                if not format_success:
                    msg = "Image Format Err: image format is not one " + \
                        "of 'image/png or image/jpeg.'" + \
                        "It is recommended to support .png or .jpeg" + \
                        "when using the REST request format."
                    self.result.set(False, msg)
                    return

            tilematrixsets = layer_object.tilematrixsetlinks
            if self._parameters['tilematrixset'] == 'sample':
                tilematrixsets = [choice(list(tilematrixsets.keys()))]

            for set in tilematrixsets:
                self.parameters_copy['tilematrixset'] = set

                tilematrixset_object = self.wmts.tilematrixsets[set]

                # Get projection from capabilities and transform
                # the center coordinate
                set_crs = CRS(tilematrixset_object.crs)
                transformer = Transformer.from_crs(CRS('EPSG:4326'),
                                                set_crs,
                                                always_xy=False)
                lat_4326 = self._parameters['latitude_4326']
                lon_4326 = self._parameters['longitude_4326']
                center_coord = transformer.transform(lat_4326,
                                                    lon_4326)

                tilematrices = tilematrixset_object.tilematrix
                if self._parameters['tilematrix'] == 'sample':
                    tilematrices = [choice(list(tilematrices.keys()))]

                for zoom in tilematrices:
                    self.parameters_copy['tilematrix'] = zoom

                    tilecol, tilerow = self.calculate_center_tile(
                        center_coord,
                        tilematrixset_object.tilematrix[zoom], set_crs)
                    self.parameters_copy['longitude_4326'] = tilecol
                    self.parameters_copy['latitude_4326'] = tilerow

                    # Let the templated parent perform
                    self.actual_request()
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

    def actual_request(self):
        """ Perform actual request to service"""

        # Actualize request query string or POST body
        # by substitution in template.
        url_base = self._resource.url

        # Remove capabilities string from url before sending request.
        rest_url_end = '/1.0.0/WMTSCapabilities.xml'
        if url_base.endswith(rest_url_end):
            url_base = url_base[0:-len(rest_url_end)]

        if '?' in url_base:
            url_base = url_base.split('?')[0]

        request_string = None
        if self.REQUEST_TEMPLATE:
            request_string = self.REQUEST_TEMPLATE
            if '?' in url_base and self.REQUEST_TEMPLATE[0] == '?':
                self.REQUEST_TEMPLATE = '&' + self.REQUEST_TEMPLATE[1:]

            if self._parameters:
                request_parms = Plugin.copy(self.parameters_copy)
                param_defs = self.get_param_defs()

                # Expand string list array to comma separated string
                for param in request_parms:
                    if param_defs[param]['type'] == 'stringlist':
                        request_parms[param] = ','.join(request_parms[param])

                request_string = self.REQUEST_TEMPLATE.format(**request_parms)

                complete_url = url_base + request_string

        self.log('Requesting: %s url=%s' % (self.REQUEST_METHOD, complete_url))

        try:
            if self.REQUEST_METHOD == 'GET':
                # Default is plain URL, e.g. for WWW:LINK
                url = url_base
                if request_string:
                    # Query String: mainly OWS:* resources
                    url = "%s%s" % (url, request_string)

                self.response = Probe.perform_get_request(self, url)

            elif self.REQUEST_METHOD == 'POST':
                self.response = Probe.perform_post_request(self,
                                                           url_base,
                                                           request_string)
        except requests.exceptions.RequestException as e:
            msg = "Request Err: %s %s" % (e.__class__.__name__, str(e))
            self.result.set(False, msg)

        if self.response:
            self.log('response: status=%d' % self.response.status_code)

            if self.response.status_code / 100 in [4, 5]:
                self.log('Error response: %s' % (str(self.response.text)))

    def calculate_center_tile(self, center_coord, tilematrix, crs):
        """
        Determine center tile row and column indexes based on
        topleft coordinate, scale, center coordinate and tilewidth/height
        """
        scale = tilematrix.scaledenominator
        topleftcorner = list(tilematrix.topleftcorner)
        center_coord = list(center_coord)

        first_axis = crs.axis_info[0].direction
        unit = crs.axis_info[0].unit_name

        # Adjust for coordinate systems that have reversed lat/lon coordinates
        if first_axis == 'north':
            center_coord.reverse()
            topleftcorner.reverse()

        # Formula for metre to degree conversion factor from:
        # https://stackoverflow.com/questions/639695/
        conv = {
            'metre': [1],
            'degree': [1 / (111320 *
                            math.cos(math.pi * center_coord[0] / 180)),
                       1 / 111320],
            'foot': [coordinate_system.UNIT_FT['conversion_factor']],
            'US survey foot': [
                coordinate_system.UNIT_US_FT['conversion_factor']]
        }

        # Calculate tile size
        tilewidth = 0.00028 * scale * tilematrix.tilewidth * conv[unit][0]
        tileheight = 0.00028 * scale * tilematrix.tileheight * conv[unit][-1]

        # Calculate tile index of center tile in the right projection
        tilecol = int((center_coord[0] - topleftcorner[0]) / tilewidth)
        tilerow = int((topleftcorner[1] - center_coord[1]) / tileheight)

        return tilecol, tilerow


class WmtsGetTileAll(WmtsGetTile):
    """
    Get WMTS GetTile for all layers.
    """

    NAME = 'WMTS GetTile for all layers.'
    DESCRIPTION = """
    WMTS GetTile for all layers.
    """

    PARAM_DEFS = Plugin.merge(WmtsGetTile.PARAM_DEFS, {})
    """Param defs"""

    def __init__(self):
        WmtsGetTile.__init__(self)
        self.wmts = None
        self.layers = None

    # Overridden: expand param-ranges from WMTS metadata
    def expand_params(self, resource):
        # Use WMTS Capabilities doc to get metadata for
        # PARAM_DEFS ranges/defaults
        try:
            self.PARAM_DEFS['kvprest']['range'] = self.test_kvp_rest()

            self.PARAM_DEFS['layers'] = {
                'type': 'stringlist',
                'description': 'All WMTS layers',
                'value': ['All layers']
            }

            wmts = self.get_metadata_cached(resource, version='1.0.0')

            layers = wmts.contents
            self.PARAM_DEFS['layers']['range'] = list(layers.keys())
            
            for layer in layers:
                layer_object = layers[layer]
                break

            bbox84 = layer_object.boundingBoxWGS84
            center_coord_84 = [(bbox84[0] + bbox84[2]) / 2,
                               (bbox84[1] + bbox84[3]) / 2]

            self.PARAM_DEFS['latitude_4326']['default'] = center_coord_84[1]
            self.PARAM_DEFS['longitude_4326']['default'] = center_coord_84[0]

        except Exception as err:
            raise err

    def before_request(self):
        """ Before request to service, overridden from base class"""

        # Get capabilities doc to get all layers
        try:
            self.wmts = self.get_metadata_cached(self._resource,
                                                 version='1.0.0')

        except Exception as err:
            self.result.set(False, str(err))

        self.REQUEST_TEMPLATE = self.REQUEST_TEMPLATE[
            self._parameters['kvprest']]

        self.layers = self.wmts.contents
