from . import EcosystemPlugin


class ListExtension(EcosystemPlugin):
    name = 'list'

    def initialize(self, ecosystem):
        self.ecosystem = ecosystem

        subparsers = ecosystem.arg_parser.add_subparsers(dest='command')
        list_parser = subparsers.add_parser('list')
        list_parser.add_argument('-v', '--versions', action='store_true')
        list_parser.add_argument('-t', '--tools', action='store_true')
        list_parser.add_argument('-hi', '--hierarchy', action='store_true')

    def execute(self, args):
        if args.versions:
            for version in self.ecosystem.get_versions():
                print version.tool, version.version
        elif args.tools:
            for tool in self.ecosystem.get_tools():
                print tool.name
        elif args.hierarchy:
            for tool in self.ecosystem.get_tools():
                print tool.name
                for version in tool.versions:
                    print '\t%s' % version.version


def register(ecosystem):
    list_extension = ListExtension()
    ecosystem.register_extension(list_extension)
