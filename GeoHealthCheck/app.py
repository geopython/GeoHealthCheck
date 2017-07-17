# coding=utf-8
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

import csv
from datetime import datetime, timedelta
from StringIO import StringIO

from flask import (flash, Flask, g, jsonify, redirect,
                   render_template, request, url_for)
from flask_babel import Babel, gettext
from flask_login import (LoginManager, login_user, logout_user,
                         current_user, login_required)
from flask_migrate import Migrate

from __init__ import __version__
from healthcheck import sniff_test_resource, run_test_resource
from init import DB
from enums import RESOURCE_TYPES
from models import Resource, Run, ProbeVars, CheckVars, Tag, User
from factory import Factory
from util import render_template2, send_email
import views

APP = Flask(__name__)
BABEL = Babel(APP)
APP.config.from_pyfile('config_main.py')
APP.config.from_pyfile('../instance/config_site.py')
APP.secret_key = APP.config['SECRET_KEY']

MIGRATE = Migrate(APP, DB)

LOGIN_MANAGER = LoginManager()
LOGIN_MANAGER.init_app(APP)

GHC_SITE_URL = APP.config['GHC_SITE_URL'].rstrip('/')

LANGUAGES = (
    ('en', 'English'),
    ('fr', 'Français'),
    ('de', 'German'),
    ('de_DE', 'German (Germany)'),
    ('nl_NL', 'Nederlands (Nederland)'),
    ('es_BO', 'Español (Bolivia)')
)


# commit or rollback shorthand
def db_commit():
    err = None
    try:
        DB.session.commit()
    except Exception as err:
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


def next_page_refresh():
    """determines when to refresh webapp based on GHC_RUN_FREQUENCY"""

    now = datetime.now()

    frequency = APP.config['GHC_RUN_FREQUENCY']

    if frequency == 'hourly':  # get next hour
        now2 = now.replace(minute=0, second=0, microsecond=0)
        refresh = timedelta(hours=1)
    elif frequency == 'daily':  # get next day
        now2 = now.replace(hour=0, minute=0, second=0, microsecond=0)
        refresh = timedelta(days=1)
    elif frequency == ['weekly']:  # get next day
        now2 = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        refresh = timedelta(weeks=1)
    elif frequency == ['monthly']:
        now2 = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        refresh = timedelta(weeks=4)
    elif frequency == ['yearly']:  # get next day
        now2 = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        refresh = timedelta(weeks=52)

    next_frequency = now2 + refresh
    differ = next_frequency - now

    return differ.seconds


@APP.template_filter('cssize_reliability')
def cssize_reliability(value, css_type=None):
    """returns CSS button class snippet based on score"""

    number = int(value)

    if APP.config['GHC_RELIABILITY_MATRIX']['red']['min'] <= number <= \
            APP.config['GHC_RELIABILITY_MATRIX']['red']['max']:
        score = 'danger'
        panel = 'red'
    elif (APP.config['GHC_RELIABILITY_MATRIX']['orange']['min'] <= number <=
            APP.config['GHC_RELIABILITY_MATRIX']['orange']['max']):
        score = 'warning'
        panel = 'yellow'
    elif (APP.config['GHC_RELIABILITY_MATRIX']['green']['min'] <= number <=
            APP.config['GHC_RELIABILITY_MATRIX']['green']['max']):
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
        'next_page_refresh': next_page_refresh(),
        'resource_types': RESOURCE_TYPES,
        'resource_types_counts': rtc['counts'],
        'resources_total': rtc['total'],
        'languages': LANGUAGES,
        'tags': tags
    }


@APP.route('/')
def home():
    """homepage"""

    resource_type = None

    if request.args.get('resource_type') in RESOURCE_TYPES.keys():
        resource_type = request.args['resource_type']

    tag = request.args.get('tag')

    query = request.args.get('q')

    response = views.list_resources(resource_type, query, tag)
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
            ghc_url = '%s/resource/%s' % (GHC_SITE_URL, r.identifier)
            json_dict['resources'].append({
                'resource_type': r.resource_type,
                'title': r.title,
                'url': r.url,
                'ghc_url': ghc_url,
                'ghc_json': '%s/json' % ghc_url,
                'ghc_csv': '%s/csv' % ghc_url,
                'first_run': r.first_run.checked_datetime.strftime(
                    '%Y-%m-%dT%H:%M:%SZ'),
                'last_run': r.last_run.checked_datetime.strftime(
                    '%Y-%m-%dT%H:%M:%SZ'),
                'status': r.last_run.success,
                'min_response_time': round(r.min_response_time, 2),
                'average_response_time': round(r.average_response_time, 2),
                'max_response_time': round(r.max_response_time, 2),
                'reliability': round(r.reliability, 2),
                'last_report': r.last_run.report
            })
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
            ghc_url = '%s%s' % (GHC_SITE_URL,
                                url_for('get_resource_by_id',
                                        identifier=r.identifier))
            writer.writerow([
                r.resource_type,
                r.title,
                r.url,
                ghc_url,
                '%s/json' % ghc_url,
                '%s/csv' % ghc_url,
                r.first_run.checked_datetime.strftime(
                    '%Y-%m-%dT%H:%M:%SZ'),
                r.last_run.checked_datetime.strftime(
                    '%Y-%m-%dT%H:%M:%SZ'),
                r.last_run.success,
                round(r.average_response_time, 2),
                round(r.reliability, 2)
            ])
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

    history_csv = '%s/resource/%s/history/csv' % (GHC_SITE_URL,
                                                  resource.identifier)
    history_json = '%s/resource/%s/history/json' % (GHC_SITE_URL,
                                                    resource.identifier)
    if 'json' in request.url_rule.rule:
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
            'status': resource.last_run.success,
            'first_run': resource.first_run.checked_datetime.strftime(
                '%Y-%m-%dT%H:%M:%SZ'),
            'last_run': resource.last_run.checked_datetime.strftime(
                '%Y-%m-%dT%H:%M:%SZ'),
            'history_csv': history_csv,
            'history_json': history_json,
            'last_report': resource.last_run.report
        }
        return jsonify(json_dict)
    elif 'csv' in request.url_rule.rule:
        output = StringIO()
        writer = csv.writer(output)
        header = [
            'identifier', 'title', 'url', 'resource_type', 'owner',
            'min_response_time', 'average_response_time', 'max_response_tie',
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
            resource.last_run.success,
            resource.first_run.checked_datetime.strftime(
                '%Y-%m-%dT%H:%M:%SZ'),
            resource.last_run.checked_datetime.strftime(
                '%Y-%m-%dT%H:%M:%SZ'),
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
                'checked_datetime': run.checked_datetime.strftime(
                    '%Y-%m-%dT%H:%M:%SZ'),
                'title': resource.title,
                'url': resource.url,
                'response_time': round(run.response_time, 2),
                'status': run.success
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
                run.checked_datetime.strftime(
                    '%Y-%m-%dT%H:%M:%SZ'),
                resource.title,
                resource.url,
                run.response_time,
                run.success,
            ])
        return output.getvalue(), 200, {'Content-type': 'text/csv'}


@APP.route('/settings')
def settings():
    """settings"""
    pass


@APP.route('/resource/<identifier>')
def get_resource_by_id(identifier):
    """show resource"""

    response = views.get_resource_by_id(identifier)
    return render_template('resource.html', resource=response)


@APP.route('/register', methods=['GET', 'POST'])
def register():
    """register a new user"""
    if not APP.config['GHC_SELF_REGISTER']:
        msg1 = gettext('This site is not configured for self-registration')
        msg2 = gettext('Please contact')
        msg = '%s.  %s %s' % (msg1, msg2,
                              APP.config['GHC_ADMIN_EMAIL'])
        return render_template('register.html', errmsg=msg)
    if request.method == 'GET':
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
    if not g.user.is_authenticated():
        return render_template('add.html')
    if request.method == 'GET':
        return render_template('add.html')

    tag_list = []

    resource_type = request.form['resource_type']
    tags = request.form.getlist('tags')
    url = request.form['url'].strip()
    resource = Resource.query.filter_by(resource_type=resource_type,
                                        url=url).first()
    if resource is not None:
        msg = gettext('Service already registered')
        flash('%s (%s, %s)' % (msg, resource_type, url), 'danger')
        if 'resource_type' in request.args:
            rtype = request.args.get('resource_type')
            return redirect(url_for('add', lang=g.current_lang,
                                    resource_type=rtype))
        return redirect(url_for('add', lang=g.current_lang))

    [title, success, response_time, message, start_time] = sniff_test_resource(
        APP.config, resource_type, url)

    if not success:
        flash(message, 'danger')
        return redirect(url_for('add', lang=g.current_lang,
                                resource_type=resource_type))

    if tags:
        for tag in tags:
            tag_found = False
            for tag_obj in Tag.query.all():
                if tag == tag_obj.name:  # use existing
                    tag_found = True
                    tag_list.append(tag_obj)
            if not tag_found:  # add new
                tag_list.append(Tag(name=tag))

    resource_to_add = Resource(current_user, resource_type, title, url,
                               tags=tag_list)

    probe_to_add = None
    checks_to_add = []

    # Always add a default Probe and Check(s)  from the GHC_PROBE_DEFAULTS conf
    if resource_type in APP.config['GHC_PROBE_DEFAULTS']:
        resource_settings = APP.config['GHC_PROBE_DEFAULTS'][resource_type]
        probe_class = resource_settings['probe_class']
        if probe_class:
            # Add the default Probe
            probe_obj = Factory.create_obj(probe_class)
            probe_to_add = ProbeVars(
                resource_to_add, probe_class,
                probe_obj.get_default_parameter_values())

            # Add optional default (parameterized) Checks to add to this Probe
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
                                param_vals[param] = param_defs[param]['value']
                        check_vars = CheckVars(
                            probe_to_add, check_class, param_vals)
                        checks_to_add.append(check_vars)

    result = run_test_resource(resource_to_add)

    run_to_add = Run(resource_to_add, result)

    DB.session.add(resource_to_add)
    if probe_to_add:
        DB.session.add(probe_to_add)
    for check_to_add in checks_to_add:
        DB.session.add(check_to_add)
    DB.session.add(run_to_add)

    try:
        DB.session.commit()
        msg = gettext('Service registered')
        flash('%s (%s, %s)' % (msg, resource_type, url), 'success')
    except Exception as err:
        DB.session.rollback()
        flash(str(err), 'danger')
        return redirect(url_for('home', lang=g.current_lang))
    else:
        return edit_resource(resource_to_add.identifier)


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
                    print('adding Probe class=%s parms=%s' %
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

            elif getattr(resource, key) != resource_identifier_dict[key]:
                # Update other resource attrs, mainly 'name'
                setattr(resource, key, resource_identifier_dict[key])
                update_counter += 1

    except Exception as err:
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

    result = run_test_resource(
        resource)

    if request.method == 'GET':
        if result.message not in ['OK', None, 'None']:
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

    return render_template('edit_resource.html', lang=g.current_lang,
                           resource=resource, probes_avail=probes_avail)


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

    runs = Run.query.filter_by(resource_identifier=resource_identifier).all()

    for run in runs:
        DB.session.delete(run)

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

    print(str(check_info))
    return render_template('includes/check_edit_form.html',
                           lang=g.current_lang,
                           check=check_vars, check_info=check_info)


@APP.route('/login', methods=['GET', 'POST'])
def login():
    """login"""
    if request.method == 'GET':
        return render_template('login.html')
    username = request.form['username']
    password = request.form['password']
    registered_user = User.query.filter_by(username=username,
                                           password=password).first()
    if registered_user is None:
        flash(gettext('Invalid username and / or password'), 'danger')
        return redirect(url_for('login', lang=g.current_lang))
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


@APP.route('/recover', methods=['GET', 'POST'])
def recover():
    """recover"""
    if request.method == 'GET':
        return render_template('recover_password.html')
    username = request.form['username']
    registered_user = User.query.filter_by(username=username, ).first()
    if registered_user is None:
        flash(gettext('Invalid username'), 'danger')
        return redirect(url_for('recover', lang=g.current_lang))

    fromaddr = '%s <%s>' % (APP.config['GHC_SITE_TITLE'],
                            APP.config['GHC_ADMIN_EMAIL'])
    toaddr = registered_user.email

    template_vars = {
        'config': APP.config,
        'password': registered_user.password
    }
    msg = render_template2('recover_password_email.txt', template_vars)

    send_email(APP.config['GHC_SMTP'], fromaddr, toaddr, msg)

    flash(gettext('Password sent via email'), 'success')

    if 'next' in request.args:
        return redirect(request.args.get('next'))
    return redirect(url_for('home', lang=g.current_lang))


#
# REST Interface Calls
#


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


if __name__ == '__main__':  # run locally, for fun
    import sys

    HOST = '0.0.0.0'
    PORT = 8000
    if len(sys.argv) > 1:
        HOST, PORT = sys.argv[1].split(':')
    APP.run(host=HOST, port=int(PORT), use_reloader=True, debug=True)
