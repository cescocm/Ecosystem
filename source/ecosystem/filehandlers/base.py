import os
import logging
from pprint import pformat

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
        uid = os.getuid()

        def wrapper(*args, **kwargs):
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

# a = EnvFileHandler()
# a.name = 'foo'
# b = EnvFileHandler()
# b.read = FileHandlerManager.unroot(b.read)
# fm = FileHandlerManager()
# fm.register_handler(a)
# fm.register_handler(b)
# fm.get_handlers()
