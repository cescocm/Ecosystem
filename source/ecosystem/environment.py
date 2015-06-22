import os
import platform
import re
import logging

logger = logging.getLogger(__name__)


class Environment:
    """Once initialized this will represent the environment defined by the
    wanted tools"""
    def __init__(self, versions, environmentDirectory=None, force=False):
        self.versions = versions
        self.variables = {}
        self.success = True
        self.force = force

        if not self.versions:
            self.success = False

        for tool in self.versions:
            tool.getVars(self)

        # check and see if any of the variables dependencies are defined
        # locally to the tool or are considered external
        ext_dependencies = []
        for name, var in self.variables.iteritems():
            if var.dependencies:
                for dep in var.dependencies:
                    if dep not in self.variables:
                        if dep not in ext_dependencies:
                            ext_dependencies.append(dep)
                    else:
                        self.variables[dep].dependents.append(name)

        # now check to see if they're already set in the environment
        missing_dependencies = []
        for dep in ext_dependencies:
            if not os.getenv(dep):
                missing_dependencies.append(dep)

        missing_dependencies = set(missing_dependencies)

        if len(missing_dependencies) > 0:
            missing_vars = str()
            for missing_var in missing_dependencies:
                if len(missing_vars) > 0:
                    missing_vars += ', '
                missing_vars += missing_var

            msg = (
                'Unable to resolve all of the required variables (%s is '
                'missing), please check your list and try again!'
            )
            logger.error(msg % missing_vars)
            self.success = False

    def getVar(self, var):
        if self.success:
            if var.name not in self.defined_variables:
                for dependency in var.dependencies:
                    if dependency in self.variables:
                        self.getVar(self.variables[dependency])
                var_value = var.getEnv()
                self.value = '%ssetenv %s %s' % (
                    self.value,
                    var.name,
                    var_value
                )
                if os.getenv(var.name):
                    if not self.force and not var.strict:
                        if var_value == '':
                            self.value = self.value + '${' + var.name + '}'
                        else:
                            self.value = '%s%s${%s}' % (
                                self.value,
                                os.pathsep,
                                var.name
                            )
                self.value = self.value + '\n'
                self.defined_variables.append(var.name)

    def getVarEnv(self, var):
        if self.success:
            if var.name not in self.defined_variables:
                for dependency in var.dependencies:
                    if dependency in self.variables:
                        self.getVarEnv(self.variables[dependency])
                var_value = var.getEnv()
                if var.name in os.environ:
                    if not self.force and not var.strict:
                        if var_value == '':
                            var_value = os.environ[var.name]
                        else:
                            var_value = os.pathsep.join(
                                [var_value, os.environ[var.name]]
                            )
                self.defined_variables.append(var.name)
                os.environ[var.name] = var_value

    def getEnv(self, SetEnvironment=False):
        # Combine all of the variable in all the tools based on a
        # dependency list
        if self.success:
            self.defined_variables = []
            self.value = '#Environment created via Ecosystem\n'

            for var_name, variable in self.variables.iteritems():
                if self.variables[var_name].hasValue():
                    if not SetEnvironment:
                        self.getVar(variable)
                    else:
                        self.getVarEnv(variable)

            if not SetEnvironment:
                return self.value

            for env_name, env_value in os.environ.iteritems():
                os.environ[env_name] = os.path.expandvars(env_value)
            for env_name, env_value in os.environ.iteritems():
                os.environ[env_name] = os.path.expandvars(env_value)


class Tool(object):
    def __init__(self, name, versions=None):
        self.name = name
        self.versions = versions or []

    def __repr__(self):
        return '<Tool %s>' % self.name


class Version:
    """Defines a tool - more specifically, a version of a tool"""
    def __init__(self, data):
        self.in_dictionary = data

        if (self.in_dictionary):
            self.tool = self.in_dictionary['tool']
            self.version = self.in_dictionary['version']
            self.platforms = self.in_dictionary['platforms']
            self.requirements = self.in_dictionary['requires']

    def getVars(self, env):
        for name, value in self.in_dictionary['environment'].iteritems():
            if name not in env.variables:
                env.variables[name] = Variable(name)
            env.variables[name].appendValue(value)

        # check for optional parameters
        if 'optional' in self.in_dictionary:
            for optional_name, optional_value in self.in_dictionary['optional'].iteritems():
                if optional_name in env.versions:
                    for name, value in optional_value.iteritems():
                        if name not in env.variables:
                            env.variables[name] = Variable(name)
                        env.variables[name].appendValue(value)

    """Check to see if the tool is supported on the current platform"""
    def plaformSupported(self):
        if (self.platforms):
            if (platform.system().lower() in self.platforms):
                return True
        return False

    """Checks to see if this tool defines the given variables"""
    def definesVariable(self, var):
        if var in self.variables:
            return True
        return False


class Variable:
    """Defines a variable required by a tool"""
    def __init__(self, name):
        self.name = name
        self.dependency_re = None
        self.dependents = []
        self.values = []
        self.dependencies = []
        self.strict = False
        self.absolute = False

    """Sets and/or appends a value to the Variable"""
    def appendValue(self, value):
        # Check to see if the value is platform dependent
        platform_value = None
        if (type(value) == dict):
            if ('common' in value):
                platform_value = value['common']

            if (platform.system().lower() in value):
                platform_value = value[platform.system().lower()]

        else:
            platform_value = value

        if(type(value) == dict):
            if ('strict' in value):
                self.strict = value['strict']
            elif ('abs' in value):
                if(type(value['abs']) == list):
                    if(platform.system().lower() in value['abs']):
                        self.absolute = True
                else:
                    self.absolute = value['abs']

        if (platform_value):
            if platform_value not in self.values:
                self.values.append(platform_value)
                var_dependencies = self.checkForDependencies(platform_value)
                if (var_dependencies):
                    for var_dependency in var_dependencies:
                        if var_dependency not in self.dependencies:
                            self.dependencies.append(var_dependency)

    def checkForDependencies(self, value):
        """Checks the value to see if it has any dependency on other Variables,
        returning them in a list"""
        if not self.dependency_re:
            self.dependency_re = re.compile(r"\${\w*}")

        matched = self.dependency_re.findall(value)
        if matched:
            dependencies = []
            for match in matched:
                dependency = match[2:-1]
                if (dependency != self.name):
                    if dependency not in dependencies:
                        dependencies.append(dependency)
            return dependencies
        else:
            return None

    def hasValue(self):
        if len(self.values) > 0:
            return True
        return False

    def getEnv(self):
        value = ''
        count = 0
        for var_value in self.values:
            if count != 0:
                value = value + os.pathsep
            if self.absolute:
                var_value = os.path.abspath(var_value)
            value = value + var_value
            count = count + 1
        return value
