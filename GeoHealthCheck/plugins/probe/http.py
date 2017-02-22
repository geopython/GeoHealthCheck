from GeoHealthCheck.proberunner import ProbeRunner
from GeoHealthCheck.plugin import Parameter

class HttpGet(ProbeRunner):
    """
    Do HTTP GET Request, to poll/ping any Resource bare url.
    """

    NAME = 'HTTP GET Resource'
    RESOURCE_TYPE = '*:*'

    REQUEST_METHOD = 'GET'

    # TODO Check as Decorators
    # @Check(checker='GeoHealthCheck.plugins.check.checkers.HttpStatusNoError', optional=False)
    # def http_error_status(self):
    #     """
    #     response not in error range: i.e. 400 or 500-range.
    #     Optional: False
    #     """
    #     pass

    RESPONSE_CHECKS = [
        {
            'name': 'http_error_status',
            'description': 'response not in error range: i.e. 400 or 500-range',
            'class': 'GeoHealthCheck.plugins.check.checkers.HttpStatusNoError'
        },
        {
            'name': 'keywords exist',
            'description': 'keywords should be in response doc',
            'class': 'GeoHealthCheck.plugins.check.checkers.ContainsStrings',
        },
        {
            'name': 'keywords not_exist',
            'description': 'keywords should be not be in response doc',
            'class': 'GeoHealthCheck.plugins.check.checkers.NotContainsStrings',
        }
    ]

class HttpGetQuery(HttpGet):
    """
    Do HTTP GET Request, to poll/ping any Resource bare url with query string.
    """

    NAME = 'HTTP GET Resource with query'
    DESCRIPTION = 'HTTP Resource responds without client (400) or server (500) error on HTTP GET with query string'
    REQUEST_TEMPLATE = '?{query}'

    @Parameter(ptype=str, default=None, required=True)
    def query(self):
        """
        The query string to add to request (without ?).
        """
        pass

class HttpPost(HttpGet):
    """
    Do HTTP POST Request, to send POST request to Resource bare url with POST body.
    """

    NAME = 'HTTP POST Resource with body'
    DESCRIPTION = 'HTTP Resource responds without client (400) or server (500) error on HTTP GET with query string'

    REQUEST_METHOD = 'POST'
    REQUEST_HEADERS = { 'content-type': '{content_type}' }
    REQUEST_TEMPLATE = '{body}'

    @Parameter(ptype=str, default=None, required=True)
    def body(self):
        """
        The post body to send.
        """
        pass

    @Parameter(ptype=str, required=True, default='text/xml;charset=UTF-8')
    def content_type(self):
        """
        The post content type to send.
        """
        pass

    def get_request_headers(self):
        """
        Overridden from ProbeRunner: construct request_headers via parameter substitution
        from content_type Parameter.
        """

        content_type = { 'post_content_type': self.content_type }
        request_headers = self.REQUEST_HEADERS.format(**content_type)

        return request_headers
