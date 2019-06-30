import json
import logging
from plugin import Plugin
from factory import Factory
from util import encode, decode
from init import App
APP = App.get_app()
LOGGER = logging.getLogger(__name__)


class ResourceAuth(Plugin):
    """
     Base class for specific Plugin implementations to perform
     authentication on a Resource.
    """

    def __init__(self):
        Plugin.__init__(self)
        self.resource = None
        self.auth_dict = None

    # Lifecycle
    def init(self, auth_dict=None):
        """
        Initialize ResourceAuth with related Resource and auth dict.
        :return:
        """
        self.auth_dict = auth_dict

    @staticmethod
    def create(auth_dict):
        auth_type = auth_dict['type']
        auth_class = ResourceAuth.get_auth_types()[auth_type]
        auth_obj = Factory.create_obj(auth_class)
        auth_obj.init(auth_dict)
        return auth_obj

    @staticmethod
    def get_auth_types():
        auth_classes = Plugin.get_plugins(
            baseclass='GeoHealthCheck.resourceauth.ResourceAuth')
        result = {}
        for auth_class in auth_classes:
            auth_obj = Factory.create_obj(auth_class)
            result[auth_obj.NAME] = auth_class

        return result

    def verify(self):
        return False

    def encode(self):
        if not self.verify():
            return None

        try:
            s = json.dumps(self.auth_dict)
            return encode(APP.config['SECRET_KEY'], s)
        except Exception as err:
            LOGGER.error('Error encoding auth: %s' % str(err))
            raise err

    @staticmethod
    def decode(encoded):
        if encoded is None:
            return None

        try:
            s = decode(APP.config['SECRET_KEY'], str(encoded))
            return json.loads(s)
        except Exception as err:
            LOGGER.error('Error decoding auth: %s' % str(err))
            raise err

    def add_auth_header(self, headers_dict):
        auth_header = self.get_auth_header()
        if auth_header:
            headers_dict.update(auth_header)
        return headers_dict

    def get_auth_header(self):
        """
        Get encoded authorization header value from config data.
        Authorization scheme-specific.
        :return: None or dict with http auth header
        """
        if not self.verify():
            return None

        auth_val = self.encode_auth_header_val()
        if not auth_val:
            return None

        return {'Authorization': auth_val.replace('\n', '')}

    def encode_auth_header_val(self):
        return None
