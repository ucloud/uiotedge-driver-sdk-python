from setuptools import setup
import sys

if not (sys.version_info[0] == 3):
    sys.exit("Link IoT Edge only support Python 3")

setup(
    name='uiotedge_driver_link_sdk',
    version='0.0.1',
    author='ucloud.cn',
    url='https://pypi.org/project/uiotedge_driver_link_sdk/',
    author_email='joy.zhou@ucloud.cn',
    packages=['uiotedgedriverlinksdk'],
    platforms="any",
    license='Apache 2 License',
    install_requires=[
        "asyncio-nats-client>=0.10.0",
        "cachetools>=4.0.0"
    ],
    description="UIoT Edge Driver Link SDK",
    long_description="UIoT Edge Driver Link SDK\n https://www.ucloud.cn/site/product/uiot.html"
)
