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
_thingclients = {}
_cache = Cache(maxsize=1024, ttl=300)


def _generate_request_id():
    return ''.join(random.sample(string.ascii_letters + string.digits, 16))


class ThingAccessClient(object):
    def __init__(self, product_sn, device_sn, on_msg_callback=None):
        self.device_sn = device_sn
        self.product_sn = product_sn
        self.callback = on_msg_callback
        self._identity = self.product_sn+'.'+self.device_sn
        self.online = False

    def logout(self, is_cached=False, duration=0):
        if self.online:
            device_logout(product_sn=self.product_sn,
                          device_sn=self.device_sn,
                          is_cached=is_cached, duration=duration)

            self.online = False
            del_connect_map(self._identity)

    def login(self, is_cached=False, duration=0):
        add_connect_map(self._identity, self)
        self.online = True

        device_login(product_sn=self.product_sn,
                     device_sn=self.device_sn,
                     is_cached=is_cached, duration=duration)

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
