from GeoHealthCheck.probe import Probe


class TmsCaps(Probe):
    """Probe for TMS main endpoint url"""

    NAME = 'TMS Capabilities'
    DESCRIPTION = 'Perform TMS Capabilities Operation and check validity'
    RESOURCE_TYPE = 'OSGeo:TMS'

    REQUEST_METHOD = 'GET'

    def __init__(self):
        Probe.__init__(self)

    CHECKS_AVAIL = {
        'GeoHealthCheck.plugins.check.checks.XmlParse': {},
        'GeoHealthCheck.plugins.check.checks.ContainsStrings': {
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

    NAME = 'TMS GetTile'
    DESCRIPTION = 'Fetch single, user-specified, TMS-tile and check validity'
    RESOURCE_TYPE = 'OSGeo:TMS'

    REQUEST_METHOD = 'GET'

    # e.g. http://geodata.nationaalgeoregister.nl/tms/1.0.0/
    # brtachtergrondkaart/1/0/0.png
    REQUEST_TEMPLATE = '/{layer}/{zoom}/{x}/{y}.{extension}'

    def __init__(self):
        Probe.__init__(self)

    PARAM_DEFS = {
        'layer': {
            'type': 'string',
            'description': 'The TMS Layer within resource endpoint',
            'default': None,
            'required': True
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
            'range': ['png', 'png8', 'png24', 'jpg', 'jpeg', 'tif', 'tiff']
        }
    }
    """Param defs"""

    CHECKS_AVAIL = {
        'GeoHealthCheck.plugins.check.checks.HttpHasImageContentType': {}
    }
    """Check for TMS GetTile"""
