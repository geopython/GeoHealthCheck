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

import json
import unittest
import sys
import os

TEST_DIR = os.path.dirname(os.path.abspath(__file__))

# Needed to find classes and plugins
sys.path.append('%s/..' % TEST_DIR)

from GeoHealthCheck.models import DB, Resource, Run, User, Tag, Probe, Check
from GeoHealthCheck.healthcheck import run_test_resource
from GeoHealthCheck.factory import Factory


class GeoHealthCheckTest(unittest.TestCase):
    def load_data(self):
        # Beware!
        self.db = DB
        self.db.create_all()

        with open('%s/fixtures.json' % TEST_DIR) as ff:
            fixtures = json.load(ff)

        # add users, keeping track of DB objects
        users = {}
        for user_name in fixtures['users']:
            user = fixtures['users'][user_name]
            user = User(user['username'],
                        user['password'],
                        user['email'],
                        user['role'])
            users[user_name] = user
            self.db.session.add(user)

        # add tags, keeping track of DB objects
        tags = {}
        for tag_str in fixtures['tags']:
            tag = fixtures['tags'][tag_str]

            tag = Tag(tag)
            tags[tag_str] = tag
            self.db.session.add(tag)

        # add Resources, keeping track of DB objects
        resources = {}
        for resource_name in fixtures['resources']:
            resource = fixtures['resources'][resource_name]

            resource_tags = []
            for tag_str in resource['tags']:
                resource_tags.append(tags[tag_str])

            resource = Resource(users[resource['owner']],
                                resource['resource_type'],
                                resource['title'],
                                resource['url'],
                                resource_tags)

            resources[resource_name] = resource
            self.db.session.add(resource)

        # add Probes, keeping track of DB objects
        probes = {}
        for probe_name in fixtures['probes']:
            probe = fixtures['probes'][probe_name]

            probe = Probe(resources[probe['resource']],
                          probe['proberunner'],
                          probe['parameters'],
                          )

            probes[probe_name] = probe
            self.db.session.add(probe)

        # add Checks, keeping track of DB objects
        checks = {}
        for check_name in fixtures['checks']:
            check = fixtures['checks'][check_name]

            check = Check(probes[check['probe']],
                          check['checker'],
                          check['parameters'],
                          )

            checks[check_name] = check
            self.db.session.add(check)

        self.db.session.commit()
        self.db.session.close()

    def setUp(self):
        # do once per test
        self.load_data()

    def tearDown(self):
        self.db = DB
        # Needed for Postgres, otherwise hangs by aggressive locking
        self.db.session.close()
        self.db.drop_all()
        self.db.session.commit()
        self.db.session.close()

    def testResourcesPresent(self):
        resources = Resource.query.all()

        self.assertEqual(len(resources), 7)

    def testPluginsPresent(self):
        from GeoHealthCheck.plugin import Plugin
        from GeoHealthCheck.factory import Factory

        plugins = Plugin.get_plugins('GeoHealthCheck.proberunner.ProbeRunner')
        for plugin in plugins:
            plugin = Factory.create_obj(plugin)
            self.assertIsNotNone(plugin)

            # Must have run_request method
            self.assertIsNotNone(plugin.run_request)

        plugins = Plugin.get_plugins('GeoHealthCheck.checker.Checker')
        for plugin in plugins:
            plugin = Factory.create_obj(plugin)
            self.assertIsNotNone(plugin)
            # Must have perform method
            self.assertIsNotNone(plugin.perform)

    def testRunResoures(self):
        # Do the whole healthcheck for all Resources for now
        resources = Resource.query.all()
        for resource in resources:
            result = run_test_resource(resource)

            run = Run(resource, result[1], result[2],
                      result[3], result[4])

            print('Adding Run: success=%s, response_time=%ss\n'
                  % (str(run.success), run.response_time))
            self.db.session.add(run)
            self.db.session.commit()

        self.db.session.close()

        # Verify
        resources = Resource.query.all()
        for resource in resources:
            # Each Resource should have one Run
            self.assertEquals(resource.runs.count(), 1)
            self.assertEquals(resource.runs[0].success, True)


if __name__ == '__main__':
    unittest.main()
