import re
import os


class Tool(object):
    def __init__(
            self, ecosystem, tool, version, platforms, requires, environment,
            optional, source, force_platform=None):
        self.tool = tool
        self.version = version
        self.platforms = platforms
        self.requires = requires
        self.platform = force_platform
        self.source = source
        self.valid = self.platform in self.platforms or \
            not self.platforms or \
            '*' in self.platforms

        self.envs = []
        for key, value in environment.items():
            self.envs.append(
                Variable(
                    tool=self,
                    key=key,
                    value=value
                )
            )

        for requirement, env in optional.items():
            for key, val in env.items():
                self.envs.append(
                    Variable(
                        tool=self,
                        key=key,
                        value=value,
                        requires=requirement
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
    dependency_regexes = [
        re.compile(r"\${\w+}"),
        re.compile(r"\$\w+"),
        re.compile(r"%\w+%"),
    ]

    def __init__(self, tool, key, value, requires=None):
        self.tool = tool
        self.key = key
        self._raw_value = value
        if isinstance(value, dict):
            value = value.get(self.tool.platform, '')
            value = value or self._raw_value.get('*', '')

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
        dependencies = list(set(dependencies))
        return dependencies
