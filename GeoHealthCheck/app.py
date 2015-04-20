#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

import csv
from StringIO import StringIO

from flask import (abort, flash, Flask, g, jsonify, redirect,
                   render_template, request, url_for)

from flask.ext.login import (LoginManager, login_user, logout_user,
                             current_user, login_required)

from __init__ import __version__
from healthcheck import run_test_resource
from init import DB
from enums import RESOURCE_TYPES
from models import Resource, Run, User, Contact
import views

APP = Flask(__name__)
APP.config.from_pyfile('config.py')
APP.config.from_pyfile('../instance/config.py')
APP.secret_key = APP.config['SECRET_KEY']

LOGIN_MANAGER = LoginManager()
LOGIN_MANAGER.init_app(APP)

GHC_SITE_URL = APP.config['GHC_SITE_URL'].rstrip('/')


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
    return redirect(url_for('login', next=url))


@APP.before_request
def before_request():
    g.user = current_user


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
    return {
        'app_version': __version__,
        'resource_types': RESOURCE_TYPES,
        'resource_types_counts': views.get_resource_types_counts(),
    }


@APP.route('/')
def home():
    """homepage"""

    resource_type = None

    if request.args.get('resource_type') in RESOURCE_TYPES.keys():
        resource_type = request.args['resource_type']

    response = views.list_resources(resource_type)
    return render_template('home.html', response=response)


@APP.route('/export')
def export():
    """export resource list as JSON"""

    resource_type = None

    if request.args.get('resource_type') in RESOURCE_TYPES.keys():
        resource_type = request.args['resource_type']

    response = views.list_resources(resource_type)
    json_dict = {'resources': []}
    for r in response['resources']:
        json_dict['resources'].append({
            'resource_type': r.resource_type,
            'title': r.title,
            'url': r.url
        })
    return jsonify(json_dict)


## Add for export csv and json
@APP.route('/csv', endpoint='csv')
@APP.route('/json', endpoint='json')
@login_required
def exportz():
    """export resource list as JSON OR CSV"""

    resource_type = None

    if request.args.get('resource_type') in RESOURCE_TYPES.keys():
        resource_type = request.args['resource_type']

    response = views.list_resources(resource_type)

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
                'last_check': r.last_run.checked_datetime.strftime(
                    '%Y-%m-%dT%H:%M:%SZ'),
                'status': r.last_run.success,
                'response_time': round(r.average_response_time, 2),
                'reliability': round(r.reliability, 2)
            })
        return jsonify(json_dict)
    elif request.url_rule.rule == '/csv':
        output = StringIO()
        writer = csv.writer(output)
        header = [
            'resource_type', 'title', 'url', 'ghc_url', 'ghc_json', 'ghc_csv',
            'last_check', 'status', 'response_time', 'reliability'
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
                r.last_run.checked_datetime.strftime(
                    '%Y-%m-%dT%H:%M:%SZ'),
                r.last_run.success,
                round(r.average_response_time, 2),
                round(r.reliability, 2)
            ])
        return output.getvalue()


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
            'average_response_time': resource.average_response_time,
            'reliability': resource.reliability,
            'status': resource.last_run.success,
            'last_check': resource.last_run.checked_datetime.strftime(
                '%Y-%m-%dT%H:%M:%SZ'),
            'history_csv': history_csv,
            'history_json': history_json
        }
        return jsonify(json_dict)
    elif 'csv' in request.url_rule.rule:
        output = StringIO()
        writer = csv.writer(output)
        header = [
            'identifier', 'title', 'url', 'resource_type', 'owner',
            'average_response_time', 'reliability', 'status', 'last_check',
            'history_csv', 'history_json'
        ]
        writer.writerow(header)
        writer.writerow([
            resource.identifier,
            resource.title,
            resource.url,
            resource.resource_type,
            resource.owner.username,
            resource.average_response_time,
            resource.reliability,
            resource.last_run.success,
            resource.last_run.checked_datetime.strftime(
                '%Y-%m-%dT%H:%M:%SZ'),
            history_csv,
            history_json
        ])
        return output.getvalue()


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
        return output.getvalue()
    

@APP.route('/settings')
def settings():
    """settings"""
    pass


@APP.route('/resource/<identifier>')
def get_resource_by_id(identifier):
    """show resource"""
    response = views.get_resource_by_id(identifier)
    respcontacts = views.get_contacts_by_id_resource(identifier)

    return render_template('resource.html', resource=response, contacts = respcontacts)


@APP.route('/register', methods=['GET', 'POST'])
def register():
    """register a new user"""
    if not APP.config['GHC_SELF_REGISTER']:
        flash(u'Este sitio no está configurado para auto-registro.  '
              u'Póngase en contacto con %s ' % APP.config['GHC_ADMIN_EMAIL'], 'warning')
        return redirect(url_for('home'))
    if request.method == 'GET':
        return render_template('register.html')
    user = User(request.form['username'],
                request.form['password'], request.form['email'])
    DB.session.add(user)
    try:
        DB.session.commit()
    except Exception, err:
        DB.session.rollback()
        bad_column = err.message.split()[2]
        bad_value = request.form[bad_column]
        flash('%s %s ya registrado' % (bad_column, bad_value), 'danger')
        return redirect(url_for('register'))
    return redirect(url_for('login'))

@APP.route('/add/<string:resource_type>/<path:resource_url>/test')
@login_required
def testAndGetName(resource_type, resource_url):
    """test a resource"""

    if resource_url is None:
        resp = jsonify(messageJson = {
            'status': 'failure',
            'message': 'El url del recurso es inválido'
        })
        return resp
    if resource_type is None:
        resp = jsonify({
            'status': 'failure',
            'message': 'El tipo de recurso es inválido'
        })
        return resp
    try:
        [title, success, response_time, message, start_time] = run_test_resource(resource_type, resource_url)
        if message not in ['OK', None, 'None']:
            messageJson = {
                'status': 'failure',
                'message': message
            }
            resp = jsonify(messageJson)
            return resp
        else:
            #flash(u'Recurso probado con éxito', 'success')
            return jsonify({'status': 'success','title': title})
    except Exception, err:
        return jsonify({'status': 'failure','message': err})
    
    
@APP.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    """add resource"""
    if not g.user.is_authenticated():
        return render_template('add.html')
    if request.method == 'GET':
        return render_template('add.html')

    resource_type = request.form['resource_type']
    url = request.form['url'].strip()
    
    notification_mails = request.form['notification_mails'].strip()
    resTitle = request.form['title'].strip()
    
    resource = Resource.query.filter_by(resource_type=resource_type, url=url).first()
    
    if resource is not None:
        flash('Servicio ya registrado (%s, %s)' % (resource_type, url),
              'danger')
        if 'resource_type' in request.args:
            rtype = request.args.get('resource_type')
            return redirect(url_for('add',
                                    resource_type=rtype))
        return redirect(url_for('add'))

    [title, success, response_time, message, start_time] = run_test_resource(
        resource_type, url)

    if not success:
        flash(message, 'danger')
        return redirect(url_for('add', resource_type=resource_type))

    resource_to_add = Resource(current_user, resource_type, resTitle, url)
    
    run_to_add = Run(resource_to_add, success, response_time, message, start_time)
    DB.session.add(resource_to_add)
    DB.session.add(run_to_add)
    
    #Adicionando los correos.
    if not notification_mails == '':
        f = notification_mails.split(";");
        for mail in f:
            contact_to_add = Contact(resource_to_add, "email", mail)
            DB.session.add(contact_to_add)
        
    try:
        DB.session.commit()
        flash('Servicio registrado (%s, %s)' % (resource_type, url), 'success')
    except Exception, err:
        DB.session.rollback()
        flash(str(err), 'danger')
    return redirect(url_for('home'))


@APP.route('/resource/<int:resource_identifier>/update', methods=['POST'])
@login_required
def update(resource_identifier):
    """update a resource"""
    update_counter = 0
    resource_identifier_dict = request.get_json()
    resource = Resource.query.filter_by(identifier=resource_identifier).first()

    if resource_identifier_dict.get("emails") is not None:
        #Eliminamos los anteriores correos, luego se eliminan.
        contacts = Contact.query.filter_by(resource_identifier=resource_identifier).all()
        for contact in contacts:
            DB.session.delete(contact)
            update_counter += 1
        if update_counter > 0:
            DB.session.commit()
        for email in resource_identifier_dict.get("emails"):
            contact_to_add = Contact(resource, "email", email)
            DB.session.add(contact_to_add)
            update_counter += 1
        
    else:
        for key, value in resource_identifier_dict.iteritems():
            if getattr(resource, key) != resource_identifier_dict[key]:
                setattr(resource, key, resource_identifier_dict[key])
                update_counter += 1
    
    try:
        if update_counter > 0:
            DB.session.commit()
        return str({'status': 'success'})
    except Exception, err:
        DB.session.rollback()
        return str({'failure': 'Error contacte con el administrador'})


@APP.route('/resource/<int:resource_identifier>/test')
@login_required
def test(resource_identifier):
    """test a resource"""
    resource = Resource.query.filter_by(identifier=resource_identifier).first()
    if resource is None:
        flash('Recurso no encontrado', 'danger')
        return redirect(request.referrer)

    [title, success, response_time, message, start_time] = run_test_resource(
        resource.resource_type, resource.url)

    if message not in ['OK', None, 'None']:
        flash('ERROR: %s' % message, 'danger')
    else:
        flash(u'Recurso probado con éxito', 'success')

    return redirect(url_for('get_resource_by_id',
                    identifier=resource_identifier))




@APP.route('/resource/<int:resource_identifier>/delete')
@login_required
def delete(resource_identifier):
    """delete a resource"""
    resource = Resource.query.filter_by(identifier=resource_identifier).first()
    if g.user.role != 'admin' and g.user.username != resource.owner.username:
        flash('Usted no tiene acceso para eliminar este recurso', 'danger')
        return redirect('/resource/%s' % resource_identifier)

    if resource is None:
        flash('Recurso no encontrado', 'danger')
        return redirect(url_for('home'))

    runs = Run.query.filter_by(resource_identifier=resource_identifier).all()

    for run in runs:
        DB.session.delete(run)
        
    contacts = Contact.query.filter_by(resource_identifier=resource_identifier).all()
    
    for contact in contacts:
        DB.session.delete(contact)

    DB.session.delete(resource)

    try:
        DB.session.commit()
        flash('Recurso eliminado', 'success')
        return redirect(url_for('home'))
    except Exception, err:
        DB.session.rollback()
        flash(str(err), 'danger')
        return redirect(url_for(request.referrer))


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
        flash(u'Nombre de usuario y / o contraseña no válidos', 'danger')
        return redirect(url_for('login'))
    login_user(registered_user)

    if 'next' in request.args:
        return redirect(request.args.get('next'))
    return redirect(url_for('home'))


@APP.route('/logout')
def logout():
    """logout"""
    logout_user()
    flash(u'Cerrado la sesión', 'success')
    if request.referrer:
        return redirect(request.referrer)
    else:
        return redirect(url_for('home'))


if __name__ == '__main__':  # run locally, for fun
    import sys
    HOST = '0.0.0.0'
    PORT = 8000
    if len(sys.argv) > 1:
        HOST, PORT = sys.argv[1].split(':')
    APP.run(host=HOST, port=int(PORT), use_reloader=True, debug=True)
