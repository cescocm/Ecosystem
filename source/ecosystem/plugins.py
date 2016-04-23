import os
import imp
import logging
import sys
import traceback

logger = logging.getLogger(__name__)


class PluginManager(object):
    def __init__(self, ecosystem, search_paths=None):
        self.search_paths = search_paths or \
            os.getenv('ECO_PLUGIN_PATH', '').split(os.pathsep)

        self.ecosystem = ecosystem
        self.discover()

    def discover(self):
        if not any(self.search_paths):
            return
        for path in self.search_paths:
            if not os.path.isdir(path):
                logger.warn('Path %s is not a directory. Skipping.' % path)
                continue

            for plugin in os.listdir(path):
                plugin_path = os.path.join(path, plugin)
                if not os.path.isfile(plugin_path):
                    continue

                name, ext = os.path.splitext(plugin)

                if not ext == '.py':
                    continue

                if sys.version_info[0] == 2:
                    try:
                        module = imp.load_source(name, plugin_path)
                    except Exception as e:
                        logger.warn(
                            'Could not load plugin "%s": %s' % (plugin_path, e)
                        )
                        logger.debug(traceback.format_exc())
                        continue
                else:
                    raise NotImplementedError('Python 3 not supported.')

                if not hasattr(module, 'initialize'):
                    logger.warn(
                        'Plugin "%s" does not have "initialize" function' %
                        plugin_path
                    )
                    continue

                try:
                    module.initialize(self)
                except Exception as e:
                    logger.warn(
                        'Could not initialize plugin "%s": %s' %
                        (plugin_path, e)
                    )
                    logger.debug(traceback.format_exc())

    def register_handler(self, handler):
        self.ecosystem.filehandler.register_handler(handler)
