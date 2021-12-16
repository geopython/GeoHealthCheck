from GeoHealthCheck.probe import Probe
import math
from pyproj import CRS, Transformer


class TileJSON(Probe):
    """
    TileJSON
    """

    NAME = 'TileJSON'
    DESCRIPTION = 'Request Mapbox TileJSON Service and ' + \
                  'request each zoom level at center coordinates'
    RESOURCE_TYPE = 'Mapbox:TileJSON'
    REQUEST_METHOD = 'GET'

    CHECKS_AVAIL = {
        'GeoHealthCheck.plugins.check.checks.HttpStatusNoError': {
            'default': True
        },
    }
    """Checks avail"""

    PARAM_DEFS = {
        'lat_4326': {
            'type': 'float',
            'description': 'latitude in EPSG:4326',
            'required': False
        },
        'lon_4326': {
            'type': 'float',
            'description': 'longitude in EPSG:4326',
            'required': False
        },
    }

    def perform_request(self):
        url_base = self._resource.url

        # Remove trailing '/' if present
        if url_base.endswith('/'):
            url_base = url_base[0:-2]

        # Add .json to url if not present yet
        if url_base.endswith('.json'):
            json_url = url_base
        else:
            json_url = url_base + '.json'

        self.log('Requesting: %s url=%s' % (self.REQUEST_METHOD, json_url))
        self.response = Probe.perform_get_request(self, json_url)
        self.run_checks()

        tile_info = self.response.json()

        if self._parameters['lat_4326'] and self._parameters['lon_4326']:
            lat = self._parameters['lat_4326']
            lon = self._parameters['lon_4326']
        else:
            if 'center' in tile_info:
                lat, lon = tile_info['center'][1], tile_info['center'][0]

            elif 'bounds' in tile_info:
                lat = (tile_info['bounds'][1] + tile_info['bounds'][3]) / 2
                lon = (tile_info['bounds'][0] + tile_info['bounds'][2]) / 2
            else:    
                err_message = 'No center coordinates given in ' + \
                              'tile.json. Please add lat/lon as ' + \
                              'probe parameters.'
                self.result.set(False, err_message)
                return

        # Convert bound coordinates to WebMercator
        transformer = Transformer.from_crs(CRS('EPSG:4326'),
                                           CRS('EPSG:3857'),
                                           always_xy=False)
        wm_coords = transformer.transform(lat, lon)

        # Circumference (2 * pi * Semi-major Axis)
        circ = 2 * math.pi * 6378137.0

        # For calculating the relative tile index for zoom levels
        x_rel = (circ / 2 + wm_coords[0]) / circ
        y_rel = (circ / 2 - wm_coords[1]) / circ

        for tile_url in tile_info['tiles']:
            zoom_list = range(tile_info.get('minzoom', 0),
                              tile_info.get('maxzoom', 22) + 1)

            for zoom in zoom_list:
                tile_count = 2 ** zoom
                zxy = {
                    'z': zoom,
                    'x': int(x_rel * tile_count),
                    'y': int(y_rel * tile_count),
                }

                # Determine the tile URL.
                zoom_url = tile_url.format(**zxy)

                self.log('Requesting zoom %s: url=%s' % (zoom, zoom_url))

                self.response = Probe.perform_get_request(self, zoom_url)
                if self.response.status_code == 204:
                    msg = 'Error response 204: No content'
                    self.result.set(False, msg)
                else:
                    self.run_checks()
