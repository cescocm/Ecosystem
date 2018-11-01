#!/usr/bin/env python
import os
import re
from setuptools import setup, find_packages


ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
init_path = os.path.join(ROOT_PATH, 'source', 'ecosystem', '__init__.py')


with open(init_path) as f:
    contents = f.read()
    VERSION = re.match(r'.*__version__ = \'(.*?)\'', contents, re.DOTALL)
    VERSION = VERSION.group(1)

setup(
    name='Ecosystem',
    version=VERSION,
    description='Cross-platform environment management system',
    url='https://github.com/PeregrineLabs/Ecosystem',
    author='Peregrine Labs',
    author_email='contact@peregrinelabs.com',
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
