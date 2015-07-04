from . import EcosystemPlugin
import subprocess
import os
import argparse


class RunExtension(EcosystemPlugin):
    name = 'run'

    def initialize(self, ecosystem):
        self.ecosystem = ecosystem
        self.parser = argparse.ArgumentParser('eco-%s' % self.name)

        self.parser.add_argument('-t', '--tools', nargs='+')
        self.parser.add_argument('-r', '--run')

    def execute(self, args):
        args, extra = self.parser.parse_known_args(args)
        env = self.get_environment(args)

        env.getEnv(os.environ)

        command = [args.run]
        if extra:
            command += extra
        self.call_process(command)

    @staticmethod
    def call_process(arguments):
        if not arguments or arguments[0] is None:
            msg = 'No valid executable command given. Please specify --run.'
            raise RuntimeError(msg)
        subprocess.call(arguments, shell=True)


def register(ecosystem):
    run_extension = RunExtension()
    ecosystem.register_extension(run_extension)
