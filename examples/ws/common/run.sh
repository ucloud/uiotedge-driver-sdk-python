#!/bin/bash -e
pip3 install -t . uiotedge_driver_link_sdk==0.0.4
pip3 install -t . websockets
zip -r ws.zip .