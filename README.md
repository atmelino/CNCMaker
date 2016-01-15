# CNCMaker

A GUI to integrate several Python based utilities that work on G-Code for CNC machines.

All the python files have to be set as executable.

Some of the files require the SciPy stack:

http://www.scipy.org/install.html

sudo apt-get install python-scipy python-numpy, python-scipy, python-tk, python-imaging-tk
sudo apt-get install python-imaging-tk


Debian package:

For simple installation on Linux systems, I have added a script that creates a Debian package: cncmaker_0.1.deb

The way this works is that the files which will be included in the package have to reside in a specific directory structure.

I put these files under the folder named "debian":

debian  
├── DEBIAN  
│   └── control  
└── usr  
    ├── bin  
    │   └── cncmaker.sh  
    ├── lib  
    │   └── cncmaker  
    │       ├── arcgenm18.py  
    │       ├── cad.py  
    │       ├── cncmaker.py  
    │       ├── counterbore.py  
    │       ├── cxf-fonts  
    │       │   └── (lots of files)  
    │       ├── drill.py  
    │       ├── dxf2gcode  
    │       │   └── (lots of files)  
    │       ├── dxfFiles  
    │       │   └── example.dxf  
    │       ├── engrave-11.py  
    │       ├── grid_v1.py  
    │       └── pocket_V1.py  
    └── share  
        ├── applications  
        │   └── cncmaker.desktop  
        ├── cncmaker  
        │   ├── changelog.Debian.gz  
        │   ├── changelog.gz  
        │   └── cncmaker.gif  
        └── pixmaps  
            └── cncmaker.png  


===================================
Improvements:
- The programs require the python-qt4 package. I haven't figured out yet how to make a debian package that requires another package, so for now, I have put the line
sudo apt-get install python-qt4
into the shell script packageCycle.sh.



