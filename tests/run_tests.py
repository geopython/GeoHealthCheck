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

sys.path.append('..')

from GeoHealthCheck.models import DB, Resource, Run, User, Tag, Probe, Check
from GeoHealthCheck.healthcheck import run_test_resource


class GeoHealthCheckTest(unittest.TestCase):

    def load_data(self):
        # Beware!
        self.db = DB
        # self.db.drop_all()
        self.db.create_all()

        with open('tests/fixtures.json') as ff:
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
                              check['check_function'],
                              check['parameters'],
                              )

            checks[check_name] = check
            self.db.session.add(check)

        self.db.session.commit()

    def setUp(self):
        # do once
        self.load_data()
        pass

    def tearDown(self):
        # self.db.drop_all()
        pass

    def testResourcesPresent(self):
        resources = Resource.query.all()

        self.assertEqual(len(resources), 6)

    def testRunResoures(self):
        resources = Resource.query.all()
        for resource in resources:
            result = run_test_resource(resource)
            print(str(result))


if __name__ == '__main__':
    unittest.main()
