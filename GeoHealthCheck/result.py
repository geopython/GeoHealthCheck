
class Result(object):
    """
     Holds result data from a Probe.

    """

    def __init__(self):
        self.success = True
        self.message = 'OK'
        self.response_time = -1
        self.start_time = -1
        self.checks = []

    def __str__(self):
        return "success=%s msg=%s response_time=%s" % (self.success, self.message, self.response_time)
