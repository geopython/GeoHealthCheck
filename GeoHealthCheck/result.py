from datetime import datetime, timezone


class Result(object):
    """
     Base class for results for Resource or Probe.
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
            self.results_failed.append(result)
            # First failed result is usually main failure reason
            self.message = self.results_failed[0].message

    def get_report(self):
        return {
            'success': self.success,
            'message': self.message,
            'response_time': self.response_time_str
        }

    def set(self, success, message):
        self.success = success
        self.message = message

    def start(self):
        self.start_time = datetime.now(timezone.utc)

    def stop(self):
        self.end_time = datetime.now(timezone.utc)

        delta = self.end_time - self.start_time
        self.response_time_secs = delta.seconds
        self.response_time_str = '%s.%s' % (delta.seconds, delta.microseconds)

    def __str__(self):
        if self.message:
            self.message = self.message
        return "success=%s msg=%s response_time=%s" % \
               (self.success, self.message, self.response_time_str)


class ResourceResult(Result):
    """
     Holds result data from a single Resource: one Resource, N Probe(Results).
     Provides Run data.
    """
    REPORT_VERSION = '1'

    def __init__(self, resource):
        Result.__init__(self)
        self.resource = resource

    def get_report(self):
        report = {
            'report_version': ResourceResult.REPORT_VERSION,
            'resource_id': self.resource.identifier,
            'resource_type': self.resource.resource_type,
            'resource_title': self.resource.title,
            'url': self.resource.url,
            'success': self.success,
            'message': self.message,
            'start_time': self.start_time.strftime(
                '%Y-%m-%dT%H:%M:%SZ'),
            'end_time': self.end_time.strftime(
                '%Y-%m-%dT%H:%M:%SZ'),
            'response_time': self.response_time_str,
            'probes': []
        }

        for probe_result in self.results:
            probe_report = probe_result.get_report()
            report['probes'].append(probe_report)

        return report


class ProbeResult(Result):
    """
     Holds result data from a single Probe: one Probe, N Checks.

    """

    def __init__(self, probe, probe_vars):
        Result.__init__(self)
        self.probe = probe
        self.probe_vars = probe_vars

    def get_report(self):
        report = {
            'probe_id': self.probe_vars.identifier,
            'class': self.probe_vars.probe_class,
            'name': getattr(self.probe, 'NAME', None),
            'success': self.success,
            'message': self.message,
            'response_time': self.response_time_str,
            'checks': []
        }

        for check_result in self.results:
            check_report = check_result.get_report()
            report['checks'].append(check_report)

        return report


class CheckResult(Result):
    """
     Holds result data from a single Check.
    """

    def __init__(self, check, check_vars, success=True, message="OK"):
        Result.__init__(self, success, message)
        self.check = check
        self.check_vars = check_vars
        self.parameters = check_vars.parameters

    def get_report(self):
        report = {
            'check_id': self.check_vars.identifier,
            'class': self.check_vars.check_class,
            'name': getattr(self.check, 'NAME', None),
            'success': self.success,
            'message': self.message,
            'response_time': self.response_time_str
        }

        return report


# Util to quickly add Results and open new one.
def push_result(obj, result, val, msg, new_result_name):
    result.set(val, msg)
    result.stop()
    obj.result.add_result(result)
    result = Result(True, new_result_name)
    result.start()
    return result
