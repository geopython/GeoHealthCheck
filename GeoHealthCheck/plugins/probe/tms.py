from GeoHealthCheck.probe import Probe
from GeoHealthCheck.plugindecor import Parameter, UseCheck


class TmsCaps(Probe):
    """Probe for TMS main endpoint url"""

    NAME = 'TMS Capabilities'
    RESOURCE_TYPE = 'OSGeo:TMS'

    REQUEST_METHOD = 'GET'

    def __init__(self):
        Probe.__init__(self)

    #
    # Checks for Probe as Decorators
    #

    @UseCheck(check_class='GeoHealthCheck.plugins.check.checks.XmlParse')
    def xml_parsable(self):
        """
        response is parsable.
        """
        pass

    #
    # Checks for Probe as Decorators
    #
    @UseCheck(check_class='GeoHealthCheck.plugins.check.checks.ContainsStrings',
        parameters={'strings': ['TileMap>']})
    def has_tilemap_element(self):
        """
        Should have TileMap element in capabilities response doc.
        """
        pass


class TmsGetTile(Probe):
    """Fetch TMS tile and check result"""

    NAME = 'TMS GetTile'
    RESOURCE_TYPE = 'OSGeo:TMS'

    REQUEST_METHOD = 'GET'

    # e.g. http://geodata.nationaalgeoregister.nl/tms/1.0.0/brtachtergrondkaart/1/0/0.png
    REQUEST_TEMPLATE = '/{layer}/{zoom}/{x}/{y}.{extension}'

    def __init__(self):
        Probe.__init__(self)

    @Parameter(ptype=str, default=None, required=True)
    def layer(self):
        """
        The TMS Layer service within resource endpoint.
        """
        pass

    @Parameter(ptype=str, default='0', required=True)
    def zoom(self):
        """
        The tile pyramid zoomlevel.
        """
        pass

    @Parameter(ptype=str, default='0', required=True)
    def x(self):
        """
        The tile x offset.
        """
        pass

    @Parameter(ptype=str, default='0', required=True)
    def y(self):
        """
        The tile y offset.
        """
        pass

    @Parameter(ptype=str, default='png', required=True, value_range=['png', 'png8', 'png24', 'jpg', 'jpeg', 'tif', 'tiff'])
    def extension(self):
        """
        The tile image extension.
        """
        pass

    @UseCheck(check_class='GeoHealthCheck.plugins.check.checks.HttpHasImageContentType')
    def has_image_content_type(self):
        pass
