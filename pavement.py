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
from StringIO import StringIO
from urllib2 import urlopen
import zipfile

from paver.easy import (Bunch, info, options, path, sh, task)

BASEDIR = os.path.abspath(os.path.dirname(__file__))

options(
    base=Bunch(
        home=path(BASEDIR),
        instance=path('%s/instance' % BASEDIR),
        static_lib=path('%s/GeoHealthCheck/static/lib' % BASEDIR),
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

    skin = 'http://startbootstrap.com/downloads/sb-admin-2.zip'
    skin_dirs = ['css', 'font-awesome-4.1.0', 'fonts', 'js', 'less']
    need_to_fetch = False

    for skin_dir in skin_dirs:
        if not os.path.exists(skin_dir):
            need_to_fetch = True

    if need_to_fetch:
        zipstr = StringIO(urlopen(skin).read())
        zipfile_obj = zipfile.ZipFile(zipstr)
        zipfile_obj.extractall(options.base.static_lib)

        for zf_mem in skin_dirs:
            src_loc = path(options.base.static_lib / 'sb-admin-2' / zf_mem)
            dest_loc = path(options.base.static_lib / zf_mem)
            if not os.path.exists(dest_loc):
                src_loc.move(dest_loc)
            else:
                info('directory already exists.  Skipping')

        shutil.rmtree(path(options.base.static_lib / 'sb-admin-2'))

    # message user
    info('GeoHealthCheck is now built. Edit settings in %s' % config_file)
    info('before deploying the application. Alternatively, you can start a')
    info('development instance with "python GeoHealthCheck/app.py"')


@task
def create():
    """create database objects and superuser account"""
    sh('python GeoHealthCheck/models.py create')


@task
def clean():
    """clean environment"""

    if os.path.exists(options.base.static_lib):
        shutil.rmtree(options.base.static_lib)
