#!/usr/bin/env python
from setuptools import setup, find_packages
import os

setup(
    name='Ecosystem',
    version='0.5.5',
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
    },
)
