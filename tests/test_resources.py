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

from GeoHealthCheck.models import (DB, Resource, Run, load_data,
                                   Recipient)
from GeoHealthCheck.healthcheck import run_test_resource
from GeoHealthCheck.notifications import _parse_webhook_location

TEST_DIR = os.path.dirname(os.path.abspath(__file__))

# Needed to find classes and plugins
sys.path.append('%s/..' % TEST_DIR)


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
            print('resource: %s result=%s' % (resource.url, result.success))
            run = Run(resource, result)

            print('Adding Run: success=%s, response_time=%ss\n'
                  % (str(run.success), run.response_time))
            self.db.session.add(run)
            self.db.session.commit()

        self.db.session.close()

        # Verify
        resources = Resource.query.all()
        for resource in resources:
            # Each Resource should have one Run
            self.assertEquals(
                resource.runs.count(), 1,
                'RunCount should be 1 for %s' % resource.url)
            self.assertEquals(
                resource.runs[0].success, True,
                'Run should be success for %s report=%s' %
                (resource.url, str(resource.runs[0])))

    def testNotificationsApi(self):
        Rcp = Recipient
        test_emails = ['test@test.com', 'other@test.com', 'unused@test.com']
        invalid_emails = ['invalid', None, object()]

        # invalid values should raise exception
        for email in invalid_emails:
            with self.assertRaises(ValueError):
                Rcp.get_or_create('email', email)

        for email in test_emails:
            Rcp.get_or_create('email', email)
        from_db = set(r[0] for r in DB.session.query(Rcp.location).all())
        self.assertEqual(from_db, set(test_emails))

        r = Resource.query.first()
        r.set_recipients('email', test_emails[:2])

        # unused email should be removed
        self.assertEqual(set(r.get_recipients('email')), set(test_emails[:2]))
        q = Rcp.query.filter(Rcp.location == test_emails[-1])
        self.assertEqual(q.count(), 0)

    def testWebhookNotifications(self):
        Rcp = Recipient

        r = Resource.query.first()

        lhost = 'http://localhost:8000/'

        # identifier, url,  params, no error
        test_data = (('', None, None, False,),
                     ('http://localhost:8000/', lhost, {}, True,),
                     ('http://localhost:8000/\n\n', lhost, {}, True,),
                     ('http://localhost:8000/\n\ntest=true', lhost, {'test': 'true'}, True,),
                     )

        for identifier, url, params, success in test_data:
            try:
                test_url, test_params = _parse_webhook_location(identifier)
                self.assertTrue(success)
                self.assertEqual(test_url, url)
                self.assertEqual(test_params, params)
            except Exception, err:
                self.assertFalse(success, str(err))


if __name__ == '__main__':
    unittest.main()
