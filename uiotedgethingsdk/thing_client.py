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


def _generate_request_id():
    return ''.join(random.sample(string.ascii_letters + string.digits, 16))


class ThingClient(object):
    def __init__(self, product_sn, device_sn,  on_msg_callback=None, on_topo_add_callback=None, on_topo_delete_callback=None, on_topo_set_change_callback=None):
        self.device_sn = device_sn
        self.product_sn = product_sn
        self.callback = on_msg_callback
        self.on_topo_add_callback = on_topo_add_callback
        self.on_topo_delete_callback = on_topo_delete_callback
        self.on_topo_set_change_callback = on_topo_set_change_callback

    def login(self):
        print("on login")
        self._login()

    def logout(self):
        print("on logout")
        self._logout()

    def _logout(self):
        _thingclients.pop(self.device_sn)
        offline_message = {
            'RequestID': _generate_request_id(),
            'Params': {
                'ProductSN': self.product_sn,
                'DeviceSN': self.device_sn
            }
        }
        topic = '/$system/%s/%s/subdev/logout' % (
            self.product_sn, self.device_sn)
        self.publish(topic=topic, payload=offline_message)

    def _login(self):
        _thingclients[self.device_sn] = self
        online_message = {
            'RequestID': _generate_request_id(),
            'Params': {
                'ProductSN': self.product_sn,
                'DeviceSN': self.device_sn
            }
        }
        topic = '/$system/%s/%s/subdev/login' % (
            self.product_sn, self.device_sn)
        self.publish(topic=topic, payload=online_message)

    def get_topo(self):
        get_topo = {
            'RequestID': _generate_request_id(),
            "Params": []
        }
        topic = '/$system/%s/%s/subdev/topo/get' % (
            self.product_sn, self.device_sn)
        self.publish(topic=topic, payload=get_topo)

    def publish(self, topic, payload):
        # publish message to message router
        data = {
            'src': 'local',
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


def _on_message(message):
    # driver message router ot subdevice
    try:
        device_sn = message['deviceSN']
        topic = message['topic']
        sub_dev = None
        if isinstance(device_sn, str):
            sub_dev = _thingclients[device_sn]
        else:
            print('unknown message deviceSN')
            return

        if isinstance(topic, str):
            if topic.endswith('/subdev/topo/get_reply') and topic.startswith('/$system/'):
                if sub_dev.on_topo_add_callback:
                    sub_dev.on_topo_add_callback(message)
            elif topic.endswith('/subdev/topo/delete_reply') and topic.startswith('/$system/'):
                if sub_dev.on_topo_delete_callback:
                    sub_dev.on_topo_delete_callback(message)
            elif topic.endswith('/subdev/topo/add_reply') and topic.startswith('/$system/'):
                if sub_dev.on_topo_add_callback:
                    sub_dev.on_topo_add_callback(message)
            elif (topic.endswith("/subdev/topo/notify/add") or topic.endswith("/subdev/topo/notify/delete")) and topic.startswith("/$system/"):
                if sub_dev.on_topo_set_change_callback:
                    sub_dev.on_topo_set_change_callback(
                        message)
            else:
                if sub_dev.on_msg_callback:
                    sub_dev.on_msg_callback(message)
        else:
            print('unknown message topic')
            return

    except Exception as e:
        print(e)


# get Config
with open("/edge/config/config.json", 'r') as load_f:
    load_dict = json.load(load_f)
    print(load_dict)
    _deviceInfos = load_dict['deviceList']
    _driverInfo = load_dict['driverInfo']

# subscribe message from router
_dirver_id = ''.join(random.sample(string.ascii_letters + string.digits, 16))
print("dirver_id: ", _dirver_id)

_natsclient.subscribe(subject='edge.local.'+_dirver_id, callback=_on_message)
