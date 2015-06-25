# Ecosystem 

## About this fork

This is a prototype to determine what features of this code are valid an useful and which are not. It is meant as a compilation of ideas to improve the original [Ecosystem](https://github.com/PeregrineLabs/Ecosystem).

## Getting Started

To install Ecosystem, you can run

    python setup.py install

After this, if python is fully configured (in Windows *C:\Python2x\Scripts* has to be in the PATH environment variable), the ecosystem executable will be available through command line:

    ecosystem --help

As it is right now, it has a similar functionality to the original [Ecosystem](https://github.com/PeregrineLabs/Ecosystem), but a slighly different syntax:

    ecosystem run -t maya2015 yeti1.3.19 -r maya
    ecosystem list --all

This are the new features:

* **Plugin system** similar to [Flask](http://flask.pocoo.org/), in which any module called "ecosystem_*" will be registered as an ecosytem extension if properly modeled. Some examples of extensions can be found in the [built in extensions](https://github.com/salvaom/Ecosystem/tree/master/source/ecosystem/ext).
* **Dynamic file handlers**, where you can define custom readers for custom extensions, so it's not limited to any file type. An example of file handlers can be found in the [built in file handlers](https://github.com/salvaom/Ecosystem/blob/master/source/ecosystem/filehandlers.py) file. To implement them, the plugin system should be used.


The discussion about this repository can be found at [google groups](https://groups.google.com/forum/#!topic/ecosystem-env/5rpPJPdO4bk).
