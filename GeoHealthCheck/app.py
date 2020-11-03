# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
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

import base64
import csv
import json
import logging
from io import StringIO

from flask import (abort, flash, g, jsonify, redirect,
                   render_template, request, url_for)
from flask_babel import gettext
from flask_login import (LoginManager, login_user, logout_user,
                         current_user, login_required)
from flask_migrate import Migrate
from itertools import chain

import views
from __init__ import __version__
from enums import RESOURCE_TYPES
from factory import Factory
from init import App
from models import Resource, Run, ProbeVars, CheckVars, Tag, User, Recipient
from resourceauth import ResourceAuth
from util import send_email, geocode, format_checked_datetime, \
    format_run_status, format_obj_value

# Module globals for convenience
LOGGER = logging.getLogger(__name__)
APP = App.get_app()
CONFIG = App.get_config()
DB = App.get_db()
BABEL = App.get_babel()

MIGRATE = Migrate(APP, DB)

LOGIN_MANAGER = LoginManager()
LOGIN_MANAGER.init_app(APP)

LANGUAGES = (
    ('en', 'English'),
    ('fr', 'Français'),
    ('de', 'German'),
    ('nl_NL', 'Nederlands (Nederland)'),
    ('es_BO', 'Español (Bolivia)'),
    ('hr_HR', 'Croatian (Croatia)')
)

# Should GHC Runner be run within GHC webapp?
if CONFIG['GHC_RUNNER_IN_WEBAPP'] is True:
    LOGGER.info('Running GHC Scheduler in WebApp')
    from scheduler import start_schedule

    # Start scheduler
    start_schedule()
else:
    LOGGER.info('NOT Running GHC Scheduler in WebApp')


# commit or rollback shorthand
def db_commit():
    err = None
    try:
        DB.session.commit()
    except Exception:
        DB.session.rollback()
    # finally:
    #     DB.session.close()
    return err


@APP.before_request
def before_request():
    g.user = current_user
    if request.args and 'lang' in request.args and request.args['lang'] != '':
        g.current_lang = request.args['lang']
    if not hasattr(g, 'current_lang'):
        g.current_lang = 'en'

    if CONFIG['GHC_REQUIRE_WEBAPP_AUTH'] is True:
        # Login is required to access GHC Webapp.
        # We need to pass-through static resources like CSS.
        if any(['/static/' in request.path,
                request.path.endswith('.ico'),
                g.user.is_authenticated,  # This is from Flask-Login
                (request.endpoint is not None
                 and getattr(APP.view_functions[request.endpoint],
                             'is_public', False))]):
            return  # Access granted
        else:
            return redirect(url_for('login'))


# Marks (endpoint-) function as always to be accessible
# (used for GHC_REQUIRE_WEBAPP_AUTH)
def public_route(decorated_function):
    decorated_function.is_public = True
    return decorated_function


@APP.teardown_appcontext
def shutdown_session(exception=None):
    DB.session.remove()


@BABEL.localeselector
def get_locale():
    return g.get('current_lang', 'en')
    # return request.accept_languages.best_match(LANGUAGES.keys())


@LOGIN_MANAGER.user_loader
def load_user(identifier):
    return User.query.get(int(identifier))


@LOGIN_MANAGER.unauthorized_handler
def unauthorized_callback():
    if request.query_string:
        url = '%s%s?%s' % (request.script_root, request.path,
                           request.query_string)
    else:
        url = '%s%s' % (request.script_root, request.path)
    return redirect(url_for('login', lang=g.current_lang, next=url))


@LOGIN_MANAGER.request_loader
def load_user_from_request(request):

    # Try to login using Basic Auth
    # Inspiration: https://flask-login.readthedocs.io
    #              /en/latest/#custom-login-using-request-loader
    basic_auth_val = request.headers.get('Authorization')
    if basic_auth_val and CONFIG['GHC_BASIC_AUTH_DISABLED'] is False:
        basic_auth_val = basic_auth_val.replace('Basic ', '', 1)
        authenticated = False
        try:
            username, password = base64.b64decode(
                basic_auth_val.encode()).split(b':')

            user = User.query.filter_by(username=username).first()
            if user:
                authenticated = user.authenticate(password)
        finally:
            # Ignore errors, they should all fail the auth attempt
            pass

        if not authenticated:
            LOGGER.warning('Unauthorized access for user=%s' % username)
            abort(401)
        else:
            return user

    # TODO: may add login via api-key or token here

    # finally, return None if both methods did not login the user
    return None


@APP.template_filter('cssize_reliability')
def cssize_reliability(value, css_type=None):
    """returns CSS button class snippet based on score"""

    number = int(value)

    if CONFIG['GHC_RELIABILITY_MATRIX']['red']['min'] <= number <= \
            CONFIG['GHC_RELIABILITY_MATRIX']['red']['max']:
        score = 'danger'
        panel = 'red'
    elif (CONFIG['GHC_RELIABILITY_MATRIX']['orange']['min'] <= number <=
          CONFIG['GHC_RELIABILITY_MATRIX']['orange']['max']):
        score = 'warning'
        panel = 'yellow'
    elif (CONFIG['GHC_RELIABILITY_MATRIX']['green']['min'] <= number <=
          CONFIG['GHC_RELIABILITY_MATRIX']['green']['max']):
        score = 'success'
        panel = 'green'
    else:  # should never really get here
        score = 'info'
        panel = 'blue'

    if css_type is not None and css_type == 'panel':
        return panel
    else:
        return score


@APP.template_filter('cssize_reliability2')
def cssize_reliability2(value):
    """returns CSS panel class snippet based on score"""

    return cssize_reliability(value, 'panel')


@APP.template_filter('round2')
def round2(value):
    """rounds a number to 2 decimal places except for values of 0 or 100"""

    if value in [0.0, 100.0]:
        return int(value)
    return round(value, 2)


@APP.context_processor
def context_processors():
    """global context processors for templates"""

    rtc = views.get_resource_types_counts()
    tags = views.get_tag_counts()
    return {
        'app_version': __version__,
        'resource_types': RESOURCE_TYPES,
        'resource_types_counts': rtc['counts'],
        'resources_total': rtc['total'],
        'languages': LANGUAGES,
        'tags': tags,
        'tagnames': list(tags.keys())
    }


@APP.route('/')
def home():
    """homepage"""

    response = views.get_health_summary()
    return render_template('home.html', response=response)


@APP.route('/csv', endpoint='csv')
@APP.route('/json', endpoint='json')
def export():
    """export resource list as JSON"""

    resource_type = None

    if request.args.get('resource_type') in RESOURCE_TYPES.keys():
        resource_type = request.args['resource_type']

    query = request.args.get('q')

    response = views.list_resources(resource_type, query)

    if request.url_rule.rule == '/json':
        json_dict = {'total': response['total'], 'resources': []}
        for r in response['resources']:
            try:
                ghc_url = '%s/resource/%s' % \
                          (CONFIG['GHC_SITE_URL'], r.identifier)
                last_run_report = '-'
                if r.last_run:
                    last_run_report = r.last_run.report

                json_dict['resources'].append({
                    'resource_type': r.resource_type,
                    'title': r.title,
                    'url': r.url,
                    'ghc_url': ghc_url,
                    'ghc_json': '%s/json' % ghc_url,
                    'ghc_csv': '%s/csv' % ghc_url,
                    'first_run': format_checked_datetime(r.first_run),
                    'last_run': format_checked_datetime(r.last_run),
                    'status': format_run_status(r.last_run),
                    'min_response_time': round(r.min_response_time, 2),
                    'average_response_time': round(r.average_response_time, 2),
                    'max_response_time': round(r.max_response_time, 2),
                    'reliability': round(r.reliability, 2),
                    'last_report': format_obj_value(last_run_report)
                })
            except Exception as e:
                LOGGER.warning(
                    'JSON error resource id=%d: %s' % (r.identifier, str(e)))

        return jsonify(json_dict)
    elif request.url_rule.rule == '/csv':
        output = StringIO()
        writer = csv.writer(output)
        header = [
            'resource_type', 'title', 'url', 'ghc_url', 'ghc_json', 'ghc_csv',
            'first_run', 'last_run', 'status', 'min_response_time',
            'average_response_time', 'max_response_time', 'reliability'
        ]
        writer.writerow(header)
        for r in response['resources']:
            try:
                ghc_url = '%s%s' % (CONFIG['GHC_SITE_URL'],
                                    url_for('get_resource_by_id',
                                            identifier=r.identifier))

                writer.writerow([
                    r.resource_type,
                    r.title,
                    r.url,
                    ghc_url,
                    '%s/json' % ghc_url,
                    '%s/csv' % ghc_url,
                    format_checked_datetime(r.first_run),
                    format_checked_datetime(r.last_run),
                    format_run_status(r.last_run),
                    round(r.min_response_time, 2),
                    round(r.average_response_time, 2),
                    round(r.max_response_time, 2),
                    round(r.reliability, 2)
                ])
            except Exception as e:
                LOGGER.warning(
                    'CSV error resource id=%d: %s' % (r.identifier, str(e)))

        return output.getvalue(), 200, {'Content-type': 'text/csv'}


@APP.route('/opensearch')
def opensearch():
    """generate OpenSearch description document"""

    content = render_template('opensearch_description.xml')

    return content, 200, {'Content-type': 'text/xml'}


@APP.route('/resource/<identifier>/csv', endpoint='csv-resource')
@APP.route('/resource/<identifier>/json', endpoint='json-resource')
def export_resource(identifier):
    """export resource as JSON or CSV"""

    resource = views.get_resource_by_id(identifier)

    history_csv = '%s/resource/%s/history/csv' % (CONFIG['GHC_SITE_URL'],
                                                  resource.identifier)
    history_json = '%s/resource/%s/history/json' % (CONFIG['GHC_SITE_URL'],
                                                    resource.identifier)
    if 'json' in request.url_rule.rule:
        last_run_report = '-'
        if resource.last_run:
            last_run_report = resource.last_run.report

        json_dict = {
            'identifier': resource.identifier,
            'title': resource.title,
            'url': resource.url,
            'resource_type': resource.resource_type,
            'owner': resource.owner.username,
            'min_response_time': resource.min_response_time,
            'average_response_time': resource.average_response_time,
            'max_response_time': resource.max_response_time,
            'reliability': resource.reliability,
            'status': format_run_status(resource.last_run),
            'first_run': format_checked_datetime(resource.first_run),
            'last_run': format_checked_datetime(resource.last_run),
            'history_csv': history_csv,
            'history_json': history_json,
            'last_report': format_obj_value(last_run_report)
        }
        return jsonify(json_dict)
    elif 'csv' in request.url_rule.rule:
        output = StringIO()
        writer = csv.writer(output)
        header = [
            'identifier', 'title', 'url', 'resource_type', 'owner',
            'min_response_time', 'average_response_time', 'max_response_time',
            'reliability', 'status', 'first_run', 'last_run', 'history_csv',
            'history_json'
        ]

        writer.writerow(header)
        writer.writerow([
            resource.identifier,
            resource.title,
            resource.url,
            resource.resource_type,
            resource.owner.username,
            resource.min_response_time,
            resource.average_response_time,
            resource.max_response_time,
            resource.reliability,
            format_run_status(resource.last_run),
            format_checked_datetime(resource.first_run),
            format_checked_datetime(resource.last_run),
            history_csv,
            history_json
        ])
        return output.getvalue(), 200, {'Content-type': 'text/csv'}


@APP.route('/resource/<identifier>/history/csv',
           endpoint='csv-resource-history')
@APP.route('/resource/<identifier>/history/json',
           endpoint='json-resource-history')
def export_resource_history(identifier):
    """export resource history as JSON or CSV"""

    resource = views.get_resource_by_id(identifier)

    if 'json' in request.url_rule.rule:
        json_dict = {'runs': []}

        for run in resource.runs:
            json_dict['runs'].append({
                'owner': resource.owner.username,
                'resource_type': resource.resource_type,
                'checked_datetime': format_checked_datetime(run),
                'title': resource.title,
                'url': resource.url,
                'response_time': round(run.response_time, 2),
                'status': format_run_status(run)
            })
        return jsonify(json_dict)
    elif 'csv' in request.url_rule.rule:
        output = StringIO()
        writer = csv.writer(output)
        header = [
            'owner', 'resource_type', 'checked_datetime', 'title', 'url',
            'response_time', 'status'
        ]
        writer.writerow(header)
        for run in resource.runs:
            writer.writerow([
                resource.owner.username,
                resource.resource_type,
                format_checked_datetime(run),
                resource.title,
                resource.url,
                round(run.response_time, 2),
                format_run_status(run),
            ])
        return output.getvalue(), 200, {'Content-type': 'text/csv'}


@APP.route('/settings')
def settings():
    """settings"""
    pass


@APP.route('/resources')
def resources():
    """lists resources with optional filter"""

    resource_type = None

    if request.args.get('resource_type') in RESOURCE_TYPES.keys():
        resource_type = request.args['resource_type']

    tag = request.args.get('tag')

    query = request.args.get('q')

    response = views.list_resources(resource_type, query, tag)
    return render_template('resources.html', response=response)


@APP.route('/resource/<identifier>')
def get_resource_by_id(identifier):
    """show resource"""

    response = views.get_resource_by_id(identifier)
    return render_template('resource.html', resource=response)


@APP.route('/register', methods=['GET', 'POST'])
def register():
    """register a new user"""
    if not CONFIG['GHC_SELF_REGISTER']:
        msg1 = gettext('This site is not configured for self-registration')
        msg2 = gettext('Please contact')
        msg = '%s.  %s %s' % (msg1, msg2,
                              CONFIG['GHC_ADMIN_EMAIL'])
        flash('%s' % msg, 'danger')
        return render_template('register.html', errmsg=msg)
    if request.method == 'GET':
        return render_template('register.html')

    # Check for existing user or email
    user = User.query.filter_by(username=request.form['username']).first()
    email = User.query.filter_by(email=request.form['email']).first()
    if user or email:
        flash('%s' % gettext('Invalid username or email'), 'danger')
        return render_template('register.html')

    user = User(request.form['username'],
                request.form['password'], request.form['email'])

    DB.session.add(user)
    try:
        DB.session.commit()
    except Exception as err:
        DB.session.rollback()
        bad_column = err.message.split()[2]
        bad_value = request.form[bad_column]
        msg = gettext('already registered')
        flash('%s %s %s' % (bad_column, bad_value, msg), 'danger')
        return redirect(url_for('register', lang=g.current_lang))
    return redirect(url_for('login', lang=g.current_lang))


@APP.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    """add resource"""
    if request.method == 'GET':
        return render_template('add.html')
    resource_type = request.form['resource_type']
    tags = request.form.getlist('tags')
    url = request.form['url'].strip()
    resources_to_add = []

    from healthcheck import sniff_test_resource, run_test_resource
    sniffed_resources = sniff_test_resource(CONFIG, resource_type, url)

    if not sniffed_resources:
        msg = gettext("No resources detected")
        LOGGER.exception()
        flash(msg, 'danger')

    for (resource_type, resource_url,
         title, success, response_time,
         message, start_time, resource_tags,) in sniffed_resources:

        tags_to_add = []
        for tag in chain(tags, resource_tags):
            tag_obj = tag
            if not isinstance(tag, Tag):
                tag_obj = Tag.query.filter_by(name=tag).first()
                if tag_obj is None:
                    tag_obj = Tag(name=tag)
            tags_to_add.append(tag_obj)

        resource_to_add = Resource(current_user,
                                   resource_type,
                                   title,
                                   resource_url,
                                   tags=tags_to_add)

        resources_to_add.append(resource_to_add)
        probe_to_add = None
        checks_to_add = []

        # Always add a default Probe and Check(s)
        # from the GHC_PROBE_DEFAULTS conf
        if resource_type in CONFIG['GHC_PROBE_DEFAULTS']:
            resource_settings = CONFIG['GHC_PROBE_DEFAULTS'][resource_type]
            probe_class = resource_settings['probe_class']
            if probe_class:
                # Add the default Probe
                probe_obj = Factory.create_obj(probe_class)
                probe_to_add = ProbeVars(
                    resource_to_add, probe_class,
                    probe_obj.get_default_parameter_values())

                # Add optional default (parameterized)
                # Checks to add to this Probe
                checks_info = probe_obj.get_checks_info()
                checks_param_info = probe_obj.get_plugin_vars()['CHECKS_AVAIL']
                for check_class in checks_info:
                    check_param_info = checks_param_info[check_class]
                    if 'default' in checks_info[check_class]:
                        if checks_info[check_class]['default']:
                            # Filter out params for Check with fixed values
                            param_defs = check_param_info['PARAM_DEFS']
                            param_vals = {}
                            for param in param_defs:
                                if param_defs[param]['value']:
                                    param_vals[param] = \
                                        param_defs[param]['value']
                            check_vars = CheckVars(
                                probe_to_add, check_class, param_vals)
                            checks_to_add.append(check_vars)

        result = run_test_resource(resource_to_add)

        run_to_add = Run(resource_to_add, result)

        DB.session.add(resource_to_add)
        # prepopulate notifications for current user
        resource_to_add.set_recipients('email', [g.user.email])

        if probe_to_add:
            DB.session.add(probe_to_add)
        for check_to_add in checks_to_add:
            DB.session.add(check_to_add)
            DB.session.add(run_to_add)

    try:
        DB.session.commit()
        msg = gettext('Services registered')
        flash('%s (%s, %s)' % (msg, resource_type, url), 'success')
    except Exception as err:
        DB.session.rollback()
        flash(str(err), 'danger')
        return redirect(url_for('home', lang=g.current_lang))

    if len(resources_to_add) == 1:
        return edit_resource(resources_to_add[0].identifier)
    return redirect(url_for('home', lang=g.current_lang))


@APP.route('/resource/<int:resource_identifier>/update', methods=['POST'])
@login_required
def update(resource_identifier):
    """update a resource"""

    update_counter = 0
    status = 'success'

    try:
        resource_identifier_dict = request.get_json()

        resource = Resource.query.filter_by(
            identifier=resource_identifier).first()

        for key, value in resource_identifier_dict.items():
            if key == 'tags':
                resource_tags = [t.name for t in resource.tags]

                tags_to_add = set(value) - set(resource_tags)
                tags_to_delete = set(resource_tags) - set(value)

                # Existing Tags: create relation else add new Tag
                all_tag_objs = Tag.query.all()
                for tag in tags_to_add:
                    tag_add_obj = None
                    for tag_obj in all_tag_objs:
                        if tag == tag_obj.name:
                            # use existing
                            tag_add_obj = tag_obj
                            break

                    if not tag_add_obj:
                        # add new
                        tag_add_obj = Tag(name=tag)
                        DB.session.add(tag_add_obj)

                    resource.tags.append(tag_add_obj)

                for tag in tags_to_delete:
                    tag_to_delete = Tag.query.filter_by(name=tag).first()
                    resource.tags.remove(tag_to_delete)

                update_counter += 1
            elif key == 'probes':
                # Remove all existing ProbeVars for Resource
                for probe_var in resource.probe_vars:
                    resource.probe_vars.remove(probe_var)

                # Add ProbeVars anew each with optional CheckVars
                for probe in value:
                    LOGGER.info('adding Probe class=%s parms=%s' %
                                (probe['probe_class'], str(probe)))
                    probe_vars = ProbeVars(resource, probe['probe_class'],
                                           probe['parameters'])
                    for check in probe['checks']:
                        check_vars = CheckVars(
                            probe_vars, check['check_class'],
                            check['parameters'])
                        probe_vars.check_vars.append(check_vars)

                    resource.probe_vars.append(probe_vars)

                update_counter += 1
            elif key == 'notify_emails':
                resource.set_recipients('email',
                                        [v for v in value if v.strip()])
            elif key == 'notify_webhooks':
                resource.set_recipients('webhook',
                                        [v for v in value if v.strip()])
            elif key == 'auth':
                resource.auth = value
            elif getattr(resource, key) != resource_identifier_dict[key]:
                # Update other resource attrs, mainly 'name'
                setattr(resource, key, resource_identifier_dict[key])
                min_run_freq = CONFIG['GHC_MINIMAL_RUN_FREQUENCY_MINS']
                if int(resource.run_frequency) < min_run_freq:
                    resource.run_frequency = min_run_freq
                update_counter += 1

        # Always update geo-IP: maybe failure on creation or
        # IP-address of URL may have changed.
        latitude, longitude = geocode(resource.url)
        if latitude != 0.0 and longitude != 0.0:
            # Only update for valid lat/lon
            resource.latitude = latitude
            resource.longitude = longitude
            update_counter += 1

    except Exception as err:
        LOGGER.error("Cannot update resource: %s", err, exc_info=err)
        DB.session.rollback()
        status = str(err)
        update_counter = 0
    # finally:
    #     DB.session.close()

    if update_counter > 0:
        err = db_commit()
        if err:
            status = str(err)

    return jsonify({'status': status})


@APP.route('/resource/<int:resource_identifier>/test', methods=['GET', 'POST'])
@login_required
def test(resource_identifier):
    """test a resource"""
    resource = Resource.query.filter_by(identifier=resource_identifier).first()
    if resource is None:
        flash(gettext('Resource not found'), 'danger')
        return redirect(request.referrer)

    from healthcheck import run_test_resource
    result = run_test_resource(
        resource)

    if request.method == 'GET':
        if result.message == 'Skipped':
            msg = gettext('INFO')
            flash('%s: %s' % (msg, result.message), 'info')
        elif result.message not in ['OK', None, 'None']:
            msg = gettext('ERROR')
            flash('%s: %s' % (msg, result.message), 'danger')
        else:
            flash(gettext('Resource tested successfully'), 'success')

        return redirect(url_for('get_resource_by_id', lang=g.current_lang,
                                identifier=resource_identifier))
    elif request.method == 'POST':
        return jsonify(result.get_report())


@APP.route('/resource/<int:resource_identifier>/edit')
@login_required
def edit_resource(resource_identifier):
    """edit a resource"""
    resource = Resource.query.filter_by(identifier=resource_identifier).first()
    if resource is None:
        flash(gettext('Resource not found'), 'danger')
        return redirect(request.referrer)

    probes_avail = views.get_probes_avail(resource.resource_type, resource)

    suggestions = json.dumps(Recipient.get_suggestions('email',
                                                       g.user.username))

    return render_template('edit_resource.html',
                           lang=g.current_lang,
                           resource=resource,
                           suggestions=suggestions,
                           auths_avail=ResourceAuth.get_auth_defs(),
                           probes_avail=probes_avail)


@APP.route('/resource/<int:resource_identifier>/delete')
@login_required
def delete(resource_identifier):
    """delete a resource"""
    resource = Resource.query.filter_by(identifier=resource_identifier).first()
    if g.user.role != 'admin' and g.user.username != resource.owner.username:
        msg = gettext('You do not have access to delete this resource')
        flash(msg, 'danger')
        return redirect(url_for('get_resource_by_id', lang=g.current_lang,
                                identifier=resource_identifier))

    if resource is None:
        flash(gettext('Resource not found'), 'danger')
        return redirect(url_for('home', lang=g.current_lang))

    resource.clear_recipients()
    DB.session.delete(resource)

    try:
        DB.session.commit()
        flash(gettext('Resource deleted'), 'success')
        return redirect(url_for('home', lang=g.current_lang))
    except Exception as err:
        DB.session.rollback()
        flash(str(err), 'danger')
        return redirect(url_for(request.referrer))


@APP.route('/probe/<string:probe_class>/<int:resource_identifier>/edit_form')
@APP.route('/probe/<string:probe_class>/edit_form')
@login_required
def get_probe_edit_form(probe_class, resource_identifier=None):
    """get the form to edit a Probe"""

    probe_obj = Factory.create_obj(probe_class)
    if resource_identifier:
        resource = views.get_resource_by_id(resource_identifier)
        if resource:
            probe_obj._resource = resource
            probe_obj.expand_params(resource)

    probe_info = probe_obj.get_plugin_vars()
    probe_vars = ProbeVars(
        None, probe_class, probe_obj.get_default_parameter_values())

    # Get only the default Checks for this Probe class
    checks_avail = probe_obj.get_checks_info_defaults()
    checks_avail = probe_obj.expand_check_vars(checks_avail)

    for check_class in checks_avail:
        check_obj = Factory.create_obj(check_class)
        check_params = check_obj.get_default_parameter_values()
        probe_check_param_defs = \
            probe_info['CHECKS_AVAIL'][check_class]['PARAM_DEFS']
        for param in probe_check_param_defs:
            if 'value' in probe_check_param_defs[param]:
                check_params[param] = probe_check_param_defs[param]['value']

        # Appends 'check_vars' to 'probe_vars' (SQLAlchemy)
        CheckVars(probe_vars, check_class, check_params)

    return render_template('includes/probe_edit_form.html',
                           lang=g.current_lang,
                           probe=probe_vars, probe_info=probe_info)


@APP.route('/check/<string:check_class>/edit_form')
@login_required
def get_check_edit_form(check_class):
    """get the form to edit a Check"""

    check_obj = Factory.create_obj(check_class)
    check_info = check_obj.get_plugin_vars()
    check_vars = CheckVars(
        None, check_class, check_obj.get_default_parameter_values())

    return render_template('includes/check_edit_form.html',
                           lang=g.current_lang,
                           check=check_vars, check_info=check_info)


@APP.route('/login', methods=['GET', 'POST'])
@public_route
def login():
    """login"""
    if request.method == 'GET':
        return render_template('login.html')
    username = request.form['username']
    password = request.form['password']
    registered_user = User.query.filter_by(username=username).first()
    authenticated = False
    if registered_user:
        # May not have upgraded to pw encryption: warn
        if len(registered_user.password) < 80:
            msg = 'Please upgrade GHC to encrypted passwords first, see docs!'
            flash(gettext(msg), 'danger')
            return redirect(url_for('login', lang=g.current_lang))

        try:
            authenticated = registered_user.authenticate(password)
        finally:
            pass

    if not authenticated:
        flash(gettext('Invalid username and / or password'), 'danger')
        return redirect(url_for('login', lang=g.current_lang))

    # Login ok
    login_user(registered_user)

    if 'next' in request.args:
        return redirect(request.args.get('next'))
    return redirect(url_for('home', lang=g.current_lang))


@APP.route('/logout')
def logout():
    """logout"""
    logout_user()
    flash(gettext('Logged out'), 'success')
    if request.referrer:
        return redirect(request.referrer)
    else:
        return redirect(url_for('home', lang=g.current_lang))


@APP.route('/reset_req', methods=['GET', 'POST'])
@public_route
def reset_req():
    """
    Reset password request handling.
    """
    if request.method == 'GET':
        return render_template('reset_password_request.html')

    # Reset request form with email
    email = request.form['email']
    registered_user = User.query.filter_by(email=email).first()
    if registered_user is None:
        LOGGER.warn('Invalid email for reset_req: %s' % email)
        flash(gettext('Invalid email'), 'danger')
        return redirect(url_for('reset_req', lang=g.current_lang))

    # Generate reset url using user-specific token
    token = registered_user.get_token()
    reset_url = '%s/reset/%s' % (CONFIG['GHC_SITE_URL'], token)

    # Create message body with reset link
    msg_body = render_template('reset_password_email.txt',
                               lang=g.current_lang, config=CONFIG,
                               reset_url=reset_url,
                               username=registered_user.username)

    try:
        from email.mime.text import MIMEText
        from email.utils import formataddr
        msg = MIMEText(msg_body, 'plain', 'utf-8')
        msg['From'] = formataddr((CONFIG['GHC_SITE_TITLE'],
                                  CONFIG['GHC_ADMIN_EMAIL']))
        msg['To'] = registered_user.email
        msg['Subject'] = '[%s] %s' % (CONFIG['GHC_SITE_TITLE'],
                                      gettext('reset password'))

        from_addr = '%s <%s>' % (CONFIG['GHC_SITE_TITLE'],
                                 CONFIG['GHC_ADMIN_EMAIL'])

        to_addr = registered_user.email

        msg_text = msg.as_string()
        send_email(CONFIG['GHC_SMTP'], from_addr, to_addr, msg_text)
    except Exception as err:
        msg = 'Cannot send email. Contact admin: '
        LOGGER.warn(msg + ' err=' + str(err))
        flash(gettext(msg) + CONFIG['GHC_ADMIN_EMAIL'], 'danger')
        return redirect(url_for('login', lang=g.current_lang))

    flash(gettext('Password reset link sent via email'), 'success')

    if 'next' in request.args:
        return redirect(request.args.get('next'))
    return redirect(url_for('home', lang=g.current_lang))


@APP.route('/reset/<token>', methods=['GET', 'POST'])
@public_route
def reset(token=None):
    """
    Reset password submit form handling.
    """

    # Must have at least a token to proceed.
    if token is None:
        return redirect(url_for('reset_req', lang=g.current_lang))

    # Token received: verify if ok, may also time-out.
    registered_user = User.verify_token(token)
    if registered_user is None:
        LOGGER.warn('Cannot find User from token: %s' % token)
        flash(gettext('Invalid token'), 'danger')
        return redirect(url_for('login', lang=g.current_lang))

    # Token and user ok: return reset form.
    if request.method == 'GET':
        return render_template('reset_password_form.html')

    # Valid token and user: change password from form-value
    password = request.form['password']
    if not password:
        flash(gettext('Password required'), 'danger')
        return redirect(url_for('reset/%s' % token, lang=g.current_lang))
    registered_user.set_password(password)
    DB.session.add(registered_user)

    try:
        DB.session.commit()
        flash(gettext('Update password OK'), 'success')
    except Exception as err:
        msg = 'Update password failed!'
        LOGGER.warn(msg + ' err=' + str(err))
        DB.session.rollback()
        flash(gettext(msg), 'danger')

    # Finally redirect user to login page
    return redirect(url_for('login', lang=g.current_lang))


#
# REST Interface Calls
#

@APP.route('/api/v1.0/summary')
@APP.route('/api/v1.0/summary/')
@APP.route('/api/v1.0/summary.<content_type>')
def api_summary(content_type='json'):
    """
    Get health summary for all Resources within this instance.
    """

    health_summary = views.get_health_summary()

    # Convert Runs to dict-like structure
    for run in ['first_run', 'last_run']:
        run_obj = health_summary.get(run, None)
        if run_obj:
            health_summary[run] = run_obj.for_json()

    # Convert Resources failing to dict-like structure
    failed_resources = []
    for resource in health_summary['failed_resources']:
        failed_resources.append(resource.for_json())
    health_summary['failed_resources'] = failed_resources

    if content_type == 'json':
        result = jsonify(health_summary)
    else:
        result = '<pre>\n%s\n</pre>' % \
                 render_template('status_report_email.txt',
                                 lang=g.current_lang, summary=health_summary)
    return result


@APP.route('/api/v1.0/probes-avail/')
@APP.route('/api/v1.0/probes-avail/<resource_type>')
@APP.route('/api/v1.0/probes-avail/<resource_type>/<int:resource_id>')
def api_probes_avail(resource_type=None, resource_id=None):
    """
    Get available (configured) Probes for this
    installation, optional for resource type
    """
    resource = None
    if resource_id:
        resource = views.get_resource_by_id(resource_id)

    probes = views.get_probes_avail(resource_type=resource_type,
                                    resource=resource)
    return jsonify(probes)


@APP.route('/api/v1.0/runs/<int:resource_id>')
@APP.route('/api/v1.0/runs/<int:resource_id>.<content_type>')
@APP.route('/api/v1.0/runs/<int:resource_id>/<int:run_id>')
@APP.route('/api/v1.0/runs/<int:resource_id>/<int:run_id>.<content_type>')
def api_runs(resource_id, run_id=None, content_type='json'):
    """
    Get Runs (History of results) for Resource.
    """
    if run_id:
        runs = [views.get_run_by_id(run_id)]
    else:
        runs = views.get_run_by_resource_id(resource_id)

    run_arr = []
    for run in runs:
        run_dict = {
            'id': run.identifier,
            'success': run.success,
            'response_time':  run.response_time,
            'checked_datetime': run.checked_datetime,
            'message':  run.message,
            'report': run.report
        }
        run_arr.append(run_dict)

    runs_dict = {'total': len(run_arr), 'runs': run_arr}
    result = 'unknown'
    if content_type == 'json':
        result = jsonify(runs_dict)
    elif content_type == 'html':
        result = render_template('includes/runs.html',
                                 lang=g.current_lang, runs=runs_dict['runs'])
    return result


if __name__ == '__main__':  # run locally, for fun
    import sys

    HOST = '0.0.0.0'
    PORT = 8000
    if len(sys.argv) > 1:
        HOST, PORT = sys.argv[1].split(':')
    APP.run(host=HOST, port=int(PORT), use_reloader=True, debug=True)
