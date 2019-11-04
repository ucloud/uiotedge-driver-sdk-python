from setuptools import setup
import sys

if not (sys.version_info[0] == 3):
    sys.exit("Link IoT Edge only support Python 3")

setup(
    name='uiotedgethingsdk',
    version='1.0',
    author='ucloud.cn',
    packages=['uiotedgethingsdk'],
    platforms="any",
    license='Apache 2 License',
    install_requires=[
        "setuptools>=16.0",
        "nats-python>=0.5.0",
        "cacheout>=0.11.2",
        "websockets>=8.0.2"
    ],
    description="UIoT Edge Driver Access SDK"
)
