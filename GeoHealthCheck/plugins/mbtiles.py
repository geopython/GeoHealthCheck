from GeoHealthCheck.probe import Probe
import requests
import math
from pyproj import Proj, transform

class MBTiles(Probe):
    """
    MBTiles
    """

    NAME = 'MBTiles'
    DESCRIPTION = 'MBTiles'
    RESOURCE_TYPE = 'MBTiles'
    REQUEST_METHOD = 'GET'

    CHECKS_AVAIL = {
        'GeoHealthCheck.plugins.check.checks.HttpStatusNoError': {
            'default': True
        },
        # 'GeoHealthCheck.plugins.check.checks.HttpHasHeaderValue': {
        #     'default': True
        # },
    }
    """Checks avail"""

    def perform_request(self):
        url_base = self._resource.url

        # Remove trailing '/' if present
        if url_base[-1] == '/':
            url_base = url_base[0:-2]

        try:
            json_url = url_base + '.json'
            self.log('Requesting: %s url=%s' % (self.REQUEST_METHOD, json_url))
            self.response = Probe.perform_get_request(self, json_url)
            self.check_response()
        except requests.exceptions.RequestException as e:
            msg = "Request Err: %s %s" % (e.__class__.__name__, str(e))
            self.result.set(False, msg)

        tile_info = self.response.json()

        # Get bounds from metadata
        lat = (tile_info['bounds'][1] + tile_info['bounds'][3]) / 2
        lon = (tile_info['bounds'][0] + tile_info['bounds'][2]) / 2

        # Convert bound coordinates to WebMercator
        wm_coords = self.to_wm(lat, lon)

        # Circumference (2 * pi * Semi-major Axis)
        circ = 2 * math.pi * 6378137.0  

        # For calculate the relative tile index for zoom levels
        x_rel = (circ / 2 + wm_coords[0]) / circ
        y_rel = (circ / 2 - wm_coords[1]) / circ

        for tile_url in tile_info['tiles']:
            self.log('Requesting: %s url=%s' % (self.REQUEST_METHOD, tile_url))

            for zoom in range(tile_info['minzoom'], tile_info['maxzoom'] + 1):
                tile_count = 2 ** zoom
                zxy = {
                    'z': zoom,
                    'x': int(x_rel * tile_count),
                    'y': int(y_rel * tile_count),
                }

                # Determine the tile URL.
                zoom_url = tile_url.format(**zxy)

                try:
                    self.response = Probe.perform_get_request(self, zoom_url)
                    self.run_checks()
                except requests.exceptions.RequestException as e:
                    msg = "Request Err: %s %s" % (e.__class__.__name__, str(e))
                    self.result.set(False, msg)

    def check_response(self):
        if self.response:
            self.log('response: status=%d' % self.response.status_code)
            if self.response.status_code / 100 in [4, 5]:
                self.log('Error response: %s' % (str(self.response.text)))

    # Formula to calculate spherical mercator coordinates.
    # Beware the axis order. When dealing with geodetic coordinates (latitude/longitude), it is
    # customary to call these in this order, although when treating them as XY, both values should be
    # swapped.
    def to_wm(self, lat, lon):
        x = 6378137.0 * math.radians(lon)
        scale = x / lon
        y = math.degrees(math.log(math.tan(math.pi / 4.0 + math.radians(lat) / 2.0)) * scale)
        return (x, y)