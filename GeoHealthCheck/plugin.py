# -*- coding: utf-8 -*-
from factory import Factory
import inspect
from plugindecor import PluginDecorator

class Plugin(object):
    """
    Abstract Base class for all GHC Plugins.
    Place your description in class doc here.
    """

    # Generic attributes, subclassses override
    AUTHOR = 'GHC Team'
    NAME = 'Fill in Name in NAME class var'

    def __init__(self):
        # The actual typed values as populated within Parameter Decorator
        self._parms = dict()

    @staticmethod
    def get_plugins(baseclass='GeoHealthCheck.plugin.Plugin', filters=None):
        """
        Class method to get list of Plugins of particular baseclass,
        default is all Plugins. filters is a list of tuples to filter out
        Plugins with class var values: (class var, value),
        e.g. `filters=[('RESOURCE_TYPE', 'OGC:*'),('RESOURCE_TYPE', 'OGC:WMS')]`.
        """
        from GeoHealthCheck.init import APP

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

    def get_parameters(self, class_name=None):
        if class_name:
            if class_name not in PluginDecorator.REGISTRY['Parameter']:
                return None

            return PluginDecorator.REGISTRY['Parameter'][class_name]

        class_name = self.__module__ + "." + self.__class__.__name__
        class_obj = Factory.create_class(class_name)

        result = dict()
        for base in class_obj.__bases__:
            b = str(base)
            base_class_name = base.__module__ + "." + base.__name__
            update = self.get_parameters(base_class_name)
            if update:
                result.update(update)

        if class_name in PluginDecorator.REGISTRY['Parameter']:
            update = self.get_parameters(class_name)
            if update:
                result.update(update)

        return result

    def __str__(self):
        return "%s" % str(self.__class__)
