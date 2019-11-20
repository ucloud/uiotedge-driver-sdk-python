class UIoTEdgeDriverException(Exception):
    def __init__(self, code, msg):
        self.code = code
        self.msg = msg


class UIoTEdgeTimeoutException(Exception):
    pass


class UIoTEdgeDeviceOfflineException(Exception):
    pass
