import os
from pprint import pformat
import json
import logging
try:
    os.getuid()
    IS_POSIX = True
except:
    IS_POSIX = False

logger = logging.getLogger(__name__)

default_gid = 1000


class FileHandlerManager(object):
    def __init__(self):
        self.handlers = []

    def register_handler(self, handler):
        self.handlers.insert(0, handler)

    def get_handlers(self):
        unroot_type = type(FileHandlerManager.unroot(lambda: None))

        for handler in self.handlers:
            handler_type = type(handler.read)
            if not handler_type == unroot_type:
                handler.read = FileHandlerManager.unroot(handler.read)
        return self.handlers

    def _get_handler_for_ext(self, ext):
        for handler in self.get_handlers():
            if ext in handler.extensions:
                return handler

    def read(self, path):
        _, extension = os.path.splitext(path)
        handler = self._get_handler_for_ext(extension)
        if not handler:
            logger.debug('No handler found for "%s"' % path)
            return []
        return handler.read(path) or []

    @staticmethod
    def unroot(func):
        if IS_POSIX:
            uid = os.getuid()

        def wrapper(*args, **kwargs):
            if IS_POSIX:
                if os.geteuid() == 0:
                    os.seteuid(default_gid)
            result = None
            try:
                result = func(*args, **kwargs)
            except:
                import traceback
                message = 'Failed reading %s with args %s:\n%s'
                logger.debug(
                    message % (
                        repr(func),
                        pformat(args),
                        traceback.format_exc()
                    )
                )
            if IS_POSIX:
                if os.geteuid() == 0:
                    os.seteuid(uid)
            return result
        return wrapper


class BaseFileHandler(object):
    extensions = []
    name = 'base_filehandler'

    def read(self, path):
        return NotImplemented


class EnvFileHandler(BaseFileHandler):
    extensions = ['.env']
    name = 'env_filehandler'

    def read(self, path):
        with file(path, 'r') as f:
            data = eval(f.read())
        return [data]


class JsonFileHandler(BaseFileHandler):
    extensions = ['.json']
    name = 'json_filehandler'

    def read(self, path):
        with file(path, 'r') as f:
            data = json.load(f)
        return [data]
