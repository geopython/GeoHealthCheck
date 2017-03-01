import sys
import requests
from plugin import Plugin

from factory import Factory
from result import ProbeResult, CheckResult


class Probe(Plugin):
    """
     Base class for specific implementations to run a Probe with Checks.
     Most Probes can be implemented using REQUEST_TEMPLATES parameterized
     via actualized PARAM_DEFS but specialized Probes may implement
     their own Requests and Checks, for example by "drilling down"
     through OWS services on an OGC OWS endpoint starting at the
     Capabilities level or for specific WWW:LINK-based REST APIs.
    """

    # Generic attributes, subclassses override
    RESOURCE_TYPE = 'Not Applicable'
    """
    Type of GHC Resource e.g. 'OGC:WMS', default not applicable.
    """

    # Request attributes, defaults, subclassses override
    REQUEST_METHOD = 'GET'
    """
    HTTP request method capitalized, GET (default) or POST.
    """

    REQUEST_HEADERS = {}
    """
    `dict` of optional requests headers.
    """

    REQUEST_TEMPLATE = ''
    """
    Template in standard Python `str.format(*args)`. The variables
    like {service} and {version} within a template are filled from 
    actual values for parameters defined in PARAM_DEFS and substituted
    from values or constant values specified by user in GUI and stored
    in DB.
    """

    # Parameter definitions and possible Checks,
    # subclassses override

    PARAM_DEFS = {}
    """
    Parameter definitions mostly for `REQUEST_TEMPLATE` but potential other
    uses in specific Probe implementations. Format is `dict` where each key 
    is a parameter name and
    the value a `dict` of: `type`, `description`, `required`, `default`,
    `range` (value range) and optional `value` item. If `value` specified,
    this value becomes fixed (non-editable) unless overridden in subclass.
    """

    CHECKS_AVAIL = {}
    """
    Available Check (classes) for this Probe in `dict` format.
    Key is a Check class (string), values are optional (default `{}`).
    In the (constant) value 'parameters' and other attributes for Check.PARAM_DEFS
    can be specified.
    """

    def __init__(self):
        Plugin.__init__(self)

    # Lifecycle
    def init(self, resource, probe_vars):
        # Probe contains the actual Probe parameters (from Models/DB) for
        # requests and a list of response Checks with their functions+parameters
        self._resource = resource
        self._probe_vars = probe_vars
        self._parameters = probe_vars.parameters
        self._check_vars = probe_vars.check_vars
        self.response = None
        self.result = None

    #
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
        url_base = self._resource.url

        request_string = None
        if self.REQUEST_TEMPLATE:
            request_string = self.REQUEST_TEMPLATE

            if self._probe_vars.parameters:
                request_parms = self._probe_vars.parameters
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

        self.log('response: status=%d' % self.response.status_code)

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
        for check_var in self._check_vars:
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
    def run(resource, probe_vars):
        """
        Class method to create and run a single Probe
        instance. Follows strict sequence of method calls.
        Each method can be overridden in subclass.
        """

        # Create Probe instance from module.class string
        probe = Factory.create_obj(probe_vars.probe_class)

        # Initialize with actual parameters
        probe.init(resource, probe_vars)

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

