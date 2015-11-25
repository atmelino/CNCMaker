#!/bin/bash

sudo cp *.py debian/usr/lib/cncmaker
sudo dpkg --build debian
mv debian.deb cncmaker_0.1.deb
