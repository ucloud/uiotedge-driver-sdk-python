class BaseEdgeException(Exception):
    def gatherAttrs(self):
        return ",".join("{}={}"
                        .format(k, getattr(self, k))
                        for k in self.__dict__.keys())

    def __str__(self):
        return "[{}:{}]".format(self.__class__.__name__, self.gatherAttrs())


class EdgeDriverLinkException(BaseEdgeException):
    def __init__(self, code, msg):
        self.code = code
        self.msg = msg


class EdgeDriverLinkTimeoutException(BaseEdgeException):
    def __str__(self):
        return "[{}:{}]".format(self.__class__.__name__, 'wait response timeout, please check network or edge connect state.')


class EdgeDriverLinkDeviceConfigException(BaseEdgeException):
    def __str__(self):
        return "[{}:{}]".format(self.__class__.__name__, 'device param error, please make sure product_sn and device_sn not null.')


class EdgeDriverLinkDeviceOfflineException(BaseEdgeException):
    def __str__(self):
        return "[{}:{}]".format(self.__class__.__name__, 'device offline, please login first.')


class EdgeDriverLinkOfflineException(BaseEdgeException):
    def __str__(self):
        return "[{}:{}]".format(self.__class__.__name__, 'edge offline, please connect first.')


class EdgeDriverLinkDeviceProductSecretException(BaseEdgeException):
    def __str__(self):
        return "[{}:{}]".format(self.__class__.__name__, 'product secret param error, please make sure product secret not null.')
