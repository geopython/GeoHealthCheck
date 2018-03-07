from GeoHealthCheck.plugin import Plugin
from GeoHealthCheck.probe import Probe


class HttpGet(Probe):
    """
    Do HTTP GET Request, to poll/ping any Resource bare url.
    """

    NAME = 'HTTP GET Resource URL'
    DESCRIPTION = 'Simple HTTP GET on Resource URL'
    RESOURCE_TYPE = '*:*'
    REQUEST_METHOD = 'GET'

    CHECKS_AVAIL = {
        'GeoHealthCheck.plugins.check.checks.HttpStatusNoError': {
            'default': True
        },
        'GeoHealthCheck.plugins.check.checks.ContainsStrings': {},
        'GeoHealthCheck.plugins.check.checks.NotContainsStrings': {},
        'GeoHealthCheck.plugins.check.checks.HttpHasContentType': {}
    }
    """Checks avail"""

    PARAM_DEFS = {
        'username': {
            'type': 'string',
            'description': 'HTTP-Basic-Authentication username',
            'default': None,
            'required': False
        },
        'password': {
            'type': 'string',
            'description': 'HTTP-Basic-Authentication password',
            'default': None,
            'required': False
        }
    }
    """Param defs"""

class HttpGetQuery(HttpGet):
    """
    Do HTTP GET Request, to poll/ping any Resource bare url with query string.
    """

    NAME = 'HTTP GET Resource URL with query'
    DESCRIPTION = """
        HTTP GET Resource URL with
        ?query string to be user-supplied (without ?)
        """
    REQUEST_TEMPLATE = '?{query}'

    PARAM_DEFS = Plugin.merge(HttpGet.PARAM_DEFS, {
        'query': {
            'type': 'string',
            'description': 'The query string to add to request (without ?)',
            'default': None,
            'required': True
        }
    })
    """Param defs"""


class HttpPost(HttpGet):
    """
    Do HTTP POST Request, to send POST request to
    Resource bare url with POST body.
    """

    NAME = 'HTTP POST Resource URL with body'
    DESCRIPTION = """
        HTTP POST to Resource URL with body
        content(-type) to be user-supplied
        """

    REQUEST_METHOD = 'POST'
    REQUEST_HEADERS = {'content-type': '{post_content_type}'}
    REQUEST_TEMPLATE = '{body}'

    PARAM_DEFS = Plugin.merge(HttpGet.PARAM_DEFS, {
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
    })
    """Param defs"""

    def get_request_headers(self):
        """
        Overridden from Probe: construct request_headers
        via parameter substitution from content_type Parameter.
        """

        # content_type =
        # {'post_content_type': self._parameters['content_type']}
        # request_headers =
        #       self.REQUEST_HEADERS['content-type'].format(**content_type)
        # Hmm seems simpler
        return {'content-type': self._parameters['content_type']}
