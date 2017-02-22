import sys
from owslib.etree import etree
from GeoHealthCheck.checker import Checker
from GeoHealthCheck.plugin import Parameter

""" Contains basic Checker classes for a ProbeRunner object."""


class HttpStatusNoError(Checker):
    """
    Checks if HTTP status code is not in the 400- or 500-range.
    """
    
    def perform(self):
        """Default check: Resource should at least give no error"""
        result = True
        msg = 'OK'
        status = self.prober.response.status_code
        overall_status = status/100
        if overall_status in [4, 5]:
            result = False
            msg = 'HTTP Error status=%d' % status
    
        return result, msg


class HttpHasHeaderValue(Checker):
    """
    Checks if header exists and has given header value.
    See http://docs.python-requests.org/en/master/user/quickstart
    """

    @Parameter(ptype=str, default=None, required=True)
    def header_name(self):
        """
        The HTTP header name.
        """
        pass

    @Parameter(ptype=str, default=None, required=True)
    def header_value(self):
        """
        The HTTP header value.
        """
        pass

    def perform(self):
        result = True
        msg = 'OK'
        name = self.header_name
        value = self.header_value
        headers = self.prober.response.headers
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

    @Parameter(ptype=str, default=None, required=True, value='content-type')
    def header_name(self):
        """
        The HTTP header name.
       """
        pass

    """Check if HTTP response has given ContentType header value"""
    def perform(self):
        return HttpHasHeaderValue.perform(self)


class XmlParse(Checker):
    """
    Checks if HTTP response is valid XML.
    """

    def perform(self):
        result = True
        msg = 'OK'
        try:
            etree.fromstring(self.prober.response.content)
        except:
            result = False
            msg = str(sys.exc_info())
    
        return result, msg


class ContainsStrings(Checker):
    """
    Checks if HTTP response contains given strings (keywords).
    """

    @Parameter(ptype=list, default=None, required=True)
    def strings(self):
        """
        The string text(s) that should be contained in response.
        """
        pass

    def perform(self):
        result = True
        msg = 'OK'
        for text in self.strings:
            try:
                result = text in self.prober.response.text
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

    def perform(self):
        result, msg = ContainsStrings.perform(self)
        if result is False and 'not in response text' in msg:
            result = True
            msg = 'OK'
        elif result is True:
            result = False
            msg = '%s in response text' % self.strings
    
        return result, msg


class NotContainsOwsException(NotContainsStrings):
    """
    Checks if HTTP response NOT contains given OWS Exceptions.
    """

    @Parameter(ptype=list, default=None, required=True, value=['ExceptionReport>', 'ServiceException>'])
    def strings(self):
        """
        The string text(s).
        """
        pass
