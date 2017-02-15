from GeoHealthCheck.proberunner import ProbeRunner

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
  <wfs:Query typeName="{typename}" srsName="{srs}" xmlns:{typename_ns}="{typename_ns_url}">
    <ogc:Filter xmlns:ogc="http://www.opengis.net/ogc">
      <ogc:BBOX>
        <ogc:PropertyName>{geom_property_name}</ogc:PropertyName>
        <gml:Envelope xmlns:gml="http://www.opengis.net/gml" srsName="{srs}">
          <gml:lowerCorner>{lower_x} {lower_y}</gml:lowerCorner>
          <gml:upperCorner>{upper_x} {upper_y}</gml:upperCorner>
        </gml:Envelope>
      </ogc:BBOX>
    </ogc:Filter>
  </wfs:Query>
</wfs:GetFeature>
    """

    REQUEST_PARAMETERS = [
        {
            'name': 'typename',
            'type': 'string'
        },
        {
            'name': 'typename_ns',
            'type': 'string'
        },
        {
            'name': 'typename_ns_url',
            'type': 'string'
        },
        {
            'name': 'geom_property_name',
            'type': 'string'
        },
        {
            'name': 'srs',
            'type': 'string'
        },
        {
            'name': 'lower_x',
            'type': 'string'
        },
        {
            'name': 'lower_y',
            'type': 'string'
        },
        {
            'name': 'upper_x',
            'type': 'string'
        },
        {
            'name': 'upper_y',
            'type': 'string'
        }
    ]

    RESPONSE_CHECKS = [
        {
            'name': 'parse_response',
            'description': 'response is parsable',
            'function': 'GeoHealthCheck.checks.xml_parse'
        },
        {
            'name': 'no OWS Exception',
            'description': 'response does not contain OWS Exception',
            'function': 'GeoHealthCheck.checks.not_contains_exception'
        },
        {
            'name': 'contains_feature_coll',
            'description': 'find FeatureCollection element in response doc',
            'function': 'GeoHealthCheck.checks.contains_string',
            'parameters': [
                {
                    'name': 'text',
                    'type': 'string',
                    'value': 'FeatureCollection>'
                }
            ]
        }
    ]

