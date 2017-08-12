import sys
import datetime
import logging
import requests
from plugin import Plugin
from init import App

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

    # Request attributes, defaults, subclasses override
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
    Check.PARAM_DEFS can be specified, including `default` if this Check
    should be added to Probe on creation.
    """

    METADATA_CACHE = {}
    """
    Cache for metadata, like capabilities documents or OWSLib Service
    instances. Saves doing multiple requests/responses. In particular for
    endpoints with 50+ Layers.
    """

    def __init__(self):
        Plugin.__init__(self)

    #
    # Lifecycle : optionally expand params from Resource metadata
    def expand_params(self, resource):
        """
        Called after creation. Use to expand PARAM_DEFS, e.g. from Resource
        metadata like WMS Capabilities. See e.g. WmsGetMapV1 class.
        :param resource:
        :return: None
        """
        pass

    def get_metadata(self, resource, version='any'):
        """
        Get metadata, specific per Resource type.
        :param resource:
        :param version:
        :return: Metadata object
        """
        return 'md'

    def get_metadata_cached(self, resource, version='any'):
        """
        Get metadata, specific per Resource type, get from cache
        if cached.
        :param resource:
        :param version:
        :return: Metadata object
        """

        key = '%s_%s_%s' % (resource.url, resource.resource_type,
                            version)

        metadata = None
        if key in Probe.METADATA_CACHE:
            entry = Probe.METADATA_CACHE[key]
            delta = datetime.datetime.utcnow() - entry['time']
            metadata = entry['metadata']

            # Don't keep cache forever, refresh every N mins
            if delta.seconds > App.get_config()['GHC_METADATA_CACHE_SECS']:
                entry = Probe.METADATA_CACHE.pop(key)
                del entry
                metadata = None

        if not metadata:
            # Get actual metadata, Resource-type specifc
            metadata = self.get_metadata(resource, version)
            if metadata and App.get_config()['GHC_METADATA_CACHE_SECS'] > 0:
                # Store entry with time, for expiry later
                entry = {
                    "metadata": metadata,
                    "time": datetime.datetime.utcnow()
                }
                Probe.METADATA_CACHE[key] = entry

        return metadata

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
            check_vars = Plugin.copy(check.get_plugin_vars())

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

    def get_checks_info_defaults(self):
        checks_avail = self.get_checks_info()
        checks_avail_default = {}
        for check_class in checks_avail:
            check_avail = checks_avail[check_class]

            # Only include default Checks if specified
            if 'default' in check_avail and check_avail['default']:
                checks_avail_default[check_class] = check_avail

        return checks_avail_default

    def get_checks_info(self):
        return Plugin.copy(Plugin.get_plugin_vars(self))['CHECKS_AVAIL']

    def get_plugin_vars(self):
        probe_vars = Plugin.copy(Plugin.get_plugin_vars(self))

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
            if '?' in url_base and self.REQUEST_TEMPLATE[0] == '?':
                self.REQUEST_TEMPLATE = '&' + self.REQUEST_TEMPLATE[1:]

            if self._parameters:
                request_parms = self._parameters
                param_defs = self.get_param_defs()

                # Expand string list array to comma separated string
                for param in request_parms:
                    if param_defs[param]['type'] == 'stringlist':
                        request_parms[param] = ','.join(request_parms[param])

                request_string = self.REQUEST_TEMPLATE.format(**request_parms)

        self.log('Requesting: %s url=%s' % (self.REQUEST_METHOD, url_base))

        try:
            headers = self.get_request_headers()
            if self.REQUEST_METHOD == 'GET':
                # Default is plain URL, e.g. for WWW:LINK
                url = url_base
                if request_string:
                    # Query String: mainly OWS:* resources
                    url = "%s%s" % (url, request_string)

                self.response = requests.get(url,
                                             headers=headers)
            elif self.REQUEST_METHOD == 'POST':
                self.response = requests.post(url_base,
                                              data=request_string,
                                              headers=headers)
        except requests.exceptions.RequestException as e:
            msg = "Request Err: %s %s" % (e.__class__.__name__, str(e))
            self.result.set(False, msg)

        if self.response:
            self.log('response: status=%d' % self.response.status_code)

            if self.response.status_code / 100 in [4, 5]:
                self.log('Error response: %s' % (str(self.response.text)))

    def run_request(self):
        """ Run actual request to service"""
        try:
            self.before_request()
            self.result.start()

            try:
                self.perform_request()
            except Exception as e:
                msg = "Perform_request Err: %s %s" % \
                      (e.__class__.__name__, str(e))
                self.result.set(False, msg)

            self.result.stop()
            self.after_request()
        except Exception as e:
            # We must never bailout because of Exception
            # in Probe.
            msg = "Probe Err: %s %s" % (e.__class__.__name__, str(e))
            LOGGER.error(msg)
            self.result.set(False, msg)

    def run_checks(self):
        """ Do the checks on the response from request"""

        # Do not run Checks if Probe already failed
        if not self.result.success:
            return

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
                msg = "Check Err: %s" % str(sys.exc_info())
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
