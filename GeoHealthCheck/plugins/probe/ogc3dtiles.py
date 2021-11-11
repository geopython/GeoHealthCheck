from GeoHealthCheck.probe import Probe
import requests


class OGC3DTiles(Probe):
    """
    OGC3DTiles
    """

    NAME = 'GET Tileset.json and tile data'
    DESCRIPTION = 'Request tileset.json, ' + \
                  'and recursively find and request tile data url'
    RESOURCE_TYPE = 'OGC:3DTiles'
    REQUEST_METHOD = 'GET'

    CHECKS_AVAIL = {
        'GeoHealthCheck.plugins.check.checks.HttpStatusNoError': {
            'default': True
        },
    }
    """Checks avail"""

    def perform_request(self):
        url_base = self._resource.url

        # Remove trailing '/' if present
        if url_base.endswith('/'):
            url_base = url_base[:-1]
        elif url_base.endswith('/tileset.json'):
            url_base = url_base.split('/tileset.json')[0]

        # Request tileset.json
        try:
            tile_url = url_base + '/tileset.json'
            self.log('Requesting: %s url=%s' % (self.REQUEST_METHOD, tile_url))
            self.response = Probe.perform_get_request(self, tile_url)
            self.log('test1')
            self.run_checks()
            self.log('test2')
        except requests.exceptions.RequestException as e:
            msg = "Request Err: Error requesting tileset.json %s %s" \
                % (e.__class__.__name__, str(e))
            self.result.set(False, msg)
            # If error occurs during request of tileset.json, no use going on
            return

        # Get data url from tileset.json and request tile data
        try:
            tile_root = self.response.json()['root']
            data_uri = self.get_3d_tileset_content_uri(tile_root)
            print('DATA URI', data_uri)
            data_url = url_base + '/' + data_uri
            self.log('Requesting: %s url=%s' % (self.REQUEST_METHOD, data_url))
            self.response = Probe.perform_get_request(self, data_url)
            self.run_checks()
        except requests.exceptions.RequestException as e:
            msg = "Request Err: Error requesting tile data %s %s" \
                % (e.__class__.__name__, str(e))
            self.result.set(False, msg)

    def get_3d_tileset_content_uri(self, tile):
        # Use recursion to find tile data url
        for child in tile['children']:
            if 'content' in child:
                return child['content']['uri']

            result = self.get_3d_tileset_content_uri(child)

            return result
