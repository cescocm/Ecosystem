import yaml
from ecosystem.handlers import BaseFileHandler


class YAMLFileHandler(BaseFileHandler):
    extensions = ['.yaml', '.yml']

    def read(self, path):
        print path
        with file(path, 'r') as f:
            return [yaml.load(f.read())]


def initialize(plugin_manager):
    plugin_manager.register_handler(YAMLFileHandler())
