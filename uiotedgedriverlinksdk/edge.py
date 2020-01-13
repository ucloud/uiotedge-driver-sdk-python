import json
import random
import string
import threading
import queue
import base64
import os
import time
import logging
import asyncio
from .exception import EdgeDriverLinkException, EdgeDriverLinkTimeoutException, EdgeDriverLinkOfflineException
from .nats import init_nats, init_nat_publish


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

_action_queue_map = {}
_connect_map = {}
_publish_queue = queue.Queue()

_edge_online_status = True

_nats_url = os.environ.get(
    'UIOTEDGE_NATS_ADDRESS') or 'tcp://127.0.0.1:4222'


def add_connect_map(key: str, value):
    _connect_map[key] = value


def del_connect_map(key: str):
    _connect_map.pop(key)


def _generate_request_id():
    return ''.join(random.sample(string.ascii_letters + string.digits, 16)).lower()


def get_edge_online_status():
    return _edge_online_status


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
    if _edge_online_status:
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
    if _edge_online_status:
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
    if _edge_online_status:
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
        _publish_queue.put(data)
    except Exception as e:
        logger.error(e)
        raise


def _on_broadcast_message(message):
    logger.debug("broadcast message: " + message)
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
    # driver message router ot subdevice
    # payload = str(message.payload, encoding="utf-8")
    logger.debug("normal message: "+message)
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


# subscribe message from router
_dirver_id = ''.join(random.sample(
    string.ascii_letters + string.digits, 16)).lower()
logger.info("dirver_id: " + _dirver_id)

# _edge_online_status_queue = queue.Queue()


# def _online_status_callback(message):
#     msg = str(message.payload, encoding="utf-8")
#     logger.debug("status message: "+msg)
#     _edge_online_status_queue.put(msg)


# def _fetch_online_status():
#     min_retry_timeout = 1
#     max_retry_timeout = 30
#     retry_timeout = min_retry_timeout
#     while True:
#         try:
#             data = {
#                 'driverID': _dirver_id
#             }
#             payload = json.dumps(data)
#             _natsclient.publish(subject='edge.state.req',
#                                 payload=payload.encode('utf-8'))

#         except Exception as e:
#             logger.error(e)

#         if _edge_online_status:
#             time.sleep(max_retry_timeout)
#         else:
#             if retry_timeout < max_retry_timeout:
#                 retry_timeout = retry_timeout + 1
#             time.sleep(retry_timeout)


# def _edge_online_status_logic():
#     while True:
#         try:
#             msg = _edge_online_status_queue.get(timeout=45)
#             js = json.loads(msg)
#             online = js['state']
#             if online == True:
#                 global _edge_online_status
#                 _edge_online_status = True
#             else:
#                 _edge_online_status = False
#         except queue.Empty:
#             logger.warn('edge offline')
#             _edge_online_status = False
#         except Exception as e:
#             logger.error(e)



def _init_nats_connect():
    loop = asyncio.new_event_loop()
    loop.run_until_complete(init_nats(loop,_nats_url,_on_message,_on_broadcast_message,_dirver_id))
    loop.run_forever()

def _init_nats_publish():
    loop = asyncio.new_event_loop()
    loop.run_until_complete(init_nat_publish(_publish_queue,_dirver_id))
    loop.run_forever()

# _fetch_online_status()
threading.Thread(target=_init_nats_connect).start()
threading.Thread(target=_init_nats_publish).start()
# threading.Thread(target=_edge_online_status_logic).start()
# threading.Thread(target=_fetch_online_status).start()
