# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2026 Tom Kralidis
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
from io import BytesIO
import os
from pathlib import Path
import shutil
import tempfile
from urllib.request import urlopen
import zipfile

from invoke import task

BASEDIR = Path(__file__).resolve().parent
HOME = BASEDIR
DOCS = BASEDIR / 'docs'
INSTANCE = BASEDIR / 'instance'
POT = BASEDIR / 'GeoHealthCheck/translations/en/LC_MESSAGES/messages.po'
STATIC_DOCS = BASEDIR / 'GeoHealthCheck/static/docs'
STATIC_LIB = BASEDIR / 'GeoHealthCheck/static/lib'
TMP = Path(tempfile.mkdtemp())
TRANSLATIONS = BASEDIR / 'GeoHealthCheck/translations'


@task
def setup(c):
    """setup plugin dependencies"""

    config_file = HOME / 'GeoHealthCheck/config_main.py'
    config_site = INSTANCE / 'config_site.py'

    # setup dirs
    if not STATIC_LIB.exists():
        STATIC_LIB.mkdir()
    if not INSTANCE.exists():
        INSTANCE.mkdir()
        data_dir = INSTANCE / 'data'
        data_dir.mkdir()
        data_dir.chmod(0o777)
        shutil.copy2(config_file, config_site)

    # setup deps
    c.run('pip3 install -r requirements.txt')

    skin = 'http://github.com/BlackrockDigital/startbootstrap-sb-admin-2/archive/v3.3.7+1.zip'  # noqa

    skin_dirs = ['dist', 'vendor']
    need_to_fetch = False

    for skin_dir in skin_dirs:
        skin_dir_path = Path('startbootstrap-sb-admin-2-3.3.7-1') / skin_dir
        if not skin_dir_path.exists():
            need_to_fetch = True

    if need_to_fetch:
        zipstr = BytesIO(urlopen(skin).read())
        zipfile_obj = zipfile.ZipFile(zipstr)
        zipfile_obj.extractall(STATIC_LIB)

        for zf_mem in skin_dirs:
            src_loc = STATIC_LIB / 'startbootstrap-sb-admin-2-3.3.7-1' / zf_mem
            dest_loc = STATIC_LIB / zf_mem
            if not dest_loc.exists():
                shutil.move(src_loc, dest_loc)
            else:
                print('directory already exists.  Skipping')

        shutil.rmtree(STATIC_LIB / 'startbootstrap-sb-admin-2-3.3.7-1')

    # install bootstrap-tagsinput to static/lib
    print('Getting select2')
    select2 = 'https://github.com/select2/select2/archive/4.0.3.zip'

    zipstr = BytesIO(urlopen(select2).read())
    zipfile_obj = zipfile.ZipFile(zipstr)
    zipfile_obj.extractall(STATIC_LIB)

    dirname = list(STATIC_LIB.glob('select2-*'))[0]
    dstdir = ''.join(dirname.name.rsplit('-', 1)[:-1])

    try:
        os.rename(dirname, dstdir)
    except OSError:
        shutil.rmtree(dstdir)
        dirname.rename(dstdir)

    # install leafletjs to static/lib
    print('Getting leaflet')
    leaflet_cdn_url = 'https://leafletjs-cdn.s3.amazonaws.com/content/leaflet'
    leafletjs = f'{leaflet_cdn_url}/v1.9.4/leaflet.zip'

    zipstr = BytesIO(urlopen(leafletjs).read())
    zipfile_obj = zipfile.ZipFile(zipstr)
    zipfile_obj.extractall(STATIC_LIB / 'leaflet')

    # install html5shiv to static/lib
    cdn_url = 'https://cdn.jsdelivr.net/npm'
    shiv_filepath = STATIC_LIB / 'html5shiv.min.js'
    with shiv_filepath.open('w') as f:
        url = f'{cdn_url}/html5shiv.min.js@3.7.2/html5shiv.min.js'
        content = urlopen(url).read().decode()
        f.write(content)

    # install respond to static/lib
    respond_filepath = STATIC_LIB / 'respond.min.js'
    with respond_filepath.open('w') as f:
        url = f'{cdn_url}/respond.min.js@1.4.2/respond.min.js'
        content = urlopen(url).read().decode()
        f.write(content)

    # build i18n .mo files
    compile_translations(c)

    # build local docs
    refresh_docs(c)

    # message user
    print(f'GeoHealthCheck is now built. Edit settings in {config_site}')
    print('before deploying the application. Alternatively, you can start a')
    print('development instance with "python3 GeoHealthCheck/app.py"')


@task
def create_secret_key(c):
    """create secret key for SECRET_KEY in instance/config_site.py"""

    secret_key = codecs.encode(os.urandom(24), 'hex').decode()
    print(f'Secret key: {secret_key}')
    print('Copy/paste this key to set the SECRET_KEY')
    print('value in instance/config_site.py')


@task
def create(c, email, username, password):
    """create database objects and superuser account"""

    args = ''
    models_py = Path('GeoHealthCheck/models.py')

    if None not in [email, username, password]:
        args = f'{username} {password} {email}'

    c.run(f'python3 {models_py} create {args}')


@task
def create_hash(c, password):
    """Create hash, mainly for passwords"""

    from util import create_hash as create_hash2

    token = create_hash2(password)
    print('Copy/paste the entire token below for example to set password')
    print(token)


@task
def upgrade(c):
    """upgrade database if changed; be sure to backup first!"""

    print('Upgrading database...')
    os.chdir(BASEDIR / 'GeoHealthCheck')
    c.run('python3 manage.py db upgrade')
    os.chdir(BASEDIR)


@task
def create_wsgi(c):
    """create WSGI wrapper and Apache2 configuration"""

    wsgi_script = INSTANCE / 'GeoHealthCheck.wsgi'

    with wsgi_script.open('w') as fh:
        fh.write('import sys\n')
        fh.write('sys.path.insert(0, \'%s\')\n' % BASEDIR)
        fh.write('from GeoHealthCheck.app import APP as application')

    wsgi_conf = INSTANCE / 'GeoHealthCheck.conf'

    with open(wsgi_conf, 'w') as fh:
        ghc_wsgi = INSTANCE / 'GeoHealthCheck.wsgi'
        fh.write(f'WSGIScriptAlias / {ghc_wsgi}\n')
        fh.write(f'<Directory {BASEDIR}/>\n')
        fh.write('Order deny,allow\n')
        fh.write('Allow from all\n')
        fh.write('</Directory>')


@task
def refresh_docs(c):
    """Build sphinx docs from scratch"""

    make = 'make'

    if os.name == 'nt':
        make = 'make.bat'

    if STATIC_DOCS.exists():
        shutil.rmtree(STATIC_DOCS)

    os.chdir(DOCS)
    c.run(f'{make} clean')
    c.run(f'{make} html')

    source_html_dir = BASEDIR / 'docs/_build/html'
    shutil.copytree(source_html_dir, STATIC_DOCS)
    os.chdir(BASEDIR)


@task
def clean(c):
    """clean environment"""

    for dir_ in [STATIC_LIB, STATIC_DOCS, TMP]:
        if dir_.exists():
            shutil.rmtree(dir_)


@task
def extract_translations(c):
    """extract translations wrapped in _() or gettext()"""

    pot_dir = Path('GeoHealthCheck/translations/en/LC_MESSAGES')
    if not pot_dir.exists():
        pot_dir.mkdir(parants=True, exist_ok=True)

    c.run(f'pybabel extract -F babel.cfg -o {POT} GeoHealthCheck')


@task
def add_language_catalogue(c, lang):
    """adds new language profile"""

    if lang is None:
        raise RuntimeError('missing lang argument')

    c.run(f'pybabel init -i {POT} -d {TRANSLATIONS} -l {lang}')


@task
def compile_translations(c):
    """build .mo files"""

    c.run(f'pybabel compile -d {TRANSLATIONS}')


@task
def update_translations(c):
    """update language strings"""

    extract_translations(c)
    c.run(f'pybabel update -i {POT} -d {TRANSLATIONS}')


@task
def runner_daemon(c):
    """Run the HealthCheck runner daemon scheduler"""

    c.run('python3 GeoHealthCheck/scheduler.py')


@task
def run_healthchecks(c):
    """Run all HealthChecks directly"""

    c.run('python3 GeoHealthCheck/healthcheck.py')


@task
def run_tests(c):
    """Run all tests"""

    c.run('python3 tests/run_tests.py')
