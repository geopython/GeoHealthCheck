# -*- coding: utf-8 -*-
#
# Plugin base class and utils for GHC.
#
# Author: Just van den Broecke
#
import os

class Parameter(object):
    """
    Decorator class to tie parameter values from the .ini file to object instance
    parameter values. Somewhat like the Python standard @property but with
    the possibility to define default values, typing and making properties required.

    Each parameter is defined by @Parameter(type, default, required).
    Basic idea comes from:  https://wiki.python.org/moin/PythonDecoratorLibrary#Cached_Properties
    """
    def __init__(self, ptype=str, default=None, required=False, value=None, range=None):
        """
        If there are no decorator arguments, the function
        to be decorated is passed to the constructor.
        """
        # print "Inside __init__()"
        self.ptype = ptype
        self.default = default
        self.required = required
        self.value = value
        self.range = None

    def __call__(self, fget, doc=None):
        """
        The __call__ method is not called until the
        decorated function is called. self is returned such that __get__ below is called
        with the Plugin instance. That allows us to cache the actual property value
        in the Plugin itself.
        """
        # Save the property name (is the name of the function calling us).
        self.parm_name = fget.__name__
        # print "Inside __call__() name=%s" % self.parm_name

        # For Sphinx documention build we need the original function with docstring.
        if bool(os.getenv('SPHINX_BUILD')):
            fget.__doc__ = '``CONFIG`` - %s' % fget.__doc__
            return fget
        else:
            return self

    def __get__(self, plugin_obj, owner):
        # Gets used so often...
        name = self.parm_name

        # If already value, transfer to parameter dict of plugin object
        if self.value:
            plugin_obj.parms[name] = self.value
            self.value = None

        # print "Inside __get__() owner=%s" % owner
        """ descr.__get__(obj[, type]) -> value """
        if name not in plugin_obj.parms:
            # Value not provided in Plugin's parms
            value = self.default

            if self.required is True and value is None:
                raise Exception('Parameter property: %s is required in parameter for %s' % (name, str(plugin_obj)))

            plugin_obj.parms[name] = value

        return plugin_obj.parms[name]


class Plugin(object):
    """
    Abstract Base class for all GHC Plugins.

    """

    # Generic attributes, subclassses override
    AUTHOR = 'GHC Team'
    NAME = 'Fill in Name'
    DESCRIPTION = 'Fill in Description'

    def __init__(self):
        # The actual typed values as populated within Parameter Decorator
        c = self.__class__
        self.parms = dict()

    def __str__(self):
        return "%s" % str(self.__class__)
