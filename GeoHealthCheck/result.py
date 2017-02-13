import datetime

class Result(object):
    """
     Holds result data from a Probe.

    """

    def __init__(self):
        self.success = True
        self.message = 'OK'
        self.start_time = None
        self.end_time = None
        self.response_time_secs = -1
        self.response_time_str = -1
        self.checks = []

    def start(self):
        self.start_time = datetime.datetime.utcnow()

    def stop(self):
        self.end_time = datetime.datetime.utcnow()

        delta = self.end_time - self.start_time
        self.response_time_secs = delta.seconds
        self.response_time_str = '%s.%s' % (delta.seconds, delta.microseconds)

    def __str__(self):
        return "success=%s msg=%s response_time=%s" % (self.success, self.message, self.response_time_str)
