from . import EcosystemPlugin
import platform
import subprocess
import os


class RunExtension(EcosystemPlugin):
    name = 'run'

    def initialize(self, ecosystem):
        self.ecosystem = ecosystem
        self.parser = ecosystem.subparser.add_parser(self.name)

        self.parser.add_argument('-t', '--tools', nargs='+')
        self.parser.add_argument('-r', '--run', nargs=1)

    def execute(self, args):
        env = self.get_environment(args)
        if env.success:
            env.getEnv(os.environ)
            self.call_process([args.run])

    @staticmethod
    def call_process(arguments):
        if platform.system().lower() == 'windows':
            subprocess.call(arguments, shell=True)
        else:
            subprocess.call(arguments)


def register(ecosystem):
    run_extension = RunExtension()
    ecosystem.register_extension(run_extension)
