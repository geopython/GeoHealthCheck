# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
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

import datetime
import json
import unittest
import sys

sys.path.append('..')

from GeoHealthCheck.models import DB, Resource, Run, User


class GeoHealthCheckTest(unittest.TestCase):
    def setUp(self):
        self.db = DB
        self.db.create_all()
        fixtures = json.load(open('fixtures.json'))
        # add users
        for user in fixtures['users']:
            account = User(user['user']['username'],
                           user['user']['password'],
                           user['user']['email'])
            self.db.session.add(account)
        # add data
        for record in fixtures['data']:
            resource = Resource(record['resource']['resource_type'],
                                record['resource']['title'],
                                record['resource']['url'])
            self.db.session.add(resource)
            for run in record['runs']:
                dt = datetime.datetime.strptime(run[0], '%Y-%m-%dT%H:%M:%SZ')
                run2 = Run(resource, run[1], run[2], dt)
                self.db.session.add(run2)
        self.db.session.commit()

    def tearDown(self):
        # self.db.drop_all()
        pass

    def testFoo(self):
        self.assertEqual(1, 1)

if __name__ == '__main__':
    unittest.main()
