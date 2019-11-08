import json
import random
import string
import threading
import queue
from pynats import NATSClient
from cacheout import Cache
from thing_exception import UIoTEdgeDriverException, UIoTEdgeTimeoutException

_deviceInfos = []
_driverInfo = None
_nats_url = 'tcp://106.75.237.117:4222'
_thingclients = {}
_cache = Cache(maxsize=1024, ttl=300)
_natsclient = NATSClient(url=_nats_url)
_natsclient.connect()


def _generate_request_id():
    return ''.join(random.sample(string.ascii_letters + string.digits, 16))


class _device_notify(object):
    def __init__(self, callback):
        self.callback = callback

    def run(self, message):
        self.callback(message)


_on_topo_change_callback = None


def set_on_topo_change_callback(callback):
    global _on_topo_change_callback
    _on_topo_change_callback = _device_notify(callback)


def get_topo(is_cached=False, duration=0):
    request_id = _generate_request_id()
    topic = '/$system/%s/%s/subdev/topo/get' % (
        "0001", "123456")

    get_topo = {
        'src': 'local',
        'topic': topic,
        'isCatched': is_cached,
        'duration': duration,
        'payload': {
            'RequestID': request_id,
            "Params": []
        }

    }
    bty = json.dumps(get_topo)
    _natsclient.publish(subject='edge.router.'+_dirver_id,
                        payload=bty.encode('utf-8'))


class ThingClient(object):
    def __init__(self, product_sn, device_sn, on_msg_callback=None, on_disable_enable_callback=None):
        self.device_sn = device_sn
        self.product_sn = product_sn
        self.callback = on_msg_callback
        self._identity = self.product_sn+'.'+self.device_sn
        self._login_queue = queue.Queue()
        self._logout_queue = queue.Queue()
        self._topo_add_queue = queue.Queue()
        self._topo_delete_queue = queue.Queue()
        self._resgister_queue = queue.Queue()
        self.status_callback = on_disable_enable_callback

    def login(self):
        self._login()

    def logout(self):
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

        try:
            self.publish(topic=topic, payload=offline_message)
            _cache.set(request_id, self._identity)  # add cache for callback

            msg = self._logout_queue.get(block=True, timeout=5)
            if msg['RetCode'] != 0:
                raise UIoTEdgeDriverException(msg['RetCode'], msg['Message'])

        except queue.Empty:
            raise UIoTEdgeTimeoutException
        except Exception as e:
            raise e

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
        try:
            self.publish(topic=topic, payload=online_message)
            _cache.set(request_id, self._identity)  # add cache for callback

            msg = self._login_queue.get(block=True, timeout=5)
            if msg['RetCode'] != 0:
                raise UIoTEdgeDriverException(msg['RetCode'], msg['Message'])

        except queue.Empty:
            raise UIoTEdgeTimeoutException
        except Exception as e:
            raise e

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

        try:
            self.publish(topic=topic, payload=register_data)
            _cache.set(request_id, self._identity)  # add cache for callback

            msg = self._resgister_queue.get(block=True, timeout=5)
            if msg['RetCode'] != 0:
                raise UIoTEdgeDriverException(msg['RetCode'], msg['Message'])

        except queue.Empty:
            raise UIoTEdgeTimeoutException
        except Exception as e:
            raise e

    def add_topo(self, is_cached=False, duration=0):
        request_id = _generate_request_id()
        add_topo_data = {
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

        try:
            self.publish(topic=topic, payload=add_topo_data,
                         is_cached=is_cached, duration=duration)
            _cache.set(request_id, self._identity)  # add cache for callback

            msg = self._topo_add_queue.get(block=True, timeout=5)
            if msg['RetCode'] != 0:
                raise UIoTEdgeDriverException(msg['RetCode'], msg['Message'])

        except queue.Empty:
            raise UIoTEdgeTimeoutException
        except Exception as e:
            raise e

    def delete_topo(self, is_cached=False, duration=0):
        request_id = _generate_request_id()
        delete_topo_data = {
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
        try:
            self.publish(topic=topic, payload=delete_topo_data,
                         is_cached=is_cached, duration=duration)
            _cache.set(request_id, self._identity)  # add cache for callback

            msg = self._topo_delete_queue.get(block=True, timeout=5)
            if msg['RetCode'] != 0:
                raise UIoTEdgeDriverException(msg['RetCode'], msg['Message'])

        except queue.Empty:
            raise UIoTEdgeTimeoutException
        except Exception as e:
            raise e

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
                    sub_dev._topo_delete_queue.put(msg)
            # on topo add callback
            elif topic.endswith('/subdev/topo/add_reply') and topic.startswith('/$system/'):

                request_id = msg['RequestID']
                if _cache.has(request_id):
                    identity = _cache.get(request_id)
                    sub_dev = _thingclients[identity]
                    sub_dev._topo_add_queue.put(msg)

            # on login and logout
            elif topic.endswith('/subdev/login_reply') and topic.startswith('/$system/'):
                request_id = msg['RequestID']
                if _cache.has(request_id):
                    identity = _cache.get(request_id)
                    sub_dev = _thingclients[identity]
                    sub_dev._login_queue.put(msg)

            elif topic.endswith('/subdev/logout_reply') and topic.startswith('/$system/'):
                request_id = msg['RequestID']
                if _cache.has(request_id):
                    identity = _cache.get(request_id)
                    sub_dev = _thingclients[identity]
                    sub_dev._logout_queue.put(msg)
            elif (topic.endswith('/subdev/enable') or topic.endswith('/subdev/disable')) and topic.startswith('/$system/'):
                try:
                    enable_list = msg['Params']
                    for sub_device in enable_list:
                        identify = sub_device['ProductSN'] + \
                            '.'+sub_device['DeviceSN']
                        if identify in _thingclients:
                            sub_dev = _thingclients[identify]
                            if sub_dev.status_callback:
                                sub_dev.status_callback(msg)
                except Exception as e:
                    print(e)

            # on normal callback
            else:
                identify = sub_device['ProductSN'] + \
                    '.'+sub_device['DeviceSN']
                if identify in _thingclients:
                    sub_dev = _thingclients[identify]
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
