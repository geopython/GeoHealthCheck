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
import logging

from sqlalchemy import func

from enums import RESOURCE_TYPES
from init import DB
from notifications import notify
import util

LOGGER = logging.getLogger(__name__)


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
    message = DB.Column(DB.Text, default='OK')

    def __init__(self, resource, success, response_time, message='OK',
                 checked_datetime=datetime.utcnow()):
        self.resource = resource
        self.success = success
        self.response_time = response_time
        self.checked_datetime = checked_datetime
        self.message = message

    def __repr__(self):
        return '<Run %r>' % (self.identifier)


class Resource(DB.Model):
    """HTTP accessible resource"""

    identifier = DB.Column(DB.Integer, primary_key=True, autoincrement=True)
    resource_type = DB.Column(DB.Text, nullable=False)
    title = DB.Column(DB.Text, nullable=False)
    url = DB.Column(DB.Text, nullable=False)
    latitude = DB.Column(DB.Float)
    longitude = DB.Column(DB.Float)
    owner_identifier = DB.Column(DB.String(20), DB.ForeignKey('user.username'))
    owner = DB.relationship('User',
                            backref=DB.backref('username2', lazy='dynamic'))
    min_response_time = DB.Column(DB.Float, default='0')
    average_response_time = DB.Column(DB.Float, default='0')
    max_response_time = DB.Column(DB.Float, default='0')
    reliability = DB.Column(DB.Integer, default='0')
    last_run_checked_datetime = DB.Column(DB.DateTime, default='1970-01-01 00:00:00')
    last_run_success = DB.Column(DB.Boolean, default='1')
    last_run_response_time = DB.Column(DB.Float, default='0')
    last_run_message = DB.Column(DB.Text, default='OK')

    def __init__(self, owner, resource_type, title, url):
        self.resource_type = resource_type
        self.title = title
        self.url = url
        self.owner = owner

        # get latitude/longitude from hostname
        try:
            self.latitude, self.longitude = util.geocode(url)
        except Exception as err:  # skip storage
            LOGGER.exception('Could not derive coordinates: %s', err)

    def __repr__(self):
        return '<Resource %r %r>' % (self.identifier, self.title)

    @property
    def get_capabilities_url(self):
        if self.resource_type.startswith('OGC:'):
            url = '%s%s' % (self.url,
                            RESOURCE_TYPES[self.resource_type]['capabilities'])
        else:
            url = self.url
        return url

    @property
    def all_response_times(self):
        return [run.response_time for run in self.runs]

    @property
    def nruns_response_times(self):
        lines = [run.response_time for run in self.runs.order_by(Run.checked_datetime.desc()).limit(100)]
        return lines[::-1]

    @property
    def first_run(self):
        return self.runs.having(func.min(Run.checked_datetime)).group_by(
            Run.checked_datetime).order_by(
                Run.checked_datetime.asc()).first()

    @property
    def f_last_run(self):
        return self.runs.having(func.max(Run.checked_datetime)).group_by(
            Run.checked_datetime).order_by(
                Run.checked_datetime.desc()).first()

    @property
    def f_average_response_time(self):
        query = [run.response_time for run in self.runs]
        return util.average(query)

    @property
    def f_min_response_time(self):
        query = [run.response_time for run in self.runs]
        return min(query)

    @property
    def f_max_response_time(self):
        query = [run.response_time for run in self.runs]
        return max(query)

    @property
    def f_reliability(self):
        total_runs = self.runs.count()
        success_runs = self.runs.filter_by(success=True).count()
        return util.percentage(success_runs, total_runs)

    def f_min_average_max(self):
        query = [run.response_time for run in self.runs]
        success_runs = self.runs.filter_by(success=True).count()
        return [min(query), util.average(query), max(query), util.percentage(success_runs, len(query)) ]

    def snippet(self):
        return util.get_python_snippet(self)

    def runs_to_json(self):
        runs = []
        for run in self.runs.group_by(Run.checked_datetime).all():
            runs.append({'datetime': run.checked_datetime.isoformat(),
                         'value': run.response_time,
                         'success': 1 if run.success else 0})
        return runs

    def limit_runs_to_json(self):
        runs = []
        for run in self.runs.group_by(Run.checked_datetime.desc()).limit(100):
            runs.append({'datetime': run.checked_datetime.isoformat(),
                         'value': run.response_time,
                         'success': 1 if run.success else 0})
        return runs

    def success_to_colors(self):
        colors = []
        for run in self.runs.group_by(Run.checked_datetime).all():
            if run.success == 1:
                colors.append('#5CB85C')  # green
            else:
                colors.append('#D9534F')  # red
        return colors


class User(DB.Model):
    """user accounts"""

    identifier = DB.Column('user_id', DB.Integer, primary_key=True,
                           autoincrement=True)
    username = DB.Column(DB.String(20), unique=True, index=True,
                         nullable=False)
    password = DB.Column(DB.String(10), nullable=False)
    email = DB.Column(DB.String(50), unique=True, index=True, nullable=False)
    role = DB.Column(DB.Text, nullable=False, default='user')
    registered_on = DB.Column(DB.DateTime)

    def __init__(self, username, password, email, role='user'):
        self.username = username
        self.password = password
        self.email = email
        self.role = role
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


def get_resource_types_counts():
    """return frequency counts and totals of registered resource types"""

    mrt = Resource.resource_type
    return [
        DB.session.query(mrt, func.count(mrt)).group_by(mrt),
        DB.session.query(mrt).count()
    ]


if __name__ == '__main__':
    import sys
    from flask import Flask
    APP = Flask(__name__)
    APP.config.from_pyfile('config_main.py')
    APP.config.from_pyfile('../instance/config_site.py')
    if len(sys.argv) > 1:
        if sys.argv[1] == 'create':
            print('Creating database objects')
            DB.create_all()

            print('Creating superuser account')
            if len(sys.argv) == 5:  # username/password/email sent
                username = sys.argv[2]
                password1 = sys.argv[3]
                email1 = sys.argv[4]
            else:
                username = raw_input('Enter your username: ').strip()
                password1 = raw_input('Enter your password: ').strip()
                password2 = raw_input('Enter your password again: ').strip()
                if password1 != password2:
                    raise ValueError('Passwords must match')
                email1 = raw_input('Enter your email: ').strip()
                email2 = raw_input('Enter your email again: ').strip()
                if email1 != email2:
                    raise ValueError('Emails must match')

            user_to_add = User(username, password1, email1, role='admin')
            DB.session.add(user_to_add)
        elif sys.argv[1] == 'drop':
            print('Dropping database objects')
            DB.drop_all()
        elif sys.argv[1] == 'run':
            print('Running health check tests')
            from healthcheck import run_test_resource
            for res in Resource.query.all():  # run all tests
                print('Testing %s %s' % (res.resource_type, res.url))
                # last_run_success = res.f_last_run.success
                run_to_add = run_test_resource(res.resource_type, res.url)

                last_run = Run(res, run_to_add[1], run_to_add[2],
                           run_to_add[3], run_to_add[4])

                print('Adding run')
                DB.session.add(last_run)
                DB.session.commit()
                # Precalculate
                values = res.f_min_average_max() # Need optimize this
                setattr(res, 'min_response_time', values[0])
                setattr(res, 'average_response_time', values[1])
                setattr(res, 'max_response_time', values[2])
                setattr(res, 'reliability', values[3])
                setattr(res, 'last_run_checked_datetime', last_run.checked_datetime)
                setattr(res, 'last_run_response_time', last_run.response_time)
                setattr(res, 'last_run_success', last_run.success)
                setattr(res, 'last_run_message', last_run.message)
                DB.session.commit()

                if APP.config['GHC_NOTIFICATIONS']:
                    notify(APP.config, res, run1, last_run.success)

        elif sys.argv[1] == 'flush':
            print('Flushing runs older than %d days' %
                  APP.config['GHC_RETENTION_DAYS'])
            for run1 in Run.query.all():
                here_and_now = datetime.utcnow()
                days_old = (here_and_now - run1.checked_datetime).days
                if days_old > APP.config['GHC_RETENTION_DAYS']:
                    print('Run older than %d days. Deleting' % days_old)
                    DB.session.delete(run1)
        # commit or rollback
        try:
            DB.session.commit()
        except Exception as err:
            DB.session.rollback()
            msg = str(err)
            print(msg)
