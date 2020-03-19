import json
import random
import string
import queue
import base64
import threading
from .exception import EdgeDriverLinkException, EdgeDriverLinkTimeoutException, EdgeDriverLinkOfflineException
from .nats import get_edge_online_status, _nat_subscribe_queue, publish_nats_msg, _driver_id, _set_edge_status
import logging

logger = logging.getLogger('uiotedgedriverlinksdk')
_action_queue_map = {}
_connect_map = {}


def add_connect_map(key: str, value):
    _connect_map[key] = value


def del_connect_map(key: str):
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


def device_login(product_sn, device_sn, is_cached=False, duration=0):
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
             is_cached=is_cached, duration=duration)


def device_logout(product_sn, device_sn, is_cached=False, duration=0):
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
             is_cached=is_cached, duration=duration)


def send_message(topic: str, payload: b'', is_cached=False, duration=0):
    _publish(topic=topic, payload=payload,
             is_cached=is_cached, duration=duration)


def _on_broadcast_message(message):
    logger.debug("broadcast message: " + str(message))
    try:
        js = json.loads(message)
        topic = js['topic']

        data = str(base64.b64decode(js['payload']), "utf-8")
        # logger.debug("broadcast message payload: " + data)

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
            logger.warn('unknown message topic')
            return

    except Exception as e:
        logger.error(e)


def _on_message(message):
    logger.debug("normal message: "+str(message))
    try:
        js = json.loads(message)
        identify = js['productSN'] + \
            '.'+js['deviceSN']

        msg = base64.b64decode(js['payload'])
        logger.debug("normal message payload: " + str(msg, 'utf-8'))
        if identify in _connect_map:
            sub_dev = _connect_map[identify]
            if sub_dev.callback:
                sub_dev.callback(msg)
        else:
            logger.warn('unknown message topic')
            return

    except Exception as e:
        logger.error(e)


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
        logger.error(e)
        raise


def init_subscribe_handler():
    while True:
        msg = _nat_subscribe_queue.get()
        logger.debug(msg)
        subject = msg.subject
        data = msg.data.decode()

        if subject == "edge.local."+_driver_id:
            _on_message(data)
        elif subject == "edge.local.broadcast":
            _on_broadcast_message(data)
        elif subject == "edge.state.reply":
            _set_edge_status()


threading.Thread(target=init_subscribe_handler).start()
