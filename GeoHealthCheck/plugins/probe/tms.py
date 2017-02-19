from GeoHealthCheck.proberunner import ProbeRunner
from GeoHealthCheck.plugin import Parameter


class TmsCaps(ProbeRunner):
    """ProbeRunner for TMS main endpoint url"""

    NAME = 'TMS Capabilities'
    DESCRIPTION = 'fetch TMS main URL and check for keywords'
    RESOURCE_TYPE = 'OSGeo:TMS'

    REQUEST_METHOD = 'GET'

    RESPONSE_CHECKS = [
        {
            'name': 'parse_response',
            'description': 'response is parsable',
            'class': 'GeoHealthCheck.plugins.checkxml_parse'
        },
        {
            'name': 'contains TileMap',
            'description': 'find TileMap(s) element in capabilities response doc',
            'class': 'GeoHealthCheck.plugins.checkcontains_string',
            'parameters': [
                {
                    'name': 'text',
                    'type': 'string',
                    'value': 'TileMap>'
                }
            ]
        }
    ]


class TmsGetTile(ProbeRunner):
    """ProbeRunner for TMS main GetTile operation"""

    NAME = 'TMS GetTile'
    DESCRIPTION = 'fetch TMS tile and check result'
    RESOURCE_TYPE = 'OSGeo:TMS'

    REQUEST_METHOD = 'GET'
    # e.g. http://geodata.nationaalgeoregister.nl/tms/1.0.0/brtachtergrondkaart/1/0/0.png
    REQUEST_TEMPLATE = '/{layer}/{zoom}/{x}/{y}.{extension}'

    @Parameter(ptype=str, default=None, required=True)
    def layer(self):
        """
        The TMS Layer service within resource endpoint.
        Required: True
        Default: None
        """
        pass

    @Parameter(ptype=str, default='0', required=True)
    def zoom(self):
        """
        The tile pyramid zoomlevel.
        Required: True
        Default: None
        """
        pass

    @Parameter(ptype=str, default='0', required=True)
    def x(self):
        """
        The tile x offset.
        Required: True
        Default: None
        """
        pass

    @Parameter(ptype=str, default='0', required=True)
    def y(self):
        """
        The tile y offset.
        Required: True
        Default: None
        """
        pass

    @Parameter(ptype=str, default='png', required=True, range=['png', 'png8', 'png24', 'jpg', 'jpeg', 'tif', 'tiff'])
    def extension(self):
        """
        The tile image extension.
        Required: True
        Default: None
        """
        pass

    RESPONSE_CHECKS = [
        {
            'name': 'has content type',
            'description': 'checks if response content type matches',
            'class': 'GeoHealthCheck.plugins.check.checkers.HttpHasContentType',
            'parameters': [
                {
                    'header_value': 'value',
                    'type': 'string'
                }
            ]
        }
    ]

