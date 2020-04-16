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
from nats.aio.errors import NatsError
import signal
import logging

_logger = logging.getLogger(__name__)


def exit_handler(signum, frame):
    sys.exit(0)


_nat_publish_queue = queue.Queue()
_nat_subscribe_queue = queue.Queue()


_driver_id = ''
_deviceInfos = []
_driverInfo = None

# get Config
_config_path = './etc/uiotedge/config.json'
with open(_config_path, 'r') as load_f:
    try:
        load_dict = json.load(load_f)
        _logger.info(str(load_dict))

        _driver_id = load_dict['driverID']

        if 'deviceList' in load_dict.keys():
            _deviceInfos = load_dict['deviceList']

        if 'driverInfo' in load_dict.keys():
            _driverInfo = load_dict['driverInfo']
    except Exception as e:
        _logger.error('load config file error:{}'.format(e))
        sys.exit(1)

_logger.info("dirver_id: {}".format(_driver_id))


class natsClientPub(object):
    def __init__(self):
        self.url = os.environ.get(
            'UIOTEDGE_NATS_ADDRESS') or 'tcp://127.0.0.1:4222'
        self.nc = NATS()
        self.loop = asyncio.new_event_loop()

    async def _publish(self):
        global _nat_publish_queue
        try:
            await self.nc.connect(servers=[self.url], loop=self.loop)
        except Exception as e1:
            _logger.error(e1)
            sys.exit(1)

        while True:
            try:
                msg = _nat_publish_queue.get()
                bty = json.dumps(msg['payload'])
                await self.nc.publish(subject=msg['subject'],
                                      payload=bty.encode('utf-8'))
                await self.nc.flush()
            except NatsError as e:
                _logger.error(e)
            except Exception as e:
                _logger.error(e)

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
            _logger.error(e1)
            sys.exit(1)

        async def message_handler(msg):
            global _nat_subscribe_queue
            # subject = msg.subject
            # reply = msg.reply
            # data = msg.data.decode()
            # sdk_print("Received a message on '{subject} {reply}': {data}".format(
            #     subject=subject, reply=reply, data=data))
            _nat_subscribe_queue.put(msg)
        await self.nc.subscribe("edge.local."+_driver_id, queue=_driver_id, cb=message_handler, is_async=True)
        await self.nc.subscribe("edge.local.broadcast", queue=_driver_id, cb=message_handler, is_async=True)
        await self.nc.subscribe("edge.state.reply", queue=_driver_id, cb=message_handler, is_async=True)
        await self.nc.flush()

    def start(self):
        self.loop.run_until_complete(self._connect())
        self.loop.run_forever()


def publish_nats_msg(msg):
    global _nat_publish_queue
    data = {
        'subject': 'edge.router.'+_driver_id,
        'payload': msg
    }
    _nat_publish_queue.put(data)


def start_pub():
    natsClientPub().start()


def start_sub():
    natsClientSub().start()


_t_nats_pub = threading.Thread(target=start_pub)
_t_nats_pub.setDaemon(True)
_t_nats_pub.start()

_t_nats_sub = threading.Thread(target=start_sub)
_t_nats_sub.setDaemon(True)
_t_nats_sub.start()
