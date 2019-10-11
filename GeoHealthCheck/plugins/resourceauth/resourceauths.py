import base64

from GeoHealthCheck.resourceauth import ResourceAuth


class NoAuth(ResourceAuth):
    """
    Checks if header exists and has given header value.
    See http://docs.python-requests.org/en/master/user/quickstart
    """

    NAME = 'None'
    DESCRIPTION = 'Default class for no auth'

    PARAM_DEFS = {}
    """Param defs"""

    def __init__(self):
        ResourceAuth.__init__(self)

    def verify(self):
        return False

    def encode(self):
        return None


class BasicAuth(ResourceAuth):
    """
    Basic authentication.
    """

    NAME = 'Basic'
    DESCRIPTION = 'Default class for no auth'

    PARAM_DEFS = {
        'username': {
            'type': 'string',
            'description': 'Username',
            'default': None,
            'required': True,
            'range': None
        },
        'password': {
            'type': 'password',
            'description': 'Password',
            'default': None,
            'required': True,
            'range': None
        }
    }
    """Param defs"""

    def __init__(self):
        ResourceAuth.__init__(self)

    def verify(self):
        if self.auth_dict is None:
            return False

        if 'data' not in self.auth_dict:
            return False

        auth_data = self.auth_dict['data']

        if auth_data.get('username', None) is None:
            return False

        if len(auth_data.get('username', '')) == 0:
            return False

        if auth_data.get('password', None) is None:
            return False

        if len(auth_data.get('password', '')) == 0:
            return False

        return True

    def encode_auth_header_val(self):
        """
        Get encoded authorization header value from config data.
        Authorization scheme-specific.
         {
            'type': 'Basic',
            'data': {
                'username': 'the_user',
                'password': 'the_password'
             }
        }


        :return: None or http Basic auth header value
        """

        # Has auth, encode as HTTP header value
        # Basic auth:
        # http://mozgovipc.blogspot.nl/2012/06/
        #   python-http-basic-authentication-with.html
        # base64 encode username and password
        # write the Authorization header
        # like: 'Basic base64encode(username + ':' + password)
        auth_creds = self.auth_dict['data']
        auth_val = base64.encodestring(
            '{}:{}'.format(auth_creds['username'], auth_creds['password']).encode())
        auth_val = "Basic %s" % auth_val
        return auth_val


class BearerTokenAuth(ResourceAuth):
    """
    Bearer token auth
    """

    NAME = 'Bearer Token'
    DESCRIPTION = 'Bearer token auth'

    PARAM_DEFS = {
        'token': {
            'type': 'password',
            'description': 'Token string',
            'default': None,
            'required': True,
            'range': None
        }
    }
    """Param defs"""

    def __init__(self):
        ResourceAuth.__init__(self)

    def verify(self):
        if self.auth_dict is None:
            return False

        if 'data' not in self.auth_dict:
            return False

        auth_data = self.auth_dict['data']

        if auth_data.get('token', None) is None:
            return False

        if len(auth_data.get('token', '')) == 0:
            return False

        return True

    def encode_auth_header_val(self):
        """
        Get encoded authorization header value from config data.
        Authorization scheme-specific.
         {
            'type': 'Bearer Token',
            'data': {
                'token': 'the_token'
             }
        }

        :return: None or http auth header value
        """

        # Bearer Type, see eg. https://tools.ietf.org/html/rfc6750
        return "Bearer %s" % self.auth_dict['data']['token']
