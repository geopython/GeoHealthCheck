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
import os

from GeoHealthCheck.__init__ import __version__


@click.command()
def cli():
    """Example thingy"""
    click.echo('Hello there!')


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
    os.system('paver setup')


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
    os.system(f"python GeoHealthCheck/app.py {host}:{port}")


@cli.command()
@click.pass_context
def db_create(ctx):
    """Create the GHC database

    Note: you still need to add a user
    """
    verbose_echo(ctx, 'GeoHC: create db')
    from GeoHealthCheck.init import App
    DB = App.get_db()
    DB.create_all()
    DB.session.remove()


@cli.command()
@click.pass_context
def db_adduser(ctx):
    """Add an user to the database
    """
    verbose_echo(ctx, 'GeoHC: add user to database')
    from GeoHealthCheck.init import App
    from GeoHealthCheck.models import User, db_commit
    DB = App.get_db()
    user_to_add = User('rob', 'bor', 'rob.v.loon@gmail.com', role='admin')
    DB.session.add(user_to_add)
    db_commit()
    DB.session.remove()


@cli.command()
@click.pass_context
def db_drop(ctx):
    verbose_echo(ctx, 'GeoHC: drop db')
    #drop_db()

@cli.command()
@click.pass_context
def db_init(ctx):
    verbose_echo(ctx, 'GeoHC: init db')

@cli.command()
@click.pass_context
def db_upgrade(ctx):
    verbose_echo(ctx, 'GeoHC: upgrade db')

@cli.command()
@click.pass_context
def db_export(ctx):
    pass

def verbose_echo(ctx, verbose_text):
    if ctx.obj['VERBOSE']:
        click.echo(verbose_text)


if __name__ == '__main__':
    cli()
