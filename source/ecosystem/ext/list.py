from . import EcosystemPlugin
import argparse


class ListExtension(EcosystemPlugin):
    name = 'list'

    def initialize(self, ecosystem):
        self.ecosystem = ecosystem

        self.parser = argparse.ArgumentParser('eco-%s' % self.name)

        self.parser.add_argument('-v', '--versions', action='store_true')
        self.parser.add_argument('-t', '--tools', action='store_true')
        self.parser.add_argument('-a', '--all', action='store_true')

    def execute(self, args):
        args = self.parser.parse_args(args)
        if not any(vars(args).values()):
            self.parser.error(
                'At least one argument required. '
                'Type --help for a list of all of them.'
            )
        if args.versions:
            for version in self.ecosystem.get_versions():
                print version.tool, version.version
        elif args.tools:
            for tool in self.ecosystem.get_tools():
                print tool.name
        elif args.all:
            for tool in self.ecosystem.get_tools():
                print tool.name
                for version in tool.versions:
                    print '\t%s' % version.version


def register(ecosystem):
    list_extension = ListExtension()
    ecosystem.register_extension(list_extension)
