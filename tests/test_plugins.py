# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>,
# Just van den Broecke <justb4@gmail.com>
#
# Copyright (c) 2014 Tom Kralidis
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# =================================================================

import unittest
import sys
import os
from GeoHealthCheck.models import DB, load_data, Resource
from GeoHealthCheck.views import get_probes_avail
from GeoHealthCheck.plugin import Plugin
from GeoHealthCheck.probe import Probe
from GeoHealthCheck.factory import Factory

TEST_DIR = os.path.dirname(os.path.abspath(__file__))

# Needed to find classes and plugins
sys.path.append('%s/..' % TEST_DIR)


class GeoHealthCheckTest(unittest.TestCase):
    def setUp(self):
        self.db = DB
        # do once per test
        load_data('%s/data/minimal.json' % TEST_DIR)

    def tearDown(self):
        self.db = DB
        # Needed for Postgres, otherwise hangs by aggressive locking
        self.db.session.close()
        self.db.drop_all()
        self.db.session.commit()
        self.db.session.close()

    def testPluginsPresent(self):

        plugins = Plugin.get_plugins('GeoHealthCheck.probe.Probe')
        for plugin in plugins:
            plugin = Factory.create_obj(plugin)
            self.assertIsNotNone(plugin)

            # Must have run_request method
            self.assertIsNotNone(plugin.run_request)

        plugins = Plugin.get_plugins('GeoHealthCheck.check.Check')
        for plugin in plugins:
            plugin = Factory.create_obj(plugin)
            self.assertIsNotNone(plugin)
            # Must have perform method
            self.assertIsNotNone(plugin.perform)

        plugins = Plugin.get_plugins(
            'GeoHealthCheck.resourceauth.ResourceAuth')
        for plugin in plugins:
            plugin = Factory.create_obj(plugin)
            self.assertIsNotNone(plugin)
            # Must have encode method
            self.assertIsNotNone(plugin.encode)

        plugins = Plugin.get_plugins(
            'GeoHealthCheck.probe.Probe',
            filters=[('RESOURCE_TYPE', 'OGC:*'), ('RESOURCE_TYPE', 'OGC:WMS')])

        for plugin in plugins:
            plugin_class = Factory.create_class(plugin)
            self.assertIsNotNone(plugin_class)

            plugin_obj = Factory.create_obj(plugin)
            self.assertIsNotNone(
                plugin_obj, 'Cannot create Plugin from string %s' + plugin)

            parameters = plugin_obj.PARAM_DEFS
            self.assertTrue(
                type(parameters) is dict, 'Plugin Parameters not a dict')

            checks = plugin_obj.CHECKS_AVAIL
            self.assertTrue(
                type(checks) is dict, 'Plugin checks not a dict')

            # Must have run_request method
            self.assertIsNotNone(plugin_obj.run_request)

            # Must have class var RESOURCE_TYPE='OGC:WMS'
            class_vars = Factory.get_class_vars(plugin)
            self.assertIn(class_vars['RESOURCE_TYPE'], ['OGC:WMS', 'OGC:*'])

    def testPluginParamDefs(self):
        plugin_obj = Factory.create_obj(
            'GeoHealthCheck.plugins.probe.owsgetcaps.WmsGetCaps')
        self.assertIsNotNone(plugin_obj)

        checks = plugin_obj.CHECKS_AVAIL
        self.assertEqual(len(checks), 3, 'WmsGetCaps should have 3 Checks')

        parameters = plugin_obj.PARAM_DEFS
        self.assertEqual(
            len(parameters), 2, 'WmsGetCaps should have 2 Parameters')

        probe_obj = Factory.create_obj(
            'GeoHealthCheck.plugins.probe.http.HttpGet')
        self.assertIsNotNone(probe_obj)
        check_vars = probe_obj.expand_check_vars(probe_obj.CHECKS_AVAIL)
        self.assertIsNotNone(check_vars)
        plugin_vars = probe_obj.get_plugin_vars()
        self.assertIsNotNone(plugin_vars)

    def testPluginChecks(self):
        plugin_obj = Factory.create_obj(
            'GeoHealthCheck.plugins.check.checks.NotContainsStrings')
        self.assertIsNotNone(plugin_obj)

        plugin_obj = Factory.create_obj(
            'GeoHealthCheck.plugins.check.checks.ContainsStrings')
        self.assertIsNotNone(plugin_obj)

        plugin_vars = plugin_obj.get_plugin_vars()
        self.assertIsNotNone(plugin_vars)

        parameters = plugin_obj.PARAM_DEFS
        self.assertEqual(
            len(parameters), 1, 'PARAM_DEFS should have 1 Parameter')
        self.assertEqual(parameters['strings']['type'], 'stringlist',
                          'PARAM_DEFS.strings[type] should be stringlist')

        plugin_obj = Factory.create_obj(
            'GeoHealthCheck.plugins.check.checks.NotContainsOwsException')
        self.assertIsNotNone(plugin_obj)

        parameters = plugin_obj.PARAM_DEFS
        self.assertEqual(
            len(parameters), 1, 'PARAM_DEFS should have 1 Parameter')
        self.assertEqual(
            parameters['strings']['value'][0], 'ExceptionReport>',
            'PARAM_DEFS.strings[0] should be ExceptionReport>')

    def testProbeViews(self):
        # All Probes available
        probes = get_probes_avail()
        total_probes_count = len(probes)
        self.assertIsNotNone(probes)
        self.assertGreater(
            total_probes_count, 0,
            'zero Probes found in app')

        for probe in probes:
            plugin_obj = Factory.create_obj(probe)
            self.assertIsNotNone(plugin_obj,
                                 'Probe create err: %s' % probe)

        # Probes per Resource Type
        resource_types = ['OGC:WMS', 'OGC:WFS', 'OGC:CSW', 'OGC:SOS']
        for resource_type in resource_types:

            probes = get_probes_avail(resource_type)
            self.assertIsNotNone(probes)
            self.assertGreater(
                len(probes), 0,
                'zero Probes for resource type %s' % resource_type)

            self.assertGreater(
                total_probes_count, len(probes),
                'total Probes must be greater than for  %s' % resource_type)

            for probe in probes:
                plugin_obj = Factory.create_obj(probe)
                self.assertIsNotNone(plugin_obj,
                                     'cannot create Probe for %s' % probe)

        # Probes per Resource instance
        resources = Resource.query.all()
        for resource in resources:

            probes = get_probes_avail(resource.resource_type, resource)
            self.assertIsNotNone(probes)
            self.assertGreater(
                len(probes), 0,
                'zero Probes for resource %s' % resource)

            for probe in probes:
                plugin_obj = Factory.create_obj(probe)
                self.assertIsNotNone(plugin_obj,
                                     'Probe create err: %s' % resource.url)

    def testProbeMetadata(self):
        # Some probes cache metadata
        probe_class = 'GeoHealthCheck.plugins.probe.wms.WmsGetMapV1'
        plugin_obj = Factory.create_obj(probe_class)
        self.assertIsNotNone(plugin_obj)
        self.assertEqual(
            plugin_obj.layer_count, 0,
            'non-zero layer_count %s' % probe_class)

        # Probes per Resource instance
        resources = Resource.query.all()
        for resource in resources:
            if resource.resource_type == 'OGC:WMS':
                md = plugin_obj.get_metadata(resource)
                md_c1 = plugin_obj.get_metadata_cached(resource,
                                                       version='1.1.1')
                self.assertNotEqual(md, md_c1)
                md_c2 = plugin_obj.get_metadata_cached(resource,
                                                       version='1.1.1')
                self.assertEqual(md_c1, md_c2)
                plugin_obj.expand_params(resource)

        for key in Probe.METADATA_CACHE:
            entry = Probe.METADATA_CACHE[key]
            self.assertIsNotNone(entry)


if __name__ == '__main__':
    unittest.main()
