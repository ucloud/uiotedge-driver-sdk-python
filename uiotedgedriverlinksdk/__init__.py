import asyncio
import json
import logging
import os
import queue
import sys
import threading
import time

from nats.aio.client import Client as NATS
from nats.aio.errors import NatsError

_driver_id = ''
_driver_name = ''
_deviceInfos = []
_driverInfo = None
_driver_name = ''
_logger = logging.getLogger()

# get Config
_config_path = './etc/uiotedge/config.json'
with open(_config_path, 'r') as load_f:
    try:
        load_dict = json.load(load_f)
        _logger.info(str(load_dict))
        # print('----config: {} -------'.format(load_dict))

        _driver_id = load_dict['driverID']
        _driver_name = load_dict['driverName']

        if 'deviceList' in load_dict.keys():
            _deviceInfos = load_dict['deviceList']

        if 'driverInfo' in load_dict.keys():
            _driverInfo = load_dict['driverInfo']
    except Exception as e:
        _logger.error('load config file error:{}'.format(e))
        sys.exit(1)

_logger.info("driver_id: {}, driver name:{}".format(_driver_id, _driver_name))


class _Logger(object):
    def __init__(self, name):
        self.url = os.environ.get(
            'UIOTEDGE_NATS_ADDRESS') or 'tcp://127.0.0.1:4222'
        self.nc = NATS()
        self.loop = asyncio.new_event_loop()
        self.queue = queue.Queue()
        self.name = name
        self.logger = logging.getLogger()
        format_str = logging.Formatter(
            '%(asctime)s - %(levelname)s: %(message)s')
        sh = logging.StreamHandler()
        sh.setFormatter(format_str)
        self.logger.addHandler(sh)

    async def _publish(self):
        try:
            await self.nc.connect(servers=[self.url], loop=self.loop)
            logging.debug('nats for logger connect success')
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
            'module': self.name,
            'level': 'debug',
            'message': msg,
            'timestamp': int(time.time()),
        }
        self.queue.put(data)
        self.logger.debug(msg)

    def info(self, msg):
        data = {
            'module': self.name,
            'level': 'info',
            'message': msg,
            'timestamp': int(time.time()),
        }
        self.queue.put(data)
        self.logger.info(msg)

    def error(self, msg):
        data = {
            'module': self.name,
            'level': 'error',
            'message': msg,
            'timestamp': int(time.time()),
        }
        self.queue.put(data)
        self.logger.error(msg)

    def warn(self, msg):
        data = {
            'module': self.name,
            'level': 'warn',
            'message': msg,
            'timestamp': int(time.time()),
        }
        self.queue.put(data)
        self.logger.warn(msg)

    def critical(self, msg):
        data = {
            'module': self.name,
            'level': 'critical',
            'message': msg,
            'timestamp': int(time.time()),
        }
        self.queue.put(data)
        self.logger.critical(msg)

    def setLevel(self, level):
        self.logger.setLevel(level)


_uiotedge_logger = _Logger(_driver_name)


def _init_logger():
    global _uiotedge_logger
    _uiotedge_logger.start()
    logging.debug('init logger success')


_t_logger = threading.Thread(target=_init_logger)
_t_logger.setDaemon(True)
_t_logger.start()


def getLogger():
    global _uiotedge_logger
    return _uiotedge_logger
