import asyncio
import json
import sys
import queue
import time
import threading
import random
import string
import os
from nats.aio.client import Client as NATS
from nats.aio.errors import ErrConnectionClosed, ErrTimeout, ErrNoServers
from cachetools import TTLCache
import signal
import logging

logger = logging.getLogger(__name__)


def exit_handler(signum, frame):
    sys.exit(0)


signal.signal(signal.SIGINT, exit_handler)
signal.signal(signal.SIGTERM, exit_handler)

_cache = TTLCache(maxsize=10, ttl=45)
_nat_publish_queue = queue.Queue()
_nat_subscribe_queue = queue.Queue()


_driver_id = ''
_deviceInfos = []
_driverInfo = None

# get Config
_config_path = './etc/uiotedge/config.json'
with open(_config_path, 'r') as load_f:
    load_dict = json.load(load_f)
    logger.info(load_dict)

    if 'driverID' in load_dict.keys():
        _driver_id = load_dict['driverID']

    if 'deviceList' in load_dict.keys():
        _deviceInfos = load_dict['deviceList']

    if 'driverInfo' in load_dict.keys():
        _driverInfo = load_dict['driverInfo']


logger.info("dirver_id: " + _driver_id)


class natsClientPub(object):
    def __init__(self):
        self.url = os.environ.get(
            'UIOTEDGE_NATS_ADDRESS') or 'tcp://127.0.0.1:4222'
        self.nc = NATS()
        self.loop = asyncio.new_event_loop()

    async def _publish(self):
        try:
            await self.nc.connect(servers=[self.url], loop=self.loop)
        except Exception as e1:
            logger.error(e1)
            sys.exit(1)

        while True:
            try:
                msg = _nat_publish_queue.get()
                bty = json.dumps(msg['payload'])
                await self.nc.publish(subject=msg['subject'],
                                      payload=bty.encode('utf-8'))
                await self.nc.flush()
            except Exception as e:
                logger.error(e)

    def start(self):
        self.loop.run_until_complete(self._publish())
        # self.loop.run_forever()


class natsClientSub(object):
    def __init__(self):
        self.url = os.environ.get(
            'UIOTEDGE_NATS_ADDRESS') or 'tcp://127.0.0.1:4222'
        self.nc = NATS()
        self.loop = asyncio.new_event_loop()

    async def _connect(self):
        try:
            await self.nc.connect(servers=[self.url], loop=self.loop)
        except Exception as e1:
            logger.error(e1)
            sys.exit(1)

        async def message_handler(msg):
            # subject = msg.subject
            # reply = msg.reply
            # data = msg.data.decode()
            # print("Received a message on '{subject} {reply}': {data}".format(
            #     subject=subject, reply=reply, data=data))
            _nat_subscribe_queue.put(msg)

        await self.nc.subscribe("edge.local."+_driver_id, queue=_driver_id, cb=message_handler, is_async=True)
        await self.nc.subscribe("edge.local.broadcast", queue=_driver_id, cb=message_handler, is_async=True)
        await self.nc.subscribe("edge.state.reply", queue=_driver_id, cb=message_handler, is_async=True)
        await self.nc.flush()

    def start(self):
        self.loop.run_until_complete(self._connect())
        self.loop.run_forever()


def get_edge_online_status():
    is_online = _cache.get('edge_status')
    if is_online:
        return True
    return False


def publish_nats_msg(msg):
    data = {
        'subject': 'edge.router.'+_driver_id,
        'payload': msg
    }
    _nat_publish_queue.put(data)


def _set_edge_status():
    _cache['edge_status'] = True


def _fetch_online_status():
    min_retry_timeout = 1
    max_retry_timeout = 30
    retry_timeout = min_retry_timeout
    while True:
        data = {
            'payload': {
                'driverID': _driver_id
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


def init_pub():
    natsClientPub().start()


def init_sub():
    natsClientSub().start()


threading.Thread(target=init_pub).start()
threading.Thread(target=init_sub).start()
threading.Thread(target=_fetch_online_status).start()
