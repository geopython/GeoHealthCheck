#
# Plugin base class and utils for GHC.
#
# Author: Just van den Broecke
#
import os
import inspect


class PluginDecorator(object):
    """
    Abstract Base Class for specific Plugin Decorators like @Parameter and @UseCheck.
    Basic idea comes from:  https://wiki.python.org/moin/PythonDecoratorLibrary#Cached_Properties.
    """

    # Global, class-wide registry for all Decorators.
    # Needed to find them later on, per class.
    REGISTRY = dict()

    def __init__(self):
        """
        If there are no decorator arguments, the function
        to be decorated is passed to the constructor.
        """
        self._name = ''

    def get_sphinx_doc(self, doc):
        """
        Construct Sphinx documentation string.
        """
        return doc

    def register(self, fget, clazz):
        """
        Register PluginDecorator class.
        """
        pass

    def get_name(self):
        return self._name

    def __call__(self, fget, doc=None):
        """
        The __call__ method is not called until the
        decorated function is called. self is returned such that __get__ below is called
        with the Plugin instance. That allows us to cache the actual property value
        in the Plugin itself.
        """
        # Save the decorator name (is the name of the function calling us).
        self._name = fget.__name__

        # Tricky bit: we need to know the calling class to
        # be able to get its Parameter data. Normally this is lost.
        # So we register the Parameter data in a class var REGISTRY.
        # http://stackoverflow.com/questions/29530443/how-to-get-the-caller-of-a-method-in-a-decorator-in-python
        stack = inspect.stack()
        caller_obj = stack[1][0]
        # module = caller_obj.f_locals['__module__']
        clazz = caller_obj.f_locals['__module__'] + '.' + stack[1][3]

        # Register Decorator with class in global registry
        # in order to find the Decorators later as that
        # info is lost on instantiation.
        self.register(fget, clazz)

        # For Sphinx documention build we need the original function with docstring.
        if bool(os.getenv('SPHINX_BUILD')):
            if not fget.__doc__ or fget.__doc__ == '':
                fget.__doc__ = 'no documentation, please provide...'
                return fget

            fget.__doc__ = self.get_sphinx_doc(fget.__doc__)
            return fget
        else:
            return self

    def __get__(self, plugin_obj, owner):
        """
        Implemented in derived PluginDecorator
        """
        return None


class Parameter(PluginDecorator):
    """
    Decorator class to tie parameter values from a Plugin instance. Somewhat like the Python
    standard @property but with the possibility to define default values, typing and
    making properties required. Plus for generating structured (Sphinx) documentation.

    Each parameter is defined by @Parameter(ptype, default, required, value, value_range).
    Basic idea comes from:  https://wiki.python.org/moin/PythonDecoratorLibrary#Cached_Properties
    """

    # Registry for all @Parameter decorators per class.
    PluginDecorator.REGISTRY['Parameter'] = dict()


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

        PluginDecorator.__init__(self)

    def get_sphinx_doc(self, doc):
        """
        Construct Sphinx documentation string.
        """
        # Build Parameter Sphinx documentation
        doc = doc.strip()
        doc = '``Parameter`` - %s\n\n' % doc
        doc += '* type: %s\n' % self.ptype

        if self.value:
            doc += '* value: %s\n' % self.value
        else:
            doc += '* required: %s\n' % self.required
            doc += '* default: %s\n' % self.default
            doc += '* value_range: %s\n' % self.value_range

        return doc

    def register(self, fget, clazz):
        """
        Register PluginDecorator class.
        """
        if clazz not in PluginDecorator.REGISTRY['Parameter']:
            PluginDecorator.REGISTRY['Parameter'][clazz] = dict()

        PluginDecorator.REGISTRY['Parameter'][clazz][self.get_name()] = {
            'type':  str(self.ptype.__name__),
            'default':  self.default,
            'required':  self.required,
            'value':  self.value,
            'value_range':  self.value_range
        }

    def __get__(self, plugin_obj, owner):
        if not plugin_obj:
            return None

        # Gets used so often...
        name = self.get_name()

        # If already value, transfer to parameter dict of plugin object
        if self.value:
            plugin_obj._parms[name] = self.value
            self.value = None

        # print "Inside __get__() owner=%s" % owner
        """ descr.__get__(obj[, type]) -> value """
        if name not in plugin_obj._parms:
            # Value not provided in Plugin's parms
            value = self.default

            if self.required is True and value is None:
                raise Exception('Parameter property: %s is required in parameter for %s' % (name, str(plugin_obj)))

            plugin_obj._parms[name] = value

        return plugin_obj._parms[name]


class UseCheck(PluginDecorator):
    """
    Decorator class to tie UseCheck values from a Plugin instance. Somewhat like the Python
    standard @property but with the possibility to define default values, typing and
    making properties required. Plus for generating structured (Sphinx) documentation.

    Each is defined by @UseCheck(check_class, parameters).
    Basic idea comes from:  https://wiki.python.org/moin/PythonDecoratorLibrary#Cached_Properties
    """

    # Registry for all @UseCheck decorators per (Probe) class.
    PluginDecorator.REGISTRY['UseCheck'] = dict()



    def __init__(self, check_class, parameters=dict()):
        """
        If there are no decorator arguments, the function
        to be decorated is passed to the constructor.
        """
        # print "Inside __init__()"
        self.value = dict(
            check_class=check_class,
            parameters=parameters)

        PluginDecorator.__init__(self)

    def get_sphinx_doc(self, doc):
        """
        Construct Sphinx documentation string.
        """
        # Build UseCheck Sphinx documentation
        doc = doc.strip()
        doc = '``UseCheck`` - %s\n\n' % doc
        doc += '* class: %s\n' % self.value['check_class']

        parameters = self.value['parameters']
        if parameters:
            doc += '*  parameters:\n'
            for parm in parameters:
                doc += '  - %s: %s\n' % (parm, parameters[parm])

        return doc

    def register(self, fget, clazz):
        """
        Register PluginDecorator class in global Registry.
        """
        if clazz not in PluginDecorator.REGISTRY['UseCheck']:
            PluginDecorator.REGISTRY['UseCheck'][clazz] = dict()

        PluginDecorator.REGISTRY['UseCheck'][clazz][self.get_name()] = self.value

    def __get__(self, plugin_obj, owner):
        if not plugin_obj:
            return None

        # Gets used so often...
        name = self.get_name()

        # If already value, transfer to parameter dict of plugin object
        if self.value:
            plugin_obj._use_checks[name] = self.value
            self.value = None

        return plugin_obj._use_checks[name]
