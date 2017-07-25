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
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_babel import Babel


def to_list(obj):
    obj_type = type(obj)
    if obj_type is str:
        return obj.replace(' ', '').split(',')
    elif obj_type is list:
        return obj
    elif obj_type is set:
        return list(obj)
    else:
        raise TypeError('unknown type for Plugin: %s' + str(obj_type))


class App:
    """
     Singleton: sole static instance of Flask App
    """
    app_instance = None
    db_instance = None
    babel_instance = None
    plugins_instance = None
    home_dir = None

    @staticmethod
    def init():
        # Do init once
        if not App.app_instance:
            app = Flask(__name__)

            # Read and override configs
            app.config.from_pyfile('config_main.py')
            app.config.from_pyfile('../instance/config_site.py')

            app.config['GHC_SITE_URL'] = \
                app.config['GHC_SITE_URL'].rstrip('/')

            app.secret_key = app.config['SECRET_KEY']

            App.db_instance = SQLAlchemy(app)
            App.babel_instance = Babel(app)

            # Plugins (via Docker ENV) must be list, but may have been
            # specified as comma-separated string, or older set notation
            app.config['GHC_PLUGINS'] = to_list(app.config['GHC_PLUGINS'])
            app.config['GHC_USER_PLUGINS'] = \
                to_list(app.config['GHC_USER_PLUGINS'])

            # Concatenate core- and user-Plugins
            App.plugins_instance = \
                app.config['GHC_PLUGINS'] + app.config['GHC_USER_PLUGINS']

            # Needed to find Plugins
            home_dir = os.path.dirname(os.path.abspath(__file__))
            App.home_dir = sys.path.append('%s/..' % home_dir)

            # Finally assign app-instance
            App.app_instance = app
            print("init.py: created GHC App instance")

    @staticmethod
    def get_app():
        App.init()
        return App.app_instance

    @staticmethod
    def get_babel():
        App.init()
        return App.babel_instance

    @staticmethod
    def get_config():
        App.init()
        return App.app_instance.config

    @staticmethod
    def get_db():
        App.init()
        return App.db_instance

    @staticmethod
    def get_home_dir():
        App.init()
        return App.home_dir

    @staticmethod
    def get_plugins():
        App.init()
        return App.plugins_instance
