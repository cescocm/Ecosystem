import re
import os
import copy
import platform


class Environment(object):
    def __init__(self, versions=None):
        self.versions = versions or []

    def resolve(self):
        _environ = copy.deepcopy(os.environ)
        for version in self.versions:
            version.resolve()


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

    def resolve(self):
        variables = [x.key for x in self.variables]
        _variables = copy.deepcopy(self.variables)
        resolved = []
        while _variables:
            variable = _variables.pop(0)
            unresolved = any(
                [x in variables for x in variable.get_dependencies()]
            )
            unresolvable = any(
                [os.environ.get(x) for x in variable.get_dependencies()]
            )
            if unresolved and not unresolvable:
                _variables.append(variable)
                continue
            variable.value = os.path.expandvars(variable.value)
            os.environ[variable.key] = variable.value
            resolved.append(variable)
        self.variables = resolved


class Variable(object):
    dependency_regexes = [
        re.compile(r"\${\w+}"),
        re.compile(r"\$\w+"),
        re.compile(r"%\w+%"),
    ]

    def __init__(self, key, value):
        self.key = key
        self.value = ''

        self.digest_data(value)
        self.dependencies = []
        self.strict = False
        self.absolute = []
        self.get_dependencies()

    def __repr__(self):
        return '<Variable Key: %s, Value: %s>' % (self.key, self.value)

    def digest_data(self, value):
        if isinstance(value, basestring):
            self.value = value

        elif isinstance(value, dict):
            for key, val in value.items():
                if key == platform.system().lower():
                    self.value = val
                elif key == 'strict':
                    self.strict = value.pop(key)
                elif key == 'abs':
                    self.absolute = value.pop(key)
                if isinstance(val, (list, set)):
                    value[key] = os.path.join(*val)
            # self.value = value.get(platform.system(), '')

    def has_dependencies(self, refresh=False):
        if refresh:
            self.get_dependencies()

        return bool(self.dependencies)

    def get_dependencies(self):
        for regex in self.dependency_regexes:
            if not isinstance(self.value, basestring):
                continue
            result = regex.findall(self.value)
            if result:
                self.dependencies += [x.strip('${}%') for x in result]
        self.dependencies = list(set(self.dependencies))
        return self.dependencies
