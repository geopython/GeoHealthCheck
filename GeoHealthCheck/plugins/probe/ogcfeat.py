from owslib.ogcapi.features import Features
from openapi_spec_validator import openapi_v3_spec_validator

from GeoHealthCheck.probe import Probe
from GeoHealthCheck.result import Result, push_result


class OGCFeatCaps(Probe):
    """Probe for OGC API - Features endpoint url"""

    NAME = 'OGC API Features (OAFeat) Capabilities'
    DESCRIPTION = 'Validate OGC API Features (OAFeat) ' \
                  'endpoint landing page'
    RESOURCE_TYPE = 'OGCFeat'

    REQUEST_METHOD = 'GET'
    REQUEST_HEADERS = {'Accept': 'application/json'}

    # e.g. https://demo.pygeoapi.io/master
    REQUEST_TEMPLATE = ''

    def __init__(self):
        Probe.__init__(self)

    CHECKS_AVAIL = {
        'GeoHealthCheck.plugins.check.checks.HttpStatusNoError': {
            'default': True
        },
        'GeoHealthCheck.plugins.check.checks.JsonParse': {
            'default': True
        },
        'GeoHealthCheck.plugins.check.checks.ContainsStrings': {
            'set_params': {
                'strings': {
                    'name': 'Contains required strings',
                    'value': ['/conformance', '/collections',
                              'service', 'links']
                }
            },
            'default': True
        },
    }
    """Validate OGC API Features (OAFeat) endpoint landing page"""


def type_for_link(links, rel):
    content_type = 'application/json'
    for link in links:
        if link['rel'] == rel:
            content_type = link.get('type', content_type)
            # We only want JSON content types (e.g. items)
            # for OWSLib for now.
            if 'json' in content_type:
                break
    return content_type


def set_accept_header(oa_feat, content_type):
    oa_feat.headers['Accept'] = content_type


class OGCFeatDrilldown(Probe):
    """
    Probe for OGC API Features (OAFeat) endpoint "drilldown" or
    "crawl": starting with top endpoint: get Collections and fetch
    Features on them etc. Uses the OWSLib owslib.ogcapi package.
    """

    NAME = 'OGC API Features (OAFeat) Drilldown'
    DESCRIPTION = 'Traverses an OGC API Features (OAFeat) API ' \
                  'endpoint by drilling down'
    RESOURCE_TYPE = 'OGCFeat'

    REQUEST_METHOD = 'GET'
    REQUEST_HEADERS = {'Accept': 'application/json'}

    PARAM_DEFS = {
        'drilldown_level': {
            'type': 'string',
            'description': 'How thorough the drilldown should be.\
                            basic: test presence endpoints, \
                            full: go through collections, fetch Features',
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
        oa_feat = None
        collections = None

        # 1.1 Test Landing Page
        result = Result(True, 'Test Landing Page')
        result.start()
        try:
            oa_feat = Features(self._resource.url,
                               headers=self.get_request_headers())
        except Exception as err:
            result.set(False, '%s:%s' % (result.message, str(err)))

        result.stop()
        self.result.add_result(result)

        # 1.2 Test top endpoints existence: /conformance
        result = Result(True, 'conformance endpoint exists')
        result.start()
        try:
            set_accept_header(oa_feat, type_for_link(
                oa_feat.links, 'conformance'))
            oa_feat.conformance()
        except Exception as err:
            result.set(False, str(err))

        result.stop()
        self.result.add_result(result)

        # 1.3 Test top endpoints existence: /collections
        result = Result(True, 'Get collections')
        result.start()
        try:
            set_accept_header(oa_feat, type_for_link(
                oa_feat.links, 'data'))
            collections = oa_feat.collections()['collections']
        except Exception as err:
            result.set(False, '%s:%s' % (result.message, str(err)))

        result.stop()
        self.result.add_result(result)

        # 1.4 Test top endpoints existence: OpenAPI doc
        result = Result(True, 'Test OpenAPI Doc')
        result.start()
        try:

            # OWSLib 0.20.0+ has call to '/api now.
            set_accept_header(oa_feat, type_for_link(
                oa_feat.links, 'service-desc'))
            api_doc = oa_feat.api()
            for attr in ['components', 'paths', 'openapi']:
                val = api_doc.get(attr, None)
                if val is None:
                    msg = 'missing attr: %s' % attr
                    result = push_result(
                        self, result, False, msg, 'Test OpenAPI doc')
                    continue
        except Exception as err:
            result.set(False, '%s:%s' % (result.message, str(err)))

        result.stop()
        self.result.add_result(result)

        if self._parameters['drilldown_level'] == 'basic':
            return

        # ASSERTION: will do full drilldown, level 2, from here

        # 2. Test layers
        # TODO: use parameters to work on less/more drilling
        # "full" could be all layers.
        result = Result(True, 'Test Collections')
        result.start()
        coll_id = ''
        try:
            for collection in collections:
                coll_id = collection['id']
                coll_id = coll_id

                try:
                    set_accept_header(oa_feat, type_for_link(
                        collection['links'], 'self'))
                    coll = oa_feat.collection(coll_id)

                    # TODO: Maybe also add crs
                    for attr in ['id', 'links']:
                        val = coll.get(attr, None)
                        if val is None:
                            msg = '%s: missing attr: %s' \
                                  % (coll_id, attr)
                            result = push_result(
                                self, result, False, msg, 'Test Collection')
                            continue
                except Exception as e:
                    msg = 'GetCollection %s: OWSLib err: %s ' \
                          % (str(e), coll_id)
                    result = push_result(
                        self, result, False, msg, 'Test GetCollection')
                    continue

                try:
                    set_accept_header(oa_feat, 'application/geo+json')
                    items = oa_feat.collection_items(coll_id, limit=1)
                except Exception as e:
                    msg = 'GetItems %s: OWSLib err: %s ' % (str(e), coll_id)
                    result = push_result(
                        self, result, False, msg, 'Test GetItems')
                    continue

                features = items.get('features', None)
                if features is None:
                    msg = 'GetItems %s: No features attr' % coll_id
                    result = push_result(
                        self, result, False, msg, 'Test GetItems')
                    continue

                type = items.get('type', '')
                if type != 'FeatureCollection':
                    msg = '%s:%s type not FeatureCollection: %s' \
                          % (coll_id, type, val)
                    result = push_result(
                        self, result, False, msg, 'Test GetItems')
                    continue

                if len(items['features']) > 0:

                    fid = items['features'][0]['id']
                    try:
                        item = oa_feat.collection_item(coll_id, fid)
                    except Exception as e:
                        msg = 'GetItem %s: OWSLib err: %s' \
                              % (str(e), coll_id)
                        result = push_result(
                            self, result, False, msg, 'Test GetItem')
                        continue

                    for attr in \
                            ['id', 'links', 'properties', 'geometry', 'type']:
                        val = item.get(attr, None)
                        if val is None:
                            msg = '%s:%s missing attr: %s' \
                                  % (coll_id, str(fid), attr)
                            result = push_result(
                                self, result, False, msg, 'Test GetItem')
                            continue

                        if attr == 'type' and val != 'Feature':
                            msg = '%s:%s type not Feature: %s' \
                                  % (coll_id, str(fid), val)
                            result = push_result(
                                self, result, False, msg, 'Test GetItem')
                            continue

        except Exception as err:
            result.set(False, 'Collection err: %s : e=%s'
                       % (coll_id, str(err)))

        result.stop()

        # Add to overall Probe result
        self.result.add_result(result)


class OGCFeatOpenAPIValidator(Probe):
    """
    Probe for OGC API Features (OAFeat) OpenAPI Document Validation.
    Uses https://pypi.org/project/openapi-spec-validator/.

    """

    NAME = 'OGC API Features (OAFeat) OpenAPI Validator'
    DESCRIPTION = 'Validates OGC API Features (OAFeat) api endpoint for ' \
                  'OpenAPI compliance'
    RESOURCE_TYPE = 'OGCFeat'
    REQUEST_HEADERS = {'Accept': 'application/json'}

    REQUEST_METHOD = 'GET'

    """Param defs"""

    def __init__(self):
        Probe.__init__(self)

    def perform_request(self):
        """
        Perform the validation.
        Uses https://github.com/p1c2u/openapi-spec-validator on
        the specfile (dict) returned from the OpenAPI endpoint.
        """

        # Step 1 basic sanity check
        result = Result(True, 'OpenAPI Sanity Check')
        result.start()
        api_doc = None
        try:
            oa_feat = Features(self._resource.url,
                               headers=self.get_request_headers())

            set_accept_header(oa_feat, type_for_link(
                oa_feat.links, 'service-desc'))
            api_doc = oa_feat.api()

            # Basic sanity check
            for attr in ['components', 'paths', 'openapi']:
                val = api_doc.get(attr, None)
                if val is None:
                    msg = 'OpenAPI doc: missing attr: %s' % attr
                    result.set(False, msg)
                    break
        except Exception as err:
            result.set(False, '%s:%s' % (result.message, str(err)))

        result.stop()
        self.result.add_result(result)

        # No use to proceed if OpenAPI basics not complied
        if api_doc is None or result.success is False:
            return

        # ASSERTION: OpenAPI doc exists, next OpenAPI Validation

        # Step 2 detailed OpenAPI Compliance test
        result = Result(True, 'Validate OpenAPI Compliance')
        result.start()
        try:
            # Call the openapi-spec-validator and iterate through errors
            errors_iterator = openapi_v3_spec_validator.iter_errors(api_doc)
            for error in errors_iterator:
                # Add each validation error as separate Result object
                result = push_result(
                    self, result, False,
                    str(error), 'OpenAPI Compliance Result')
        except Exception as err:
            result.set(False, '%s:%s' % (result.message, str(err)))

        result.stop()

        # Add to overall Probe result
        self.result.add_result(result)


# class OGCAPIFeaturesCollection(Probe):
#     """Probe for OGC API Features (OAFeat) - Features Collection endpoint"""
#
#     NAME = 'OGC API Features Collection'
#     DESCRIPTION = 'Validate an OGC API Features Collection'
#     RESOURCE_TYPE = 'OGCFeat'
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
#                     'name': 'Must contain links to at least Feature'
#                             'Collections, Conformance and OpenAPI
#                             endpoint',
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
#
#     # Overridden: expand param-ranges from WMS metadata
#     def expand_params(self, resource):
#
#         # Use WMS Capabilities doc to get metadata for
#         # PARAM_DEFS ranges/defaults
#         try:
#             wms = self.get_metadata_cached(resource, version='1.1.1')
#             layers = wms.contents
#             self.layer_count = len(layers)
#
#             # Layers to select
#             self.PARAM_DEFS['layers']['range'] = list(layers.keys())
#
#             # Image Format
#             for oper in wms.operations:
#                 if oper.name == 'GetMap':
#                     self.PARAM_DEFS['format']['range'] = \
#                         oper.formatOptions
#                     break
#
#             # Take random layer to determine generic attrs
#             for layer_name in layers:
#                 layer_entry = layers[layer_name]
#                 break
#
#             # SRS
#             srs_range = layer_entry.crsOptions
#             self.PARAM_DEFS['srs']['range'] = srs_range
#
#             # bbox list: 0-3 is bbox, 4 is SRS
#             bbox = layer_entry.boundingBox
#             bbox_srs = bbox[4]
#             self.PARAM_DEFS['srs']['default'] = bbox_srs
#             # if it is not EPSG:4326 we need to transform bbox
#             # if bbox_srs != 'EPSG:4326':
#             #     bbox = transform_bbox('EPSG:4326', bbox_srs, bbox[:-1])
#
#             self.PARAM_DEFS['bbox']['default'] = \
#                 [str(x) for x in bbox[:-1]]
#
#             self.PARAM_DEFS['exceptions']['range'] = wms.exceptions
#         except Exception as err:
#             raise err
