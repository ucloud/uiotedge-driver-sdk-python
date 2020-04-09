#!/bin/bash -e

if [ -e "./ws.zip" ] ; then
    rm ./ws.zip
fi

mkdir tmp
cp index.py tmp

cd tmp
pip3 install -t . uiotedge_driver_link_sdk==0.0.20 #打包驱动SDK
pip3 install -t . tornado -i https://mirrors.aliyun.com/pypi/simple/ #打包自己的依赖
zip -r ws.zip .

cd ..
cp tmp/ws.zip .
rm -rf tmp

