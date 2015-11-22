#!/bin/bash

sudo dpkg --build debian
mv debian.deb cncmaker_0.1.deb
