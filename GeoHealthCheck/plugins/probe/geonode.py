
from urlparse import urlparse
import requests


GEONODE_OWS_API = '/api/ows_endpoints/'
def get_ows_endpoints(base_url):
    r = requests.get('{}{}'.format(base_url.rstrip('/'), GEONODE_OWS_API))
    url = urlparse(base_url)
    base_name = 'GeoNode {}: {{}}'.format(url.hostname)
    if r.status_code != 200:
        raise ValueError("Errorous response from GeoNode at {}: {}".format(base_url, r.text))

    try:
        data = r.json()
    except (TypeError, ValueError,), err:
        raise ValueError("Cannot decode response from GeoNode at {}: {}".format(base_url, err))
    
    def update(val):
        val['title'] = base_name.format(val['type'])
        return val

    return [update(d) for d in data['data']]

def make_default_tags(base_url):
    url = urlparse(base_url)
    tag_name = 'GeoNode: {}'.format(url.hostname)
    return [tag_name]

def endpoints_to_resources(endpoints, tags, owner):
    out = []
    for endpoint in endpoints:
        r = Resource(owner=owner, **endpoint)
        r.tags = tags
        out.append(r)
    return out

