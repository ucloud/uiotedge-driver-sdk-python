import json
import random
import string
import threading
import queue
from pynats import NATSClient
from cacheout import Cache
from .thing_exception import UIoTEdgeDriverException, UIoTEdgeTimeoutException, UIoTEdgeDeviceOfflineException

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


_on_status_change_callback = None


def set_on_status_change_callback(callback):
    global _on_status_change_callback
    _on_status_change_callback = _device_notify(callback)


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
    def __init__(self, product_sn, device_sn, on_msg_callback=None):
        self.device_sn = device_sn
        self.product_sn = product_sn
        self.callback = on_msg_callback
        self._identity = self.product_sn+'.'+self.device_sn
        self._login_queue = queue.Queue()
        self._topo_add_queue = queue.Queue()
        self._topo_delete_queue = queue.Queue()
        self._resgister_queue = queue.Queue()
        self.online = False

    def logout(self):
        if self.online:
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
            data = json.dumps(offline_message)
            self._publish_without_login(
                topic=topic, payload=data)

            self.online = False
            _thingclients.pop(self._identity)

    def login(self, is_cached=False, duration=0, timeout=5):
        _thingclients[self._identity] = self

        request_id = _generate_request_id()
        topic = '/$system/%s/%s/subdev/login' % (
            self.product_sn, self.device_sn)

        login_data = {
            'RequestID': request_id,
            'Params': [
                {
                    'ProductSN': self.product_sn,
                    'DeviceSN': self.device_sn
                }
            ]
        }

        try:
            data = json.dumps(login_data)
            self._publish_without_login(
                topic=topic, payload=data, is_cached=is_cached, duration=duration)
            _cache.set(request_id, self._identity)  # add cache for callback

            # wait for response
            msg = self._login_queue.get(block=True, timeout=timeout)
            if msg['RetCode'] != 0:
                raise UIoTEdgeDriverException(msg['RetCode'], msg['Message'])

        except queue.Empty:
            _thingclients.pop(self._identity)
            raise UIoTEdgeTimeoutException
        except UIoTEdgeDriverException as e:
            _thingclients.pop(self._identity)
            raise e
        except Exception as e:
            _thingclients.pop(self._identity)
            raise e

        self.online = True

    def register(self, product_secret, timeout=5):
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
            data = json.dumps(register_data)
            self._publish_without_login(
                topic=topic, payload=data)
            _cache.set(request_id, self._identity)  # add cache for callback

            msg = self._resgister_queue.get(block=True, timeout=timeout)
            if msg['RetCode'] != 0:
                raise UIoTEdgeDriverException(msg['RetCode'], msg['Message'])

        except queue.Empty:
            raise UIoTEdgeTimeoutException
        except UIoTEdgeDriverException as e:
            raise e
        except Exception as e:
            raise e

    def add_topo(self, is_cached=False, duration=0, timeout=5):
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
            data = json.dumps(add_topo_data)
            self._publish_without_login(topic=topic, payload=data,
                                        is_cached=is_cached, duration=duration)
            _cache.set(request_id, self._identity)  # add cache for callback

            msg = self._topo_add_queue.get(block=True, timeout=timeout)
            if msg['RetCode'] != 0:
                raise UIoTEdgeDriverException(msg['RetCode'], msg['Message'])

        except queue.Empty:
            raise UIoTEdgeTimeoutException
        except UIoTEdgeDriverException as e:
            raise e
        except Exception as e:
            raise e

    def delete_topo(self, is_cached=False, duration=0, timeout=5):
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
            data = json.dumps(delete_topo_data)
            self._publish_without_login(topic=topic, payload=data,
                                        is_cached=is_cached, duration=duration)
            _cache.set(request_id, self._identity)  # add cache for callback

            msg = self._topo_delete_queue.get(block=True, timeout=timeout)
            if msg['RetCode'] != 0:
                raise UIoTEdgeDriverException(msg['RetCode'], msg['Message'])

        except queue.Empty:
            raise UIoTEdgeTimeoutException
        except UIoTEdgeDriverException as e:
            raise e
        except Exception as e:
            raise e

    def _publish_without_login(self, topic: str, payload: str, is_cached=False, duration=0):
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

    def publish(self, topic, payload: str, is_cached=False, duration=0):
        if self.online:
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


def _on_broadcast_message(message):
    # driver message router ot subdevice
    payload = str(message.payload, encoding="utf-8")
    print("broadcast message: ", payload)
    try:
        js = json.loads(payload)
        sub_dev = None
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
                # do nothing
                pass
            elif topic.endswith('/subdev/enable') and topic.startswith('/$system/'):
                if _on_status_change_callback:
                    msg['Status'] = 'enable'
                    _on_status_change_callback.run(msg)
            elif topic.endswith('/subdev/disable') and topic.startswith('/$system/'):
                if _on_status_change_callback:
                    msg['Status'] = 'disable'
                    _on_status_change_callback.run(msg)
            # on normal callback
            else:
                print('unknown message content', js)
        else:
            print('unknown message topic')
            return

    except Exception as e:
        print(e)


def _on_message(message):
    # driver message router ot subdevice
    payload = str(message.payload, encoding="utf-8")
    print("normal message: ", payload)
    js = json.loads(payload)
    try:
        msg = js['payload']
        identify = js['productSN'] + \
            '.'+js['deviceSN']
        if identify in _thingclients:
            sub_dev = _thingclients[identify]
            if sub_dev.callback:
                sub_dev.callback(msg)
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

_natsclient.subscribe(subject='edge.local.broadcast',
                      callback=_on_broadcast_message)


def _wait():
    _natsclient.wait()


threading.Thread(target=_wait).start()
