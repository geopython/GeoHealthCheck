# ============================================================================
#
# Authors: Rob van Loon <borrob@me.com>
#
# Copyright (c) 2019 Rob van Loon
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
import click

from GeoHealthCheck.__init__ import __version__


def verbose_echo(ctx, verbose_text):
    if ctx.obj['VERBOSE']:
        click.echo(verbose_text)


def abort_if_false(ctx, _, value):
    if not value:
        ctx.abort()


def sphinx_make():
    """return what command Sphinx is using for make"""
    from os import name
    if name == 'nt':
        return 'make.bat'
    return 'make'


@click.group()
@click.pass_context
@click.option('--verbose', '-v', is_flag=True, help='Verbose')
def cli(ctx, verbose):
    ctx.ensure_object(dict)
    ctx.obj['VERBOSE'] = verbose


@cli.command()
@click.pass_context
def version(ctx):
    """Show the current version of GHC
    """
    verbose_echo(ctx, 'GeoHC: get version')
    click.echo(__version__)


@cli.command()
@click.pass_context
@click.option('--basepath', '-p', type=str, help='path to the directory to'
              'install the instance data and help files.')
def create_instance(ctx, basepath):
    """Create an instance of GeoHealthCheck App
    """
    verbose_echo(ctx, 'GeoHC: create instance')
    import glob
    import os
    import shutil
    from io import BytesIO
    from pathlib import Path
    from urllib.request import urlopen
    import zipfile
    basedir = os.path.abspath(os.path.dirname(__file__))
    if (basepath is not None):
        basedir = os.path.abspath(basepath)
        verbose_echo(ctx, 'Setting base install directory to %s' % basedir)
    basedir_parent = os.path.normpath(str(Path(basedir).parent))
    config_file = os.path.normpath('%s/config_main.py' % basedir)
    config_site = os.path.normpath(basedir_parent + '/instance/config_site.py')

    # setup dirs
    if not os.path.exists(os.path.normpath('%s/static/lib' % basedir)):
        os.mkdir(os.path.normpath('%s/static/lib' % basedir))
    if not os.path.exists(os.path.normpath('%s/instance' % basedir_parent)):
        os.mkdir(os.path.normpath('%s/instance' % basedir_parent))
        # setup config
        shutil.copy(config_file, config_site)
    if not os.path.exists(os.path.normpath('%s/instance/data'
                          % basedir_parent)):
        data_dir = os.path.normpath('%s/instance/data' % basedir_parent)
        os.mkdir(data_dir, mode=0o777)

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
        zipfile_obj.extractall(os.path.normpath('%s/static/lib' % basedir))

        for zf_mem in skin_dirs:
            src_loc = os.path.normpath('%s/static/lib/'
                                       'startbootstrap-sb-admin-2-3.3.7-1/%s'
                                       % (basedir, zf_mem))
            dest_loc = os.path.normpath('%s/static/lib/%s' % (basedir, zf_mem))
            if not os.path.exists(dest_loc):
                shutil.move(src_loc, dest_loc)
            else:
                click.echo('directory already exists.  Skipping')

        shutil.rmtree(os.path.normpath('%s/static/lib/'
                                       'startbootstrap-sb-admin-2-3.3.7-1'
                                       % basedir))

    # install sparklines to static/site/js
    with open(os.path.normpath('%s/static/lib/'
                               'jspark.js' % basedir), 'w') as f:
        content = urlopen('http://ejohn.org/files/jspark.js').read().decode()
        content.replace('red', 'green')
        f.write(content)

    # install bootstrap-tagsinput to static/lib
    click.echo('Getting select2')
    select2 = 'https://github.com/select2/select2/archive/4.0.3.zip'

    zipstr = BytesIO(urlopen(select2).read())
    zipfile_obj = zipfile.ZipFile(zipstr)
    zipfile_obj.extractall(os.path.normpath('%s/static/lib' % basedir))
    dirname = glob.glob(os.path.normpath('%s/static/lib/select2-*'
                                         % basedir))[0]
    dstdir = ''.join(dirname.rsplit('-', 1)[:-1])
    try:
        shutil.move(dirname, dstdir)
    except OSError:
        shutil.rmtree(dstdir)
        shutil.move(dirname, dstdir)

    # install leafletjs to static/lib
    click.echo('Getting leaflet')
    leafletjs = 'http://cdn.leafletjs.com/downloads/leaflet-0.7.5.zip'

    zipstr = BytesIO(urlopen(leafletjs).read())
    zipfile_obj = zipfile.ZipFile(zipstr)
    zipfile_obj.extractall(os.path.normpath('%s/static/lib/leaflet' % basedir))

    # install html5shiv to static/lib
    with open(os.path.normpath('%s/static/lib/html5shiv.min.js' % basedir),
              'w') as f:
        url = 'http://oss.maxcdn.com/html5shiv/3.7.2/html5shiv.min.js'
        content = urlopen(url).read().decode()
        f.write(content)

    # install respond to static/lib
    with open(os.path.normpath('%s/static/lib/respond.min.js' % basedir),
              'w') as f:
        url = 'http://oss.maxcdn.com/respond/1.4.2/respond.min.js'
        content = urlopen(url).read().decode()
        f.write(content)

    # build i18n .mo files
    compile_translations(ctx, path=basedir)

    # build local docs
    update_documentation(ctx, basepath=basedir_parent)

    # message user
    click.echo('GeoHealthCheck is now built. Edit settings like the secret-key'
               ' and the database connection string in %s' % config_site)
    click.echo('before deploying the application. Alternatively, you can')
    click.echo('start a development instance with ')
    click.echo('"python GeoHealthCheck/app.py"')
    verbose_echo(ctx, 'GeoHC: finished creating the instance.')


@cli.command()
@click.pass_context
@click.option('--host', '-h', default='0.0.0.0', help='IP to host the app')
@click.option('--port', '-p', default=8000, help='port number to host the app')
def serve(ctx, host, port):
    """
    Run the app. Press 'ctrl-c' to exit again.

    This function is a wrapper around `python GeoHealthCheck/app.py`
    """
    verbose_echo(ctx, 'GeoHC: serve')
    click.echo('Press ctrl-c to exit.')
    from os import system, chdir
    chdir('GeoHealthCheck')
    system(f"python app.py {host}:{port}")


@cli.command()
@click.pass_context
def create_secret_key(ctx):
    """
    Create a secret key for the application.
    """
    from codecs import encode
    from os import urandom
    click.echo('Secret key: \'%s\'' % encode(urandom(24), 'hex').decode())
    click.echo('Copy/paste this key to set the SECRET_KEY value in '
               'instance/config_site.py')


@cli.command()
@click.option('-p', '--password', prompt=True, hide_input=True,
              help='password')
@click.pass_context
def create_hash(ctx, password):
    """Create a password hash
    """
    from GeoHealthCheck.util import create_hash
    token = create_hash(password)
    click.echo('Copy/paste the entire token below for example to set password')
    click.echo(token)


@cli.command()
@click.pass_context
def create_wsgi(ctx):
    """Create an apache wsgi and conf file"""
    verbose_echo(ctx, 'GeoHC: creating apache wsgi and conf files.')
    import os
    basedir = os.path.abspath(os.path.dirname(__file__))
    instance = '%s%sinstance' % (basedir, os.sep)
    verbose_echo(ctx, 'GeoHC: Files will be created in: %s' % instance)

    wsgi_script = '%s%sGeoHealthCheck.wsgi' % (instance, os.sep)
    with open(wsgi_script, 'w') as ff:
        ff.write('import sys\n')
        ff.write('sys.path.insert(0, \'%s\')\n' % basedir)
        ff.write('from GeoHealthCheck.app import APP as application')
    verbose_echo(ctx, 'GeoHC: finished wsgi script.')

    wsgi_conf = '%s%sGeoHealthCheck.conf' % (instance, os.sep)
    with open(wsgi_conf, 'w') as ff:
        ff.write('WSGIScriptAlias / %s%sGeoHealthCheck.wsgi\n' % (instance,
                                                                  os.sep))
        ff.write('<Directory %s%s>\n' % (basedir, os.sep))
        ff.write('Order deny,allow\n')
        ff.write('Allow from all\n')
        ff.write('</Directory>')
    verbose_echo(ctx, 'GeoHC: finished conf file.')


@cli.command()
@click.pass_context
def update_docs(ctx):
    """Update the spinx build of the documentation."""
    update_documentation(ctx)


def update_documentation(ctx, basepath=None):
    verbose_echo(ctx, 'GeoHC: start building documentation.')

    import os
    import shutil
    from pathlib import Path

    basedir = str(Path(os.path.abspath(os.path.dirname(__file__))).parent)
    if basepath:
        basedir = os.path.abspath(basepath)
    static_docs = os.path.normpath('%s/GeoHealthCheck/static/docs' % basedir)
    docs = os.path.normpath('%s/docs' % basedir)

    if os.path.exists(static_docs):
        verbose_echo(ctx, 'GeoHC: deleting previous doc directory.')
        shutil.rmtree(static_docs)

    os.chdir(docs)
    make = sphinx_make()
    verbose_echo(ctx, 'GeoHC: cleaning old documentation.')
    os.system('%s clean' % make)
    verbose_echo(ctx, 'GeoHC: building new documentation.')
    os.system('%s html' % make)
    os.chdir(basedir)

    verbose_echo(ctx, 'GeoHC: copying documentation to build folder.')
    source_html_dir = os.path.normpath('%s/docs/_build/html' % basedir)
    shutil.copytree(source_html_dir, static_docs)
    click.echo('GeoHC: finished refreshing documentation.')


@cli.command()
@click.pass_context
def clean(ctx):
    """Clean Environment
    """
    import os
    import shutil
    import tempfile

    basedir = os.path.abspath(os.path.dirname(__file__))
    static_docs = os.path.normpath('%s/GeoHealthCheck/static/docs' % basedir)
    static_lib = os.path.normpath('%s/GeoHealthCheck/static/lib' % basedir)
    tmp = os.path.normpath(tempfile.mkdtemp())

    try:
        shutil.rmtree(static_lib)
        verbose_echo(ctx, 'GeoHC: removed %s' % static_lib)
    except FileNotFoundError:
        pass
    try:
        shutil.rmtree(tmp)
        verbose_echo(ctx, 'GeoHC: removed temp directory: %s' % tmp)
    except FileNotFoundError:
        pass
    try:
        shutil.rmtree(static_docs)
        verbose_echo(ctx, 'GeoHC: removed %s' % static_docs)
    except FileNotFoundError:
        pass

    click.echo('GeoHC: finished cleaning environment.')


@cli.command()
@click.pass_context
def lang_extract_translations(ctx):
    """extract translations wrapped in _() or gettext()"""
    verbose_echo(ctx, 'GeoHC: extracting translations')
    import os

    pot_dir = os.path.normpath('GeoHealthCheck/translations/en/LC_MESSAGES')
    verbose_echo(ctx, 'GeoHC: Translations directory: %s' % pot_dir)
    if not os.path.exists(pot_dir):
        pot_dir.makedirs()

    basedir = os.path.abspath(os.path.dirname(__file__))
    base_pot = os.path.normpath('%s/GeoHealthCheck/translations/en/'
                                'LC_MESSAGES/messages.po' % basedir)
    verbose_echo(ctx, 'GeoHC: starting translation')
    os.system('pybabel extract -F babel.cfg -o %s GeoHealthCheck' % base_pot)
    click.echo('GeoHC: finished extracting translations.')


@cli.command()
@click.option('-l', '--lang', required=True, help='2-letter language code')
@click.pass_context
def lang_add_language_catalogue(ctx, lang):
    """adds new language profile"""
    verbose_echo(ctx, 'GeoHC: Adding language catalogue.')
    import os
    basedir = os.path.abspath(os.path.dirname(__file__))
    base_pot = os.path.normpath(
        '%s/translations/en/LC_MESSAGES/messages.po' % basedir)
    translations = os.path.normpath('%s/translations' % basedir)
    verbose_echo(ctx, 'GeoHC: Base translation set: %s' % base_pot)
    os.system('pybabel init -i %s -d %s -l %s' % (
        base_pot, translations, lang))
    click.echo('GeoHC: Finished translating: %s' % lang)


@cli.command()
@click.pass_context
def lang_compile_translations(ctx):
    compile_translations(ctx)


def compile_translations(ctx, path=None):
    """build language files"""
    verbose_echo(ctx, 'GeoHC: start building language files.')
    import os
    basedir = path if path else os.path.abspath(os.path.dirname(__file__))
    translations = os.path.normpath('%s/translations' % basedir)
    os.system('pybabel compile -d %s' % translations)
    click.echo('GeoHC: Finished building language files.')


@cli.command()
@click.pass_context
def lang_update_translations(ctx):
    """update language strings"""
    verbose_echo(ctx, 'GeoHC: update translations.')
    lang_extract_translations(ctx)

    import os
    basedir = os.path.abspath(os.path.dirname(__file__))
    base_pot = os.path.normpath(
        '%s/GeoHealthCheck/translations/en/LC_MESSAGES/messages.po' % basedir)
    translations = os.path.normpath('%s/GeoHealthCheck/translations' % basedir)
    os.system('pybabel update -i %s -d %s' % (base_pot, translations))
    click.echo('GeoHC: Finished updating translations.')


@cli.command()
@click.pass_context
def runner_daemon(ctx):
    """Run the HealthCheck runner daemon scheduler"""
    verbose_echo(ctx, 'GeoHC: going to run the scheduler daemon. Press ctrl-c '
                      'to stop.')
    import os
    os.system('python %s' % os.path.normpath('GeoHealthCheck/scheduler.py'))


@cli.command()
@click.pass_context
def run_healthchecks(ctx):
    """Run all HealthChecks directly"""
    verbose_echo(ctx, 'GeoHC: going to run all the healthchecks once.')
    import os
    os.system('python %s' % os.path.normpath('GeoHealthCheck/healthcheck.py'))
    click.echo('GeoHC: Finished running the healthchecks.')


@cli.command()
@click.pass_context
def run_tests(ctx):
    """Run all tests"""
    import os
    os.system('python %s' % os.path.normpath('tests/run_tests.py'))


@cli.command()
@click.pass_context
def build_wheel(ctx):
    """Build a python wheel"""
    verbose_echo(ctx, 'GeoHC: Build a python wheel')
    from os import system
    system('python setup.py bdist_wheel')
    click.echo('GeoHC: Finished building a wheel.')


# Database sub commands
@cli.group()
@click.pass_context
@click.option('--verbose', '-v', is_flag=True, help='Verbose')
def db(ctx, verbose):
    """Database subcommands"""
    ctx.ensure_object(dict)
    ctx.obj['VERBOSE'] = verbose


@db.command()
@click.pass_context
def create(ctx):
    """Create the GHC database

    Note: you still need to add a user
    """
    verbose_echo(ctx, 'GeoHC: create db')
    from GeoHealthCheck.init import App
    from GeoHealthCheck.models import db_commit
    verbose_echo(ctx, 'GeoHC: get database')
    DB = App.get_db()
    verbose_echo(ctx, 'GeoHC: create all tables')
    DB.create_all()
    db_commit()
    DB.session.remove()
    click.echo('Database is created. Use `geohc db-adduser` to add users to '
               'the database.')


@db.command()
@click.pass_context
@click.option('-u', '--user', type=str, help='username', prompt=True)
@click.option('-e', '--email', type=str, help='email address', prompt=True)
@click.option('-p', '--password', type=str, help='password', prompt=True,
              hide_input=True, confirmation_prompt=True)
@click.option('-r', '--role', type=click.Choice(['admin', 'user']),
              prompt=True, help='role for this user')
def adduser(ctx, user, email, password, role):
    """Add an user to the database
    """
    verbose_echo(ctx, 'GeoHC: add user to database')
    from GeoHealthCheck.init import App
    from GeoHealthCheck.models import User, db_commit
    verbose_echo(ctx, 'GeoHC: get database')
    DB = App.get_db()
    verbose_echo(ctx, 'GeoHC: create user')
    user_to_add = User(user, password, email, role=role)
    verbose_echo(ctx, 'GeoHC: adding user to database')
    DB.session.add(user_to_add)
    db_commit()
    DB.session.remove()
    click.echo(f'User {user} is added.')


@db.command()
@click.pass_context
@click.option('-y', '--yes', is_flag=True, callback=abort_if_false,
              expose_value=False, help='Confirm dropping tables',
              prompt='This will drop the tables in the database. Are you '
                     'sure?')
def drop(ctx):
    """Drop the current database
    """
    verbose_echo(ctx, 'GeoHC: drop db')
    click.confirm("This will drop the tables in the database. Are you sure?",
                  abort=True)
    verbose_echo(ctx, 'User confirmed dropping tables')
    from GeoHealthCheck.init import App
    from GeoHealthCheck.models import db_commit
    verbose_echo(ctx, 'GeoHC: get database')
    DB = App.get_db()
    verbose_echo(ctx, 'GeoHC: dropping all tables')
    DB.drop_all()
    db_commit()
    DB.session.remove()
    click.echo('Database dropped all tables.')


@db.command()
@click.pass_context
@click.option('-f', '--file', type=click.Path(), multiple=False, required=True,
              help='Path to the file to load into the database. MUST be JSON.')
@click.option('-y', '--yes', is_flag=True, callback=abort_if_false,
              expose_value=False, help='Confirm dropping old content.',
              prompt='WARNING: all database data will be lost. Proceed?')
def load(ctx, file):
    """Load JSON into the database

    e.g. test/data/fixtures.json
    """
    verbose_echo(ctx, 'GeoHC: load data into db')
    verbose_echo(ctx, 'User confirmed loading new data and losing old data.')
    from GeoHealthCheck.init import App
    from GeoHealthCheck.models import load_data
    DB = App.get_db()
    if file[-5:].lower() != '.json':
        click.echo("File must have '.json' file extension. Aborting import.")
        ctx.exit()
    verbose_echo(ctx, 'Start loading file.')
    load_data(file)
    verbose_echo(ctx, 'Data loaded!')
    DB.session.remove()
    click.echo('Finished loading data.')


@db.command()
@click.pass_context
def flush(ctx):
    """Flush runs: remove old data over retention date.
    """
    verbose_echo(ctx, 'GeoHC: flush old runs from database.')
    from GeoHealthCheck.models import flush_runs
    flush_runs()
    click.echo('Finished flushing old runs from database.')


@db.command()
@click.pass_context
def upgrade(ctx):
    """Upgrade the database
    """
    verbose_echo(ctx, 'GeoHC: upgrade db')
    from os import system, chdir
    chdir('GeoHealthCheck')
    system('python manage.py db upgrade')
    click.echo('Upgrade DB finished.')


@db.command()
@click.pass_context
def export(ctx):
    click.exho('GeoHC: todo- write export.')


if __name__ == '__main__':
    cli()
