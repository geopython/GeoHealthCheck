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

import codecs
import glob
import os
import shutil
import tempfile
from io import BytesIO
from urllib.request import urlopen
import zipfile

from paver.easy import (Bunch, call_task, cmdopts, info, options,
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
        os.chmod(path(data_dir), 0o777)
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
        zipstr = BytesIO(urlopen(skin).read())
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
        content = urlopen('http://ejohn.org/files/jspark.js').read().decode()
        content.replace('red', 'green')
        f.write(content)

    # install bootstrap-tagsinput to static/lib
    info('Getting select2')
    select2 = 'https://github.com/select2/select2/archive/4.0.3.zip'

    zipstr = BytesIO(urlopen(select2).read())
    zipfile_obj = zipfile.ZipFile(zipstr)
    zipfile_obj.extractall(options.base.static_lib)
    dirname = glob.glob(options.base.static_lib / 'select2-*')[0]
    dstdir = ''.join(dirname.rsplit('-', 1)[:-1])
    try:
        os.rename(dirname, dstdir)
    except OSError:
        shutil.rmtree(dstdir)
        os.rename(dirname, dstdir)

    # install leafletjs to static/lib
    info('Getting leaflet')
    leafletjs = 'http://cdn.leafletjs.com/downloads/leaflet-0.7.5.zip'

    zipstr = BytesIO(urlopen(leafletjs).read())
    zipfile_obj = zipfile.ZipFile(zipstr)
    zipfile_obj.extractall(options.base.static_lib / 'leaflet')

    # install html5shiv to static/lib
    cdn_url = 'https://cdn.jsdelivr.net/npm'
    with open(path(options.base.static_lib / 'html5shiv.min.js'), 'w') as f:
        url = \
            '{}/html5shiv.min.js@3.7.2/html5shiv.min.js'.format(cdn_url)
        content = urlopen(url).read().decode()
        f.write(content)

    # install respond to static/lib
    with open(path(options.base.static_lib / 'respond.min.js'), 'w') as f:
        url = '{}/respond.min.js@1.4.2/respond.min.js'.format(cdn_url)
        content = urlopen(url).read().decode()
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
    info('Secret key: \'%s\'' % codecs.encode(os.urandom(24), 'hex').decode())
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
    sh('python %s create %s' % (path('GeoHealthCheck/models.py'), args))


@task
@cmdopts([
    ('password=', 'p', 'password')
])
def create_hash(options):
    """
    Create hash, mainly for passwords.
    Usage: paver create_hash -p mypass
    """

    import sys
    sys.path.insert(0, BASEDIR + '/GeoHealthCheck')
    from util import create_hash
    token = create_hash(options.get('password', None))
    info('Copy/paste the entire token below for example to set password')
    info(token)


@task
def upgrade():
    """upgrade database if changed; be sure to backup first!"""

    info('Upgrading database...')
    with pushd(path('%s/GeoHealthCheck' % BASEDIR)):
        sh('python manage.py db upgrade')


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
        source_html_dir = path('%s/docs/_build/html' % BASEDIR)
        source_html_dir.copytree(options.base.static_docs)


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
    """extract translations wrapped in _() or gettext()"""

    pot_dir = path('GeoHealthCheck/translations/en/LC_MESSAGES')
    if not os.path.exists(pot_dir):
        pot_dir.makedirs()

    sh('pybabel extract -F babel.cfg -o %s GeoHealthCheck' % options.base.pot)


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


@task
def runner_daemon():
    """Run the HealthCheck runner daemon scheduler"""
    sh('python %s' % path('GeoHealthCheck/scheduler.py'))


@task
def run_healthchecks():
    """Run all HealthChecks directly"""
    sh('python %s' % path('GeoHealthCheck/healthcheck.py'))


def sphinx_make():
    """return what command Sphinx is using for make"""

    if os.name == 'nt':
        return 'make.bat'
    return 'make'


@task
def run_tests():
    """Run all tests"""
    sh('python %s' % path('tests/run_tests.py'))
