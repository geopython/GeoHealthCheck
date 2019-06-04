from owslib.wfs import WebFeatureService

from GeoHealthCheck.probe import Probe
from GeoHealthCheck.result import Result


class WFS3Drilldown(Probe):
    """
    Probe for WFS3 endpoint "drilldown": starting
    with top endpoint: get Collections and do
    GetItems on them etc. Using OWSLib.WebFeatureService.

    TODO: needs finalization.
    """

    NAME = 'WFS3 Drilldown'
    DESCRIPTION = 'Traverses a OGC WFS3 (REST) API endpoint by drilling down'
    RESOURCE_TYPE = 'OGC:WFS3'

    REQUEST_METHOD = 'GET'

    # PARAM_DEFS = {
    #     'drilldown_level': {
    #         'type': 'string',
    #         'description': 'How heavy the drilldown should be.',
    #         'default': 'minor',
    #         'required': True,
    #         'range': ['minor', 'moderate', 'full']
    #     }
    # }
    """Param defs"""

    def __init__(self):
        Probe.__init__(self)

    def perform_request(self):
        """
        Perform the drilldown.
        See https://github.com/geopython/OWSLib/blob/
        master/tests/doctests/wfs3_GeoServerCapabilities.txt
        """
        wfs3 = None
        collections = None

        # 1. Test top endpoints existence
        result = Result(True, 'Test Top Endpoints')
        result.start()
        try:
            wfs3 = WebFeatureService(self._resource.url, version='3.0')
            wfs3.conformance()
            collections = wfs3.collections()
        except Exception as err:
            result.set(False, str(err))

        result.stop()
        self.result.add_result(result)

        # 2. Test layers
        # TODO: use parameters to work on less/more drilling
        # "full" could be all layers.
        result = Result(True, 'Test Collections')
        result.start()
        coll_name = ''
        try:
            for collection in collections:
                coll_name = collection['name']
                coll_name = coll_name.encode('utf-8')

                try:
                    items = wfs3.collection_items(coll_name, limit=2)
                except Exception as e:
                    msg = 'GetItems %s: OWSLib err: %s ' % (str(e), coll_name)
                    result = self.add_result(result,
                                             False, msg, 'Test GetItems')
                    continue

                features = items.get('features', None)
                if not features:
                    msg = 'GetItems %s: No features attr' % coll_name
                    result = self.add_result(result,
                                             False, msg, 'Test GetItems')
                    continue

                if len(items['features']) > 0:

                    fid = items['features'][0]['id']
                    try:
                        item = wfs3.collection_item(coll_name, fid)
                    except Exception as e:
                        msg = 'GetItem %s: OWSLib err: %s' \
                              % (str(e), coll_name)
                        result = self.add_result(result,
                                                 False, msg, 'Test GetItem')
                        continue

                    for attr in ['id', 'links', 'properties', 'type']:
                        val = item.get(attr, None)
                        if not val:
                            msg = '%s:%s no attr=%s' \
                                  % (coll_name, str(fid), attr)
                            result = self.add_result(
                                result, False, msg, 'Test GetItem')
                            continue

        except Exception as err:
            result.set(False, 'Collection err: %s : e=%s'
                       % (coll_name, str(err)))

        result.stop()

        # Add to overall Probe result
        self.result.add_result(result)

    def add_result(self, result, val, msg, new_result_name):
        result.set(val, msg)
        result.stop()
        self.result.add_result(result)
        result = Result(True, new_result_name)
        result.start()
        return result

# class WFS3Caps(Probe):
#     """Probe for OGC WFS3 API main endpoint url"""
#
#     NAME = 'OGC WFS3 API Capabilities'
#     DESCRIPTION = 'Perform OGC WFS3 API Capabilities
#     Operation and check validity'
#     RESOURCE_TYPE = 'OGC:WFS3'
#
#     REQUEST_METHOD = 'GET'
#
#     # e.g. https://demo.pygeoapi.io/master/collections?f=json
#     REQUEST_TEMPLATE = '/{endpoint}?f=json'
#
#     def __init__(self):
#         Probe.__init__(self)
#
#     PARAM_DEFS = {
#         'endpoint': {
#             'type': 'string',
#             'description': 'The OGC WFS3 API service endpoint type',
#             'default': '/collections',
#             'required': True,
#             'range': ['collections', 'conformance', 'api']
#         }
#     }
#     """Param defs"""
#
#     CHECKS_AVAIL = {
#         'GeoHealthCheck.plugins.check.checks.HttpStatusNoError': {
#             'default': True
#         },
#         'GeoHealthCheck.plugins.check.checks.JsonParse': {
#             'default': True
#         }
#     }
#     """Check for OGC WFS3 API OGC WFS3 API service endpoint
#     availability"""
#
#
# class WFS3Collection(Probe):
#     """Probe for OGC WFS3 API main endpoint url"""
#
#     NAME = 'OGC WFS3 API Capabilities'
#     DESCRIPTION = 'Perform OGC WFS3 API Capabilities Operation and
#     check validity'
#     RESOURCE_TYPE = 'OGC:WFS3'
#
#     REQUEST_METHOD = 'GET'
#
#     def __init__(self):
#         Probe.__init__(self)
#
#     CHECKS_AVAIL = {
#         'GeoHealthCheck.plugins.check.checks.HttpStatusNoError': {
#             'default': True
#         },
#         'GeoHealthCheck.plugins.check.checks.JsonParse': {
#             'default': True
#         },
#         'GeoHealthCheck.plugins.check.checks.ContainsStrings': {
#             'default': True,
#             'set_params': {
#                 'strings': {
#                     'name': 'Must contain links to at least WFS3 Collections,
#                     Conformance and OpenAPI endpoint',
#                     'value': ['links', 'href', '/collections',
#                     '/conformance', '/api']
#                 }
#             }
#         },
#     }
#     """
#     Checks avail for all specific Caps checks.
#     Optionally override Check.PARAM_DEFS using set_params
#     e.g. with specific `value` or even `name`.
#     """
