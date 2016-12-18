import os
import logging
import traceback
import platform
from ecosystem import errors
from ecosystem import handlers
from ecosystem import plugins
from ecosystem import tool as ecotool
from ecosystem import presets

logger = logging.getLogger(__name__)


class Ecosystem(object):
    def __init__(
            self, env_search_paths=None, plugin_searach_paths=None,
            preset_searach_paths=None, force_platform=None):
        self.search_paths = env_search_paths or \
            os.getenv('ECO_ENV', '').split(os.pathsep)

        self.force_platform = force_platform or platform.system().lower()

        self.filehandler = handlers.FileHandlerManager()
        self.pluginmanager = plugins.PluginManager(self, plugin_searach_paths)
        self.presetmanager = presets.PresetManager(self, preset_searach_paths)
        self._tools = {}
        self.discover()

    def discover(self):
        for path in self.search_paths:

            if not os.path.isdir(path):
                logger.debug('Path %s is not a directory. Skipping.' % path)
                continue

            for envfile in os.listdir(path):
                envfile_path = os.path.join(path, envfile)
                if not os.path.isfile(envfile_path):
                    continue

                ext = os.path.splitext(envfile)[-1]
                handler = self.filehandler.file_handlers.get(ext)

                if not handler:
                    continue

                try:
                    tools = handler.read_env(envfile_path)
                except Exception as e:
                    logger.warn('Could not read "%s": %s' % (envfile_path, e))
                    logger.debug(traceback.format_exc())
                    continue

                for _tool in tools:
                    try:
                        _tool = ecotool.Tool(
                            ecosystem=self,
                            tool=_tool['tool'],
                            version=_tool['version'],
                            platforms=_tool.get('platforms', '*'),
                            requires=_tool.get('requires', []),
                            environment=_tool['environment'],
                            optional=_tool.get('optional', {}),
                            force_platform=self.force_platform,
                            source=envfile_path
                        )
                        if not _tool.valid:
                            message = (
                                'Skipping tool "%s": '
                                'not supported for platform "%s"'
                            )
                            logger.debug(message % (
                                _tool.name, self.force_platform))
                            continue

                    except Exception as e:
                        logger.warn(
                            'Could not load env file "%s": %s.' % (
                                envfile_path, e)
                        )
                        logger.debug(traceback.format_exc())
                        continue

                    if self._tools.get(_tool.name):
                        logger.warn(
                            'Overriding duplicate tool "%s"' % _tool.name)

                    self._tools[_tool.name] = _tool

    def get_tool(self, tool):
        _tool = self._tools.get(tool)
        if not _tool:
            raise errors.ToolNotFoundError('Tool %s does not exist.' % tool)

        return _tool

    def list_tools(self):
        return sorted(self._tools.keys())

    def list_presets(self):
        return self.presetmanager.list_presets()

    def get_environment(self, *tools):
        _tools = []
        for tool in tools:
            _tools.append(self.get_tool(tool))

        env = Environment(self, *_tools)
        return env

    def get_preset(self, name):
        return self.presetmanager.get_preset(name)


class Environment(object):
    def __init__(self, ecosystem, *tools):
        self.tools = tools
        self.ecosystem = ecosystem

    def __repr__(self):
        return '<%s.%s "%s">' % (
            __name__,
            self.__class__.__name__,
            ', '.join([x.name for x in self.tools])
        )

    def __enter__(self):
        self._previous_environment = dict()
        self._previous_environment.update(os.environ)

        self.environ = self.resolve()

        return self

    def __exit__(self, exception_type, exception_val, trace):
        os.environ.clear()
        os.environ.update(self._previous_environment)

    def __add__(self, other):
        if not isinstance(other, Environment):
            raise TypeError('Can only be added to other Environment objects.')

        return Environment(self.ecosystem, self.tools + other.tools)

    def __radd__(self, other):
        if not isinstance(other, Environment):
            raise TypeError('Can only be added to other Environment objects.')

        self.tools += other.tools
        return self

    def __sub__(self, other):
        if not isinstance(other, Environment):
            raise TypeError('Can only be added to other Environment objects.')

        return Environment(self.ecosystem, self.tools - other.tools)

    def __rsub__(self, other):
        if not isinstance(other, Environment):
            raise TypeError('Can only be added to other Environment objects.')

        self.tools -= other.tools
        return self

    def resolve(self):
        self.check_requirements()

        variables = []

        for tool in self.tools:
            for var in self.sort_by_dependency(tool.envs):
                variables.append(var)

        var_keys = [x.key for x in variables]

        for curr_var in variables:

            for dependency in curr_var.get_dependencies():
                if dependency not in var_keys + os.environ.keys():
                    raise errors.MissingDependencyError(
                        'Variable "%s" of tool "%s" cannot be resolved: '
                        'Environment "%s" is missing' % (
                            curr_var.key,
                            curr_var.tool.name,
                            dependency
                        )
                    )

            prev = os.environ.get(curr_var.key, '')
            prev = [x for x in prev.split(os.pathsep) if x]
            prev.append(curr_var.value)
            os.environ[str(curr_var.key)] = str(os.pathsep.join(prev))

        for i in range(3):
            for env_name, env_value in os.environ.iteritems():
                os.environ[env_name] = os.path.expandvars(env_value)

        environ = dict()
        environ.update(os.environ)
        return environ

    def sort_by_dependency(self, variables):
        return sorted(variables, key=lambda x: len(x.dependencies))

    def check_requirements(self):
        tool_names = [x.tool for x in self.tools]
        for tool in self.tools:
            for requirement in tool.requires:
                if requirement not in tool_names:
                    raise errors.MissingRequirementError(
                        'Tool "%s" misses requirement "%s"' % (
                            tool.name, requirement)
                    )

    def get_environ(self):
        with self:
            return self.environ
