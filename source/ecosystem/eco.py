import os
import platform
import logging
import filehandlers

logger = logging.getLogger(__name__)


class Ecosystem(object):
    def __init__(self, operative_system=None):
        self.operative_system = operative_system or platform.system()
        self.filehandler_manager = filehandlers.base.FileHandlerManager()
        self.register_handler(filehandlers.base.EnvFileHandler())

    def scan_envs(self):
        all_files = []
        for path in os.getenv('ECO_ENV', '').split(os.pathsep):
            if not os.path.isdir(path):
                logger.debug('Skipping invalid scan path "%s"' % path)
                continue
            files = [os.path.join(path, x) for x in os.listdir(path)]
            all_files += files

        return all_files

    def register_handler(self, handler):
        self.filehandler_manager.register_handler(handler)


class Tool(object):
    def __init__(self, data):
        self.name = None
        self.versions = []


class Variable(object):
    def __init__(self, data):
        pass

a = Ecosystem()
b = a.scan_envs()
print a.filehandler_manager.read(b[0])
