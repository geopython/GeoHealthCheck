from GeoHealthCheck.probe import Probe
from owslib.wcs import WebCoverageService


class WcsGetCoverage(Probe):
    """
    Get WCS coverage image using the OGC WCS GetCoverage v2.0.1 Operation.
    """

    NAME = 'WCS GetCoverage v2.0.1'
    DESCRIPTION = """
    Do WCS GetCoverage v2.0.1 request with user-specified parameters
    for single Layer.
    """
    RESOURCE_TYPE = 'OGC:WCS'

    REQUEST_METHOD = 'GET'
    REQUEST_TEMPLATE = '?SERVICE=WCS&VERSION=2.0.1' + \
                       '&REQUEST=GetCoverage&COVERAGEID={layer}' + \
                       '&FORMAT={format}' + \
                       '&SUBSET=x({subset[0]},{subset[2]})' + \
                       '&SUBSET=y({subset[1]},{subset[3]})' + \
                       '&SUBSETTINGCRS={subsetting_crs}' + \
                       '&WIDTH={width}&HEIGHT={height}'

    PARAM_DEFS = {
        'layer': {
            'type': 'stringlist',
            'description': 'The WCS Layer ID, select one',
            'default': [],
            'required': True,
            'range': None
        },
        'format': {
            'type': 'string',
            'description': 'Image outputformat',
            'default': [],
            'required': True,
            'range': None
        },
        'subset': {
            'type': 'bbox',
            'description': 'The WCS subset of x and y axis',
            'default': ['-180', '-90', '180', '90'],
            'required': True,
            'range': None
        },
        'subsetting_crs': {
            'type': 'string',
            'description': 'The crs of SUBSET and also OUTPUTCRS',
            'default': '',
            'required': True,
            'range': None
        },
        'width': {
            'type': 'string',
            'description': 'The image width',
            'default': '10',
            'required': True
        },
        'height': {
            'type': 'string',
            'description': 'The image height',
            'default': '10',
            'required': True
        }
    }
    """Param defs"""

    CHECKS_AVAIL = {
        'GeoHealthCheck.plugins.check.checks.HttpStatusNoError': {
            'default': True
        },
        'GeoHealthCheck.plugins.check.checks.NotContainsOwsException': {
            'default': True
        },
        'GeoHealthCheck.plugins.check.checks.HttpHasImageContentType': {
            'default': True
        }
    }
    """
    Checks for WCS GetCoverage Response available.
    Optionally override Check PARAM_DEFS using set_params
    e.g. with specific `value` or even `name`.
    """
    def __init__(self):
        Probe.__init__(self)
        self.layer_count = 0

    def get_metadata(self, resource, version='2.0.1'):
        """
        Get metadata, specific per Resource type.
        :param resource:
        :param version:
        :return: Metadata object
        """
        return WebCoverageService(resource.url, version=version)

    # Overridden: expand param-ranges from WCS metadata
    def expand_params(self, resource):

        # Use WCS Capabilities doc to get metadata for
        # PARAM_DEFS ranges/defaults
        try:
            wcs = self.get_metadata_cached(resource, version='2.0.1')
            layers = wcs.contents
            self.layer_count = len(layers)

            # Layers to select
            self.PARAM_DEFS['layer']['range'] = list(layers.keys())

            # Take random layer to determine generic attrs
            for layer_name in layers:
                layer_entry = layers[layer_name]
                break

            # Image Format
            self.PARAM_DEFS['format']['range'] = layer_entry.supportedFormats

            # SRS
            bbox = layer_entry.boundingboxes
            subsetting_crs = bbox[0]['nativeSrs']
            self.PARAM_DEFS['subsetting_crs']['default'] = subsetting_crs

            # BBOX
            self.log('bbox: %s' % str(bbox[0]['bbox']))
            self.PARAM_DEFS['subset']['default'] = bbox[0]['bbox']

        except Exception as err:
            raise err
