import asyncio
import json
from pynats import NATSClient

nats_url = 'tcp://106.75.237.117:4222'
thingclients = {}
natsclient = NATSClient(url=nats_url, socket_timeout=5)
natsclient.connect()


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
        thingclients[self.deviceSN] = self
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
        natsclient.publish(subject='nats.router', payload=bty.encode('utf-8'))


class Config(object):
    def __init__(self, config=None):
        self.config = config

    def getDriverInfo(self):
        return _driverInfo

    def getThingInfos(self):
        return _thingInfos


def getConfig():
    if _driverInfo is None:
        config = {"deviceList": _thingInfos}
    else:
        config = {
            "config": _driverInfo,
            "deviceList": _thingInfos}
    return json.dumps(config)


def on_message(message):
    # TODO driver message router ot subdevice
    device_sn = message['deviceSN']
    thingclients[device_sn].callback(message)


_thingInfos = []
_driverInfo = None
# TODO get Config
with open("/edge/config/config.json", 'r') as load_f:
    load_dict = json.load(load_f)
    print(load_dict)

# subscribe message from router
dirver_id = '000001'
natsclient.subscribe(subject='edge.driver.'+dirver_id, callback=on_message)
