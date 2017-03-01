from plugin import Plugin


class Check(Plugin):
    """
     Base class for specific Plugin implementations to perform
     a check  on results from a Probe.
    """

    PARAM_DEFS = {}
    """
    Check parameter definitions, defaults, subclassses override
    """

    def __init__(self):
        Plugin.__init__(self)
        self.probe = None

    # Lifecycle
    def init(self, probe, parameters):
        """
        Initialize Checker with parent Probe and parameters dict.
        :return:
        """

        self.probe = probe
        self._parameters = parameters

    # Lifecycle
    def perform(self):
        """
        Perform this Check's specific check. TODO: return Result object.
        :return:
        """
        return True, 'OK'
