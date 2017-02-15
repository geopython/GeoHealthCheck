from GeoHealthCheck.proberunner import ProbeRunner


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
            'function': 'GeoHealthCheck.checks.xml_parse'
        },
        {
            'name': 'contains TileMap',
            'description': 'find TileMap(s) element in capabilities response doc',
            'function': 'GeoHealthCheck.checks.contains_string',
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
    REQUEST_PARAMETERS = [
        {
            'name': 'layer',
            'type': 'string'
        },
        {
            'name': 'zoom',
            'type': 'string'
        },
        {
            'name': 'x',
            'type': 'string'
        },
        {
            'name': 'y',
            'type': 'string'
        },
        {
            'name': 'extension',
            'type': 'string'
        }
    ]

    RESPONSE_CHECKS = [
        {
            'name': 'has content type',
            'description': 'checks if response content type matches',
            'function': 'GeoHealthCheck.checks.http_has_content_type',
            'parameters': [
                {
                    'name': 'value',
                    'type': 'string'
                }
            ]
        }
    ]


class TmsGetTileTop(TmsGetTile):
    """
    ProbeRunner for TMS main GetTile operation assuming
    toplevel tile 0/0/0.{extension}. No parameters except layername
    and extension and HTTP content type for Check needed.
    """

    NAME = 'TMS Get Top Level Tile'
    DESCRIPTION = 'fetch TMS top level tile and check if appropriate content type'

    # e.g. http://geodata.nationaalgeoregister.nl/tms/.0.0/brtachtergrondkaart/0/0/0.png
    REQUEST_PARAMETERS = [
        {
            'name': 'layer',
            'type': 'string'
        },
        {
            'name': 'zoom',
            'type': 'string',
            'value': '0'
        },
        {
            'name': 'x',
            'type': 'string',
            'value': '0'
        },
        {
            'name': 'y',
            'type': 'string',
            'value': '0'
        },
        {
            'name': 'extension',
            'type': 'string'
        }
    ]
