import time


def sdk_print(msg):
    print('[driver log]: time={} , msg={}'.format(time.strftime(
        "%Y-%m-%d %H:%M:%S", time.localtime()), msg))
