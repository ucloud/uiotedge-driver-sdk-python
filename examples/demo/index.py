import json
import logging
import time

from uiotedgedriverlinksdk import getLogger
from uiotedgedriverlinksdk.client import Config, SubDevice
from uiotedgedriverlinksdk.exception import BaseEdgeException

logging.getLogger().setLevel(logging.DEBUG)
# 配置log
log = getLogger()
log.setLevel(logging.DEBUG)

# 主函数
if __name__ == "__main__":
    try:
        # 获取驱动及子设备配置信息
        driverConfig = Config().getDriverInfo()
        log.info('driver config:{}'.format(driverConfig))

        # 从驱动配置获取设备数据上报周期
        uploadPeriod = 5
        if "period" in driverConfig.keys() and isinstance(driverConfig['period'], int):
            uploadPeriod = int(driverConfig['period'])

        deviceInfoList = Config().getDeviceInfos()
        log.info('device list config:{}'.format(deviceInfoList))
    except Exception as e:
        log.error('load driver config error: {}'.format(str(e)))
        exit(1)

    try:
        # 判断是否绑定子设备
        if len(deviceInfoList) < 1:
            log.error(
                'subdevice null, please bind sub device for dirver')
            while True:
                time.sleep(60)

        # 取其中一个子设备
        subDeviceInfo = deviceInfoList[0]

        # 获取子设备的ProductSN ，key值为 ‘productSN’
        productSN = subDeviceInfo['productSN']
        # 获取子设备的DeviceSN ，key值为 ‘deviceSN’
        deviceSN = subDeviceInfo['deviceSN']

        def callback(topic: str, payload: b''):
            log.info("recv message from {} : {}".format(topic, str(payload)))

        # 初始化一个子设备对象
        subDevice = SubDevice(product_sn=productSN,
                              device_sn=deviceSN, on_msg_callback=callback)
        # 子设备上线
        subDevice.login()

        # 获取当前子设备的配置
        deviceConfig = subDeviceInfo['config']
        log.info('sub device config:{}'.format(deviceConfig))

        # 从子设备配置获取子设备上报topic定义
        topic = "/{}/{}/upload".format(productSN, deviceSN)  # 此处为默认topic
        if 'topic' in deviceConfig and isinstance(deviceConfig['topic'], str):
            topic = deviceConfig['topic'].format(productSN, deviceSN)

        # 从子设备配置获取子设备上报参数名称
        param = 'RelayStatus'  # 此处定义默认属性名称： RelayStatus
        if 'paramName' in deviceConfig and isinstance(deviceConfig['paramName'], str):
            param = deviceConfig['paramName']

        i = 0
        while True:
            relayStatus = ("on", "off")[i % 2 == 0]
            payload = {
                "timestamp": time.time(),
                param: relayStatus
            }
            byts = json.dumps(payload).encode('utf-8')

            subDevice.publish(topic, byts)
            log.info("upload {} : {}".format(topic, str(byts)))

            time.sleep(uploadPeriod)
            i = i+1

    except BaseEdgeException:
        log.error('Edge Exception: {}'.format(str(e)))
    except Exception as e:
        log.error('Exception error: {}'.format(str(e)))
