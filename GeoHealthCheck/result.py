import datetime


class Result(object):
    """
     Base class for results for Resource or Probe.
     TODO: finalize Result processing/storage.
    """

    def __init__(self, success=True, message='OK'):
        self.success = success
        self.message = message
        self.start_time = None
        self.end_time = None
        self.response_time_secs = -1
        self.response_time_str = -1
        self.results = []
        self.results_failed = []

    def add_result(self, result):
        self.results.append(result)
        if not result.success:
            self.success = False
            self.message = result.message
            self.results_failed.append(result)

    def start(self):
        self.start_time = datetime.datetime.utcnow()

    def stop(self):
        self.end_time = datetime.datetime.utcnow()

        delta = self.end_time - self.start_time
        self.response_time_secs = delta.seconds
        self.response_time_str = '%s.%s' % (delta.seconds, delta.microseconds)

    def __str__(self):
        return "success=%s msg=%s response_time=%s" % (self.success, self.message, self.response_time_str)


class ResourceResult(Result):
    """
     Holds result data from a single Resource: one Resource, N Probe(Results).
     Provides Run data.
    """

    def __init__(self, resource):
        Result.__init__(self)
        self.resource = resource

    def get_run_data(self):
        return [self.resource.title, self.success, self.response_time_str, self.message, self.start_time]


class ProbeResult(Result):
    """
     Holds result data from a single Probe: one Probe, N Checks.

    """

    def __init__(self, probe):
        Result.__init__(self)
        self.probe = probe


class CheckResult(Result):
    """
     Holds result data from a single Check.
    """

    def __init__(self, check, parameters, success, message):
        Result.__init__(self, success, message)
        self.check = check
        self.parameters = parameters
