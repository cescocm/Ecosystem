import re
import os


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
            self.values['common'] = value

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
