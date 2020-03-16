#!/bin/bash -e
pip3 install -t . uiotedge_driver_link_sdk #打包驱动SDK
pip3 install -t . websockets #打包自己的依赖
zip -r ws.zip .