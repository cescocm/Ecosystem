import sys
import os
import logging

import abc

logger = logging.getLogger(__name__)


def discover():
    extension_modules = []

    for path in sys.path:
        if not os.path.isdir(path):
            continue
        for module in os.listdir(path):
            if 'egg' in module or 'dist' in module:
                module = module.split('-')[0]
            module = module.split('.')[0]
            if module.startswith('ecosystem_') and not module.startswith('_'):
                extension_modules.append(module)

    return extension_modules


def import_module(module):
    _module = None
    try:
        _module = __import__(module)
    except:
        pass
    return _module


def register_extension(module, ecosystem):
    register_func = getattr(module, 'register', None)
    if register_func and hasattr(register_func, '__call__'):
        register_func(ecosystem)


class EcosystemPlugin(object):
    name = None
    requirements = []

    @abc.abstractmethod
    def initialize(self, ecosystem):
        raise NotImplementedError()

    @abc.abstractmethod
    def execute(self, *args, **kwargs):
        raise NotImplementedError()
