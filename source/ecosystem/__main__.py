import sys
import argparse
from ecosystem import Ecosystem, Environment
import subprocess
import platform
import logging

logger = logging.getLogger('ecosystem')
levels = {
    'info': logging.INFO,
    'warning': logging.WARNING,
    'debug': logging.DEBUG
}


def main(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(prog='ecosystem')

    list_grp = parser.add_argument_group('list')
    list_grp.add_argument('-l', '--list', action='store_true', default=False)

    run_grp = parser.add_argument_group('run')
    run_grp.add_argument('-t', '--tools', nargs='+')
    run_grp.add_argument('-r', '--run', nargs=1)

    common_grp = parser.add_argument_group('common')
    common_grp.add_argument('--verbosity', type=str, default='info')

    args, extra = parser.parse_known_args(args)
    logger.setLevel(levels.get(args.verbosity, logging.INFO))

    eco = Ecosystem()

    if args.list:
        sys.stdout.write('\n'.join(eco.list_tools()))
        return

    if args.run:

        tools = []
        for tool in args.tools:
            tools.append(eco.get_tool(tool))
        env = Environment(*tools)

        with env:
            subprocess.call(
                args.run + extra,
                shell='Win' in platform.system()
            )

if __name__ == '__main__':
    main()
