import json
import logging as _logger
import sys

_driver_id = ''
_deviceInfos = []
_driverInfo = None
_driver_name = ''

# get Config
_config_path = './etc/uiotedge/config.json'
with open(_config_path, 'r') as load_f:
    try:
        load_dict = json.load(load_f)
        _logger.info(str(load_dict))
        print('----config: {} -------'.format(load_dict))

        _driver_id = load_dict['driverID']

        if 'deviceList' in load_dict.keys():
            _deviceInfos = load_dict['deviceList']

        if 'driverInfo' in load_dict.keys():
            _driverInfo = load_dict['driverInfo']
    except Exception as e:
        _logger.error('load config file error:{}'.format(e))
        sys.exit(1)

_logger.info("dirver_id: {}".format(_driver_id))
