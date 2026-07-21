from types import SimpleNamespace
from unittest.mock import Mock, patch

from GeoHealthCheck.plugins.probe.ogcfeat import OGCFeatDrilldown
from GeoHealthCheck.result import ProbeResult


def test_full_drilldown_skips_non_feature_collections():
    features = Mock()
    features.headers = {}
    features.links = [
        {'rel': 'conformance', 'type': 'application/json'},
        {'rel': 'data', 'type': 'application/json'},
        {'rel': 'service-desc', 'type': 'application/json'},
    ]
    features.conformance.return_value = {}
    features.collections.return_value = {
        'collections': [
            {
                'id': 'lakes',
                'itemType': 'tile',
                'links': [
                    {'rel': 'self', 'type': 'application/json'},
                    {'rel': 'items', 'type': 'application/geo+json'},
                ],
            }
        ]
    }
    features.api.return_value = {
        'components': {},
        'paths': {},
        'openapi': '3.0.0',
    }

    probe = object.__new__(OGCFeatDrilldown)
    probe._resource = SimpleNamespace(url='https://example.test')
    probe._parameters = {'drilldown_level': 'full'}
    probe.result = ProbeResult(probe, {})
    probe.get_request_headers = lambda: {'Accept': 'application/json'}

    with patch(
            'GeoHealthCheck.plugins.probe.ogcfeat.Features',
            return_value=features):
        probe.perform_request()

    features.collection.assert_not_called()
    features.collection_items.assert_not_called()
    assert probe.result.success
