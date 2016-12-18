import json
import os
import logging

import types
import six

logger = logging.getLogger(__name__)


class FileHandlerManager(object):
    def __init__(self):
        self.file_handlers = {}
        self.register_handler(EnvFileHandler())
        self.register_handler(JsonHandler())
        self.register_handler(PythonHandler())

    def register_handler(self, handler):
        for extension in handler.extensions:
            if self.file_handlers.get(extension):
                logger.warn(
                    'Duplicate handlers for extension "%s"' % extension)
            self.file_handlers[extension] = handler

    def read(self, path):
        extension = os.path.splitext(path)[-1]
        handler = self.file_handlers.get(extension)

        if not handler:
            logger.warn('No handler found for "%s"' % path)
            return

        return handler.read(path) or []


class BaseFileHandler(object):
    extensions = []

    def read_env(self, file_path):
        raise NotImplementedError()

    def read_preset(self, file_path):
        raise NotImplementedError()


class EnvFileHandler(BaseFileHandler):
    extensions = ['.env']

    def read_env(self, path):
        with file(path, 'r') as f:
            return [eval(f.read())]

    def read_preset(self, file_path):
        return self.read_env(file_path)


class JsonHandler(BaseFileHandler):
    extensions = ['.json']

    def read_env(self, file_path):
        with open(file_path, 'r') as f:
            return [json.load(f)]

    def read_preset(self, file_path):
        return self.read_env(file_path)


class PythonHandler(BaseFileHandler):
    extensions = ['.py']

    def read_module(self, file_path):
        name, ext = os.path.splitext(os.path.split(file_path)[-1])

        module = types.ModuleType(name)
        module.__file__ = file_path

        with open(file_path, 'r') as f:
            module = six.exec_(f.read(), module.__dict__)

        return module

    def read_env(self, file_path):
        module = self.read_module(file_path)

        if not hasattr(module, 'get_tools'):
            logger.warn('Env file "%s" does not have "get_tools" function')
            return []

        return module.get_tools()

    def read_preset(self, file_path):
        module = self.read_module(file_path)

        if not hasattr(module, 'get_presets'):
            logger.warn('Preset file "%s" does not have "get_tools" function')
            return []

        return module.get_presets()
