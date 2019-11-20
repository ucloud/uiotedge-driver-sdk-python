import json
import random
import string
import threading
import queue
import base64
import os
from pynats import NATSClient
from cacheout import Cache
from .edge import send_message, device_login, device_logout, del_connect_map, add_connect_map
from .thing_exception import UIoTEdgeDriverException, UIoTEdgeTimeoutException, UIoTEdgeDeviceOfflineException

_deviceInfos = []
_driverInfo = None


class ThingAccessClient(object):
    def __init__(self, product_sn: str = '', device_sn: str = '', on_msg_callback=None):
        self.device_sn = device_sn
        self.product_sn = product_sn
        self.product_secret = ''
        self.callback = on_msg_callback
        self._identity = self.product_sn+'.'+self.device_sn
        self.online = False

    def set_product_sn(self, product_sn):
        self.product_sn = product_sn

    def set_device_sn(self, device_sn):
        self.device_sn = device_sn

    def set_product_secret(self, product_secret):
        self.product_secret = product_secret

    def logout(self):
        if self.online:
            device_logout(product_sn=self.product_sn,
                          device_sn=self.device_sn,
                          is_cached=True, duration=30)

            self.online = False
            del_connect_map(self._identity)

    def login(self):
        add_connect_map(self._identity, self)
        self.online = True

        device_login(product_sn=self.product_sn,
                     device_sn=self.device_sn,
                     is_cached=True, duration=30)

    def publish(self, topic: str, payload: b'', is_cached=False, duration=0):
        if self.online:
            send_message(topic, payload, is_cached=is_cached,
                         duration=duration)
        else:
            raise UIoTEdgeDeviceOfflineException


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


# get Config
_config_path = os.environ.get(
    'UIOT_EDGE_LINK_DRIVER_PATH') or '/edge/config/config.json'
with open(_config_path, 'r') as load_f:
    load_dict = json.load(load_f)
    print(load_dict)
    _deviceInfos = load_dict['deviceList']
    _driverInfo = load_dict['driverInfo']
