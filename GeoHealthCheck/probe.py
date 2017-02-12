import sys
import datetime
import requests
from factory import Factory
from result import Result

class Probe(object):
    """
     Base class for specific Request&Check implementations.

    """

    # Generic attributes, subclassses override
    AUTHOR = 'GHC Team'
    NAME = 'Fill in Name'
    DESCRIPTION = 'Fill in Description'
    RESOURCE_TYPE = 'OGC:*'

    # Request attributes
    REQUEST_METHOD = 'GET'
    REQUEST_HEADERS = None
    REQUEST_TEMPLATE = ''
    REQUEST_PARAMETERS = None

    # Possible response checks attributes
    RESPONSE_CHECKS = None

    # Lifecycle
    def init(self, config=None):
        # Config contains the actual parameters (from Models/DB) for Request and Checks
        self.config = config

        self.response = None
        self.result = Result()

    # Lifecycle
    def exit(self):
        pass

    def log(self, text):
        print('%s: %s' % (self.__class__.__name__, text))

    def do_request(self):
        """ Perform actual request to service"""

        # Actualize request query string or POST body
        # by substitution in template.
        request_template = self.REQUEST_TEMPLATE
        request_parms = self.config.parameters
        request_string = request_template.format(**request_parms)

        url_base = self.config.resource.url
        self.log('Doing request: method=%s url=%s' % (self.REQUEST_METHOD, url_base))
        self.result.start_time = datetime.datetime.utcnow()
        if self.REQUEST_METHOD == 'GET':
            url = url_base + request_string
            self.response = requests.get(url,
                                         headers=self.REQUEST_HEADERS)
        elif self.REQUEST_METHOD == 'POST':
            self.response = requests.post(url_base,
                                          data=request_string,
                                          headers=self.REQUEST_HEADERS)

        self.log('response: status=%d' % (self.response.status_code))
        if self.response.status_code != 200:
            self.log('response: %s' % (str(self.response.text)))

        end_time = datetime.datetime.utcnow()

        delta = end_time - self.result.start_time
        self.result.response_time = '%s.%s' % (delta.seconds, delta.microseconds)

    def do_checks(self):
        """ Do the checks on the response from request"""

        # Config also determines which actual checks are performed from possible
        # Checks in Probe
        checks = self.config.checks
        for check in checks:
            fun_str = check.check_identifier
            fun = Factory.create_function(fun_str)
            try:
                result = fun(self, check.parameters)
            except:
                msg = "Exception: %s" % str(sys.exc_info())
                self.log(msg)
                result = False, msg
            self.log('Check: fun=%s result=%s' % (fun_str, result[0]))

            self.result.checks.append({'check': fun_str, 'success' : result[0], 'message' : result[1]})

    # Lifecycle
    def calc_result(self):
        """ Calculate overall result from the Result object"""

        check_results = self.result.checks
        for check_result in check_results:
            if check_result['success'] is False:
                self.result.success = False
                self.result.message = check_result['message']
                break

        self.log("Result: %s" % str(self.result))

    @staticmethod
    def run(config):
        """ Class method to create and run a single Probe"""

        # Create Probe instance from module.class string
        probe = Factory.create_obj(config.request_identifier)

        # Initialize with actual parameters
        probe.init(config)

        # Perform request
        probe.do_request()

        # Perform the Probe's checks
        probe.do_checks()

        # Determine result
        probe.calc_result()

        # Lifecycle
        probe.exit()

        # Return result
        return probe.result

    def __str__(self):
        return "%s" % str(self.__class__)
