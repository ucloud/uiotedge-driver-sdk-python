#!/bin/bash -e
pip3 install -t . uiotedge_driver_link_sdk==0.0.4 #打包驱动SDK
pip3 install -t . websockets #打包自己的依赖
zip -r ws.zip .