from GeoHealthCheck.probe import Probe
from GeoHealthCheck.plugin import Plugin
from GeoHealthCheck.util import transform_bbox
from owslib.wfs import WebFeatureService


class WfsGetFeatureBbox(Probe):
    """
    do WFS GetFeature in BBOX
    """

    NAME = "WFS GetFeature in BBOX for SINGLE FeatureType"
    DESCRIPTION = """
        WFS GetFeature in BBOX for SINGLE FeatureType.
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
outputFormat="text/xml; subtype=gml/3.1.1"
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
                    'value': ['FeatureCollection']
                }
            }
        }
    }
    """
    Checks for WFS GetFeature Response available.
    Optionally override Check PARAM_DEFS using set_params
    e.g. with specific `value` or even `name`.
    """

    def __init__(self):
        Probe.__init__(self)
        self.layer_count = 0

    def get_metadata(self, resource, version='1.1.0'):
        """
        Get metadata, specific per Resource type.
        :param resource:
        :param version:
        :return: Metadata object
        """
        return WebFeatureService(resource.url, version=version)

    # Overridden: expand param-ranges from WFS metadata
    def expand_params(self, resource):

        # Use WFS Capabilities doc to get metadata for
        # PARAM_DEFS ranges/defaults
        try:
            wfs = self.get_metadata_cached(resource, version='1.1.0')
            feature_types = wfs.contents
            feature_type_names = list(feature_types.keys())
            self.layer_count = len(feature_type_names)

            ft_namespaces = set([name.split(':')[0] if ':' in name else None
                                 for name in feature_type_names])
            ft_namespaces = filter(None, list(ft_namespaces))

            # In some cases default NS is used: no FT NSs
            nsmap = None
            if len(ft_namespaces) > 0:
                try:
                    # issue #243 this depends if lxml etree present
                    # and used by OWSLib ! Otherwise fall-back.
                    nsmap = wfs._capabilities.nsmap
                except Exception:
                    # Fall-back
                    pass

            if not nsmap:
                # Just build dummy NS map, to satisfy REQUEST_TEMPLATE
                ft_namespaces = ['dummyns']
                nsmap = {ft_namespaces[0]: 'http://dummy.ns/'}
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

            # Take random feature_type to determine generic attrs
            for feature_type_name in feature_types:
                feature_type_entry = feature_types[feature_type_name]
                break

            # SRS
            crs_list = feature_type_entry.crsOptions
            srs_range = ['EPSG:%s' % crs.code for crs in crs_list]
            self.PARAM_DEFS['srs']['range'] = srs_range
            default_srs = srs_range[0]
            self.PARAM_DEFS['srs']['default'] = default_srs

            # bbox as list: 0-3 is bbox llx, lly, ulx, uly
            bbox = feature_type_entry.boundingBoxWGS84

            # It looks like the first SRS is the default
            # if it is not EPSG:4326 we need to transform bbox
            if default_srs != 'EPSG:4326':
                bbox = transform_bbox('EPSG:4326', srs_range[0], bbox)

            # Convert bbox floats to str
            self.PARAM_DEFS['bbox']['default'] = \
                [str(f) for f in bbox]

            # self.PARAM_DEFS['exceptions']['range'] = wfs.exceptions
        except Exception as err:
            raise err


class WfsGetFeatureBboxAll(WfsGetFeatureBbox):
    """
    Do WFS GetFeature for each FeatureType in WFS.
    """

    NAME = "WFS GetFeature in BBOX for ALL FeatureTypes"
    DESCRIPTION = """
        WFS GetFeature in BBOX for ALL FeatureTypes.
        """
    # Copy all PARAM_DEFS from parent to have own instance
    PARAM_DEFS = Plugin.merge(WfsGetFeatureBbox.PARAM_DEFS, {})

    def __init__(self):
        WfsGetFeatureBbox.__init__(self)
        self.wfs = None
        self.feature_types = None

    # Overridden: expand param-ranges from WFS metadata
    # from single-layer GetFeature parent Probe and set layers
    # fixed to *
    def expand_params(self, resource):
        WfsGetFeatureBbox.expand_params(self, resource)
        val = 'all %d feature types' % self.layer_count

        self.PARAM_DEFS['type_name']['range'] = [val]
        self.PARAM_DEFS['type_name']['value'] = val
        self.PARAM_DEFS['type_name']['default'] = val

    def before_request(self):
        """ Before request to service, overridden from base class"""

        # Get capabilities doc to get all layers
        try:
            self.wfs = self.get_metadata_cached(self._resource,
                                                version='1.1.0')
            self.feature_types = self.wfs.contents.keys()
        except Exception as err:
            self.result.set(False, str(err))

    def perform_request(self):
        """ Perform actual request to service, overridden from base class"""

        if not self.feature_types:
            self.result.set(False, 'Found no WFS Feature Types')
            return

        self.result.start()

        results_failed_total = []
        for feature_type in self.feature_types:
            self._parameters['type_name'] = feature_type

            # Let the templated parent perform
            Probe.perform_request(self)
            self.run_checks()

            # Only keep failed feature_type results
            # otherwise with 100s of FTs the report grows out of hand...
            results_failed = self.result.results_failed
            if len(results_failed) > 0:
                # We have a failed feature_type: add to result message
                for result in results_failed:
                    result.message = 'feature_type %s: %s' % \
                                     (feature_type, result.message)

                results_failed_total += results_failed
                self.result.results_failed = []

            self.result.results = []

        self.result.results_failed = results_failed_total
