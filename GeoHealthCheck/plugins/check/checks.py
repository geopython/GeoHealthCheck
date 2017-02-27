import sys
from owslib.etree import etree
from GeoHealthCheck.plugin import Plugin
from GeoHealthCheck.check import Check

""" Contains basic Check classes for a Probe object."""


class HttpStatusNoError(Check):
    """
    Checks if HTTP status code is not in the 400- or 500-range.
    """

    def __init__(self):
        Check.__init__(self)

    def perform(self):
        """Default check: Resource should at least give no error"""
        result = True
        msg = 'OK'
        status = self.probe.response.status_code
        overall_status = status / 100
        if overall_status in [4, 5]:
            result = False
            msg = 'HTTP Error status=%d' % status

        return result, msg


class HttpHasHeaderValue(Check):
    """
    Checks if header exists and has given header value.
    See http://docs.python-requests.org/en/master/user/quickstart
    """

    PARAM_DEFS = {
        'header_name': {
            'type': 'string',
            'description': 'The HTTP header name',
            'default': None,
            'required': True,
            'range': None
        },
        'header_value': {
            'type': 'string',
            'description': 'The HTTP header value',
            'default': None,
            'required': True,
            'range': None
        }
    }
    """Param defs"""


    def __init__(self):
        Check.__init__(self)

    def perform(self):
        result = True
        msg = 'OK'
        name = self.get_param('header_name')
        value = self.get_param('header_value')
        headers = self.probe.response.headers
        if name not in headers:
            result = False
            msg = 'HTTP response has no header %s' % name
        elif headers[name] != value:
            result = False
            msg = 'HTTP response header %s has no value %s' % (name, value)

        return result, msg


class HttpHasContentType(HttpHasHeaderValue):
    """
    Checks if HTTP response has content type.
    """

    PARAM_DEFS = Plugin.merge(HttpHasHeaderValue.PARAM_DEFS, {
        'header_name': {
            'value': 'content-type'
        }
    })
    """Params defs for header content type."""

    def __init__(self):
        HttpHasHeaderValue.__init__(self)

    def perform(self):
        return HttpHasHeaderValue.perform(self)


class HttpHasImageContentType(Check):
    """
    Checks if HTTP response has image content type.
    """

    def __init__(self):
        Check.__init__(self)

    """
    Check if HTTP response has image/ ContentType header value
    """
    def perform(self):
        result = True
        msg = 'OK'
        name = 'content-type'
        headers = self.probe.response.headers
        if name not in headers:
            result = False
            msg = 'HTTP response has no header %s' % name
        elif 'image/' not in headers[name]:
            result = False
            msg = 'HTTP response header %s is not image type' % name

        return result, msg


class XmlParse(Check):
    """
    Checks if HTTP response is valid XML.
    """

    def __init__(self):
        Check.__init__(self)

    def perform(self):
        result = True
        msg = 'OK'
        try:
            etree.fromstring(self.probe.response.content)
        except:
            result = False
            msg = str(sys.exc_info())

        return result, msg


class ContainsStrings(Check):
    """
    Checks if HTTP response contains given strings (keywords).
    """

    PARAM_DEFS = {
        'strings': {
            'type': 'stringlist',
            'description': 'The string text(s) that should be contained in response',
            'default': None,
            'required': True,
            'range': None
        }
    }
    """Param defs"""

    def __init__(self):
        Check.__init__(self)

    def perform(self):
        result = True
        msg = 'OK'
        for text in self.get_param('strings'):
            try:
                result = text in self.probe.response.text
                if result is False:
                    msg = '%s not in response text' % text
                    break
            except:
                result = False
                msg = str(sys.exc_info())
                break

        return result, msg


class NotContainsStrings(ContainsStrings):
    """
    Checks if HTTP response NOT contains given strings (keywords).
    """

    PARAM_DEFS = Plugin.copy(ContainsStrings.PARAM_DEFS)
    """Param defs"""

    def __init__(self):
        ContainsStrings.__init__(self)

    def perform(self):
        result, msg = ContainsStrings.perform(self)
        if result is False and 'not in response text' in msg:
            result = True
            msg = 'OK'
        elif result is True:
            result = False
            msg = '%s in response text' % str(self.get_param('strings'))

        return result, msg


class NotContainsOwsException(NotContainsStrings):
    """
    Checks if HTTP response NOT contains given OWS Exceptions.
    """

    PARAM_DEFS = Plugin.merge(ContainsStrings.PARAM_DEFS, {
        'strings': {
            'value': ['ExceptionReport>', 'ServiceException>']
        }
    })
    """Param defs"""
