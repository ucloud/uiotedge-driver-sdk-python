import time


def sdk_print(msg):
    print('[driver log]: time={} , msg={}'.format(time.strftime(
        "%Y-%m-%d %H:%M:%S", time.localtime()), msg))


def sdk_error(msg):
    print('[driver error]: time={} , msg={}'.format(time.strftime(
        "%Y-%m-%d %H:%M:%S", time.localtime()), msg))
