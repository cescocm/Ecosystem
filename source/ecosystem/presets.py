import os
import logging
import traceback
from ecosystem import errors
import subprocess
import platform

logger = logging.getLogger(__name__)


class PresetManager(object):
    def __init__(self, ecosystem, search_paths=None):
        self.search_paths = search_paths or \
            os.getenv('ECO_PRESET_PATH', '').split(os.pathsep)

        self.ecosystem = ecosystem
        self._presets = {}
        self.discover()

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
                            'default_command': preset['default_command']
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

                    self._presets[preset_object['name']] = preset_object

    def get_preset(self, name):
        preset = self._presets.get(name)
        if not preset:
            raise errors.PresetNotFoundError(
                'Preset "%s" does not exist.' % name
            )

        return Preset(
            ecosystem=self.ecosystem,
            name=preset['name'],
            tools=preset['tools'],
            default_command=preset['default_command']
        )

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

    def run(self, command=None, blocking=True):
        environment = self.get_environment()
        command = command or self.default_command
        if not isinstance(command, (set, list, tuple)):
            command = [command]

        command = map(str, command)

        with environment:
            envs = environment.environ

        if blocking:
            return subprocess.check_output(
                command,
                env=envs,
                shell='win' in platform.system().lower()
            )
        else:
            proc = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stdin=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=envs,
                shell='win' in platform.system().lower()
            )
            return proc

    def get_environment(self):
        return self.ecosystem.get_environment(*self.tools)
