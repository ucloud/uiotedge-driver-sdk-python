import json
import random
import string
import queue
import base64
import threading
import time
from cachetools import TTLCache
from uiotedgedriverlinksdk.exception import EdgeDriverLinkException, EdgeDriverLinkTimeoutException, EdgeDriverLinkOfflineException
from uiotedgedriverlinksdk.nats import _nat_subscribe_queue, publish_nats_msg, _nat_publish_queue
from uiotedgedriverlinksdk import _driver_id
from uiotedgedriverlinksdk.logger import getLogger

_logger = getLogger()
_action_queue_map = {}
_connect_map = {}

_cache = TTLCache(maxsize=10, ttl=30)


def get_edge_online_status():
    global _cache
    is_online = _cache.get('edge_status')
    if is_online:
        return True
    return False


def add_connect_map(key: str, value):
    global _connect_map
    _connect_map[key] = value


def del_connect_map(key: str):
    global _connect_map
    _connect_map.pop(key)


def _generate_request_id():
    return ''.join(random.sample(string.ascii_letters + string.digits, 16)).lower()


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


def get_topo(timeout=5):
    global _action_queue_map
    request_id = _generate_request_id()
    topic = '/$system/%s/%s/subdev/topo/get' % (
        _generate_request_id(), "123456")

    get_topo = {
        'RequestID': request_id,
        "Params": []
    }
    try:
        data = json.dumps(get_topo)
        _publish(topic=topic, payload=data.encode('utf-8'),
                 is_cached=False, duration=0)
        q = queue.Queue()
        _action_queue_map[request_id] = q

        msg = q.get(timeout=5)
        if msg['RetCode'] != 0:
            raise EdgeDriverLinkException(msg['RetCode'], msg['Message'])

        return msg

    except queue.Empty:
        raise EdgeDriverLinkTimeoutException
    except EdgeDriverLinkException as e:
        raise e
    except Exception as e:
        raise e
    finally:
        _action_queue_map.pop(request_id)


def add_topo(product_sn, device_sn, timeout=5):
    global _action_queue_map
    if get_edge_online_status():
        request_id = _generate_request_id()
        topic = '/$system/%s/%s/subdev/topo/add' % (
            product_sn, device_sn)

        add_topo = {
            'RequestID': request_id,
            "Params": [
                {
                    'ProductSN': product_sn,
                    'DeviceSN': device_sn
                }
            ]
        }
        try:
            data = json.dumps(add_topo)
            _publish(topic=topic, payload=data.encode('utf-8'),
                     is_cached=False, duration=0)
            q = queue.Queue()
            _action_queue_map[request_id] = q

            msg = q.get(timeout=5)

            _action_queue_map.pop(request_id)
            if msg['RetCode'] != 0:
                raise EdgeDriverLinkException(msg['RetCode'], msg['Message'])

        except queue.Empty:
            raise EdgeDriverLinkTimeoutException
        except EdgeDriverLinkException as e:
            raise e
        except Exception as e:
            raise e
    else:
        raise EdgeDriverLinkOfflineException


def delete_topo(product_sn, device_sn, timeout=5):
    global _action_queue_map
    if get_edge_online_status():
        request_id = _generate_request_id()
        topic = '/$system/%s/%s/subdev/topo/delete' % (
            product_sn, device_sn)

        delete_topo = {
            'RequestID': request_id,
            "Params": [
                {
                    'ProductSN': product_sn,
                    'DeviceSN': device_sn
                }
            ]
        }

        try:
            data = json.dumps(delete_topo)
            _publish(topic=topic, payload=data.encode('utf-8'),
                     is_cached=False, duration=0)
            q = queue.Queue()
            _action_queue_map[request_id] = q

            msg = q.get(timeout=5)

            _action_queue_map.pop(request_id)
            if msg['RetCode'] != 0:
                raise EdgeDriverLinkException(msg['RetCode'], msg['Message'])

        except queue.Empty:
            raise EdgeDriverLinkTimeoutException
        except EdgeDriverLinkException as e:
            raise e
        except Exception as e:
            raise e
    else:
        raise EdgeDriverLinkOfflineException


def register_device(product_sn, device_sn, product_secret, timeout=5):
    global _action_queue_map
    if get_edge_online_status():
        request_id = _generate_request_id()
        register_data = {
            'RequestID': request_id,
            "Params": [
                {
                    'ProductSN': product_sn,
                    'DeviceSN': device_sn,
                    'ProductSecret': product_secret
                }
            ]
        }
        topic = '/$system/%s/%s/subdev/register' % (
            product_sn, device_sn)

        try:
            data = json.dumps(register_data)
            _publish(topic=topic, payload=data.encode('utf-8'),
                     is_cached=False, duration=0)
            q = queue.Queue()
            _action_queue_map[request_id] = q

            msg = q.get(timeout=timeout)
            _action_queue_map.pop(request_id)
            if msg['RetCode'] != 0:
                raise EdgeDriverLinkException(msg['RetCode'], msg['Message'])

        except queue.Empty:
            raise EdgeDriverLinkTimeoutException
        except EdgeDriverLinkException as e:
            raise e
        except Exception as e:
            raise e
    else:
        raise EdgeDriverLinkOfflineException


def device_login_async(product_sn, device_sn):
    request_id = _generate_request_id()
    topic = '/$system/%s/%s/subdev/login' % (
        product_sn, device_sn)

    device_login_msg = {
        'RequestID': request_id,
        "Params": [
            {
                'ProductSN': product_sn,
                'DeviceSN': device_sn
            }
        ]
    }
    data = json.dumps(device_login_msg)
    _publish(topic=topic, payload=data.encode('utf-8'),
             is_cached=False, duration=0)


def device_logout_async(product_sn, device_sn):
    request_id = _generate_request_id()
    topic = '/$system/%s/%s/subdev/logout' % (
        product_sn, device_sn)

    device_logout_msg = {
        'RequestID': request_id,
        "Params": [
            {
                'ProductSN': product_sn,
                'DeviceSN': device_sn
            }
        ]
    }
    data = json.dumps(device_logout_msg)
    _publish(topic=topic, payload=data.encode('utf-8'),
             is_cached=False, duration=0)


def device_login_sync(product_sn, device_sn, timeout=5):
    global _action_queue_map
    request_id = _generate_request_id()
    topic = '/$system/%s/%s/subdev/login' % (
        product_sn, device_sn)

    device_login_msg = {
        'RequestID': request_id,
        "Params": [
            {
                'ProductSN': product_sn,
                'DeviceSN': device_sn
            }
        ]
    }

    try:
        data = json.dumps(device_login_msg)
        _publish(topic=topic, payload=data.encode('utf-8'),
                 is_cached=False, duration=0)
        q = queue.Queue()
        _action_queue_map[request_id] = q

        msg = q.get(timeout=timeout)
        _action_queue_map.pop(request_id)
        if msg['RetCode'] != 0:
            raise EdgeDriverLinkException(msg['RetCode'], msg['Message'])

    except queue.Empty:
        raise EdgeDriverLinkTimeoutException
    except EdgeDriverLinkException as e:
        raise e
    except Exception as e:
        raise e


def device_logout_sync(product_sn, device_sn, timeout=5):
    global _action_queue_map
    request_id = _generate_request_id()
    topic = '/$system/%s/%s/subdev/logout' % (
        product_sn, device_sn)

    device_logout_msg = {
        'RequestID': request_id,
        "Params": [
            {
                'ProductSN': product_sn,
                'DeviceSN': device_sn
            }
        ]
    }

    try:
        data = json.dumps(device_logout_msg)
        _publish(topic=topic, payload=data.encode('utf-8'),
                 is_cached=False, duration=0)
        q = queue.Queue()
        _action_queue_map[request_id] = q

        msg = q.get(timeout=timeout)
        _action_queue_map.pop(request_id)
        if msg['RetCode'] != 0:
            raise EdgeDriverLinkException(msg['RetCode'], msg['Message'])

    except queue.Empty:
        raise EdgeDriverLinkTimeoutException
    except EdgeDriverLinkException as e:
        raise e
    except Exception as e:
        raise e


def send_message(topic: str, payload: b'', is_cached=False, duration=0):
    _publish(topic=topic, payload=payload,
             is_cached=is_cached, duration=duration)


def _on_broadcast_message(message):
    global _on_topo_change_callback
    global _on_status_change_callback
    global _action_queue_map
    _logger.debug("recv message:{} " .format(str(message)))
    try:
        js = json.loads(message)
        topic = js['topic']

        data = str(base64.b64decode(js['payload']), "utf-8")
        # _logger.debug("broadcast message payload: " + data)

        msg = json.loads(data)

        if isinstance(topic, str) and topic.startswith("/$system/"):
            # on topo change callback
            if topic.endswith("/subdev/topo/notify/add"):
                if _on_topo_change_callback:
                    msg['operaction'] = 'add'
                    _on_topo_change_callback.run(msg)

            elif topic.endswith("/subdev/topo/notify/delete"):
                if _on_topo_change_callback:
                    msg['operaction'] = 'delete'
                    _on_topo_change_callback.run(msg)

            elif topic.endswith('/subdev/enable'):
                if _on_status_change_callback:
                    msg['operaction'] = 'enable'
                    _on_status_change_callback.run(msg)

            elif topic.endswith('/subdev/disable'):
                if _on_status_change_callback:
                    msg['operaction'] = 'disable'
                    _on_status_change_callback.run(msg)

            else:
                request_id = msg['RequestID']
                if request_id in _action_queue_map:
                    q = _action_queue_map[request_id]
                    q.put(msg)
        else:
            _logger.debug('unknown message topic:{}'.format(topic))
            return

    except Exception as e:
        _logger.error(e)


def _on_message(message):
    global _connect_map
    _logger.debug("recv message: {}".format(str(message)))
    try:
        js = json.loads(message)
        identify = js['productSN'] + \
            '.'+js['deviceSN']

        topic = js['topic']
        msg = base64.b64decode(js['payload'])
        # _logger.debug("normal message payload: {}".format(str(msg, 'utf-8')))
        if identify in _connect_map:
            sub_dev = _connect_map[identify]
            if sub_dev.callback:
                sub_dev.callback(topic, msg)
        else:
            _logger.error('unknown message topic:{}'.format(topic))
            return

    except Exception as e:
        _logger.error(e)


def _publish(topic: str, payload: b'', is_cached=False, duration=0):
    try:
        payload_encode = base64.b64encode(payload)
        data = {
            'src': 'local',
            'topic': topic,
            'isCatched': is_cached,
            'duration': duration,
            'payload': str(payload_encode, 'utf-8')
        }
        publish_nats_msg(data)
    except Exception as e:
        _logger.error(e)
        raise e


def _set_edge_status():
    global _cache
    _cache['edge_status'] = True


def init_subscribe_handler():
    while True:
        msg = _nat_subscribe_queue.get()
        # _logger.debug(msg)
        subject = msg.subject
        data = msg.data.decode()

        if subject == "edge.local.broadcast":
            _on_broadcast_message(data)
        elif subject == "edge.state.reply":
            _set_edge_status()
        else:
            _on_message(data)


def _get_device_list():
    global _connect_map
    result = []
    for v in _connect_map.values():
        result.append(v.get_device_info())

    return result


def fetch_online_status():
    min_retry_timeout = 1
    max_retry_timeout = 15
    retry_timeout = min_retry_timeout
    while True:
        device_list = _get_device_list()
        data = {
            'payload': {
                'driverID': _driver_id,
                'devices': device_list
            },
            'subject': 'edge.state.req'
        }

        _nat_publish_queue.put(data)

        if get_edge_online_status():
            time.sleep(max_retry_timeout)
        else:
            if retry_timeout < max_retry_timeout:
                retry_timeout = retry_timeout + 1
            time.sleep(retry_timeout)


_t_sub = threading.Thread(target=init_subscribe_handler)
_t_sub.setDaemon(True)
_t_sub.start()

_t_online = threading.Thread(target=fetch_online_status)
_t_online.setDaemon(True)
_t_online.start()
