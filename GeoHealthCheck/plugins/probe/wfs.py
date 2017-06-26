from GeoHealthCheck.probe import Probe
from owslib.wfs import WebFeatureService


class WfsGetFeatureBbox(Probe):
    """
    do WFS GetFeature in BBOX
    """

    NAME = 'WFS GetFeature in BBOX'
    DESCRIPTION = """
        Do WFS GetFeature request in BBOX with user-specified parameters
        """
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
  <wfs:Query typeName="{type_name}" srsName="{srs}"
        xmlns:{type_ns_prefix}="{type_ns_uri}">
    <ogc:Filter xmlns:ogc="http://www.opengis.net/ogc">
      <ogc:BBOX>
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
            'required': True,
            'range': None
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
            'default': None,
            'required': True,
            'value': 'Not Required',
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
        'GeoHealthCheck.plugins.check.checks.XmlParse': {
            'default': True
        },
        'GeoHealthCheck.plugins.check.checks.NotContainsOwsException': {
            'default': True
        },
        'GeoHealthCheck.plugins.check.checks.ContainsStrings': {
            'default': True,
            'set_params': {
                'strings': {
                    'name': 'Must contain FeatureCollection Element',
                    'description': """
                        Has FeatureCollection element in response doc
                        """,
                    'value': ['FeatureCollection>']
                }
            }
        }
    }
    """
    Checks for WFS GetFeature Response available.
    Optionally override Check PARAM_DEFS using set_params
    e.g. with specific `value` or even `name`.
    """

    # Overridden: expand param-ranges from WMS metadata
    def expand_params(self, resource):

        # Use WMS Capabilities doc to get metadata for
        # PARAM_DEFS ranges/defaults
        try:
            wfs = WebFeatureService(resource.url, version="1.1.0")
            feature_types = wfs.contents
            feature_type_names = list(feature_types.keys())
            ft_namespaces = set([name.split(':')[0] if ':' in name else None
                                 for name in feature_type_names])
            ft_namespaces = filter(None, list(ft_namespaces))

            # In some cases default NS is used: no FT NSs
            if len(ft_namespaces) > 0:
                nsmap = wfs._capabilities.nsmap
            else:
                # Just use dummy NS, to satisfy REQUEST_TEMPLATE
                ft_namespaces = ['notapplicable']
                nsmap = {ft_namespaces[0]: 'http://not.appli.cable/'}
                self.PARAM_DEFS['type_ns_prefix']['value'] = ft_namespaces[0]
                self.PARAM_DEFS['type_ns_uri']['value'] = \
                    nsmap[ft_namespaces[0]]

            # FeatureTypes to select
            self.PARAM_DEFS['type_name']['range'] = feature_type_names
            self.PARAM_DEFS['type_ns_prefix']['range'] = ft_namespaces
            self.PARAM_DEFS['type_ns_uri']['range'] = \
                [nsmap[ns] for ns in ft_namespaces]

            # Image Format
            # for oper in wfs.operations:
            #     if oper.name == 'GetFeature':
            #         self.PARAM_DEFS['format']['range'] = \
            #             oper.formatOptions
            #         break

            # Take first feature_type to determine generic attrs
            feature_type_name, feature_type_entry = feature_types.popitem()

            # SRS
            crs_list = feature_type_entry.crsOptions
            srs_range = ['EPSG:%s' % crs.code for crs in crs_list]
            self.PARAM_DEFS['srs']['range'] = srs_range

            # bbox list: 0-3 is bbox, 4 is SRS
            bbox = feature_type_entry.boundingBoxWGS84
            self.PARAM_DEFS['srs']['default'] = srs_range[0]
            self.PARAM_DEFS['bbox']['default'] = \
                ['{:.2f}'.format(x) for x in bbox]

            # self.PARAM_DEFS['exceptions']['range'] = wfs.exceptions
        except Exception as err:
            raise err
