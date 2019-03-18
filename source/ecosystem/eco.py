import os
import logging
import traceback
import platform
import collections
import json
import tempfile

from ecosystem import errors
from ecosystem import handlers
from ecosystem import plugins
from ecosystem import tool as ecotool
from ecosystem import presets

logger = logging.getLogger(__name__)

try:
    basestring
except NameError:
    basestring = str


class Ecosystem(object):
    def __init__(
            self, env_search_paths=None, plugin_searach_paths=None,
            preset_search_paths=None, force_platform=None,
            normalize_paths=False):
        self.search_paths = env_search_paths or \
            os.getenv('ECO_ENV', '').split(os.pathsep)

        self.force_platform = force_platform or platform.system().lower()

        self._tools = {}
        self.filehandler = handlers.FileHandlerManager()
        self.discover()
        self.pluginmanager = plugins.PluginManager(self, plugin_searach_paths)
        self.presetmanager = presets.PresetManager(self, preset_search_paths)
        self._normalize_paths = normalize_paths

    def discover(self, append=False):
        if not append:
            self._tools = {}

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
                        versions = _tool['version']
                    except IndexError:
                        logger.warn(
                            'Tool from "%s" does not have any version.' %
                            envfile_path
                        )
                        continue

                    if isinstance(versions, basestring):
                        versions = [versions]

                    for version in versions:
                        try:
                            tool_obj = ecotool.Tool(
                                ecosystem=self,
                                tool=_tool['tool'],
                                version=version,
                                platforms=_tool.get('platforms', '*'),
                                requires=_tool.get('requires', []),
                                environment=_tool['environment'],
                                optional=_tool.get('optional', {}),
                                force_platform=self.force_platform,
                                source=envfile_path
                            )
                            if not tool_obj.valid:
                                message = (
                                    'Skipping tool "%s": '
                                    'not supported for platform "%s"'
                                )
                                logger.debug(message % (
                                    tool_obj.name, self.force_platform))
                                continue

                        except Exception as e:
                            logger.warn(
                                'Could not load env file "%s": %s.' % (
                                    envfile_path, e)
                            )
                            logger.debug(traceback.format_exc())
                            continue

                        if self._tools.get(tool_obj.name):
                            logger.debug(
                                'Overriding duplicate tool "%s"' %
                                tool_obj.name
                            )

                        self._tools[tool_obj.name] = tool_obj

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
            if tool.startswith('preset:'):
                preset = self.get_preset(tool.replace('preset:', ''))
                for ptool in preset.tools:
                    _tools.append(self.get_tool(ptool))
            else:
                _tools.append(self.get_tool(tool))

        env = Environment(self, *_tools)
        return env

    def get_preset(self, name):
        return self.presetmanager.get_preset(name)


class Environment(object):
    def __init__(self, ecosystem, *tools):
        self.tools = tools
        self.ecosystem = ecosystem
        self._normalize_paths = False

    def setPathNormalization(self, value):
        self._normalize_paths = value

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

        tools = self.tools + other.tools
        return Environment(self.ecosystem, *tools)

    def __radd__(self, other):
        if not isinstance(other, Environment):
            raise TypeError('Can only be added to other Environment objects.')

        self.tools += other.tools
        return self

    def __sub__(self, other):
        if not isinstance(other, Environment):
            raise TypeError(
                'Can only be subtracted to other Environment objects.')

        tools = [x for x in self.tools if x not in other.tools]
        return Environment(self.ecosystem, *tools)

    def __rsub__(self, other):
        if not isinstance(other, Environment):
            raise TypeError(
                'Can only be subtracted to other Environment objects.')

        self.tools = [x for x in self.tools if x not in other.tools]
        return self

    def remove_duplicates(self):
        tooldict = collections.OrderedDict()
        for tool in self.tools:
            if tool.tool in tooldict:
                logger.debug(
                    ('Duplicate tool "{}" found environment. '
                     'Using exiting tool "{}"'
                     ).format(tool.name, tooldict[tool.tool].name)
                )
                continue

            tooldict[tool.tool] = tool

        self.tools = tooldict.values()

    def _serializable_environ(self):
        environ = {}

        for key, val in os.environ.items():
            environ[str(key)] = str(val)
        return environ

    def resolve(self, store_previous=True):
        self.check_requirements()

        variables = []

        for tool in self.tools:
            for var in self.sort_by_dependency(tool.envs):
                variables.append(var)

        var_keys = [x.key.upper() for x in variables]

        if store_previous:
            destination = tempfile.NamedTemporaryFile(suffix='.json',
                                                      prefix='ecosystem.dump.',
                                                      delete=False)
            with open(destination.name, 'w') as f:
                json.dump(self._serializable_environ(), f, indent=4)

            os.environ['ECO_PREVIOUS_ENV'] = destination.name

        for curr_var in variables:

            for dependency in curr_var.get_dependencies():
                if dependency not in var_keys + list(os.environ.keys()):
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
            if self._normalize_paths:
                prev = [os.path.normpath(x) for x in prev]

            if curr_var.mode() == 'append':
                prev.append(curr_var.value)
            elif curr_var.mode() == 'prepend':
                prev.insert(0, curr_var.value)
            elif curr_var.mode() == 'expand':
                prev = [os.path.expandvars(curr_var.value)]
            else:
                raise ValueError('Variable "{}" has an unsupported mode "{}"'
                                 .format(curr_var.key, curr_var.mode()))

            os.environ[str(curr_var.key)] = str(os.pathsep.join(prev))

        for i in range(3):
            for env_name, env_value in os.environ.items():
                os.environ[env_name] = os.path.expandvars(env_value)

        tools = os.pathsep.join([x.name for x in self.tools])
        os.environ['ECO_SESSION_TOOLS'] = str(tools)

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
