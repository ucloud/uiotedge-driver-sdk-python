import logging
import os
import asyncio
import queue
import sys
import json
import time
from nats.aio.client import Client as NATS
from nats.aio.errors import NatsError
from uiotedgedriverlinksdk import _driver_id


class _Logger(object):
    def __init__(self):
        self.url = os.environ.get(
            'UIOTEDGE_NATS_ADDRESS') or 'tcp://127.0.0.1:4222'
        self.nc = NATS()
        self.loop = asyncio.new_event_loop()
        self.queue = queue.Queue()
        self.start()

    async def _publish(self):
        try:
            await self.nc.connect(servers=[self.url], loop=self.loop)
        except Exception as e1:
            logging.error(e1)
            sys.exit(1)

        while True:
            try:
                msg = self.queue.get()
                bty = json.dumps(msg)
                await self.nc.publish(subject='edge.log.upload',
                                      payload=bty.encode('utf-8'))
                await self.nc.flush()
            except NatsError as e:
                logging.error(e)
            except Exception as e:
                logging.error(e)

    def start(self):
        self.loop.run_until_complete(self._publish())

    def debug(self, msg):
        data = {
            'module': os.environ.get("UIOTEDGE_INSTANCE_NAME") or _driver_id,
            'level': 'debug',
            'message': msg,
            'timestamp': time.time(),
        }
        self.queue.put(data)

    def info(self, msg, *args):
        data = {
            'module': os.environ.get("UIOTEDGE_INSTANCE_NAME") or _driver_id,
            'level': 'info',
            'message': msg,
            'timestamp': time.time(),
        }
        self.queue.put(data)

    def error(self, msg, *args):
        data = {
            'module': os.environ.get("UIOTEDGE_INSTANCE_NAME") or _driver_id,
            'level': 'error',
            'message': msg,
            'timestamp': time.time(),
        }
        self.queue.put(data)

    def warn(self, msg, *args):
        data = {
            'module': os.environ.get("UIOTEDGE_INSTANCE_NAME") or _driver_id,
            'level': 'warn',
            'message': msg,
            'timestamp': time.time(),
        }
        self.queue.put(data)

    def critical(self, msg, *args):
        data = {
            'module': os.environ.get("UIOTEDGE_INSTANCE_NAME") or _driver_id,
            'level': 'critical',
            'message': msg,
            'timestamp': time.time(),
        }
        self.queue.put(data)


_uiotedge_logger = _Logger()


def getLogger():
    global _uiotedge_logger
    return _uiotedge_logger
