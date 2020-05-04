import logging
import re
import os


logger = logging.getLogger(__name__)


class Tool(object):
    '''Define a tool - specifically, a version of a tool'''

    def __init__(self, ecosystem, tool, version, platforms, requires, environment,
                 optional, source, wanted_tools, force_platform=None):
        self.tool = tool
        self.version = version
        self.platforms = platforms
        self.requires = requires
        self.optional = optional
        self.platform = force_platform
        self.source = source
        self.wanted_tools = wanted_tools
        self.valid = self.platform in self.platforms or \
            not self.platforms or \
            '*' in self.platforms

        self.envs = []
        # Add all key/values from environment section of json to envs
        for key, value in environment.items():
            self.envs.append(
                Variable(
                    tool=self,
                    key=key,
                    value=value
                )
            )
        # Add filtered key/values from optionals section of json to envs
        for optional_requirement, env in optional.items():
            if optional_requirement in str(self.wanted_tools):
                for key, value in env.items():
                    self.envs.append(
                        Variable(
                            tool=self,
                            key=key,
                            value=value,
                            requires=optional_requirement
                        )
                    )

    def __repr__(self):
        return '<%s.%s "%s%s">' % (
            __name__,
            self.__class__.__name__,
            self.tool, self.version
        )

    @property
    def name(self):
        return self.tool + self.version


class Variable(object):
    '''Define a variable required by a tool'''

    dependency_regexes = [
        re.compile(r"\${\w+}"),
        re.compile(r"\$\w+"),
        re.compile(r"%\w+%"),
    ]

    def __init__(self, tool, key, value, requires=None):
        self.tool = tool
        self.key = key
        self._raw_value = value
        self._mode = 'append'
        if isinstance(value, dict):
            value = self._raw_value.get(self.tool.platform, '')
            value = value or self._raw_value.get('*', '')

            self._mode = self._raw_value.get('mode', self._mode)

        if isinstance(value, (list, tuple, set)):
            value = os.pathsep.join(value)

        self.value = self.format_value(value)

        self.requires = requires
        self.dependencies = self.get_dependencies()

    def __repr__(self):
        return '<%s.%s "%s">' % (
            __name__,
            self.__class__.__name__,
            self.key
        )

    def mode(self):
        return self._mode

    def format_value(self, value):
        format_args = dict(
            tool=self.tool.tool,
            version=self.tool.version,
            platform=self.tool.platform
        )
        return value % format_args

    def get_dependencies(self):
        dependencies = []
        for regex in self.dependency_regexes:
            result = regex.findall(self.value)
            if result:
                dependencies += [x.strip('${}%') for x in result]
        dependencies = list(set([x.upper() for x in dependencies]))
        return dependencies
