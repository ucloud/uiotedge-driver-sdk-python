#!/bin/bash -e
python3 setup.py check
python3 setup.py build
sudo python3 setup.py install --force
#sudo python3 setup.py sdist upload -r pypi