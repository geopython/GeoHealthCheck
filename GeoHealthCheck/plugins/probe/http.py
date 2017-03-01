from GeoHealthCheck.probe import Probe


class HttpGet(Probe):
    """
    Do HTTP GET Request, to poll/ping any Resource bare url.
    """

    NAME = 'HTTP GET Resource URL'
    RESOURCE_TYPE = '*:*'
    REQUEST_METHOD = 'GET'

    CHECKS_AVAIL = {
        'GeoHealthCheck.plugins.check.checkers.HttpStatusNoError': {},
        'GeoHealthCheck.plugins.check.checkers.ContainsStrings': {},
        'GeoHealthCheck.plugins.check.checkers.NotContainsStrings': {},
    }
    """Checks avail"""


class HttpGetQuery(HttpGet):
    """
    Do HTTP GET Request, to poll/ping any Resource bare url with query string.
    """

    NAME = 'HTTP GET Resource URL with query'
    DESCRIPTION = 'HTTP GET Resource URL with query string to be supplied'
    REQUEST_TEMPLATE = '?{query}'

    PARAM_DEFS = {
        'query': {
            'type': 'string',
            'description': 'The query string to add to request (without ?)',
            'default': None,
            'required': True
        }
    }
    """Param defs"""


class HttpPost(HttpGet):
    """
    Do HTTP POST Request, to send POST request to Resource bare url with POST body.
    """

    NAME = 'HTTP POST Resource URL with body'
    DESCRIPTION = 'HTTP Resource responds without client (400) or server (500) error on HTTP GET with query string'

    REQUEST_METHOD = 'POST'
    REQUEST_HEADERS = {'content-type': '{post_content_type}'}
    REQUEST_TEMPLATE = '{body}'

    PARAM_DEFS = {
        'body': {
            'type': 'string',
            'description': 'The post body to send',
            'default': None,
            'required': True
        },
        'content_type': {
            'type': 'string',
            'description': 'The post content type to send',
            'default': 'text/xml;charset=UTF-8',
            'required': True
        }
    }
    """Param defs"""

    def get_request_headers(self):
        """
        Overridden from Probe: construct request_headers via parameter substitution
        from content_type Parameter.
        """

        content_type = {'post_content_type': self.content_type }
        request_headers = self.REQUEST_HEADERS.format(**content_type)

        return request_headers
