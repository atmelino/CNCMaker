#!/bin/bash

# purge
sudo rm cncmaker_0.1.deb
sudo dpkg -P cncmaker

#build
chmod a+x *.py
cp *.py debian/usr/lib/cncmaker
sudo dpkg --build debian
mv debian.deb cncmaker_0.1.deb

#install
sudo apt-get install python-qt4
sudo dpkg -i cncmaker_0.1.deb
sudo chmod 777 cncmaker_0.1.deb

echo to start:
echo call cncmaker.sh




