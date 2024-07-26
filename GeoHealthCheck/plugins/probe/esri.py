from GeoHealthCheck.probe import Probe
from GeoHealthCheck.result import Result, push_result

class ESRIDrilldown(Probe):
    """
    Probe for ESRI Feature- or MapServer endpoint "drilldown": starting
    with top /FeatureServer or /MapServer endpoint: get Layers and get Features on these.
    Test e.g. from https://sampleserver6.arcgisonline.com/arcgis/rest/services
    (at least sampleserver6 is ArcGIS 10.6.1 supporting Paging).
    """

    NAME = 'ESRI Drilldown'

    DESCRIPTION = 'Traverses an ESRI Feature- or MapServer ' \
                  '(REST) API endpoint by drilling down'

    RESOURCE_TYPE = 'ESRI'

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

    def perform_esri_get_request(self, url):
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

        # Be sure to use bare root URL http://.../FeatureServer or http://.../MapServer
        es_url = self._resource.url.split('?')[0]

        # Add service type to the url
        if "FEATURESERVER" in es_url.upper():
            service_type = "FeatureServer"
        elif "MAPSERVER" in es_url.upper():
            service_type = "MapServer"
        else:
            raise Exception("No FeatureServer of MapServer in url")

        # Assemble request templates with root FS URL
        req_tpl = {
            'es_caps': es_url + '?f=json',

            'layer_caps': es_url + '/%d?f=json',

            'get_features': es_url +
            '/%d/query?where=1=1'
            '&outFields=*&resultOffset=0&'
            'resultRecordCount=1&f=json',

            'get_feature_by_id': es_url +
            "/%d/query?where=%s='%s'&resultRecordCount=1&outFields=*&f=json"
        }

        # 1. Test top Service endpoint existence
        result = Result(True, f"Test Service Endpoint (type={service_type})")
        result.start()
        layers = []
        try:
            es_caps = self.perform_esri_get_request(req_tpl['es_caps'])
            for attr in ['currentVersion', 'layers']:
                val = es_caps.get(attr, None)
                if val is None:
                    msg = 'Service: missing attr: %s' % attr
                    result = push_result(
                        self, result, False, msg, 'Test Layer:')
                    continue

            layers = es_caps.get('layers', [])

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
                layer_caps.append(self.perform_esri_get_request(
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
        layer_id = 0
        try:
            for layer_id in layer_ids:
                try:
                    features = self.perform_esri_get_request(
                        req_tpl['get_features'] % layer_id)
                    if service_type == 'FeatureServer':
                        obj_id_field_name = features['objectIdFieldName']
                    elif service_type == 'MapServer':
                        obj_id_field_name = features['displayFieldName']
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
