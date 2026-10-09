"""The resource editor must work while an OGC service is unavailable."""

import os
import unittest
from unittest.mock import patch

from app import APP
from models import DB, CheckVars, ProbeVars, Resource, User, load_data
from GeoHealthCheck.plugins.probe.wmts import WmtsGetTile, WmtsGetTileAll


TEST_DIR = os.path.dirname(os.path.abspath(__file__))


class OfflineResourceEditTest(unittest.TestCase):
    def setUp(self):
        with patch('models.util.geocode', return_value=(0.0, 0.0)):
            load_data('%s/data/minimal.json' % TEST_DIR)
            owner = User.query.filter_by(username='admin').one()
            resource = Resource(owner, 'OGC:WMTS', 'Offline WMTS',
                                'https://example.invalid/wmts', [])
            resource.active = False

        probe = ProbeVars(resource,
                          'GeoHealthCheck.plugins.probe.wmts.WmtsGetTile',
                          {'layers': ['layer_a', 'layer_b'],
                           'tilematrixset': 'EPSG:4326',
                           'kvprest': 'KVP'})
        CheckVars(probe,
                  'GeoHealthCheck.plugins.check.checks.HttpStatusNoError',
                  {})
        DB.session.add(resource)
        DB.session.commit()
        self.resource_id = resource.identifier
        self.client = APP.test_client()
        response = self.client.post('/login',
                                    data={'username': 'admin',
                                          'password': 'admin'})
        self.assertEqual(response.status_code, 302)

    def tearDown(self):
        DB.session.remove()
        DB.drop_all()

    def test_edit_page_does_not_expand_remote_probe_parameters(self):
        with patch.object(WmtsGetTile, 'expand_params') as expand_tile, \
                patch.object(WmtsGetTileAll, 'expand_params') as expand_all:
            response = self.client.get(
                '/resource/%d/edit' % self.resource_id)

        self.assertEqual(response.status_code, 200)
        expand_tile.assert_not_called()
        expand_all.assert_not_called()
        self.assertIn(b'value="layer_a,layer_b"', response.data)
        # A saved value outside the static choices must not become the
        # browser's first choice when the form is saved.
        self.assertIn(b'value="EPSG:4326"', response.data)
        self.assertIn(b'value="KVP"', response.data)

    def test_probe_parameter_definitions_are_isolated(self):
        first = WmtsGetTile()
        second = WmtsGetTile()
        first.PARAM_DEFS['layers']['range'] = ['another_resource']

        self.assertIsNone(second.PARAM_DEFS['layers']['range'])
        self.assertIsNone(WmtsGetTile.PARAM_DEFS['layers']['range'])


if __name__ == '__main__':
    unittest.main()
