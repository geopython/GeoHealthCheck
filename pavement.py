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

from paver.easy import (Bunch, info, needs, options, path, pushd, sh, task)

BASEDIR = os.path.abspath(os.path.dirname(__file__))

options(
    base=Bunch(
        home=path(BASEDIR),
        docs=path('%s/docs' % BASEDIR),
        instance=path('%s/instance' % BASEDIR),
        static_lib=path('%s/GeoHealthCheck/static/lib' % BASEDIR),
        tmp=path(tempfile.mkdtemp())
    ),
)


@task
def setup():
    """setup plugin dependencies"""

    config_file = options.base.home / 'GeoHealthCheck/config.py'

    # setup dirs
    if not os.path.exists(options.base.static_lib):
        options.base.static_lib.mkdir()
    if not os.path.exists(options.base.instance):
        options.base.instance.mkdir()
        data_dir = options.base.instance / 'data'
        data_dir.mkdir()
        data_dir.chmod(0777)
        # setup config
        config_file.copy(options.base.instance)

    # setup deps
    sh('pip install -r requirements.txt')

    # split URL to keep pep8 happy
    skin = '/'.join(['https://github.com',
                     'IronSummitMedia/startbootstrap-sb-admin-2',
                     'archive/v1.0.3.zip'])

    skin_dirs = ['dist', 'bower_components']
    need_to_fetch = False

    for skin_dir in skin_dirs:
        skin_dir_path = os.sep.join(
            ['startbootstrap-sb-admin-2-1.0.3', skin_dir])
        if not os.path.exists(skin_dir_path):
            need_to_fetch = True

    if need_to_fetch:
        zipstr = StringIO(urlopen(skin).read())
        zipfile_obj = zipfile.ZipFile(zipstr)
        zipfile_obj.extractall(options.base.static_lib)

        for zf_mem in skin_dirs:
            src_loc = path(options.base.static_lib /
                           'startbootstrap-sb-admin-2-1.0.3' / zf_mem)
            dest_loc = path(options.base.static_lib / zf_mem)
            if not os.path.exists(dest_loc):
                src_loc.move(dest_loc)
            else:
                info('directory already exists.  Skipping')

        shutil.rmtree(path(options.base.static_lib /
                           'startbootstrap-sb-admin-2-1.0.3'))

    # install sparklines to static/site/js
    with open(path(options.base.static_lib / 'jspark.js'), 'w') as f:
        content = urlopen('http://ejohn.org/files/jspark.js').read()
        content.replace('red', 'green')
        f.write(content)

    leafletjs = 'http://cdn.leafletjs.com/downloads/leaflet-0.7.5.zip'

    zipstr = StringIO(urlopen(leafletjs).read())
    zipfile_obj = zipfile.ZipFile(zipstr)
    zipfile_obj.extractall(options.base.static_lib / 'leaflet')

    # message user
    info('GeoHealthCheck is now built. Edit settings in %s' % config_file)
    info('before deploying the application. Alternatively, you can start a')
    info('development instance with "python GeoHealthCheck/app.py"')


@task
def create_secret_key():
    """create secret key for SECRET_KEY in instance/config.py"""
    info('Secret key: \'%s\'' % os.urandom(24))
    info('Copy/paste this key to set the SECRET_KEY')
    info('value in instance/config.py')


@task
def create():
    """create database objects and superuser account"""
    sh('python GeoHealthCheck/models.py create')


@task
def create_wsgi():
    """create WSGI wrapper and Apache2 configuration"""
    with open('%s%sGeoHealthCheck.wsgi' % (BASEDIR, os.sep), 'w') as ff:
        ff.write('import sys\n')
        ff.write('sys.path.insert(0, \'%s\')\n' % BASEDIR)
        ff.write('from GeoHealthCheck.app import APP as application')

    with open('%s%sGeoHealthCheck.conf' % (BASEDIR, os.sep), 'w') as ff:
        ff.write('WSGIScriptAlias / %s%sGeoHealthCheck.wsgi\n' %
                 (BASEDIR, os.sep))
        ff.write('<Directory %s%s>\n' % (BASEDIR, os.sep))
        ff.write('Order deny,allow\n')
        ff.write('Allow from all\n')
        ff.write('</Directory>')


@task
def refresh_docs():
    """Build sphinx docs from scratch"""

    make = sphinx_make()

    with pushd(options.base.docs):
        sh('%s clean' % make)
        sh('%s html' % make)


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


def sphinx_make():
    """return what command Sphinx is using for make"""

    if os.name == 'nt':
        return 'make.bat'
    return 'make'
