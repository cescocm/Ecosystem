import os
import logging
import traceback

from ecosystem import errors
from ecosystem import utils

logger = logging.getLogger(__name__)


class PresetManager(object):
    def __init__(self, ecosystem, search_paths=None):
        self.search_paths = search_paths or \
            os.getenv('ECO_PRESET_PATH', '').split(os.pathsep)

        self.ecosystem = ecosystem
        self._presets = {}
        self.discover()
        self.expand_presets()

    def discover(self):
        for path in self.search_paths:

            if not os.path.isdir(path):
                logger.debug('Path %s is not a directory. Skipping.' % path)
                continue

            for preset in os.listdir(path):
                preset_path = os.path.join(path, preset)

                if not os.path.isfile(preset_path):
                    continue

                ext = os.path.splitext(preset)[-1]
                handler = self.ecosystem.filehandler.file_handlers.get(ext)

                if not handler:
                    continue

                try:
                    presets = handler.read_preset(preset_path)
                except Exception as e:
                    logger.warn('Could not read "%s": %s' % (preset_path, e))
                    logger.debug(traceback.format_exc())
                    continue

                for preset in presets:
                    try:
                        preset_object = {
                            'name': preset['name'],
                            'tools': preset['tools'],
                            'default_command': preset.get('default_command')
                        }
                    except (IndexError, KeyError) as e:
                        logger.warn(
                            'Unable to load preset "%s": %s' % (preset_path, e)
                        )
                        logger.debug(traceback.format_exc())
                        continue

                    if preset_object['name'] in self._presets:
                        logger.warn(
                            'Overriding preset "%s" with file "%s"' % (
                                preset_object['name'], preset_path
                            )
                        )

                    _preset = Preset(self.ecosystem, **preset_object)
                    self._presets[preset_object['name']] = _preset

    def expand_presets(self):
        sorted_presets = []

        for preset in self._presets.values():
            index = 0
            dependencies = preset.subpresets()
            for i, _preset in reversed(list(enumerate(sorted_presets))):
                if _preset.name in dependencies:
                    index = i + 1

            sorted_presets.insert(index, preset)

        for preset in sorted_presets:
            for dep in preset.subpresets():
                dep_preset = self._presets.get(dep)

                if not dep_preset:
                    logger.warn('Could not find dependency preset "{}" for '
                                'preset "{}"'.format(dep, preset.name))
                    continue

                idx = preset.subpreset_index(dep)
                if not idx:
                    logger.warn('Dependency "{}" of preset "{}" is not of '
                                'format "preset:presetName"'
                                .format(dep, preset.name))
                    continue

                preset_tools = [self.ecosystem.get_tool(x).tool
                                for x in preset.tools
                                if not x.startswith('preset:')]

                preset.tools.pop(idx)
                for tool in reversed(dep_preset.tools):
                    toolobj = self.ecosystem.get_tool(tool)
                    if toolobj.tool in preset_tools:
                        logger.warning(
                            'Duplicate tool "{}" found in preset {} while '
                            'expanding it. Keeping first tool found.'
                            .format(toolobj.tool, preset.name))
                        continue

                    preset.tools.insert(idx, tool)

    def get_preset(self, name):
        preset = self._presets.get(name)
        if not preset:
            raise errors.PresetNotFoundError(
                'Preset "%s" does not exist.' % name
            )

        return preset

    def list_presets(self):
        return sorted(self._presets.keys())


class Preset(object):
    def __init__(self, ecosystem, name, tools, default_command):
        self.ecosystem = ecosystem
        self.name = name
        self.tools = tools
        self.default_command = default_command

    def __repr__(self):
        return '<%s.%s "%s">' % (
            __name__,
            self.__class__.__name__,
            self.name
        )

    def subpreset_index(self, preset):
        for i, tool in enumerate(self.tools):
            if tool.startswith('preset:{}'.format(preset)):
                return i

    def subpresets(self):
        subp = []
        for tool in self.tools:
            if tool.startswith('preset:'):
                subp.append(tool.split(':')[-1])

        return subp

    def run(self, command=None, detached=True):
        environment = self.get_environment()
        command = command or self.default_command

        if not command:
            raise ValueError('No command specified')

        if not isinstance(command, (set, list, tuple)):
            command = [command]

        command = map(str, command)

        with environment:
            envs = environment.environ

        for key, val in envs.items():
            envs[str(key)] = str(val)

        return utils.call_process(command, detached=detached, env=envs)

    def get_environment(self):
        return self.ecosystem.get_environment(*self.tools)


def merge(*presets):
    environment = None
    ecosystems = []
    for preset in presets:
        ecosystems.append(preset.ecosystem)
        if not environment:
            environment = preset.get_environment()
        else:
            environment += preset.get_environment()

    if len(list(set(ecosystems))) != 1:
        raise RuntimeError(
            'Presets do not come from the same Ecosystems instance')

    return environment
