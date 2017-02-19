from GeoHealthCheck.proberunner import ProbeRunner
from GeoHealthCheck.plugin import Parameter

class WfsGetFeatureBbox(ProbeRunner):
    NAME = 'WFS GetFeature in BBOX'
    DESCRIPTION = 'do WFS GetFeature in BBOX'
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

    @Parameter(ptype=str, default=None, required=True)
    def type_name(self):
        """
        The TMS Layer service within resource endpoint.
        Required: True
        Default: None
        """
        pass

    @Parameter(ptype=str, default='0', required=True)
    def type_ns_prefix(self):
        """
        The typename namespace prefix.
        Required: True
        Default: None
        """
        pass

    @Parameter(ptype=str, required=True)
    def type_ns_uri(self):
        """
        The typename namespace URI.
        Required: True
        Default: None
        """
        pass

    @Parameter(ptype=str, default='the_geom', required=True)
    def geom_property_name(self):
        """
        The geometry property of the feature type.
        Required: True
        Default: None
        """
        pass

    @Parameter(ptype=str, default='EPSG:4326', required=True, value_range='fromCapabilities')
    def srs(self):
        """
        The SRS as EPSG: code.
        Required: True
        Default: None
        """
        pass

    @Parameter(ptype=list, default=['-180', '-90', '180', '90'], required=True)
    def bbox(self):
        """
        The bounding box as lower_X, lower_Y, upper_X, uppoer_Y in SRS scheme.
        Required: True
        Default: None
        """
        pass

    RESPONSE_CHECKS = [
        {
            'name': 'parse_response',
            'description': 'response is parsable',
            'class': 'GeoHealthCheck.plugins.check.checkers.XmlParse'
        },
        {
            'name': 'no OWS Exception',
            'description': 'response does not contain OWS Exception',
            'class': 'GeoHealthCheck.plugins.check.checkers.NotContainsOwsException'
        },
        {
            'name': 'contains_feature_coll',
            'description': 'find FeatureCollection element in response doc',
            'class': 'GeoHealthCheck.plugins.check.checkers.ContainsStrings',
            'parameters': [
                {
                    'name': 'text',
                    'type': 'string',
                    'value': 'FeatureCollection>'
                }
            ]
        }
    ]

