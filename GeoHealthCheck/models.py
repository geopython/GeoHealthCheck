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

from datetime import datetime

from sqlalchemy import func

from init import DB
import util

RESOURCE_TYPES = {
    'OGC:WMS': 'Web Map Service (WMS)',
    'OGC:WFS': 'Web Feature Service (WFS)',
    'OGC:CSW': 'Catalogue Service (CSW)'
}


class Run(DB.Model):
    """measurement of resource state"""

    identifier = DB.Column(DB.Integer, primary_key=True, autoincrement=True)
    resource_identifier = DB.Column(DB.Integer,
                                    DB.ForeignKey('resource.identifier'))
    resource = DB.relationship('Resource',
                               backref=DB.backref('runs', lazy='dynamic'))
    checked_datetime = DB.Column(DB.DateTime, nullable=False)
    success = DB.Column(DB.Boolean, nullable=False)
    response_time = DB.Column(DB.Float, nullable=False)

    def __init__(self, resource, success, response_time,
                 checked_datetime=datetime.utcnow()):
        self.resource = resource
        self.success = success
        self.response_time = response_time
        self.checked_datetime = checked_datetime

    def __repr__(self):
        return '<Run %r>' % (self.identifier)


class Resource(DB.Model):
    """HTTP accessible resource"""

    identifier = DB.Column(DB.Integer, primary_key=True, autoincrement=True)
    resource_type = DB.Column(DB.Text, nullable=False)
    title = DB.Column(DB.Text, nullable=False)
    url = DB.Column(DB.Text, nullable=False)
    owner_identifier = DB.Column(DB.Text, DB.ForeignKey('user.username'))
    owner = DB.relationship('User',
                            backref=DB.backref('username2', lazy='dynamic'))

    def __init__(self, owner, resource_type, title, url):
        self.resource_type = resource_type
        self.title = title
        self.url = url
        self.owner = owner

    def __repr__(self):
        return '<Resource %r %r>' % (self.identifier, self.title)

    @property
    def last_run(self):
        return self.runs.having(func.max(Run.checked_datetime)).group_by(
            Run.checked_datetime).first()

    @property
    def reliability(self):
        total_runs = self.runs.count()
        success_runs = self.runs.filter_by(success=True).count()
        return util.percentage(success_runs, total_runs)

    def snippet(self):
        return util.get_python_snippet(self)

    def runs_to_json(self):
        runs = []
        for run in self.runs.group_by(Run.checked_datetime).all():
            runs.append({'datetime': run.checked_datetime.isoformat(),
                         'value': run.response_time})
        return runs


class User(DB.Model):
    """user accounts"""

    identifier = DB.Column('user_id', DB.Integer, primary_key=True,
                           autoincrement=True)
    username = DB.Column(DB.String(20), unique=True, index=True,
                         nullable=False)
    password = DB.Column(DB.String(10), nullable=False)
    email = DB.Column(DB.String(50), unique=True, index=True, nullable=False)
    registered_on = DB.Column(DB.DateTime)

    def __init__(self, username, password, email):
        self.username = username
        self.password = password
        self.email = email
        self.registered_on = datetime.utcnow()

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.identifier)

    def __repr__(self):
        return '<User %r>' % (self.username)


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == 'create':
            print('Creating database objects')
            DB.create_all()
        elif sys.argv[1] == 'drop':
            print('Dropping database objects')
            DB.drop_all()
