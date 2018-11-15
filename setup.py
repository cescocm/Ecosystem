#!/usr/bin/env python
import os
import imp
from setuptools import setup, find_packages


version_file = os.path.abspath('source/ecosystem/__init__.py')
version_mod = imp.load_source('ecosystem', version_file)


setup(
    name='ecosystemS',
    version=version_mod.__version__,
    packages=find_packages(os.path.join(os.path.dirname(__file__), 'source')),
    package_dir={
        '': 'source'
    },
    entry_points={
        'console_scripts': [
            'ecosystem = ecosystem.__main__:main',
        ],
        'gui_scripts': [
            'ecosystemw = ecosystem.__main__:main'
        ]
    },
)
