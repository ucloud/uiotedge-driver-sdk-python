import asyncio
import json
import random
import string
from pynats import NATSClient

_deviceInfos = []
_driverInfo = None
_nats_url = 'tcp://106.75.237.117:4222'
_thingclients = {}
_natsclient = NATSClient(url=_nats_url, socket_timeout=5)
_natsclient.connect()


class ThingClient(object):
    def __init__(self, deviceSN, productKey, callback):
        self.deviceSN = deviceSN
        self.productKey = productKey
        self.callback = callback

    def online(self):
        # TODO send online message
        pass

    def offline(self):
        # TODO send offline
        pass

    def registerAndOnline(self):
        # TODO do register and online
        _thingclients[self.deviceSN] = self
        pass

    def unregister(self):
        # TODO do unregister
        pass

    def publish(self, topic, payload):
        # publish message to message router
        data = {
            'deviceSN': self.deviceSN,
            'topic': topic,
            'payload': payload
        }
        bty = json.dumps(data)
        _natsclient.publish(subject='nats.router', payload=bty.encode('utf-8'))


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


def on_message(message):
    # TODO driver message router ot subdevice
    device_sn = message['deviceSN']
    _thingclients[device_sn].callback(message)


# get Config
with open("/edge/config/config.json", 'r') as load_f:
    load_dict = json.load(load_f)
    print(load_dict)
    _deviceInfos = load_dict['deviceList']
    _driverInfo = load_dict['driverInfo']

# subscribe message from router
_dirver_id = ''.join(random.sample(string.ascii_letters + string.digits, 16))
print("dirver_id: ", _dirver_id)

_natsclient.subscribe(subject='edge.local.'+_dirver_id, callback=on_message)
