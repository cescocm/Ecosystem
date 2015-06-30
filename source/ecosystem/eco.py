import platform
import os
import logging
import filehandlers
import argparse
import ext
import environment

logger = logging.getLogger(__name__)


class Ecosystem(object):
    def __init__(self, operative_system=None):
        self.operative_system = operative_system or platform.system()
        self.filehandler_manager = filehandlers.FileHandlerManager()
        self.register_handler(filehandlers.EnvFileHandler())
        self.register_handler(filehandlers.JsonFileHandler())

        self.arg_parser = argparse.ArgumentParser(prog='Ecosystem')
        self.subparser = self.arg_parser.add_subparsers(dest='command')
        self.extensions = {}

        self.discover_extensions()

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

    def get_versions(self):
        versions = []
        for env_file in self.scan_envs():
            data = self.filehandler_manager.read(env_file)
            for version in data:
                version = environment.Version(version)
                if version.plaformSupported():
                    versions.append(version)
        return versions

    def get_tools(self):
        versions = self.get_versions()
        tools = {}
        for version in versions:
            tool = version.tool
            if tool not in tools:
                tools[tool] = environment.Tool(tool)
            tools[tool].versions.append(version)

        return tools.values()

    def discover_extensions(self):
        import ecosystem.ext.list
        import ecosystem.ext.run
        import ecosystem.ext.build
        ecosystem.ext.register_extension(ecosystem.ext.list, self)
        ecosystem.ext.register_extension(ecosystem.ext.run, self)
        ecosystem.ext.register_extension(ecosystem.ext.build, self)

        extensions = ext.discover()
        for extension in extensions:
            module = ext.import_module(extension)
            ext.register_extension(module, self)

    def register_extension(self, extension):
        self.extensions[extension.name] = extension
        extension.initialize(self)

    def execute_args(self, args):
        command = getattr(args, 'command', None)
        if command:
            extension = self.extensions.get(command)
            if not extension:
                raise ValueError('Extension %s not found' % command)
            extension.execute(args)
