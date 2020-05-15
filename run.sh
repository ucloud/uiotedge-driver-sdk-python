#!/bin/bash -e
python3 setup.py check
python3 setup.py build
sudo python3 setup.py install --force
sudo python3 setup.py sdist bdist_wheel || true
sudo python3 -m twine upload dist/*.whl

sudo rm -rf build
sudo rm -rf dist
sudo rm -rf uiotedge_driver_link_sdk.egg-info

