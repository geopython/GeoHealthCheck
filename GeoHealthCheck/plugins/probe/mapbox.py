from GeoHealthCheck.probe import Probe
import math


class TileJSON(Probe):
    """
    TileJSON
    """

    NAME = 'TileJSON'
    DESCRIPTION = 'Request Mapbox TileJSON Service and' + \
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
        'check_lat': {
            'type': 'float',
            'description': 'latitude',
            'required': False
        },
        'check_lon': {
            'type': 'float',
            'description': 'longitude',
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

        if not tile_info['tilejson'].startswith('2'):
            self.result.set(False, 'Only versions 2.x.x are supported')

        if self._parameters['check_lat'] and self._parameters['check_lon']:
            lat = self._parameters['check_lat']
            lon = self._parameters['check_lon']
        else:
            center_coords = tile_info['center']

            if not center_coords:
                # Center is optional, if non-existent: get bounds from metadata
                lat = (tile_info['bounds'][1] + tile_info['bounds'][3]) / 2
                lon = (tile_info['bounds'][0] + tile_info['bounds'][2]) / 2
            else:
                lat, lon = center_coords[1], center_coords[0]

        # Convert bound coordinates to WebMercator
        try:
            wm_coords = self.to_wm(lat, lon)
        except Exception as e:
            self.result.set(False, 'Error converting coordinates: %s' % (e))

        # Circumference (2 * pi * Semi-major Axis)
        circ = 2 * math.pi * 6378137.0

        # For calculating the relative tile index for zoom levels
        x_rel = (circ / 2 + wm_coords[0]) / circ
        y_rel = (circ / 2 - wm_coords[1]) / circ

        for tile_url in tile_info['tiles']:
            self.log('Requesting: %s url=%s' % (self.REQUEST_METHOD, tile_url))

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

                self.response = Probe.perform_get_request(self, zoom_url)
                if self.response.status_code == 204:
                    msg = 'Error response 204: No content'
                    self.result.set(False, msg)
                else:
                    self.run_checks()

    # Formula to calculate spherical mercator coordinates.
    def to_wm(self, lat, lon):
        x = 6378137.0 * math.radians(lon)
        scale = x / lon
        y = math.degrees(math.log(math.tan(
            math.pi / 4.0 + math.radians(lat) / 2.0)) * scale)
        return (x, y)
