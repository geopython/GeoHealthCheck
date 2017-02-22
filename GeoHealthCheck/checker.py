from plugin import Plugin

class Checker(Plugin):
    """
     Base class for specific implementations to perform a check
     on Result from a ProbeRunner.

    """

    TAGS = []

    # Check parameter definitions, defaults, subclassses override
    PARAMETERS = None

    # Lifecycle
    def init(self, probe_runner, parameters):
        """
        Initialize Checker with parent ProbeRunner and parameters dict.
        :return:
        """
        self.prober = probe_runner
        self.parms = parameters

    # Lifecycle
    def perform(self):
        """
        Perform the Checker's specific check.
        :return:
        """
        return True, 'OK'
