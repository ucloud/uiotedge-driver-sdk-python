import logging
import os
from logging import handlers


class _Logger(object):
    def __init__(self,  filename='', level=logging.INFO, when='D', backCount=3):
        self.logger = logging.getLogger(filename)
        format_str = logging.Formatter(
            '%(asctime)s - %(levelname)s: %(message)s')  # 设置日志格式
        self.logger.setLevel(level)  # 设置日志级别
        sh = logging.StreamHandler()  # 往屏幕上输出
        sh.setFormatter(format_str)  # 设置屏幕上显示的格式
        th = handlers.TimedRotatingFileHandler(
            filename=filename, when=when, backupCount=backCount, encoding='utf-8')  # 往文件里写入#指定间隔时间自动生成文件的处理器
        th.setFormatter(format_str)  # 设置文件里写入的格式
        self.logger.addHandler(sh)  # 把对象加到logger里
        self.logger.addHandler(th)


_driverLogPath = './var/log/uiotedge'
_driverLogName = './var/log/uiotedge/driver.log'
if not os.path.exists(_driverLogPath):
    os.makedirs(_driverLogPath)
if not os.path.isfile(_driverLogName):
    fd = open(_driverLogName, mode='w', encoding='utf-8')
    fd.close()

_uiotedge_logger = _Logger(_driverLogName, level=logging.INFO)


def getLogger():
    global _uiotedge_logger
    return _uiotedge_logger.logger
