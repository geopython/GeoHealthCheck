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

    def __init__(self, ptype=str, default=None, required=False, value=None, value_range=None):
        """
        If there are no decorator arguments, the function
        to be decorated is passed to the constructor.
        """
        # print "Inside __init__()"
        self.ptype = ptype
        self.default = default
        self.required = required
        self.value = value
        self.value_range = value_range

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

    @staticmethod
    def get_plugins(baseclass='GeoHealthCheck.plugin.Plugin', filters=None):
        """
        Class method to get list of Plugins of particular baseclass,
        default is all Plugins
        """
        from GeoHealthCheck.init import APP
        from factory import Factory
        import inspect

        plugins = APP.config['GHC_PLUGINS']
        result = []
        baseclass = Factory.create_class(baseclass)

        def add_result(plugin_name, class_obj):
            if not filters:
                result.append(plugin_name)
            else:
                vars = Factory.get_class_vars(class_obj)
                for filter in filters:
                    if vars[filter[0]] == filter[1]:
                        result.append(plugin_name)
                        break

        for plugin_name in plugins:
            try:

                # Assume module first
                module = Factory.create_module(plugin_name)
                for name in dir(module):
                    class_obj = getattr(module, name)
                    # Must be a class object inheriting from baseclass
                    # but not the baseclass itself
                    if inspect.isclass(class_obj) \
                            and baseclass in inspect.getmro(class_obj) and \
                                    baseclass != class_obj:
                        add_result('%s.%s' % (plugin_name, name), class_obj)
            except:
                # Try for full classname
                try:
                    class_obj = Factory.create_class(plugin_name)
                    if baseclass in inspect.getmro(class_obj)\
                            and baseclass != class_obj:
                        add_result(plugin_name, class_obj)
                except:
                    print('cannot create obj class=%s' % plugin_name)

        return result

    def __str__(self):
        return "%s" % str(self.__class__)
