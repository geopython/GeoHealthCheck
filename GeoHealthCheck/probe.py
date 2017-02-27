import sys
import requests
from plugin import Plugin
from plugindecor import PluginDecorator

from factory import Factory
from result import ProbeResult, CheckResult


class Probe(Plugin):
    """
     Base class for specific implementations to run a Probe with Checks.

    """

    # Generic attributes, subclassses override
    RESOURCE_TYPE = '*:*'

    # Request attributes, defaults, subclassses override
    REQUEST_METHOD = 'GET'
    REQUEST_HEADERS = {}
    REQUEST_TEMPLATE = ''

    def __init__(self):
        # The actual typed values as populated within Parameter Decorator
        Plugin.__init__(self)
        self._use_checks = dict()

    # Possible response checks attributes, instance determines which
    # checks are selected and their parameters using @UseCheck decorator

    # Lifecycle
    def init(self, probe_vars=None):
        # Probe contains the actual Probe parameters (from Models/DB) for
        # requests and a list of response Checks with their functions+parameters
        self.probe_vars = probe_vars
        self.response = None
        self.result = None


    def get_checks(self, class_name=None):
        if class_name:
            if class_name not in PluginDecorator.REGISTRY['UseCheck']:
                return None

            return PluginDecorator.REGISTRY['UseCheck'][class_name]

        class_name = self.__module__ + "." + self.__class__.__name__
        class_obj = Factory.create_class(class_name)

        result = dict()
        for base in class_obj.__bases__:
            update = self.get_checks(base.__module__ + "." + base.__name__)
            if update:
                result.update(update)

        if class_name in PluginDecorator.REGISTRY['UseCheck']:
            update = self.get_checks(class_name)
            if update:
                result.update(update)

        return result

    # Lifecycle
    def exit(self):
        pass

    def log(self, text):
        print('%s: %s' % (self.__class__.__name__, text))

    def create_result(self):
        """ Create ProbeResult object that gathers all results for single Probe"""

        self.result = ProbeResult(self)

    def create_check_result(self, check, parameters, success, message):
        """ Create CheckResult object that gathers all results for single Check"""

        return CheckResult(check, parameters, success, message)

    def before_request(self):
        """ Before running actual request to service"""

        self.create_result()

        self.result.start()

    def after_request(self):
        """ After running actual request to service"""

        self.result.stop()

    def get_request_headers(self):
        return self.REQUEST_HEADERS

    def perform_request(self):
        """ Perform actual request to service"""

        # Actualize request query string or POST body
        # by substitution in template.
        url_base = self.probe_vars.resource.url

        request_string = None
        if self.REQUEST_TEMPLATE:
            request_string = self.REQUEST_TEMPLATE

            if self.probe_vars.parameters:
                request_parms = self.probe_vars.parameters
                request_string = self.REQUEST_TEMPLATE.format(**request_parms)

        self.log('Doing request: method=%s url=%s' % (self.REQUEST_METHOD, url_base))

        if self.REQUEST_METHOD == 'GET':
            # Default is plain URL, e.g. for WWW:LINK
            url = url_base
            if request_string:
                # Query String: mainly OWS:* resources
                url = "%s%s" % (url, request_string)
                
            self.response = requests.get(url,
                                         headers=self.get_request_headers())
        elif self.REQUEST_METHOD == 'POST':
            self.response = requests.post(url_base,
                                          data=request_string,
                                          headers=self.get_request_headers())

        self.log('response: status=%d' % (self.response.status_code))

        if self.response.status_code /100 in [4,5]:
            self.log('Errro response: %s' % (str(self.response.text)))


    def run_request(self):
        """ Run actual request to service"""
        self.before_request()
        self.perform_request()
        self.after_request()

    def run_checks(self):
        """ Do the checks on the response from request"""

        # Config also determines which actual checks are performed from possible
        # Checks in Probe. Checks are performed by Checker instances.
        check_vars = self.probe_vars.check_vars
        for check_var in check_vars:
            check_class = check_var.check_class
            check = Factory.create_obj(check_class)
            try:
                check.init(self, check_var.parameters)
                result = check.perform()
            except:
                msg = "Exception: %s" % str(sys.exc_info())
                self.log(msg)
                result = False, msg
            self.log('Check: fun=%s result=%s' % (check_class, result[0]))

            self.result.add_result(self.create_check_result(
                check_var, check_var.parameters, result[0], result[1]))

     # Lifecycle
    def calc_result(self):
        """ Calculate overall result from the Result object"""
        self.log("Result: %s" % str(self.result))

    @staticmethod
    def run(probe_vars):
        """ Class method to create and run a single Probe"""

        # Create Probe instance from module.class string
        probe = Factory.create_obj(probe_vars.probe_class)

        # Initialize with actual parameters
        probe.init(probe_vars)

        # Perform request
        probe.run_request()

        # Perform the Probe's checks
        probe.run_checks()

        # Determine result
        probe.calc_result()

        # Lifecycle
        probe.exit()

        # Return result
        return probe.result

