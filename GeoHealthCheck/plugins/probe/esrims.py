from GeoHealthCheck.probe import Probe
from GeoHealthCheck.result import Result, push_result


class ESRIMSDrilldown(Probe):
    """
    Probe for ESRI MapServer endpoint "drilldown": starting
    with top /MapServer endpoint: get Layers and get Features on these.
    Test e.g. from https://sampleserver6.arcgisonline.com/arcgis/rest/services
    (at least sampleserver6 is ArcGIS 10.6.1 supporting Paging).
    """

    NAME = 'ESRIMS Drilldown'

    DESCRIPTION = 'Traverses an ESRI MapServer ' \
                  '(REST) API endpoint by drilling down'

    RESOURCE_TYPE = 'ESRI:MS'

    REQUEST_METHOD = 'GET'

    PARAM_DEFS = {
        'drilldown_level': {
            'type': 'string',
            'description': 'How heavy the drilldown should be.\
                            basic: test presence of Capabilities, \
                            full: go through Layers, get Features',
            'default': 'basic',
            'required': True,
            'range': ['basic', 'full']
        }
    }
    """Param defs"""

    def __init__(self):
        Probe.__init__(self)

    def get_request_headers(self):
        headers = Probe.get_request_headers(self)

        # Clear possibly dangling ESRI header
        # https://github.com/geopython/GeoHealthCheck/issues/293
        if 'X-Esri-Authorization' in headers:
            del headers['X-Esri-Authorization']

        if 'Authorization' in headers:
            # https://enterprise.arcgis.com/en/server/latest/
            #     administer/linux/about-arcgis-tokens.htm
            auth_val = headers['Authorization']
            if 'Bearer' in auth_val:
                headers['X-Esri-Authorization'] = headers['Authorization']
        return headers

    def perform_esrims_get_request(self, url):
        response = self.perform_get_request(url).json()
        error_msg = 'code=%d message=%s'
        # May have error like:
        # {
        #   "error" :
        #   {
        #     "code" : 499,
        #     "message" : "Token Required",
        #     "messageCode" : "GWM_0003",
        #     "details" : [
        #       "Token Required"
        #     ]
        #   }
        # }
        if 'error' in response:
            err = response['error']
            raise Exception(error_msg % (err['code'], err['message']))

        return response

    def perform_request(self):
        """
        Perform the drilldown.
        """

        # Be sure to use bare root URL http://.../MapServer
        ms_url = self._resource.url.split('?')[0]

        # Assemble request templates with root MS URL
        req_tpl = {
            'ms_caps': ms_url + '?f=json',

            'layer_caps': ms_url + '/%d?f=json',

            'get_features': ms_url +
            '/%d/query?where=1=1'
            '&outFields=*&resultOffset=0&'
            'resultRecordCount=1&f=json',

            'get_feature_by_id': ms_url +
            '/%d/query?where=%s=%s&outFields=*&f=json'
        }

        # 1. Test top Service endpoint existence
        result = Result(True, 'Test Service Endpoint')
        result.start()
        layers = []
        try:
            ms_caps = self.perform_esrims_get_request(req_tpl['ms_caps'])
            for attr in ['currentVersion', 'layers']:
                val = ms_caps.get(attr, None)
                if val is None:
                    msg = 'Service: missing attr: %s' % attr
                    result = push_result(
                        self, result, False, msg, 'Test Layer:')
                    continue

            layers = ms_caps.get('layers', [])

        except Exception as err:
            result.set(False, str(err))

        result.stop()
        self.result.add_result(result)

        if len(layers) == 0:
            return

        # 2. Test each Layer Capabilities
        result = Result(True, 'Test Layer Capabilities')
        result.start()
        layer_ids = []
        layer_caps = []
        try:

            for layer in layers:
                if layer['subLayerIds'] is None:
                    layer_ids.append(layer['id'])

            for layer_id in layer_ids:
                layer_caps.append(self.perform_esrims_get_request(
                    req_tpl['layer_caps'] % layer_id))

        except Exception as err:
            result.set(False, str(err))

        result.stop()
        self.result.add_result(result)

        if self._parameters['drilldown_level'] == 'basic':
            return

        # ASSERTION: will do full drilldown from here

        # 3. Test getting Features from Layers
        result = Result(True, 'Test Layers')
        result.start()
        layer_id = -1
        try:
            for layer_id in layer_ids:

                try:
                    features = self.perform_esrims_get_request(
                        req_tpl['get_features'] % layer_id)
                    obj_id_field_name = "OBJECTID" #features['objectIdFieldName']
                    features = features['features']
                    if len(features) == 0:
                        continue

                    # At least one Feature: use first and try to get by id
                    object_id = features[0]['attributes'][obj_id_field_name]
                    feature = self.perform_get_request(
                        req_tpl['get_feature_by_id'] % (
                            layer_id, obj_id_field_name,
                            str(object_id))).json()

                    feature = feature['features']
                    if len(feature) == 0:
                        msg = 'layer: %d: missing Feature - id: %s' \
                              % (layer_id, str(object_id))
                        result = push_result(
                            self, result, False, msg,
                            'Test Layer: %d' % layer_id)

                except Exception as e:
                    msg = 'GetLayer: id=%d: err=%s ' \
                          % (layer_id, str(e))
                    result = push_result(
                        self, result, False, msg, 'Test Get Features:')
                    continue

        except Exception as err:
            result.set(False, 'Layer: id=%d : err=%s'
                       % (layer_id, str(err)))

        result.stop()

        # Add to overall Probe result
        self.result.add_result(result)
