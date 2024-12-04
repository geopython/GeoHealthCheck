import oracledb

from GeoHealthCheck.probe import Probe
from GeoHealthCheck.result import Result, push_result

class OracleDrilldown(Probe):
    """
    Probe for Oracle Database endpoint "drilldown"
    Possible tests are 'basic' for testing the connection to the database (is it up-and-running).
    Or 'full' for testing both the connection and if Oracle Spatial functionality is available.
    """

    NAME = 'Oracle Drilldown'

    DESCRIPTION = 'Checks an Oracle database connection, use a string like "host=<hostname>;port=<portnumber>;service=<servicename>" to define the database connection'

    RESOURCE_TYPE = 'ORACLE'

    REQUEST_METHOD = 'DB'

    PARAM_DEFS = {
        'drilldown_level': {
            'type': 'string',
            'description': 'Which drilldown should be used.\
                            basic: test connection, \
                            full: test connection and check Oracle Spatial',
            'default': 'basic',
            'required': True,
            'range': ['basic', 'full']
        }
    }
    """Param defs"""

    def __init__(self):
        Probe.__init__(self)

    def perform_ora_get_request(self, connectstring,sql):
        response = None
        try:
            with oracledb.connect(connectstring) as con:
                cursor = con.cursor()
                result, = cursor.execute(sql)
                response = repr(result)
        except Exception as err:
            raise Exception("Error: " + err)

        return response

    def perform_request(self):
        """
        Perform the drilldown.
        """

        d = {}
        for c in self._resource.url.split(";"):
            key = c.split("=")[0]
            value = c.split("=")[1]
            d[key.lower()] = value

        # Check connection data
        host = None
        servicename = None
        portnumber = "1521"
        if "host" in self._resource.url.lower():
            host = d["host"]
        if "service" in self._resource.url.lower():
            servicename = d["service"]
        if "port" in self._resource.url.lower():
            portnumber = d["port"]

        if host is None or servicename is None:
            raise Exception("No Database host or service in url")

        # Assemble request templates with root FS URL
        if self._resource.auth['type'] == 'Basic':
            usr = self._resource.auth['data']['username']
            pwd = self._resource.auth['data']['password']
            dsn = '{usr}/{pwd}@{host}:{portnumber}/{service}'.format(usr=usr,pwd=pwd,host=host,portnumber=portnumber,service=servicename)
        else:
            raise Exception("No username and password as Basic authentication saved")

        req_tpl = {
            'connectstring':dsn,
            'basic_check':'select to_char(current_date) from dual',
            'full_check':"select SDO_UTIL.FROM_WKTGEOMETRY('POINT(155000 463000)') from dual"
        }

        # 1. Test top Service endpoint existence
        result = Result(True, f"Test Oracle connection")
        result.start()
        try:
            ora_result = self.perform_ora_get_request(req_tpl['connectstring'],req_tpl['basic_check'])
            if ora_result is None:
                result.set(False,"Error: The query '{}' was not executed".format(req_tpl['basic_check']))
        except Exception as err:
            result.set(False, str(err))

        result.stop()
        self.result.add_result(result)

        if self._parameters['drilldown_level'] == 'basic':
            return

        # ASSERTION: will do full drilldown from here

        # 2. Test Oracle Spatial
        result = Result(True, 'Test Oracle Spatial')
        result.start()
        try:
            ora_result = self.perform_ora_get_request(req_tpl['connectstring'],req_tpl['full_check'])
            if ora_result is None:
                result.set(False, "Error: The query '{}' was not executed".format(req_tpl['full_check']))
        except Exception as err:
            result.set(False, str(err))

        result.stop()

        # Add to overall Probe result
        self.result.add_result(result)
