import logging


def configure_logger(level=logging.INFO):
    logger = logging.getLogger('uiotedgedriverlinksdk')
    logger.setLevel(level)
    ch = logging.StreamHandler()
    ch.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)
