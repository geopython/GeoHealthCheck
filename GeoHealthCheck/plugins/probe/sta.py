from GeoHealthCheck.probe import Probe
from GeoHealthCheck.plugin import Plugin
from GeoHealthCheck.plugins.probe.http import HttpGet


class StaCaps(Probe):
    """Probe for SensorThings API main endpoint url"""

    NAME = 'STA Capabilities'
    DESCRIPTION = 'Perform STA Capabilities Operation and check validity'
    RESOURCE_TYPE = 'OGC:STA'

    REQUEST_METHOD = 'GET'

    def __init__(self):
        Probe.__init__(self)

    PARAM_DEFS = Plugin.merge(HttpGet.PARAM_DEFS, {})
    """Param defs"""

    CHECKS_AVAIL = {
        'GeoHealthCheck.plugins.check.checks.HttpStatusNoError': {
            'default': True
        },
        'GeoHealthCheck.plugins.check.checks.JsonParse': {
            'default': True
        },
        'GeoHealthCheck.plugins.check.checks.ContainsStrings': {
            'default': True,
            'set_params': {
                'strings': {
                    'name': 'Must contain STA Entity names',
                    'value': ['Things', 'Datastreams', 'Observations',
                              'FeaturesOfInterest', 'Locations']
                }
            }
        },
    }
    """
    Checks avail for all specific Caps checks.
    Optionally override Check.PARAM_DEFS using set_params
    e.g. with specific `value` or even `name`.
    """


class StaGetEntities(Probe):
    """Fetch STA entities of type and check result"""

    NAME = 'STA GetEntities'
    DESCRIPTION = 'Fetch all STA Entities of given type'
    RESOURCE_TYPE = 'OGC:STA'

    REQUEST_METHOD = 'GET'

    # e.g. http://52.26.56.239:8080/OGCSensorThings/v1.0/Things
    REQUEST_TEMPLATE = '/{entities}'

    def __init__(self):
        Probe.__init__(self)

    PARAM_DEFS = Plugin.merge(StaCaps.PARAM_DEFS, {
        'entities': {
            'type': 'string',
            'description': 'The STA Entity collection type',
            'default': 'Things',
            'required': True,
            'range': ['Things', 'DataStreams', 'Observations',
                      'Locations', 'Sensors', 'FeaturesOfInterest',
                      'ObservedProperties', 'HistoricalLocations']
        }
    })
    """Param defs"""

    CHECKS_AVAIL = {
        'GeoHealthCheck.plugins.check.checks.HttpStatusNoError': {
            'default': True
        },
        'GeoHealthCheck.plugins.check.checks.JsonParse': {
            'default': True
        }
    }
    """Check for STA Get entity Collection"""
