import json
import random
import string
import threading
from pynats import NATSClient
from cacheout import Cache

_deviceInfos = []
_driverInfo = None
_nats_url = 'tcp://106.75.237.117:4222'
_thingclients = {}
_cache = Cache(maxsize=1024, ttl=300)
_natsclient = NATSClient(url=_nats_url)
_natsclient.connect()


def _generate_request_id():
    return ''.join(random.sample(string.ascii_letters + string.digits, 16))


class _device_topo(object):
    def __init__(self, callback):
        self.callback = callback

    def run(self, message):
        self.callback(message)


_on_topo_change_callback = None


def set_on_topo_change_callback(callback):
    global _on_topo_change_callback
    _on_topo_change_callback = _device_topo(callback)


def get_topo():
    request_id = _generate_request_id()
    topic = '/$system/%s/%s/subdev/topo/get' % (
        "0001", "123456")

    get_topo = {
        'src': 'local',
        'topic': topic,
        'payload': {
            'RequestID': request_id,
            "Params": []
        }

    }
    bty = json.dumps(get_topo)
    _natsclient.publish(subject='edge.router.'+_dirver_id,
                        payload=bty.encode('utf-8'))
    # _cache.set(request_id, self._identity)


class ThingClient(object):
    def __init__(self, product_sn, device_sn, on_msg_callback=None, on_topo_add_callback=None, on_topo_delete_callback=None):
        self.device_sn = device_sn
        self.product_sn = product_sn
        self.callback = on_msg_callback
        self.on_topo_add_callback = on_topo_add_callback
        self.on_topo_delete_callback = on_topo_delete_callback
        self._identity = self.product_sn+'.'+self.device_sn

    def login(self):
        # print("on login")
        self._login()

    def logout(self):
        # print("on logout")
        self._logout()

    def _logout(self):
        _thingclients.pop(self._identity)
        request_id = _generate_request_id()
        offline_message = {
            'RequestID': request_id,
            'Params': [
                {
                    'ProductSN': self.product_sn,
                    'DeviceSN': self.device_sn
                }
            ]
        }
        topic = '/$system/%s/%s/subdev/logout' % (
            self.product_sn, self.device_sn)
        self.publish(topic=topic, payload=offline_message)

        # _cache.set(request_id, self._identity)  # add cache for callback

    def _login(self):
        _thingclients[self._identity] = self

        request_id = _generate_request_id()
        online_message = {
            'RequestID': request_id,
            'Params': [
                {
                    'ProductSN': self.product_sn,
                    'DeviceSN': self.device_sn
                }
            ]
        }
        topic = '/$system/%s/%s/subdev/login' % (
            self.product_sn, self.device_sn)
        self.publish(topic=topic, payload=online_message)

        # _cache.set(request_id, self._identity)  # add cache for callback

    def register(self, product_secret):
        request_id = _generate_request_id()
        register_data = {
            'RequestID': request_id,
            "Params": [
                {
                    'ProductSN': self.product_sn,
                    'DeviceSN': self.device_sn,
                    'ProductSecret': product_secret
                }
            ]
        }
        topic = '/$system/%s/%s/subdev/register' % (
            self.product_sn, self.device_sn)
        self.publish(topic=topic, payload=register_data)

    def add_topo(self, is_cached=False, duration=0):
        request_id = _generate_request_id()
        get_topo = {
            'RequestID': request_id,
            "Params": [
                {
                    'ProductSN': self.product_sn,
                    'DeviceSN': self.device_sn
                }
            ]
        }
        topic = '/$system/%s/%s/subdev/topo/add' % (
            self.product_sn, self.device_sn)
        self.publish(topic=topic, payload=get_topo,
                     is_cached=is_cached, duration=duration)
        _cache.set(request_id, self._identity)  # add cache for callback

    def delete_topo(self, is_cached=False, duration=0):
        request_id = _generate_request_id()
        get_topo = {
            'RequestID': request_id,
            "Params": [
                {
                    'ProductSN': self.product_sn,
                    'DeviceSN': self.device_sn
                }
            ]
        }
        topic = '/$system/%s/%s/subdev/topo/delete' % (
            self.product_sn, self.device_sn)
        self.publish(topic=topic, payload=get_topo,
                     is_cached=is_cached, duration=duration)
        _cache.set(request_id, self._identity)  # add cache for callback

    def publish(self, topic, payload, is_cached=False, duration=0):
        # publish message to message router
        data = {
            'src': 'local',
            'topic': topic,
            'isCatched': is_cached,
            'duration': duration,
            'payload': payload
        }
        bty = json.dumps(data)
        _natsclient.publish(subject='edge.router.'+_dirver_id,
                            payload=bty.encode('utf-8'))


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

    payload = str(message.payload, encoding="utf-8")
    # print(payload)
    js = json.loads(payload)
    try:
        topic = js['topic']
        msg = js['payload']
        if isinstance(topic, str):
            # on topo change callback
            if (topic.endswith("/subdev/topo/notify/add") or topic.endswith("/subdev/topo/notify/delete") or topic.endswith('/subdev/topo/get_reply')) and topic.startswith("/$system/"):

                if _on_topo_change_callback:
                    _on_topo_change_callback.run(msg)

            # on topo delete callback
            elif topic.endswith('/subdev/topo/delete_reply') and topic.startswith('/$system/'):

                request_id = msg['RequestID']
                if _cache.has(request_id):
                    identity = _cache.get(request_id)
                    sub_dev = _thingclients[identity]
                    if sub_dev.on_topo_delete_callback:
                        sub_dev.on_topo_delete_callback(msg)
            # on topo add callback
            elif topic.endswith('/subdev/topo/add_reply') and topic.startswith('/$system/'):

                request_id = msg['RequestID']
                if _cache.has(request_id):
                    identity = _cache.get(request_id)
                    sub_dev = _thingclients[identity]
                    if sub_dev.on_topo_add_callback:
                        sub_dev.on_topo_add_callback(msg)

            # on login and logout
            elif topic.endswith('/subdev/login_reply') and topic.startswith('/$system/'):
                request_id = msg['RequestID']
                ret_code = msg['RetCode']
                print('login retcode', ret_code, " request_id:", request_id)

            elif topic.endswith('/subdev/logout_reply') and topic.startswith('/$system/'):
                request_id = msg['RequestID']
                ret_code = msg['RetCode']
                print('logout retcode', ret_code, " request_id:", request_id)

            # on normal callback
            else:
                device_sn = msg['deviceSN']
                sub_dev = None
                if isinstance(device_sn, str):
                    sub_dev = _thingclients[device_sn]
                else:
                    print('unknown message deviceSN')
                    return
                if sub_dev.on_msg_callback:
                    sub_dev.on_msg_callback(msg)
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

_natsclient.subscribe(subject='edge.local.'+_dirver_id,
                      callback=_on_message)


def _wait():
    _natsclient.wait()


threading.Thread(target=_wait).start()
