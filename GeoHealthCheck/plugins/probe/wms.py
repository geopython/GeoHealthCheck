from GeoHealthCheck.probe import Probe


class WmsGetMapV1(Probe):
    """
    Get WMS map image using the WMS GetMap operation.
    """

    NAME = 'WMS GetMap WMS v1.1.1. operation'
    DESCRIPTION = 'Do WMS GetMap v1.1.1 request with user-specified parameters'
    RESOURCE_TYPE = 'OGC:WMS'

    REQUEST_METHOD = 'GET'
    REQUEST_TEMPLATE = '?SERVICE=WMS&VERSION=1.1.1&' + \
                       'REQUEST=GetMap&LAYERS={layers}&SRS={srs}&' + \
                       'BBOX={bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}&' + \
                       'WIDTH={width}&HEIGHT={height}&FORMAT={format}' + \
                       '&STYLES={styles}&EXCEPTIONS={exceptions}'

    def __init__(self):
        Probe.__init__(self)

    PARAM_DEFS = {
        'layers': {
            'type': 'stringlist',
            'description': 'The WMS Layers, comma separated',
            'default': [],
            'required': True,
            'range': None
        },
        'srs': {
            'type': 'string',
            'description': 'The SRS as EPSG: code',
            'default': 'EPSG:4326',
            'required': True,
            'range': None
        },
        'bbox': {
            'type': 'bbox',
            'description': 'The WMS bounding box',
            'default': ['-180', '-90', '180', '90'],
            'required': True,
            'range': None
        },
        'width': {
            'type': 'string',
            'description': 'The image width',
            'default': '256',
            'required': True
        },
        'height': {
            'type': 'string',
            'description': 'The image height',
            'default': '256',
            'required': True
        },
        'format': {
            'type': 'string',
            'description': 'The image format',
            'default': 'image/png',
            'required': True
        },
        'styles': {
            'type': 'string',
            'description': 'The Styles to apply',
            'default': None,
            'required': False
        },
        'exceptions': {
            'type': 'string',
            'description': 'The Exception format to use',
            'default': 'application/vnd.ogc.se_xml',
            'required': True
        }

    }
    """Param defs"""

    CHECKS_AVAIL = {
        'GeoHealthCheck.plugins.check.checks.HttpHasImageContentType': {},
        'GeoHealthCheck.plugins.check.checks.NotContainsOwsException': {}
    }
    """
    Checks for WMS GetMap Response available.
    Optionally override Check PARAM_DEFS using set_params
    e.g. with specific `value` or even `name`.
    """
