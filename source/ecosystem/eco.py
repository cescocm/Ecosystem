import os
import logging
import traceback
import platform
from ecosystem import errors
from ecosystem import handlers
from ecosystem import plugins
from ecosystem import tool as ecotool

logger = logging.getLogger(__name__)


class Ecosystem(object):
    def __init__(self, search_paths=None, force_platform=None):
        self.search_paths = search_paths or \
            os.getenv('ECO_ENV', '').split(os.pathsep)

        self.force_platform = force_platform or platform.system().lower()

        self.filehandler = handlers.FileHandlerManager()
        self.pluginmanager = plugins.PluginManager(self)
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
                    tools = handler.read(envfile_path)
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
            raise errors.InvalidTool('Tool %s does not exist.' % tool)

        return _tool

    def list_tools(self):
        return sorted(self._tools.keys())


class Environment(object):
    def __init__(self, *tools):
        self.tools = tools
        self.tool_names = [x.tool for x in self.tools]

    def __repr__(self):
        return '<%s.%s "%s">' % (
            __name__,
            self.__class__.__name__,
            ', '.join([x.name for x in self.tools])
        )

    def __enter__(self):
        self._previous_environment = dict()
        self._previous_environment.update(os.environ)

        self.resolve()

        return self

    def __exit__(self, exception_type, exception_val, trace):
        os.environ.clear()
        os.environ.update(self._previous_environment)

    def resolve(self):
        sorted_tools = self.sort_by_requirement()

        variables = []

        for tool in sorted_tools:
            for var in self.sort_by_dependency(tool.envs):
                if var.requires and var.requires not in self.tool_names:
                    continue
                variables.append(var)

        var_keys = [x.key for x in variables]

        while variables:
            curr_var = variables.pop(0)

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

            curr_var.value = os.path.expandvars(curr_var.value)

            if len(curr_var.get_dependencies()) == 0:
                prev = os.environ.get(curr_var.key, '')
                prev = [x for x in prev.split(os.pathsep) if x]
                prev.append(curr_var.value)
                os.environ[curr_var.key] = os.pathsep.join(prev)
                continue
            else:
                variables.append(curr_var)

        environ = dict()
        environ.update(os.environ)
        return environ

    def sort_by_dependency(self, variables):
        return sorted(variables, key=lambda x: len(x.dependencies))

    def sort_by_requirement(self):
        requirement_list = []
        for tool in self.tools:
            for requirement in tool.requires:
                if requirement not in self.tool_names:
                    raise errors.MissingRequirementError(
                        'Tool "%s" misses requirement "%s"' % (
                            tool.name, requirement)
                    )
            requirement_list.append([tool, len(tool.requires)])

        requirement_list = sorted(requirement_list, key=lambda x: x[1])
        requirement_list = [x[0] for x in requirement_list]
        return requirement_list
