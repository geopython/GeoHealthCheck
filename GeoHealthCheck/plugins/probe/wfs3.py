import requests
from owslib.wfs import WebFeatureService
from openapi_spec_validator import openapi_v3_spec_validator

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

    PARAM_DEFS = {
        'drilldown_level': {
            'type': 'string',
            'description': 'How heavy the drilldown should be.\
                            basic: test presence endpoints, \
                            full: go through collections, fetch items',
            'default': 'basic',
            'required': True,
            'range': ['basic', 'full']
        }
    }
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

            # TODO: OWSLib 0.17.1 has no call to '/api yet.
            url = wfs3._build_url('api')
            api = requests.get(url).json()
            for attr in ['components', 'paths', 'openapi']:
                val = api.get(attr, None)
                if val is None:
                    msg = '/api: missing attr: %s' % attr
                    result = add_result(
                        self, result, False, msg, 'Test Collection')
                    continue

            collections = wfs3.collections()
        except Exception as err:
            result.set(False, str(err))

        result.stop()
        self.result.add_result(result)

        if self._parameters['drilldown_level'] == 'basic':
            return

        # ASSERTION: will do full drilldown from here

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
                    coll = wfs3.collection(coll_name)

                    # TODO: Maybe also add crs
                    for attr in ['name', 'links']:
                        val = coll.get(attr, None)
                        if val is None:
                            msg = '%s: missing attr: %s' \
                                  % (coll_name, attr)
                            result = add_result(
                                self, result, False, msg, 'Test Collection')
                            continue
                except Exception as e:
                    msg = 'GetCollection %s: OWSLib err: %s ' \
                          % (str(e), coll_name)
                    result = add_result(
                        self, result, False, msg, 'Test GetCollection')
                    continue

                try:
                    items = wfs3.collection_items(coll_name, limit=1)
                except Exception as e:
                    msg = 'GetItems %s: OWSLib err: %s ' % (str(e), coll_name)
                    result = add_result(
                        self, result, False, msg, 'Test GetItems')
                    continue

                features = items.get('features', None)
                if features is None:
                    msg = 'GetItems %s: No features attr' % coll_name
                    result = add_result(
                        self, result, False, msg, 'Test GetItems')
                    continue

                type = items.get('type', '')
                if type != 'FeatureCollection':
                    msg = '%s:%s type not FeatureCollection: %s' \
                          % (coll_name, type, val)
                    result = add_result(
                        self, result, False, msg, 'Test GetItems')
                    continue

                if len(items['features']) > 0:

                    fid = items['features'][0]['id']
                    try:
                        item = wfs3.collection_item(coll_name, fid)
                    except Exception as e:
                        msg = 'GetItem %s: OWSLib err: %s' \
                              % (str(e), coll_name)
                        result = add_result(
                            self, result, False, msg, 'Test GetItem')
                        continue

                    for attr in \
                            ['id', 'links', 'properties', 'geometry', 'type']:
                        val = item.get(attr, None)
                        if val is None:
                            msg = '%s:%s missing attr: %s' \
                                  % (coll_name, str(fid), attr)
                            result = add_result(
                                self, result, False, msg, 'Test GetItem')
                            continue

                        if attr == 'type' and val != 'Feature':
                            msg = '%s:%s type not Feature: %s' \
                                  % (coll_name, str(fid), val)
                            result = add_result(
                                self, result, False, msg, 'Test GetItem')
                            continue

        except Exception as err:
            result.set(False, 'Collection err: %s : e=%s'
                       % (coll_name, str(err)))

        result.stop()

        # Add to overall Probe result
        self.result.add_result(result)


class WFS3OpenAPIValidator(Probe):
    """
    Probe for WFS3 OpenAPI Spec Validation (/api endpoint).
    Uses https://pypi.org/project/openapi-spec-validator/.

    """

    NAME = 'WFS3 OpenAPI Validator'
    DESCRIPTION = 'Validates WFS3 /api endpoint for OpenAPI compliance'
    RESOURCE_TYPE = 'OGC:WFS3'

    REQUEST_METHOD = 'GET'

    """Param defs"""

    def __init__(self):
        Probe.__init__(self)

    def perform_request(self):
        """
        Perform the validation.
        See https://github.com/p1c2u/openapi-spec-validator
        """

        # 1. Test basic validation
        result = Result(True, 'Basic API Endpoint Test')
        result.start()
        api_url = None
        api_doc = None
        try:
            wfs3 = WebFeatureService(self._resource.url, version='3.0')

            # TODO: OWSLib 0.17.1 has no call to '/api yet.
            api_url = wfs3._build_url('api')
            api_doc = requests.get(api_url).json()
            for attr in ['components', 'paths', 'openapi']:
                val = api_doc.get(attr, None)
                if val is None:
                    msg = '/api: missing attr: %s' % attr
                    result.set(False, msg)
                    break
        except Exception as err:
            result.set(False, str(err))

        result.stop()
        self.result.add_result(result)

        # No use to proceed if OpenAPI basics not complied
        if api_doc is None or result.success is False:
            return

        # ASSERTION: /api exists, next OpenAPI Validation

        result = Result(True, 'Validate OpenAPI Compliance')
        result.start()
        try:
            # val_result = validate_spec_url(api_url)
            errors_iterator = openapi_v3_spec_validator.iter_errors(api_doc)
            for error in errors_iterator:
                result = add_result(
                    self, result, False,
                    str(error), "OpenAPI Compliance Result")
        except Exception as err:
            result.set(False, 'API Validation err: e=%s' % str(err))

        result.stop()

        # Add to overall Probe result
        self.result.add_result(result)


# Util to quickly add Results and open new one.
def add_result(obj, result, val, msg, new_result_name):
    result.set(val, msg)
    result.stop()
    obj.result.add_result(result)
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
