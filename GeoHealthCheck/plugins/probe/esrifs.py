import requests

from GeoHealthCheck.probe import Probe
from GeoHealthCheck.result import Result


class ESRIFSDrilldown(Probe):
    """
    Probe for ESRI FeatureServer endpoint "drilldown": starting
    with top endpoint: get Layers and do Queries on these etc.
    """

    NAME = 'ESRIFS Drilldown'
    DESCRIPTION = 'Traverses an ESRI FeatureServer ' \
                  '(REST) API endpoint by drilling down'
    RESOURCE_TYPE = 'ESRI:FS'

    REQUEST_METHOD = 'GET'

    PARAM_DEFS = {
        'drilldown_level': {
            'type': 'string',
            'description': 'How heavy the drilldown should be.\
                            basic: test presence Capabilities, \
                            full: go through Layers, get features',
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
        """

        fs_url = self._resource.url.split('?')[0]

        # Assemble request templates with root FS URL
        req_tpl = {
            'fs_caps': fs_url + '?f=json',
            'layer_caps': fs_url + '/%d?f=json',
            'get_features': fs_url +
            '/%d/query?where=1=1'
            '&outFields=*&resultOffset=0&'
            'resultRecordCount=1&f=json',
            'get_feature_by_id': fs_url +
            '/%d/query?where=%s=%s&outFields=*&f=json'
        }

        # 1. Test top Service endpoint existence
        result = Result(True, 'Test Service Endpoint')
        result.start()
        layers = []
        try:

            fs_caps = requests.get(req_tpl['fs_caps']).json()
            for attr in ['currentVersion', 'layers']:
                val = fs_caps.get(attr, None)
                if val is None:
                    msg = 'Service: missing attr: %s' % attr
                    result = add_result(
                        self, result, False, msg, 'Test Layer:')
                    continue

            layers = fs_caps.get('layers', [])

        except Exception as err:
            result.set(False, str(err))

        result.stop()
        self.result.add_result(result)

        if len(layers) == 0:
            return

        # 2. Test each Layer Capabilities
        layer_ids = []
        layer_caps = []
        try:

            for layer in layers:
                layer_ids.append(layer['id'])

            for layer_id in layer_ids:
                layer_caps.append(requests.get(
                    req_tpl['layer_caps'] % layer_id).json())

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
                    features = requests.get(
                        req_tpl['get_features'] % layer_id).json()
                    obj_id_field_name = features['objectIdFieldName']
                    features = features['features']
                    if len(features) == 0:
                        continue

                    object_id = features[0]['attributes'][obj_id_field_name]
                    feature = requests.get(req_tpl['get_feature_by_id']
                                           % (layer_id, obj_id_field_name,
                                              str(object_id))).json()

                    feature = feature['features']
                    if len(feature) == 0:
                        msg = 'layer: %d: missing feature id: %s' \
                              % (layer_id, str(object_id))
                        result = add_result(
                            self, result, False, msg,
                            'Test Layer: %d' % layer_id)

                except Exception as e:
                    msg = 'GetLayer: id=%d: err=%s ' \
                          % (layer_id, str(e))
                    result = add_result(
                        self, result, False, msg, 'Test Get Features:')
                    continue

        except Exception as err:
            result.set(False, 'Layer: id=%d : err=%s'
                       % (layer_id, str(err)))

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
