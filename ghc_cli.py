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
def create_instance(ctx):
    """Create an instance of GeoHealthCheck App

    This command is a copy of `paver setup`
    """
    verbose_echo(ctx, 'GeoHC: create instance')
    # calling paver for the setup
    # TODO: phase out paver and switch to click
    from os import system
    system('paver setup')
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
    from os import system
    system(f"python GeoHealthCheck/app.py {host}:{port}")


@cli.command()
@click.pass_context
def db_create(ctx):
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
    click.echo('Database is created. Use `geohc db-adduser` to add users to the database.')


@cli.command()
@click.pass_context
@click.option('-u', '--user', type=str, help='username', prompt=True)
@click.option('-e', '--email', type=str, help='email address', prompt=True)
@click.option('-p', '--password', type=str, help='password', prompt=True, hide_input=True,
              confirmation_prompt=True)
@click.option('-r', '--role', type=click.Choice(['admin', 'user']), prompt=True,
              help='role for this user')
def db_adduser(ctx, user, email, password, role):
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


@cli.command()
@click.pass_context
@click.option('-y', '--yes', is_flag=True, callback=abort_if_false,
              expose_value=False, help='Confirm dropping tables',
              prompt='This will drop the tables in the database. Are you sure?')
def db_drop(ctx):
    """Drop the current database
    """
    verbose_echo(ctx, 'GeoHC: drop db')
    click.confirm("This will drop the tables in the database. Are you sure?", abort=True)
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


@cli.command()
@click.pass_context
@click.option('-f', '--file', type=click.Path(), multiple=False, required=True,
              help='Path to the file to load into the database. MUST be JSON.')
@click.option('-y', '--yes', is_flag=True, callback=abort_if_false,
              expose_value=False, help='Confirm dropping old content.',
              prompt='WARNING: all database data will be lost. Proceed?')
def db_load(ctx, file):
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

@cli.command()
@click.pass_context
def db_flush(ctx):
    """Flush runs: remove old data over retention date.
    """
    verbose_echo(ctx, 'GeoHC: flush old runs from database.')
    from GeoHealthCheck.models import flush_runs
    flush_runs()
    click.echo('Finished flushing old runs from database.')

@cli.command()
@click.pass_context
def db_upgrade(ctx):
    verbose_echo(ctx, 'GeoHC: upgrade db')

@cli.command()
@click.pass_context
def db_export(ctx):
    pass


if __name__ == '__main__':
    cli()
