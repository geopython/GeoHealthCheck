import psycopg2

from GeoHealthCheck.probe import Probe
from GeoHealthCheck.result import Result, push_result

class PostgresDrilldown(Probe):
    """
    Probe for Postgres Database endpoint "drilldown"
    Possible tests are 'basic' for testing the connection to the database (is it up-and-running).
    Or 'full' for testing both the connection and if ESRI's ST_GEOMETRY library is available.
    """

    NAME = 'Postgres Drilldown'

    DESCRIPTION = 'Checks a Postgres database connection, use a string like "host=<hostname>;port=<portnumber>;database=<databasename>" to define the database connection'

    RESOURCE_TYPE = 'POSTGRES'

    REQUEST_METHOD = 'DB'

    PARAM_DEFS = {
        'drilldown_level': {
            'type': 'string',
            'description': 'Which drilldown should be used.\
                            basic: test connection, \
                            full: test connection and check ESRI ST_GEOMETRY',
            'default': 'basic',
            'required': True,
            'range': ['basic', 'full']
        }
    }
    """Param defs"""

    def __init__(self):
        Probe.__init__(self)

    def perform_pg_get_request(self, host,databasename,portnumber,usr,pwd,sql):
        response = None
        try:
            con = psycopg2.connect(dbname=databasename, host=host, user=usr, password=pwd, port=portnumber)
            cursor = con.cursor()
            result = cursor.execute(sql)
            response = cursor.rowcount
            con.close()
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
        databasename = None
        portnumber = "5432"
        if "host" in self._resource.url.lower():
            host = d["host"]
        if "database" in self._resource.url.lower():
            databasename = d["database"]
        if "port" in self._resource.url.lower():
            portnumber = d["port"]

        if host is None or databasename is None:
            raise Exception("No Database host or databasename in url")

        # Assemble request templates with root FS URL
        try:
            if self._resource.auth['type'] == 'Basic':
                usr = self._resource.auth['data']['username']
                pwd = self._resource.auth['data']['password']
        except Exception:
            raise Exception("No username and password as Basic authentication saved")

        req_tpl = {
            'basic_check':'SELECT CURRENT_DATE',
            'full_check':"select sde.st_x(sde.st_point (155000, 463000, 28992)) as X, sde.st_y(sde.st_point (155000, 463000, 28992)) as Y"
        }

        # 1. Test top Service endpoint existence
        result = Result(True, f"Test Postgres connection")
        result.start()
        try:
            pg_result = self.perform_pg_get_request(host,databasename,portnumber,usr,pwd,req_tpl['basic_check'])
            # pg_result = self.perform_pg_get_request(req_tpl['connectstring'],req_tpl['basic_check'])
            if pg_result is None:
                result.set(False,"Error: The query '{}' was not executed".format(req_tpl['basic_check']))
        except Exception as err:
            result.set(False, str(err))

        result.stop()
        self.result.add_result(result)

        if self._parameters['drilldown_level'] == 'basic':
            return

        # ASSERTION: will do full drilldown from here

        # 2. Test ESRI ST_GEOMETRY
        result = Result(True, 'Test Postgres ESRI ST_GEOMETRY')
        result.start()
        try:
            pg_result = self.perform_pg_get_request(host,databasename,portnumber,usr,pwd,req_tpl['full_check'])
            if pg_result is None:
                result.set(False, "Error: The query '{}' was not executed".format(req_tpl['full_check']))
        except Exception as err:
            result.set(False, str(err))

        result.stop()

        # Add to overall Probe result
        self.result.add_result(result)
