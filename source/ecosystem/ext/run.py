from . import EcosystemPlugin
from .. import environment
import platform
import subprocess
import os


class RunExtension(EcosystemPlugin):
    name = 'run'

    def initialize(self, ecosystem):
        self.ecosystem = ecosystem
        list_parser = ecosystem.subparser.add_parser(self.name)

        list_parser.add_argument('-t', '--tools', nargs='+')
        list_parser.add_argument('-r', '--run', nargs=1)

    def execute(self, args):
        versions = self.ecosystem.get_versions()
        _versions = [x.tool + x.version for x in versions]

        if not args.tools:
            raise RuntimeError('No tools specified')
        not_in_eco = []
        for tool in args.tools:
            if tool not in _versions:
                not_in_eco.append(tool)
        if not_in_eco:
            raise RuntimeError(
                'Some tools cannot be found: %s' % ', '.join(not_in_eco)
            )
        env = environment.Environment(
            [x for x in versions if x.tool + x.version in args.tools]
        )
        if env.success:
            env.getEnv(os.environ)
            call_process([args.run])


def call_process(arguments):
    if platform.system().lower() == 'windows':
        subprocess.call(arguments, shell=True)
    else:
        subprocess.call(arguments)


def register(ecosystem):
    run_extension = RunExtension()
    ecosystem.register_extension(run_extension)
