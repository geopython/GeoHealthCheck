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

TEST_DIR = os.path.dirname(os.path.abspath(__file__))

# Needed to find classes and plugins
sys.path.append('%s/..' % TEST_DIR)

from GeoHealthCheck.models import DB, Resource, Run, User, Tag, Probe, Check, load_data
from GeoHealthCheck.healthcheck import run_test_resource


class GeoHealthCheckTest(unittest.TestCase):

    def setUp(self):
        self.db = DB
        # do once per test
        load_data('%s/data/fixtures.json' % TEST_DIR)

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
