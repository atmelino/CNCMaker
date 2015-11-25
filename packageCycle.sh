#!/bin/bash

# purge
rm cncmaker_0.1.deb
sudo dpkg -P cncmaker

#build
sudo dpkg --build debian
mv debian.deb cncmaker_0.1.deb

#install
sudo dpkg -i cncmaker_0.1.deb

echo to start:
echo call cncmaker.sh




