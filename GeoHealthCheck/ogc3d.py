from GeoHealthCheck.probe import Probe
import requests


class B3DMTileset(Probe):
    """
    OGC3D
    """

    NAME = 'OGC3D'
    DESCRIPTION = 'OGC3D'
    RESOURCE_TYPE = 'OGC:3D'
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
        if url_base[-1] == '/':
            url_base = url_base[0:-2]

        try:
            tile_url = url_base + '/tileset.json'
            self.log('Requesting: %s url=%s' % (self.REQUEST_METHOD, tile_url))
            self.response = Probe.perform_get_request(self, tile_url)
            self.check_response()
        except requests.exceptions.RequestException as e:
            #msg clear voor welk request
            msg = "Request Err: %s %s" % (e.__class__.__name__, str(e))
            self.result.set(False, msg)

        try:
            data_uri = self.get_3d_tileset_content_uri(self.response.json())
            data_url = url_base + '/' + data_uri
            self.log('Requesting: %s url=%s' % (self.REQUEST_METHOD, data_url))
            self.response = Probe.perform_get_request(self, data_url)
            self.check_response()
        except requests.exceptions.RequestException as e:
            msg = "Request Err: %s %s" % (e.__class__.__name__, str(e))
            self.result.set(False, msg)

    def check_response(self):
        if self.response:
            self.log('response: status=%d' % self.response.status_code)
            if self.response.status_code / 100 in [4, 5]:
                self.log('Error response: %s' % (str(self.response.text)))

    def get_3d_tileset_content_uri(self, tileset_json):
        if 'content' in tileset_json['root']:
            return tileset_json['root']['content']['uri']

        for child in tileset_json['root']['children']:
            if 'content' in child:
                return child['content']['uri']