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

import os
import shutil
import tempfile
from StringIO import StringIO
from urllib2 import urlopen
import zipfile

from paver.easy import (Bunch, call_task, cmdopts, info, needs, options,
                        path, pushd, sh, task)

BASEDIR = os.path.abspath(os.path.dirname(__file__))

options(
    base=Bunch(
        home=path(BASEDIR),
        docs=path('%s/docs' % BASEDIR),
        instance=path('%s/instance' % BASEDIR),
        pot=path('%s/GeoHealthCheck/translations/en/LC_MESSAGES/messages.po' %
                 BASEDIR),
        static_docs=path('%s/GeoHealthCheck/static/docs' % BASEDIR),
        static_lib=path('%s/GeoHealthCheck/static/lib' % BASEDIR),
        tmp=path(tempfile.mkdtemp()),
        translations=path('%s/GeoHealthCheck/translations' % BASEDIR)
    ),
)


@task
def setup():
    """setup plugin dependencies"""

    config_file = options.base.home / 'GeoHealthCheck/config_main.py'
    config_site = options.base.instance / 'config_site.py'

    # setup dirs
    if not os.path.exists(options.base.static_lib):
        options.base.static_lib.mkdir()
    if not os.path.exists(options.base.instance):
        options.base.instance.mkdir()
        data_dir = options.base.instance / 'data'
        data_dir.mkdir()
        # data_dir.chmod(0777) gives failure on Python 2.7 Paver 1.2.1
        os.chmod(path(data_dir), 0777)
        # setup config
        config_file.copy(config_site)

    # setup deps
    sh('pip install -r requirements.txt')

    skin = 'http://github.com/BlackrockDigital/startbootstrap-sb-admin-2/archive/v3.3.7+1.zip'  # noqa

    skin_dirs = ['dist', 'vendor']
    need_to_fetch = False

    for skin_dir in skin_dirs:
        skin_dir_path = os.sep.join(
            ['startbootstrap-sb-admin-2-3.3.7-1', skin_dir])
        if not os.path.exists(skin_dir_path):
            need_to_fetch = True

    if need_to_fetch:
        zipstr = StringIO(urlopen(skin).read())
        zipfile_obj = zipfile.ZipFile(zipstr)
        zipfile_obj.extractall(options.base.static_lib)

        for zf_mem in skin_dirs:
            src_loc = path(options.base.static_lib /
                           'startbootstrap-sb-admin-2-3.3.7-1' / zf_mem)
            dest_loc = path(options.base.static_lib / zf_mem)
            if not os.path.exists(dest_loc):
                src_loc.move(dest_loc)
            else:
                info('directory already exists.  Skipping')

        shutil.rmtree(path(options.base.static_lib /
                           'startbootstrap-sb-admin-2-3.3.7-1'))

    # install sparklines to static/site/js
    with open(path(options.base.static_lib / 'jspark.js'), 'w') as f:
        content = urlopen('http://ejohn.org/files/jspark.js').read()
        content.replace('red', 'green')
        f.write(content)

    # install leafletjs to static/lib
    leafletjs = 'http://cdn.leafletjs.com/downloads/leaflet-0.7.5.zip'

    zipstr = StringIO(urlopen(leafletjs).read())
    zipfile_obj = zipfile.ZipFile(zipstr)
    zipfile_obj.extractall(options.base.static_lib / 'leaflet')

    # install html5shiv to static/lib
    with open(path(options.base.static_lib / 'html5shiv.min.js'), 'w') as f:
        url = 'http://oss.maxcdn.com/html5shiv/3.7.2/html5shiv.min.js'
        content = urlopen(url).read()
        f.write(content)

    # install respond to static/lib
    with open(path(options.base.static_lib / 'respond.min.js'), 'w') as f:
        url = 'http://oss.maxcdn.com/respond/1.4.2/respond.min.js'
        content = urlopen(url).read()
        f.write(content)

    # build i18n .mo files
    call_task('compile_translations')

    # build local docs
    call_task('refresh_docs')

    # message user
    info('GeoHealthCheck is now built. Edit settings in %s' % config_site)
    info('before deploying the application. Alternatively, you can start a')
    info('development instance with "python GeoHealthCheck/app.py"')


@task
def create_secret_key():
    """create secret key for SECRET_KEY in instance/config_site.py"""
    info('Secret key: \'%s\'' % os.urandom(24).encode('hex'))
    info('Copy/paste this key to set the SECRET_KEY')
    info('value in instance/config_site.py')


@task
@cmdopts([
    ('email=', 'e', 'email'),
    ('username=', 'u', 'username'),
    ('password=', 'p', 'password')
])
def create(options):
    """create database objects and superuser account"""

    args = ''
    username = options.get('username', None)
    password = options.get('password', None)
    email = options.get('email', None)

    if all([username, password, email]):
        args = '%s %s %s' % (username, password, email)
    sh('python GeoHealthCheck/models.py create %s' % args)


@task
def create_wsgi():
    """create WSGI wrapper and Apache2 configuration"""
    wsgi_script = '%s%sGeoHealthCheck.wsgi' % (options.base.instance, os.sep)
    with open(wsgi_script, 'w') as ff:
        ff.write('import sys\n')
        ff.write('sys.path.insert(0, \'%s\')\n' % BASEDIR)
        ff.write('from GeoHealthCheck.app import APP as application')

    wsgi_conf = '%s%sGeoHealthCheck.conf' % (options.base.instance, os.sep)
    with open(wsgi_conf, 'w') as ff:
        ff.write('WSGIScriptAlias / %s%sGeoHealthCheck.wsgi\n' %
                 (options.base.instance, os.sep))
        ff.write('<Directory %s%s>\n' % (BASEDIR, os.sep))
        ff.write('Order deny,allow\n')
        ff.write('Allow from all\n')
        ff.write('</Directory>')


@task
def refresh_docs():
    """Build sphinx docs from scratch"""

    make = sphinx_make()

    if os.path.exists(options.base.static_docs):
        shutil.rmtree(options.base.static_docs)

    with pushd(options.base.docs):
        sh('%s clean' % make)
        sh('%s html' % make)
        sh('mkdir %s' % options.base.static_docs)
        sh('cp -rp %s/docs/_build/html/* %s' % (BASEDIR,
                                                options.base.static_docs))


@task
@needs('refresh_docs')
def publish_docs():
    """publish documentation to http://geopython.github.io/GeoHealthCheck"""

    with pushd(options.base.tmp):
        sh('git clone git@github.com:geopython/GeoHealthCheck.git')
        with pushd('GeoHealthCheck'):
            sh('git checkout gh-pages')
            sh('cp -rp %s/docs/_build/html/* .' % options.base.home)
            sh('git add .')
            sh('git commit -am "update live docs [ci skip]"')
            sh('git push origin gh-pages')
    shutil.rmtree(options.base.tmp)


@task
def clean():
    """clean environment"""

    if os.path.exists(options.base.static_lib):
        shutil.rmtree(options.base.static_lib)
    if os.path.exists(options.base.tmp):
        shutil.rmtree(options.base.tmp)
    if os.path.exists(options.base.static_docs):
        shutil.rmtree(options.base.static_docs)


@task
def extract_translations():
    """extrect translations wrapped in _() or gettext()"""

    pot_dir = path('GeoHealthCheck/translations/en/LC_MESSAGES')
    if not os.path.exists(pot_dir):
        pot_dir.makedirs()

    sh('pybabel extract -F babel.cfg -o %st GeoHealthCheck' % options.base.pot)


@task
@cmdopts([
    ('lang=', 'l', '2-letter language code'),
])
def add_language_catalogue(options):
    """adds new language profile"""

    lang = options.get('lang', None)

    if lang is None:
        raise RuntimeError('missing lang argument')

    sh('pybabel init -i %s -d %s -l %s' % (
       options.base.pot, options.base.translations, lang))


@task
def compile_translations():
    """build .mo files"""

    sh('pybabel compile -d %s' % options.base.translations)


@task
def update_translations():
    """update language strings"""

    call_task('extract_translations')
    sh('pybabel update -i %s -d %s' % (
        options.base.pot, options.base.translations))


def sphinx_make():
    """return what command Sphinx is using for make"""

    if os.name == 'nt':
        return 'make.bat'
    return 'make'
