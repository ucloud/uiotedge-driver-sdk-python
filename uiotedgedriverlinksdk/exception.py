class BaseUIoTEdgeException(Exception):
    def gatherAttrs(self):
        return ",".join("{}={}"
                        .format(k, getattr(self, k))
                        for k in self.__dict__.keys())

    def __str__(self):
        return "[{}:{}]".format(self.__class__.__name__, self.gatherAttrs())


class UIoTEdgeDriverException(BaseUIoTEdgeException):
    def __init__(self, code, msg):
        self.code = code
        self.msg = msg


class UIoTEdgeTimeoutException(BaseUIoTEdgeException):
    def __str__(self):
        return "[{}:{}]".format(self.__class__.__name__, 'wait response timeout, please check network or edeg connect state.')


class UIoTEdgeDeviceOfflineException(BaseUIoTEdgeException):
    def __str__(self):
        return "[{}:{}]".format(self.__class__.__name__, 'device offline, please login first.')


class UIoTEdgeOfflineException(BaseUIoTEdgeException):
    def __str__(self):
        return "[{}:{}]".format(self.__class__.__name__, 'edge offline, please connect first.')
