# -*- coding: utf-8 -*-
from factory import Factory
import logging
import inspect
import collections
import copy
from init import App

LOGGER = logging.getLogger(__name__)


class Plugin(object):
    """
    Abstract Base class for all GHC Plugins.
    Derived classes should fill in all class variables that
    are UPPER_CASE, unless they ar fine with default-values from
    superclass(es).
    """

    # Generic attributes, subclassses override
    AUTHOR = 'GHC Team'
    """
    Plugin author or team.
    """

    NAME = 'Name missing in NAME class var'
    """
    Short name of Plugin. TODO: i18n e.g. NAME_nl_NL ?
    """

    DESCRIPTION = 'Description missing in DESCRIPTION class var'
    """
    Longer description of Plugin.
    TODO: optional i18n e.g. DESCRIPTION_de_DE ?
    """

    PARAM_DEFS = {}
    """
     Plugin Parameter definitions.
    """

    def __init__(self):
        self._parameters = {}

    def get_param(self, param_name):
        """
        Get actual parameter value. `param_name` should be defined
        in `PARAM_DEFS`.
        """

        if param_name not in self._parameters:
            return None
        return self._parameters[param_name]

    def get_default_parameter_values(self):

        """
        Get all default parameter values
        """
        params = getattr(self, 'PARAM_DEFS', {})
        param_values = {}
        for param in params:
            param_values[param] = ''
            if 'default' in params[param]:
                if params[param]['default']:
                    param_values[param] = params[param]['default']

            if 'value' in params[param]:
                param_values[param] = params[param]['value']

        return param_values

    def get_var_names(self):
        """
        Get all Plugin variable names as a dict
        """
        return ['AUTHOR', 'NAME', 'DESCRIPTION', 'PARAM_DEFS']

    def get_plugin_vars(self):
        """
        Get all (uppercase) class variables of a class
        as a dict
        """

        plugin_vars = {}
        var_names = self.get_var_names()
        for var_name in var_names:
            plugin_vars[var_name] = getattr(self, var_name, None)
        return plugin_vars

    def get_param_defs(self):
        """
        Get all PARAM_DEFS as dict.
        """

        return self.get_plugin_vars()['PARAM_DEFS']

    @staticmethod
    def copy(obj):
        """
        Deep copy of usually `dict` object.
        """
        return copy.deepcopy(obj)

    @staticmethod
    def merge(dict1, dict2):
        """
        Recursive merge of two `dict`, mainly used for PARAM_DEFS, CHECKS_AVAIL
        overriding.
        :param dict1: base dict
        :param dict2: dict to merge into dict1
        :return: deep copy of dict2 merged into dict1
        """

        def dict_merge(dct, merge_dct):
            """ Recursive dict merge. Inspired by :meth:``dict.update()``,
            instead of updating only top-level keys, dict_merge recurses
            down into dicts nested to an arbitrary depth, updating keys.
            The ``merge_dct`` is merged into ``dct``.
            See https://gist.github.com/angstwad/bf22d1822c38a92ec0a9

            :param dct: dict onto which the merge is executed
            :param merge_dct: dict merged into dct
            :return: None
            """
            for k, v in merge_dct.items():
                if k in dct and isinstance(dct[k], dict) \
                        and isinstance(merge_dct[k], collections.Mapping):
                    dict_merge(dct[k], merge_dct[k])
                else:
                    dct[k] = merge_dct[k]

        result_dict = copy.deepcopy(dict1)
        dict_merge(result_dict, dict2)
        return result_dict

    @staticmethod
    def get_plugins(baseclass='GeoHealthCheck.plugin.Plugin', filters=None):
        """
        Class method to get list of Plugins of particular baseclass (optional),
        default is all Plugins. filters is a list of tuples to filter out
        Plugins with class var values: (class var, value),
        e.g. `filters=[('RESOURCE_TYPE', 'OGC:*'),
        ('RESOURCE_TYPE', 'OGC:WMS')]`.
        """

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

        plugins = App.get_plugins()
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
            except Exception:
                # Try for full classname
                try:
                    class_obj = Factory.create_class(plugin_name)
                    if baseclass in inspect.getmro(class_obj) \
                            and baseclass != class_obj:
                        add_result(plugin_name, class_obj)
                except Exception:
                    LOGGER.warn('cannot create obj class=%s' % plugin_name)

        return result

    def __str__(self):
        return "%s" % str(self.__class__)
