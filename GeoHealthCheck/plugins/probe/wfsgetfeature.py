from GeoHealthCheck.probe import Probe


class WfsGetFeatureBbox(Probe):
    """
    do WFS GetFeature in BBOX
    """

    NAME = 'WFS GetFeature in BBOX'
    RESOURCE_TYPE = 'OGC:WFS'

    REQUEST_METHOD = 'POST'
    REQUEST_HEADERS = {
        'content-type': 'text/xml;charset=UTF-8'
    }
    REQUEST_TEMPLATE = """<wfs:GetFeature
xmlns:wfs="http://www.opengis.net/wfs"
service="WFS"
version="1.1.0"
outputFormat="GML2"
xsi:schemaLocation="http://www.opengis.net/wfs
http://schemas.opengis.net/wfs/1.1.0/wfs.xsd"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <wfs:Query typeName="{type_name}" srsName="{srs}" xmlns:{type_ns_prefix}="{type_ns_uri}">
    <ogc:Filter xmlns:ogc="http://www.opengis.net/ogc">
      <ogc:BBOX>
        <ogc:PropertyName>{geom_property_name}</ogc:PropertyName>
        <gml:Envelope xmlns:gml="http://www.opengis.net/gml" srsName="{srs}">
          <gml:lowerCorner>{bbox[0]} {bbox[1]}</gml:lowerCorner>
          <gml:upperCorner>{bbox[2]} {bbox[3]}</gml:upperCorner>
        </gml:Envelope>
      </ogc:BBOX>
    </ogc:Filter>
  </wfs:Query>
</wfs:GetFeature>
    """
    def __init__(self):
        Probe.__init__(self)

    PARAM_DEFS = {
        'type_name': {
            'type': 'string',
            'description': 'The WFS FeatureType name',
            'default': None,
            'required': True
        },
        'type_ns_prefix': {
            'type': 'string',
            'description': 'The WFS FeatureType namespace prefix',
            'default': None,
            'required': True,
            'range': None
        },
        'type_ns_uri': {
            'type': 'string',
            'description': 'The WFS FeatureType namespace URI',
            'default': '0',
            'required': True,
            'range': None
        },
        'geom_property_name': {
            'type': 'string',
            'description': 'Name of the geometry property within FeatureType',
            'default': 'the_geom',
            'required': True,
            'range': None
        },
        'srs': {
            'type': 'string',
            'description': 'The SRS as EPSG: code',
            'default': 'EPSG:4326',
            'required': True,
            'range': None
        },
        'bbox': {
            'type': 'bbox',
            'description': 'The tile image extension',
            'default': ['-180', '-90', '180', '90'],
            'required': True,
            'range': None
        }
    }
    """Param defs"""

    CHECKS_AVAIL = {
        'GeoHealthCheck.plugins.check.checks.XmlParse': {},
        'GeoHealthCheck.plugins.check.checks.NotContainsOwsException': {},
        'GeoHealthCheck.plugins.check.checks.ContainsStrings': {
            'parameters': {
                'description': 'Has FeatureCollection element in response doc',
                'strings': ['FeatureCollection>']
            }
        }
    }
    """Checks for WFS GetFeature Response available"""
