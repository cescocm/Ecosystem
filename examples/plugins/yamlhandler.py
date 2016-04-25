import yaml
from ecosystem.handlers import BaseFileHandler


class YAMLFileHandler(BaseFileHandler):
    extensions = ['.yaml', '.yml']

    def read_env(self, path):
        with file(path, 'r') as f:
            return [yaml.load(f.read())]

    def read_preset(self, path):
        return self.read_env(path)


def initialize(plugin_manager):
    plugin_manager.register_handler(YAMLFileHandler())
