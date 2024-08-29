import sys
from owslib.etree import etree
from GeoHealthCheck.util import CONFIG
from GeoHealthCheck.plugin import Plugin
from GeoHealthCheck.check import Check
from html import escape


""" Contains basic Check classes for a Probe object."""


class HttpStatusNoError(Check):
    """
    Checks if HTTP status code is not in the 400- or 500-range.
    """

    NAME = 'HTTP status should not be errored'
    DESCRIPTION = 'Response should not contain a HTTP 400 or 500 range Error'

    def __init__(self):
        Check.__init__(self)

    def perform(self):
        """Default check: Resource should at least give no error"""
        status = self.probe.response.status_code
        overall_status = status // 100
        if overall_status in [4, 5]:
            self.set_result(False, 'HTTP Error status=%d' % status)


class HttpHasHeaderValue(Check):
    """
    Checks if header exists and has given header value.
    See http://docs.python-requests.org/en/master/user/quickstart
    """

    NAME = 'Has specific HTTP Header value'
    DESCRIPTION = 'HTTP response has specific HTTP Header value'

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

        self.set_result(result, msg)


class HttpHasContentType(HttpHasHeaderValue):
    """
    Checks if HTTP response has content type.
    """

    NAME = 'Has specific Content-Type'
    DESCRIPTION = 'HTTP response has specific Content-Type'

    PARAM_DEFS = Plugin.merge(HttpHasHeaderValue.PARAM_DEFS, {
        'header_name': {
            'value': 'content-type'
        }
    })
    """Params defs for header content type."""

    def __init__(self):
        HttpHasHeaderValue.__init__(self)

    def perform(self):
        HttpHasHeaderValue.perform(self)


class HttpHasImageContentType(Check):
    """
    Checks if HTTP response has image content type.
    """

    NAME = 'HTTP response is image'
    DESCRIPTION = 'HTTP response has image/* Content-Type'

    def __init__(self):
        Check.__init__(self)

    """
    Check if HTTP response has image/ ContentType header value
    """
    def perform(self):
        result = True
        msg = 'OK'
        name = 'content-type'
        response = self.probe.response
        headers = response.headers
        if name not in headers:
            result = False
            msg = 'HTTP response has no header %s' % name
        elif 'image/' not in headers[name]:
            result = False
            msg = 'HTTP response header %s is not image type' % name
            if type(response.content) is str:
                rsp_str = response.content
                if len(rsp_str) > 256:
                    rsp_str = rsp_str[-256:]
                msg += ' - error: ' + escape(rsp_str)
        self.set_result(result, msg)


class XmlParse(Check):
    """
    Checks if HTTP response is valid XML.
    """

    NAME = 'Valid XML response'
    DESCRIPTION = 'HTTP response contains valid XML'

    def __init__(self):
        Check.__init__(self)

    def perform(self):
        try:
            etree.fromstring(
                self.probe.response.content,
                parser=etree.XMLParser(huge_tree=CONFIG['GHC_LARGE_XML']))
        except Exception:
            self.set_result(False, str(sys.exc_info()))


class JsonParse(Check):
    """
    Checks if HTTP response is valid JSON.
    """

    NAME = 'Valid JSON response'
    DESCRIPTION = 'HTTP response contains valid JSON'

    def __init__(self):
        Check.__init__(self)

    def perform(self):
        import json
        try:
            json.loads(self.probe.response.content)
        except Exception:
            self.set_result(False, str(sys.exc_info()))


class ContainsStrings(Check):
    """
    Checks if HTTP response contains given strings (keywords).
    """

    NAME = 'Response contains strings'
    DESCRIPTION = \
        'HTTP response contains all (comma-separated) strings specified'

    PARAM_DEFS = {
        'strings': {
            'type': 'stringlist',
            'description':
                'The string text(s) that should be contained \
                 in response (comma-separated)',
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
            except Exception:
                result = False
                msg = str(sys.exc_info())
                break

        self.set_result(result, msg)


class NotContainsStrings(ContainsStrings):
    """
    Checks if HTTP response NOT contains given strings (keywords).
    """

    NAME = 'Response NOT contains strings'
    DESCRIPTION = """
        HTTP response does not contain any of the
        (comma-separated) strings specified
        """

    PARAM_DEFS = {
        'strings': {
            'type': 'stringlist',
            'description':
                """The string text(s) that should NOT be
                contained in response (comma-separated)""",
            'default': None,
            'required': True,
            'range': None
        }
    }
    """Param defs"""

    def __init__(self):
        ContainsStrings.__init__(self)

    def perform(self):
        result = True
        msg = 'OK'
        for text in self.get_param('strings'):
            try:
                result = text not in self.probe.response.text
                if result is False:
                    if 'exception' in self.probe.response.text.lower():
                        msg = self.probe.response.text
                    else:
                        msg = '%s in response text' % text
                    break
            except Exception:
                result = False
                msg = str(sys.exc_info())
                break

        self.set_result(result, msg)


class NotContainsOwsException(NotContainsStrings):
    """
    Checks if HTTP response NOT contains given OWS Exceptions.
    """

    NAME = 'Response NOT contains OWS Exception'
    DESCRIPTION = 'HTTP response does not contain an OWS Exception'

    PARAM_DEFS = Plugin.merge(ContainsStrings.PARAM_DEFS, {
        'strings': {
            'value': ['ExceptionReport>', 'ServiceException>']
        }
    })
    """Param defs"""
