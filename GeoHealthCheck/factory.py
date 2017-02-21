class Factory:
    """
    Object, Function class Factory (Pattern).
    Based on: http://stackoverflow.com/questions/2226330/instantiate-a-python-class-from-a-name
    """

    @staticmethod
    def create_obj(class_string):

        # Get value for 'class' property
        try:
            if not class_string:
                raise ValueError('Class name not provided')

            # class object from module.class name
            class_obj = Factory.create_class(class_string)

            # class instance from class object with constructor args
            return class_obj()
        except Exception, e:
            print("cannot create object instance from class '%s' e=%s" % (class_string, str(e)))
            raise e

    @staticmethod
    def create_class(class_string):
        """Returns class instance specified by a string.

        Args:
            class_string: The string representing a class.

        Raises:
            ValueError if module part of the class is not specified.
        """
        class_obj = None
        try:
            module_name, dot, class_name = class_string.rpartition('.')
            if module_name == '':
                raise ValueError('Class name must contain module part.')
            class_obj = getattr(
                __import__(module_name, globals(), locals(), [class_name], -1), class_name)
        except Exception, e:
            print("cannot create class '%s'" % class_string)
            raise e

        return class_obj

    @staticmethod
    def create_module(module_string):
        """Returns module instance specified by a string.

        Args:
            module_string: The string representing a module.

        Raises:
            ValueError if module can not be imported from string.
        """
        module_obj = None
        try:
            module_obj = __import__(module_string, globals(), locals(), fromlist=[''])
        except Exception, e:
            # print("cannot create module from '%s'" % module_string)
            raise e

        return module_obj

    @staticmethod
    def create_function(function_string):
        # Creating a global function instance is the same as a class instance
        return Factory.create_class(function_string)

    @staticmethod
    def get_class_vars(clazz):

        """
        Class method to get all class variables of a class
        as a dict
        """
        import inspect
        
        if type(clazz) is str:
            clazz = Factory.create_class(clazz)

        members = inspect.getmembers(clazz)
        # return members
        vars = dict()
        for member in members:
            key, value = member
            if not key.startswith('__') \
                and not inspect.isclass(value) \
                and not inspect.isfunction(value) \
                and not inspect.isbuiltin(value) \
                and not inspect.ismethod(value):

                vars[key] = value

        return vars

        # return {
        #     key:value for key,
        #         value in clazz.__dict__.items()
        #         if not key.startswith('__') and not callable(key)
        #         }
