from setuptools import setup
import sys

if not (sys.version_info[0] == 3):
    sys.exit("Link IoT Edge only support Python 3")

setup(
    name='uiotedge_driver_link_sdk',
    version='1.0',
    author='ucloud.cn',
    packages=['uiotedgedriverlinksdk'],
    platforms="any",
    license='Apache 2 License',
    install_requires=[
        "setuptools>=16.0",
        "nats-python>=0.5.0",
        "websockets>=8.0.2"
    ],
    description="UIoT Edge Driver Link SDK"
)
