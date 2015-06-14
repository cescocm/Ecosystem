import platform
import os
import re
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

    def get_versions(self):
        versions = []
        for env_file in self.scan_envs():
            data = self.filehandler_manager.read(env_file)
            for version in data:
                version = Version(version)
                if version.is_valid():
                    versions.append(version)
        return versions

    def get_tools(self):
        versions = self.get_versions()
        tools = {}
        for version in versions:
            tool = version.tool
            if tool not in tools:
                tools[tool] = Tool(tool)
            tools[tool].versions.append(version)

        return tools.values()


class Tool(object):
    def __init__(self, name, versions=None):
        self.name = name
        self.versions = versions or []

    def __repr__(self):
        return '<Tool %s>' % self.name


class Version(object):
    def __init__(self, data):
        self.tool = data.get('tool')
        self.version = data.get('version')
        self.platforms = data.get('platforms', [])
        self.requirements = data.get('requirements', [])
        self._environment = data.get('environment', {})
        self.variables = []
        self.digest_variables(self._environment)

        self._valid = False
        if all([self.tool, self.version, self.variables]):
            self._valid = True

    def __repr__(self):
        return '<Version %s v%s>' % (self.tool, self.version)

    def is_valid(self):
        return self._valid

    def digest_variables(self, environment):
        for key, val in environment.items():
            self.variables.append(Variable(key, val))


class Variable(object):
    dependency_regexes = [
        re.compile(r"\${\w+}"),
        re.compile(r"\$\w+"),
        re.compile(r"%\w+%"),
    ]

    def __init__(self, key, value):
        self.key = key
        self.values = {
            'windows': '',
            'linux': '',
            'darwin': '',
            'common': ''
        }

        self.dependencies = []
        self.digest_data(value)
        self.get_dependencies()

    def digest_data(self, value):
        if isinstance(value, basestring):
            for key, val in self.values.items():
                self.values[key] = value

        elif isinstance(value, dict):
            for key, val in value.items():
                if isinstance(val, (list, set)):
                    value[key] = os.path.join(*val)
            self.values.update(value)

    def has_dependencies(self):
        return bool(self.dependencies)

    def get_dependencies(self):
        for key, val in self.values.items():
            for regex in self.dependency_regexes:
                if not isinstance(val, basestring):
                    continue
                result = regex.findall(val)
                if result:
                    self.dependencies += [x.strip('${}%') for x in result]
        self.dependencies = list(set(self.dependencies))
        return self.dependencies

a = Ecosystem()
b = a.scan_envs()
for tool in a.get_tools():
    print tool.name
    for version in tool.versions:
        print '\t%s' % version.version
        for variable in version.variables:
            print '\t\t', variable.key, variable.values
