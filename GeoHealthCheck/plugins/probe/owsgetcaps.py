from GeoHealthCheck.plugin import Plugin
from GeoHealthCheck.probe import Probe


class OwsGetCaps(Probe):
    """
    Fetch OWS capabilities doc
    """

    AUTHOR = 'GHC Team'
    NAME = 'OWS GetCapabilities'
    DESCRIPTION = 'Perform GetCapabilities Operation and check validity'
    # Abstract Base Class for OGC OWS GetCaps Probes
    # Needs specification in subclasses
    # RESOURCE_TYPE = 'OGC:ABC'

    REQUEST_METHOD = 'GET'
    REQUEST_TEMPLATE = \
        '?SERVICE={service}&VERSION={version}&REQUEST=GetCapabilities'

    PARAM_DEFS = {
        'service': {
            'type': 'string',
            'description': 'The OWS service within resource endpoint',
            'default': None,
            'required': True
        },
        'version': {
            'type': 'string',
            'description': 'The OWS service version within resource endpoint',
            'default': None,
            'required': True,
            'range': None
        }
    }
    """Param defs, to be specified in subclasses"""

    CHECKS_AVAIL = {
        'GeoHealthCheck.plugins.check.checks.HttpStatusNoError': {
            'default': True
        },
        'GeoHealthCheck.plugins.check.checks.XmlParse': {
            'default': True
        },
        'GeoHealthCheck.plugins.check.checks.NotContainsOwsException': {
            'default': True
        },
        'GeoHealthCheck.plugins.check.checks.ContainsStrings': {
            'set_params': {
                'strings': {
                    'name': 'Contains Title Element',
                    'value': ['Title>']
                }
            },
            'default': True
        },
    }
    """
    Checks avail for all specific Caps checks.
    Optionally override Check PARAM_DEFS using set_params
    e.g. with specific `value`.
    """


class WmsGetCaps(OwsGetCaps):
    """Fetch WMS capabilities doc"""

    NAME = 'WMS GetCapabilities'
    RESOURCE_TYPE = 'OGC:WMS'

    PARAM_DEFS = Plugin.merge(OwsGetCaps.PARAM_DEFS, {

        'service': {
            'value': 'WMS'
        },
        'version': {
            'default': '1.3.0',
            'range': ['1.1.1', '1.3.0']
        }
    })
    """Param defs"""


class WfsGetCaps(OwsGetCaps):
    """WFS GetCapabilities Probe"""

    NAME = 'WFS GetCapabilities'
    RESOURCE_TYPE = 'OGC:WFS'

    def __init__(self):
        OwsGetCaps.__init__(self)

    PARAM_DEFS = Plugin.merge(OwsGetCaps.PARAM_DEFS, {
        'service': {
            'value': 'WFS'
        },
        'version': {
            'default': '1.1.0',
            'range': ['1.0.0', '1.1.0', '2.0.2']
        }
    })
    """Param defs"""


class WcsGetCaps(OwsGetCaps):
    """WCS GetCapabilities Probe"""

    NAME = 'WCS GetCapabilities'
    RESOURCE_TYPE = 'OGC:WCS'

    PARAM_DEFS = Plugin.merge(OwsGetCaps.PARAM_DEFS, {
        'service': {
            'value': 'WCS'
        },
        'version': {
            'default': '1.1.0',
            'range': ['1.1.0', '1.1.1', '2.0.1']
        }
    })
    """Param defs"""


class CswGetCaps(OwsGetCaps):
    """CSW GetCapabilities Probe"""

    NAME = 'CSW GetCapabilities'
    RESOURCE_TYPE = 'OGC:CSW'

    PARAM_DEFS = Plugin.merge(OwsGetCaps.PARAM_DEFS, {
        'service': {
            'value': 'CSW'
        },
        'version': {
            'default': '2.0.2',
            'range': ['2.0.2']
        }
    })
    """Param defs"""


class WmtsGetCaps(OwsGetCaps):
    """WMTS GetCapabilities Probe"""

    NAME = 'WMTS GetCapabilities'
    RESOURCE_TYPE = 'OGC:WMTS'

    def __init__(self):
        OwsGetCaps.__init__(self)

    PARAM_DEFS = Plugin.merge(OwsGetCaps.PARAM_DEFS, {
        'service': {
            'value': 'WMTS'
        },
        'version': {
            'default': '1.0.0',
            'range': ['1.0.0']
        }
    })
    """Param defs"""


class WpsGetCaps(OwsGetCaps):
    """WPS GetCapabilities Probe"""

    NAME = 'WPS GetCapabilities'
    RESOURCE_TYPE = 'OGC:WPS'

    PARAM_DEFS = Plugin.merge(OwsGetCaps.PARAM_DEFS, {
        'service': {
            'value': 'WPS'
        },
        'version': {
            'default': '1.0.0',
            'range': ['1.0.0', '2.0.0']
        }
    })
    """Param defs"""


class SosGetCaps(OwsGetCaps):
    """SOS GetCapabilities Probe"""

    NAME = 'SOS GetCapabilities'
    RESOURCE_TYPE = 'OGC:SOS'

    PARAM_DEFS = Plugin.merge(OwsGetCaps.PARAM_DEFS, {
        'service': {
            'value': 'SOS'
        },
        'version': {
            'default': '1.0.0',
            'range': ['1.0.0', '2.0.0']
        }
    })
    """Param defs"""
