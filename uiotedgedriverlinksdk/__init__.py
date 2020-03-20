import time
import logging

loggers = {}
_log_level = logging.INFO


def set_log_level(level=logging.INFO):
    global _log_level
    _log_level = level


def _get_logger(name):
    global loggers
    global _log_level
    if loggers.get(name):
        log = loggers.get(name)
        log.setLevel(_log_level)
        return log
    else:
        logger = logging.getLogger(name)
        logger.setLevel(_log_level)
        ch = logging.StreamHandler()
        ch.setLevel(_log_level)
        formatter = logging.Formatter(
            "%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        loggers[name] = logger

        return logger


def sdk_print(msg):
    _get_logger("uiotedgedriverlinksdk").debug(msg)


def sdk_error(msg):
    _get_logger("uiotedgedriverlinksdk").error(msg)
