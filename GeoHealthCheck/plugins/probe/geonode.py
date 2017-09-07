
from urlparse import urlparse
import requests

GEONODE_OWS_API = '/api/ows_endpoints/'


def get_ows_endpoints(base_url):
    r = requests.get('{}{}'.format(base_url.rstrip('/'), GEONODE_OWS_API))
    url = urlparse(base_url)
    base_name = 'GeoNode {}: {{}}'.format(url.hostname)
    if r.status_code != 200:
        msg = "Errorous response from GeoNode at {}: {}".format(base_url,
                                                                r.text)
        raise ValueError(msg)

    try:
        data = r.json()
    except (TypeError, ValueError,), err:
        msg = "Cannot decode response from GeoNode at {}: {}".format(base_url,
                                                                     err)
        raise ValueError(msg)

    def update(val):
        val['title'] = base_name.format(val['type'])
        return val

    return [update(d) for d in data['data']]


def make_default_tags(base_url):
    url = urlparse(base_url)
    tag_name = 'GeoNode: {}'.format(url.hostname)
    return [tag_name]
