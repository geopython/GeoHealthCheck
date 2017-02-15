from GeoHealthCheck.proberunner import ProbeRunner

class HttpPing(ProbeRunner):
    """Ping"""

    NAME = 'HTTP Ping'
    DESCRIPTION = 'HTTP Resource responds without client (400) or server (500) error'

    REQUEST_METHOD = 'GET'
    REQUEST_TEMPLATE = None
    REQUEST_PARAMETERS = None

    RESPONSE_CHECKS = [
        {
            'name': 'http_error_status',
            'description': 'response not in error range: i.e. 400 or 500-range',
            'function': 'GeoHealthCheck.checks.http_status_no_error'
        }
    ]

