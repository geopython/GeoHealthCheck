from plugin import Plugin
from result import CheckResult


class Check(Plugin):
    """
     Base class for specific Plugin implementations to perform
     a check  on results from a Probe.
    """

    def __init__(self):
        Plugin.__init__(self)
        self.probe = None

    # Lifecycle
    def init(self, probe, check_vars):
        """
        Initialize Checker with parent Probe and parameters dict.
        :return:
        """

        self.probe = probe
        self.check_vars = check_vars
        self._parameters = check_vars.parameters
        self._result = CheckResult(self, check_vars)
        self._result.start()

    # Lifecycle
    def set_result(self, success, message):
        self._result.set(success, message)
        self._result.stop()

    # Lifecycle
    def perform(self):
        """
        Perform this Check's specific check. TODO: return Result object.
        :return:
        """
        pass
