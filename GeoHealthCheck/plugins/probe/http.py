from GeoHealthCheck.probe import Probe
from GeoHealthCheck.plugindecor import Parameter, UseCheck


class HttpGet(Probe):
    """
    Do HTTP GET Request, to poll/ping any Resource bare url.
    """

    NAME = 'HTTP GET Resource URL'
    RESOURCE_TYPE = '*:*'
    REQUEST_METHOD = 'GET'

    def __init__(self):
        Probe.__init__(self)

    @UseCheck(check_class='GeoHealthCheck.plugins.check.checks.HttpStatusNoError')
    def no_http_error(self):
        """
        response not in error range: i.e. 400 or 500-range.
        """
        pass

    @UseCheck(check_class='GeoHealthCheck.plugins.check.checks.ContainsStrings')
    def contains_strings(self):
        """
        keywords should be in response doc.
        """
        pass

    @UseCheck(check_class='GeoHealthCheck.plugins.check.checks.NotContainsStrings')
    def not_contains_strings(self):
        """
        keywords should NOT be in response doc.
        """
        pass


class HttpGetQuery(HttpGet):
    """
    Do HTTP GET Request, to poll/ping any Resource bare url with query string.
    """

    NAME = 'HTTP GET Resource URL with query'
    DESCRIPTION = 'HTTP Resource responds without client (400) or server (500) error on HTTP GET with query string'
    REQUEST_TEMPLATE = '?{query}'

    def __init__(self):
        HttpGet.__init__(self)

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

    NAME = 'HTTP POST Resource URL with body'
    DESCRIPTION = 'HTTP Resource responds without client (400) or server (500) error on HTTP GET with query string'

    REQUEST_METHOD = 'POST'
    REQUEST_HEADERS = {'content-type': '{content_type}'}
    REQUEST_TEMPLATE = '{body}'

    def __init__(self):
        HttpGet.__init__(self)

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
        Overridden from Probe: construct request_headers via parameter substitution
        from content_type Parameter.
        """

        content_type = { 'post_content_type': self.content_type }
        request_headers = self.REQUEST_HEADERS.format(**content_type)

        return request_headers
