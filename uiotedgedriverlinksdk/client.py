import json
from uiotedgedriverlinksdk.edge import send_message, device_login_async, device_login_sync, device_logout_async, device_logout_sync, del_connect_map, add_connect_map
from uiotedgedriverlinksdk.exception import EdgeDriverLinkDeviceOfflineException, EdgeDriverLinkDeviceConfigException
from uiotedgedriverlinksdk.nats import _driverInfo, _deviceInfos


class ThingAccessClient(object):
    def __init__(self, product_sn: str = '', device_sn: str = '', on_msg_callback=None):
        self.device_sn = device_sn
        self.product_sn = product_sn
        self.product_secret = ''
        self.callback = on_msg_callback
        self.online = False
        if self.product_sn != '' and self.device_sn != '':
            self._identity = self.product_sn+'.'+self.device_sn

    def set_product_sn(self, product_sn: str):
        self.product_sn = product_sn
        if self.product_sn != '' and self.device_sn != '':
            self._identity = self.product_sn+'.'+self.device_sn

    def set_device_sn(self, device_sn: str):
        self.device_sn = device_sn
        if self.product_sn != '' and self.device_sn != '':
            self._identity = self.product_sn+'.'+self.device_sn

    def set_product_secret(self, product_secret: str):
        self.product_secret = product_secret

    def set_msg_callback(self, msg_callback):
        self.callback = msg_callback

    def get_device_info(self):
        return {
            "productSN": self.product_sn,
            "deviceSN": self.device_sn
        }

    def logout(self, sync=False, timeout=5):
        if self.online:
            if sync:
                device_logout_sync(product_sn=self.product_sn,
                                   device_sn=self.device_sn,
                                   timeout=timeout)
            else:
                device_logout_async(product_sn=self.product_sn,
                                    device_sn=self.device_sn)
            self.online = False
            del_connect_map(self._identity)

    def login(self, sync=False, timeout=5):
        if self._identity == '':
            raise EdgeDriverLinkDeviceConfigException

        add_connect_map(self._identity, self)

        if sync:
            device_login_sync(product_sn=self.product_sn,
                              device_sn=self.device_sn, timeout=timeout)
        else:
            device_login_async(product_sn=self.product_sn,
                               device_sn=self.device_sn)
        self.online = True

    def publish(self, topic: str, payload: b''):
        if self.online:
            send_message(topic, payload, is_cached=False,
                         duration=0)
        else:
            raise EdgeDriverLinkDeviceOfflineException


class Config(object):
    def __init__(self, config=None):
        self.config = config

    def getDriverInfo(self):
        return _driverInfo

    def getDeviceInfos(self):
        return _deviceInfos


def getConfig():
    if _driverInfo is None:
        config = {"deviceList": _deviceInfos}
    else:
        config = {
            "config": _driverInfo,
            "deviceList": _deviceInfos}
    return json.dumps(config)
