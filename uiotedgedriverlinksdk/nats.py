import asyncio
import json
import sys
import queue
import time
import logging
import threading
import random
import string
import os
from nats.aio.client import Client as NATS
from nats.aio.errors import ErrConnectionClosed, ErrTimeout, ErrNoServers

_nat_publish_queue = queue.Queue()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

_edge_online_status = False
_edge_online_status_queue = queue.Queue()


_driver_id = ''.join(random.sample(
    string.ascii_letters + string.digits, 16)).lower()
logger.info("dirver_id: " + _driver_id)

class natsClient(object):
    def __init__(self, msg_handler, broadcast_msg_handler):
        self.url = os.environ.get(
            'UIOTEDGE_NATS_ADDRESS') or 'tcp://127.0.0.1:4222'
        self.loop = asyncio.new_event_loop()
        self.nc = NATS()
        self.msg_handler = msg_handler
        self.broadcast_msg_handler = broadcast_msg_handler
        self.connect()

    def connect(self):
        t = threading.Thread(target=self.start_loop)
        t.start()
        asyncio.run_coroutine_threadsafe(self.wait_for_msg(), self.loop)

    def start_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def wait_for_msg(self):
        async def online_handler(msg):
            data = msg.data.decode()
            logger.debug("recv online message:"+data)
            _edge_online_status_queue.put(data)

        async def msg_handler(msg):
            data = msg.data.decode()
            logger.debug("recv message:"+data)
            self.msg_handler(msg)
        
        async def broadcast_handler(msg):
            data = msg.data.decode()
            logger.debug("recv broadcast message:"+data)
            self.broadcast_msg_handler(msg)

        try:
            print(self.url)
            await self.nc.connect(servers=[self.url], loop=self.loop)
            logger.debug('connect success')
        except Exception as e:
            logger.error(e)
            sys.exit(0)

        if self.nc.is_connected:
            await self.nc.subscribe("edge.local."+_driver_id, cb=msg_handler)
            await self.nc.subscribe("edge.local.broadcast", cb=broadcast_handler)
            await self.nc.subscribe("edge.state.reply", cb=online_handler)
            await self.nc.flush()
        while True:
            try:
                msg = _nat_publish_queue.get()
                bty = json.dumps(msg['payload'])
                await self.nc.publish(subject=msg['subject'],
                                      payload=bty.encode('utf-8'))
                await self.nc.flush()
            except Exception as e:
                logger.error(e)

    def publish(self, msg):
        publish_nats_msg(msg)


def get_edge_online_status():
    return _edge_online_status


def publish_nats_msg(msg):
    data = {
        'subject': 'edge.router.'+_driver_id,
        'payload': msg
    }
    _nat_publish_queue.put(data)


def _init_edge_status():
    while True:
        try:
            msg = _edge_online_status_queue.get(timeout=45)
            js = json.loads(msg)
            online = js['state']
            global _edge_online_status
            if online == True:
                _edge_online_status = True
            else:
                _edge_online_status = False
        except queue.Empty:
            _edge_online_status = False
            logger.warn("edge offline")
        except Exception as e:
            logger.error(e)


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

        if _edge_online_status:
            time.sleep(max_retry_timeout)
        else:
            if retry_timeout < max_retry_timeout:
                retry_timeout = retry_timeout + 1
            time.sleep(retry_timeout)


threading.Thread(target=_init_edge_status).start()
threading.Thread(target=_fetch_online_status).start()
