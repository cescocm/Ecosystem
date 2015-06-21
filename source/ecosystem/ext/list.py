from . import EcosystemPlugin


class ListExtension(EcosystemPlugin):
    name = 'list'

    def initialize(self, ecosystem):
        self.ecosystem = ecosystem

        list_parser = ecosystem.subparser.add_parser(self.name)

        list_parser.add_argument('-v', '--versions', action='store_true')
        list_parser.add_argument('-t', '--tools', action='store_true')
        list_parser.add_argument('-a', '--all', action='store_true')

    def execute(self, args):
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
