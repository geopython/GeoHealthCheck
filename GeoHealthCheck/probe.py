import sys
import logging
import requests
from plugin import Plugin

from factory import Factory
from result import ProbeResult

LOGGER = logging.getLogger(__name__)


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
    is a parameter name and the value a `dict` of: `type`, `description`,
    `required`, `default`, `range` (value range) and optional `value` item.
    If `value` specified, this value becomes fixed (non-editable) unless
    overridden in subclass.
    """

    CHECKS_AVAIL = {}
    """
    Available Check (classes) for this Probe in `dict` format.
    Key is a Check class (string), values are optional (default `{}`).
    In the (constant) value 'parameters' and other attributes for
    Check.PARAM_DEFS can be specified.
    """

    def __init__(self):
        Plugin.__init__(self)

    # Lifecycle
    def init(self, resource, probe_vars):
        """
        Probe contains the actual Probe parameters (from Models/DB) for
        requests and a list of response Checks with their
        functions and parameters
        :param resource:
        :param probe_vars:
        :return: None
        """
        self._resource = resource
        self._probe_vars = probe_vars
        self._parameters = probe_vars.parameters
        self._check_vars = probe_vars.check_vars
        self.response = None

        # Create ProbeResult object that gathers all results for single Probe
        self.result = ProbeResult(self, self._probe_vars)

    #
    # Lifecycle
    def exit(self):
        pass

    def get_var_names(self):
        var_names = Plugin.get_var_names(self)
        var_names.extend([
            'RESOURCE_TYPE',
            'REQUEST_METHOD',
            'REQUEST_HEADERS',
            'REQUEST_TEMPLATE',
            'CHECKS_AVAIL'
        ])
        return var_names

    def expand_check_vars(self, checks_avail):
        for check_class in checks_avail:
            check_avail = checks_avail[check_class]
            check = Factory.create_obj(check_class)
            check_vars = check.get_plugin_vars()

            # Check if Probe class overrides Check Params
            # mainly "value" entries.
            if 'set_params' in check_avail:
                set_params = check_avail['set_params']
                for set_param in set_params:
                    if set_param in check_vars['PARAM_DEFS']:
                        param_orig = check_vars['PARAM_DEFS'][set_param]
                        param_override = set_params[set_param]
                        param_def = Plugin.merge(param_orig, param_override)
                        check_vars['PARAM_DEFS'][set_param] = param_def

            checks_avail[check_class] = check_vars
        return checks_avail

    def get_plugin_vars(self):
        probe_vars = Plugin.get_plugin_vars(self)
        probe_vars['CHECKS_AVAIL'] = \
            self.expand_check_vars(probe_vars['CHECKS_AVAIL'])
        return probe_vars

    def log(self, text):
        LOGGER.info(text)

    def before_request(self):
        """ Before running actual request to service"""
        pass

    def after_request(self):
        """ After running actual request to service"""
        pass

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

        self.log('Requesting: %s url=%s' % (self.REQUEST_METHOD, url_base))

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

        if self.response.status_code / 100 in [4, 5]:
            self.log('Error response: %s' % (str(self.response.text)))

    def run_request(self):
        """ Run actual request to service"""
        try:
            self.result.start()
            self.before_request()
            self.perform_request()
            self.after_request()
            self.result.stop()
        except:
            # We must never bailout because of Exception
            # in Probe.
            msg = "Exception: %s" % str(sys.exc_info())
            self.log(msg)
            self.result.set(False, msg)

    def run_checks(self):
        """ Do the checks on the response from request"""

        # Config also determines which actual checks are performed
        # from possible Checks in Probe. Checks are performed
        # by Check instances.
        for check_var in self._check_vars:
            check = None
            try:
                check_class = check_var.check_class
                check = Factory.create_obj(check_class)
            except:
                LOGGER.error("Cannot create Check class: %s %s"
                             % (check_class, str(sys.exc_info())))

            if not check:
                continue

            try:
                check.init(self, check_var)
                check.perform()
            except:
                msg = "Exception: %s" % str(sys.exc_info())
                LOGGER.error(msg)
                check.set_result(False, msg)

            self.log('Check: fun=%s result=%s' % (check_class,
                                                  check._result.success))

            self.result.add_result(check._result)

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
        probe = None
        try:
            # Create Probe instance from module.class string
            probe = Factory.create_obj(probe_vars.probe_class)
        except:
            LOGGER.error("Cannot create Probe class: %s %s"
                         % (probe_vars.probe_class, str(sys.exc_info())))

        if not probe:
            return

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
