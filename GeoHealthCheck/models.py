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
import logging
from flask_babel import gettext as _
from datetime import datetime, timedelta
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from sqlalchemy import func, and_

from sqlalchemy.orm import deferred
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

import util
from enums import RESOURCE_TYPES
from factory import Factory
from init import App
from resourceauth import ResourceAuth
from wtforms.validators import Email, ValidationError
from owslib.util import bind_url

APP = App.get_app()
DB = App.get_db()
LOGGER = logging.getLogger(__name__)


# Complete handle of old runs deletion
def flush_runs():
    retention_days = int(APP.config['GHC_RETENTION_DAYS'])
    LOGGER.info('Flushing runs older than %d days' % retention_days)
    all_runs = Run.query.all()
    run_count = 0
    for run in all_runs:
        days_old = (datetime.utcnow() - run.checked_datetime).days
        if days_old > retention_days:
            run_count += 1
            DB.session.delete(run)
    db_commit()
    LOGGER.info('Deleted %d Runs' % run_count)

    DB.session.remove()


class Run(DB.Model):
    """measurement of resource state"""

    identifier = DB.Column(DB.Integer, primary_key=True, autoincrement=True)
    resource_identifier = DB.Column(DB.Integer,
                                    DB.ForeignKey('resource.identifier'))
    resource = DB.relationship('Resource',
                               backref=DB.backref('runs', lazy='dynamic',
                                                  cascade="all,delete"))
    checked_datetime = DB.Column(DB.DateTime, nullable=False)
    success = DB.Column(DB.Boolean, nullable=False)
    response_time = DB.Column(DB.Float, nullable=False)
    message = DB.Column(DB.Text, default='OK')

    # Make report 'deferred' as not to be included in all queries.
    report = deferred(DB.Column(DB.Text, default={}))

    def __init__(self, resource, result,
                 checked_datetime=datetime.utcnow()):
        self.resource = resource
        self.success = result.success
        self.response_time = result.response_time_str
        self.checked_datetime = checked_datetime
        self.message = result.message
        self.report = result.get_report()

    def __lt__(self, other):
        return self.identifier < other.identifier

    def __le__(self, other):
        return self.identifier <= other.identifier

    def __eq__(self, other):
        return self.identifier == other.identifier

    def __gt__(self, other):
        return self.identifier > other.identifier

    def __ge__(self, other):
        return self.identifief >= other.identifier

    def __hash__(self):
        return hash(f"{self.identifier}{self.checked_datetime}{self.resource}")

    # JSON string object specifying report for the Run
    # See http://docs.sqlalchemy.org/en/latest/orm/mapped_attributes.html
    _report = DB.Column("report", DB.Text, default={})

    @property
    def report(self):
        return json.loads(self._report)

    @report.setter
    def report(self, report):
        self._report = json.dumps(report)

    def __repr__(self):
        return '<Run %r>' % (self.identifier)

    def for_json(self):
        return {
            'success': self.success,
            'response_time': self.response_time,
            'checked_datetime': self.checked_datetime,
            'message': self.message
        }


class ProbeVars(DB.Model):
    """
    Identifies and parameterizes single Probe class. Probe
    instance applies to single parent Resource.
    """

    identifier = DB.Column(DB.Integer, primary_key=True, autoincrement=True)
    resource_identifier = DB.Column(DB.Integer,
                                    DB.ForeignKey('resource.identifier'))
    resource = DB.relationship(
        'Resource', backref=DB.backref('probe_vars',
                                       lazy='dynamic',
                                       cascade="all, delete-orphan"))
    probe_class = DB.Column(DB.Text, nullable=False)

    # JSON string object specifying actual parameters for the Probe
    # See http://docs.sqlalchemy.org/en/latest/orm/mapped_attributes.html
    _parameters = DB.Column("parameters", DB.Text, default={})

    def __init__(self, resource_obj, probe_class, parameters={}):
        self.resource = resource_obj
        self.probe_class = probe_class
        self.parameters = parameters

    @property
    def parameters(self):
        return json.loads(self._parameters)

    @parameters.setter
    def parameters(self, parameters):
        self._parameters = json.dumps(parameters)

    @property
    def probe_instance(self):
        return Factory.create_obj(self.probe_class)

    @property
    def name(self):
        return self.probe_instance.NAME

    @property
    def probe_parameters(self):
        return self.probe_instance.REQUEST_PARAMETERS

    def __repr__(self):
        return '<ProbeVars %r>' % self.identifier


class CheckVars(DB.Model):
    """Identifies and parameterizes check function, applies to single Probe"""

    identifier = DB.Column(DB.Integer, primary_key=True, autoincrement=True)
    probe_vars_identifier = DB.Column(
        DB.Integer, DB.ForeignKey('probe_vars.identifier'))
    probe_vars = DB.relationship(
        'ProbeVars', backref=DB.backref(
            'check_vars', cascade="all, delete-orphan"))
    check_class = DB.Column(DB.Text, nullable=False)

    # JSON string object specifying actual parameters for the Check
    # See http://docs.sqlalchemy.org/en/latest/orm/mapped_attributes.html
    _parameters = DB.Column("parameters", DB.Text, default={})

    def __init__(self, probe_vars, check_class, parameters={}):
        self.probe_vars = probe_vars
        self.check_class = check_class
        self.parameters = parameters

    @property
    def parameters(self):
        return json.loads(self._parameters)

    @parameters.setter
    def parameters(self, parameters):
        self._parameters = json.dumps(parameters)

    def __repr__(self):
        return '<CheckVars %r>' % self.identifier


class Tag(DB.Model):
    id = DB.Column(DB.Integer, primary_key=True)
    name = DB.Column(DB.String(100), unique=True, nullable=False)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<Tag %r>' % (self.name)


resource_tags = DB.Table('resource_tags',
                         DB.Column('identifier', DB.Integer, primary_key=True,
                                   autoincrement=True),
                         DB.Column('tag_id', DB.Integer,
                                   DB.ForeignKey('tag.id')),
                         DB.Column('resource_identifier', DB.Integer,
                                   DB.ForeignKey('resource.identifier')))


def _validate_webhook(value):
    from GeoHealthCheck.notifications import _parse_webhook_location
    try:
        _parse_webhook_location(value)
    except ValueError as err:
        raise ValidationError('{}: {}'.format(value, err))
    return value


def _validate_email(value):
    if not value:
        raise ValidationError("Email cannot be empty value")
    try:
        if not value.strip():
            raise ValidationError("Email cannot be empty value")
    except AttributeError:
        raise ValidationError("Email cannot be empty value")

    v = Email()

    class dummy_value(object):
        data = value

        @staticmethod
        def gettext(*args, **kwargs):
            return _(*args, **kwargs)

    dummy_form = None
    v(dummy_form, dummy_value())


class Recipient(DB.Model):
    """
    Notification recipient
    """
    TYPE_EMAIL = 'email'
    TYPE_WEBHOOK = 'webhook'
    TYPES = (TYPE_EMAIL, TYPE_WEBHOOK,)
    __tablename__ = 'recipient'
    VALIDATORS = {TYPE_EMAIL: [_validate_email],
                  TYPE_WEBHOOK: [_validate_webhook]}

    id = DB.Column(DB.Integer, primary_key=True)
    # channel type. email for now, more may come later
    channel = DB.Column(DB.Enum(*TYPES, name='recipient_channel_types'),
                        default=TYPE_EMAIL, nullable=False)
    # recipient's identification, payload
    # this can be url, or more rich configuration, depending on channel
    location = DB.Column(DB.Text, nullable=False)
    resources = DB.relationship('Resource',
                                secondary='resourcenotification',
                                lazy='dynamic',
                                backref=DB.backref('recipients',
                                                   lazy='dynamic'))

    def __init__(self, channel, location):
        self.channel = channel
        self.location = location

    @classmethod
    def validate(cls, channel, value):
        """
        Validate if provided value is correct for given channel
        """
        try:
            validators = cls.VALIDATORS[channel]
        except KeyError:
            return

        for v in validators:
            try:
                v(value)
            except (ValidationError, TypeError) as err:
                raise ValueError("Bad value: {}".format(err), err)

    def is_email(self):
        return self.channel == self.TYPE_EMAIL

    def is_webhook(self):
        return self.channel == self.TYPE_WEBHOOK

    @classmethod
    def burry_dead(cls):
        RN = ResourceNotification
        q = DB.session.query(cls) \
            .join(RN,
                  RN.recipient_id == cls.id,
                  isouter=True) \
            .filter(RN.recipient_id.is_(None))
        for item in q:
            DB.session.delete(item)

    @classmethod
    def get_or_create(cls, channel, location):
        try:
            cls.validate(channel, location)
        except ValidationError as err:
            raise ValueError("invalid value {}: {}".format(location, err))

        try:
            r = DB.session.query(cls) \
                .filter(and_(cls.channel == channel,
                             cls.location == location)) \
                .one()
        except (MultipleResultsFound, NoResultFound,):
            r = cls(channel=channel, location=location)
            DB.session.add(r)
            DB.session.flush()
        return r

    @classmethod
    def get_suggestions(cls, channel, for_user):
        """
        Return list of values to autocomplete for specific user
        and channel.
        """
        Rcp = cls
        Res = Resource
        ResNot = ResourceNotification

        q = DB.session.query(Rcp.location) \
            .join(ResNot, ResNot.recipient_id == Rcp.id) \
            .join(Res, Res.identifier == ResNot.resource_id) \
            .group_by(Rcp.location) \
            .filter(and_(Res.owner_identifier == for_user,
                         Rcp.channel == channel))
        return [item[0] for item in q]


class ResourceNotification(DB.Model):
    """
    m2m for Recipient <-> Resource
    """
    __tablename__ = 'resourcenotification'

    resource_id = DB.Column(DB.Integer,
                            DB.ForeignKey('resource.identifier'),
                            primary_key=True)
    recipient_id = DB.Column(DB.Integer,
                             DB.ForeignKey('recipient.id'),
                             primary_key=True)
    resource = DB.relationship('Resource', lazy=False)
    recipient = DB.relationship('Recipient', lazy=False)


class Resource(DB.Model):
    """HTTP accessible resource"""

    identifier = DB.Column(DB.Integer, primary_key=True, autoincrement=True)
    resource_type = DB.Column(DB.Text, nullable=False)
    active = DB.Column(DB.Boolean, nullable=False, default=True)
    title = DB.Column(DB.Text, nullable=False)
    url = DB.Column(DB.Text, nullable=False)
    latitude = DB.Column(DB.Float)
    longitude = DB.Column(DB.Float)
    owner_identifier = DB.Column(DB.Text, DB.ForeignKey('user.username'))
    owner = DB.relationship('User',
                            backref=DB.backref('username2', lazy='dynamic'))
    tags = DB.relationship('Tag', secondary=resource_tags, backref='resource')
    run_frequency = DB.Column(DB.Integer, default=60)
    _auth = DB.Column('auth', DB.Text, nullable=True, default=None)

    def __init__(self, owner, resource_type, title, url, tags, auth=None):
        self.resource_type = resource_type
        self.active = True
        self.title = title
        self.url = url
        self.owner = owner
        self.tags = tags
        self.auth = auth
        self.auth_obj = None
        self.latitude, self.longitude = util.geocode(url)

    def __repr__(self):
        return '<Resource %r %r>' % (self.identifier, self.title)

    @property
    def get_capabilities_url(self):
        if self.resource_type.startswith('OGC:') \
                and self.resource_type not in \
                ['OGC:STA', 'OGC:WFS3', 'ESRI:FS', 'OGC:3D']:
            url = '%s%s' % (bind_url(self.url),
                            RESOURCE_TYPES[self.resource_type]['capabilities'])
        else:
            url = self.url
        return url

    @property
    def all_response_times(self):
        result = [0]
        if self.runs.count() > 0:
            result = [run.response_time for run in self.runs]
        return result

    @property
    def first_run(self):
        return self.runs.order_by(
            Run.checked_datetime.asc()).first()

    @property
    def last_run(self):
        return self.runs.order_by(
            Run.checked_datetime.desc()).first()

    @property
    def average_response_time(self):
        result = 0
        if self.runs.count() > 0:
            query = [run.response_time for run in self.runs]
            result = util.average(query)
        return result

    @property
    def min_response_time(self):
        result = 0
        if self.runs.count() > 0:
            query = [run.response_time for run in self.runs]
            result = min(query)
        return result

    @property
    def max_response_time(self):
        result = 0
        if self.runs.count() > 0:
            query = [run.response_time for run in self.runs]
            result = max(query)
        return result

    @property
    def reliability(self):
        result = 0
        if self.runs.count() > 0:
            total_runs = self.runs.count()
            success_runs = self.runs.filter_by(success=True).count()
            result = util.percentage(success_runs, total_runs)
        return result

    @property
    def tags2csv(self):
        return ','.join([t.name for t in self.tags])

    def snippet(self):
        if not self.last_run:
            return 'No Runs yet'

        report = '''
        - time: %s <br/>
        - success: %s <br/>
        - message: %s <br/>
        - response_time: %s
        ''' % (self.last_run.checked_datetime,
               self.last_run.success,
               self.last_run.message,
               self.last_run.response_time)

        return report

    def runs_to_json(self):
        runs = []
        for run in self.runs.order_by(Run.checked_datetime).all():
            runs.append({'id': run.identifier,
                         'datetime': run.checked_datetime.isoformat(),
                         'value': run.response_time,
                         'success': 1 if run.success else 0})
        return runs

    def success_to_colors(self):
        colors = []
        for run in self.runs.order_by(Run.checked_datetime).all():
            if run.success == 1:
                colors.append('#5CB85C')  # green
            else:
                colors.append('#D9534F')  # red
        return colors

    def clear_recipients(self, channel=None, burry_dead=True):
        RN = ResourceNotification
        Rcp = Recipient
        if channel:
            # clear specific channel
            to_delete = self.get_recipients(channel)
            if to_delete:
                to_del_rcp = DB.session.query(RN) \
                    .join(Rcp,
                          Rcp.id == RN.recipient_id) \
                    .filter(
                    and_(RN.resource_id ==
                         self.identifier,
                         Rcp.channel == channel,
                         Rcp.location.in_(to_delete))
                )
            else:
                to_del_rcp = []
        else:
            # remove all m2m connections for Resource<->Recipient
            to_del_rcp = DB.session.query(RN) \
                .join(Rcp,
                      Rcp.id == RN.recipient_id) \
                .filter(
                RN.resource_id ==
                self.identifier,
            )
        for rcp_ntf in to_del_rcp:
            DB.session.delete(rcp_ntf)
        if burry_dead:
            Rcp.burry_dead()
        DB.session.flush()

    def get_recipients(self, channel):
        q = self.recipients
        return [item.location for item in q if item.channel == channel]

    def set_recipients(self, channel, items):

        # create new rcp first
        to_add = []
        for item in items:
            to_add.append(Recipient.get_or_create(channel, item))

        self.clear_recipients(channel, burry_dead=False)

        for r in to_add:
            self.recipients.append(r)
        DB.session.flush()
        Recipient.burry_dead()
        DB.session.flush()
        return self.get_recipients(channel)

    def dump_recipients(self):
        """
        Return dictionary with channel ->recipients mapping
        """
        out = {}
        for c in Recipient.TYPES:
            out[c] = self.get_recipients(c)
        return out

    @property
    def auth(self):
        return ResourceAuth.decode(self._auth)

    @property
    def auth_type(self):
        if not self.has_auth():
            return 'None'
        return self.auth['type']

    @auth.setter
    def auth(self, auth_dict):
        if auth_dict is None:
            self._auth = None
            return

        self.auth_obj = ResourceAuth.create(auth_dict)
        self._auth = self.auth_obj.encode()

    def has_auth(self):
        return self._auth is not None

    def add_auth_header(self, headers_dict):
        if 'Authorization' in headers_dict:
            del headers_dict['Authorization']

        if not self.has_auth():
            return headers_dict

        self.auth_obj = ResourceAuth.create(self.auth)

        return self.auth_obj.add_auth_header(headers_dict)

    def for_json(self):
        return {
            'identifier': self.identifier,
            'resource_type': self.resource_type,
            'url': self.url,
            'title': self.title,
            'active': self.active,
            'owner': self.owner.username,
            'owner_identifier': self.owner.identifier,
            'run_frequency': self.run_frequency,
            'reliability': round(self.reliability, 1)
        }


class ResourceLock(DB.Model):
    """lock resource for multiprocessing runs"""

    identifier = DB.Column(DB.Integer,
                           primary_key=True, autoincrement=False, unique=True)
    resource_identifier = DB.Column(
        DB.Integer, DB.ForeignKey('resource.identifier'), unique=True)
    resource = DB.relationship('Resource',
                               backref=DB.backref('locks', lazy='dynamic',
                                                  cascade="all,delete"))
    owner = DB.Column(DB.Text, nullable=False, default='NOT SET')

    start_time = DB.Column(DB.DateTime, nullable=False)
    end_time = DB.Column(DB.DateTime, nullable=False)

    def __init__(self, resource, owner, interval_mins):
        self.identifier = resource.identifier
        self.resource = resource
        self.owner = owner
        self.init_datetimes(interval_mins)

    def init_datetimes(self, interval_mins):
        self.start_time = datetime.utcnow()
        # Subtract some space from end-time to allow obtain at scheduled time
        minutes = interval_mins - 1
        self.end_time = self.start_time + timedelta(minutes=minutes)

    def has_expired(self):
        now = datetime.utcnow()
        return now > self.end_time

    def obtain(self, owner, frequency):
        if not self.has_expired():
            return False

        self.owner = owner
        self.init_datetimes(frequency)
        return True

    def __repr__(self):
        return '<ResourceLock rsc_id=%r>' % self.identifier


class User(DB.Model):
    """
    user accounts.
    Token handling thanks to:
    https://navaspot.wordpress.com/2014/06/25/\
              how-to-implement-forgot-password-feature-in-flask/
    """

    identifier = DB.Column('user_id', DB.Integer, primary_key=True,
                           autoincrement=True)
    username = DB.Column(DB.String(20), unique=True, index=True,
                         nullable=False)
    password = DB.Column(DB.String(255), nullable=False)
    email = DB.Column(DB.String(50), unique=True, index=True, nullable=False)
    role = DB.Column(DB.Text, nullable=False, default='user')
    registered_on = DB.Column(DB.DateTime)

    def __init__(self, username, password, email, role='user'):
        self.username = username
        self.set_password(password)
        self.email = email
        self.role = role
        self.registered_on = datetime.utcnow()

    def authenticate(self, password):
        return util.verify_hash(password, self.password)

    def encrypt(self, string):
        # https://passlib.readthedocs.io/en/stable/narr/hash-tutorial.html
        return util.create_hash(string)

    def get_token(self, expiration=7200):
        s = Serializer(APP.config['SECRET_KEY'], expiration)
        return s.dumps({'user': self.get_id()}).decode('utf-8')

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.identifier

    def set_password(self, password):
        self.password = self.encrypt(password)

    @staticmethod
    def verify_token(token):
        s = Serializer(APP.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except Exception:
            return None
        user_id = data.get('user')
        if user_id:
            return User.query.get(user_id)
        return None

    def __repr__(self):
        return '<User %r>' % (self.username)


def get_resource_types_counts():
    """return frequency counts and totals of registered resource types"""

    mrt = Resource.resource_type
    return [
        DB.session.query(mrt, func.count(mrt)).group_by(mrt),
        DB.session.query(mrt).count()
    ]


def get_resources_count():
    """return number of rows for Resource"""
    return DB.session.query(func.count(Resource.identifier)).scalar()


def get_runs_count():
    """return number of rows for Run"""
    return DB.session.query(func.count(Run.identifier)).scalar()


def get_runs_status_count(success=True):
    """return number of rows for Run with given run status"""
    return DB.session.query(Run.success).filter(Run.success == success).count()


def get_first_run():
    """return last Run"""
    return DB.session.query(Run).filter(
        Run.identifier == DB.session.query(func.min(Run.identifier))).first()


def get_last_run():
    """return last Run"""
    return DB.session.query(Run).filter(
        Run.identifier == DB.session.query(func.max(Run.identifier))).first()


def get_last_run_per_resource():
    """return last N Runs with results for each Resource"""

    # We need an Innerjoin on same table
    # example: https://stackoverflow.com/questions/2411559/
    #    how-do-i-query-sql-for-a-latest-record-date-for-each-user

    sql = """
    select t.resource_identifier, t.identifier, t.success
    from Run t
    inner join (
        select resource_identifier, max(identifier) as MaxId
        from Run
        group by resource_identifier
    ) tm on t.resource_identifier = tm.resource_identifier
    and t.identifier = tm.MaxId;
    """

    # Use raw query on SQLAlchemy, as the programmatic buildup
    # would be overly complex, if even possible.
    last_runs = DB.session.execute(sql)
    return last_runs


def get_tag_counts():
    """return counts of all tags"""

    query = DB.session.query(Tag.name,
                             DB.func.count(Resource.identifier)).join(
        Resource.tags).group_by(Tag.id)
    return dict(query)


def load_data(file_path):
    # Beware!
    DB.drop_all()
    db_commit()

    DB.create_all()

    with open(file_path) as ff:
        objects = json.load(ff)

    # add users, keeping track of DB objects
    users = {}
    for user_name in objects['users']:
        user = objects['users'][user_name]
        user = User(user['username'],
                    user['password'],
                    user['email'],
                    user['role'])
        users[user_name] = user
        DB.session.add(user)

    # add tags, keeping track of DB objects
    tags = {}
    for tag_str in objects['tags']:
        tag = objects['tags'][tag_str]

        tag = Tag(tag)
        tags[tag_str] = tag
        DB.session.add(tag)

    # add Resources, keeping track of DB objects
    resources = {}
    for resource_name in objects['resources']:
        resource = objects['resources'][resource_name]

        resource_tags = []
        for tag_str in resource['tags']:
            resource_tags.append(tags[tag_str])

        resource = Resource(users[resource['owner']],
                            resource['resource_type'],
                            resource['title'],
                            resource['url'],
                            resource_tags)

        resources[resource_name] = resource
        DB.session.add(resource)

    # add Probes, keeping track of DB objects
    probes = {}
    for probe_name in objects['probe_vars']:
        probe = objects['probe_vars'][probe_name]

        probe = ProbeVars(resources[probe['resource']],
                          probe['probe_class'],
                          probe['parameters'],
                          )

        probes[probe_name] = probe
        DB.session.add(probe)

    # add Checks, keeping track of DB objects
    checks = {}
    for check_name in objects['check_vars']:
        check = objects['check_vars'][check_name]

        check = CheckVars(probes[check['probe_vars']],
                          check['check_class'],
                          check['parameters'],
                          )

        checks[check_name] = check
        DB.session.add(check)

    db_commit()


# commit or rollback shorthand
def db_commit():
    try:
        DB.session.commit()
    except Exception as err:
        DB.session.rollback()
        msg = str(err)
        LOGGER.error(msg)


if __name__ == '__main__':
    import sys

    APP = App.get_app()

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
                username = input('Enter your username: ').strip()
                password1 = input('Enter your password: ').strip()
                password2 = input('Enter your password again: ').strip()
                if password1 != password2:
                    raise ValueError('Passwords must match')
                email1 = input('Enter your email: ').strip()
                email2 = input('Enter your email again: ').strip()
                if email1 != email2:
                    raise ValueError('Emails must match')

            user_to_add = User(username, password1, email1, role='admin')
            DB.session.add(user_to_add)
            db_commit()
        elif sys.argv[1] == 'drop':
            print('Dropping database objects')
            DB.drop_all()
            db_commit()
        elif sys.argv[1] == 'load':
            print('Load database from JSON file (e.g. tests/fixtures.json)')
            if len(sys.argv) > 2:
                file_path = sys.argv[2]
                yesno = 'n'
                if len(sys.argv) == 3:
                    print('WARNING: all DB data will be lost! Proceed?')
                    yesno = input(
                        'Enter y (proceed) or n (abort): ').strip()
                elif len(sys.argv) == 4:
                    yesno = sys.argv[3]
                else:
                    sys.exit(0)

                if yesno == 'y':
                    print('Loading data....')
                    load_data(file_path)
                    print('Data loaded')
                else:
                    print('Aborted')
            else:
                print('Provide path to JSON file, e.g. tests/fixtures.json')

        elif sys.argv[1] == 'run':
            print('NOTICE: models.py no longer here.')
            print('Use: python healthcheck.py or upcoming cli.py')
        elif sys.argv[1] == 'flush':
            flush_runs()

        DB.session.remove()
