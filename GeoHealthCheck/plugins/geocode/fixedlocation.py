from GeoHealthCheck.geocoder import Geocoder


class FixedLocation(Geocoder):
    """
    Spoof getting  a geolocation for a server by provinding a fixed lat, lon
    result. The lat, lon can be specified in the initialisation parameters.
    When omitted: default to 0, 0.
    """

    NAME = 'Fixed geolocation'

    DESCRIPTION = 'Geolocater service returning a fixed position (so ' \
                  'actually no real geolocation).'

    LATITUDE = 0
    """
    Parameter with the default latitude position. This is overruled when the
    latitude option is provided in the init step.
    """

    LONGITUDE = 0
    """
    Parameter with the default longitude position. This is overruled when the
    longitude option is provided in the init step.
    """

    def __init__(self):
        super().__init__()
        self._lat = self.LATITUDE
        self._lon = self.LONGITUDE

    def init(self, geocode_vars={}):
        """
        Initialise the geocoder service with an optional dictionary.

        When the dictionary contains the element `lat` and/or `lon`, then these
        values are used to position the server.
        """
        super().init(geocode_vars)
        self._lat = geocode_vars.get('lat', self.LATITUDE)
        self._lon = geocode_vars.get('lon', self.LONGITUDE)

    def locate(self, _=None):
        """
        Perform a geocoding to locate a server. In this case it will render a
        fixed position, so provinding the adress of the server is optional.
        """
        return (self._lat, self._lon)
