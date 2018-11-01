import sys
import argparse
from ecosystem import Ecosystem
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
    list_subgrp = list_grp.add_mutually_exclusive_group()
    list_subgrp.add_argument(
        '-l', '--list', action='store_true', default=False)
    list_subgrp.add_argument(
        '-L', '--list-presets', action='store_true', default=False)

    run_grp = parser.add_argument_group('run')
    run_grp.add_argument('-r', '--run', nargs='*')

    source_subgrp = run_grp.add_mutually_exclusive_group()
    source_subgrp.add_argument('-t', '--tools', nargs='+')
    source_subgrp.add_argument('-p', '--preset', type=str)

    common_grp = parser.add_argument_group('common')
    common_grp.add_argument('--verbosity', type=str, default='info')

    args, extra = parser.parse_known_args(args)
    logger.setLevel(levels.get(args.verbosity, logging.INFO))

    eco = Ecosystem()

    if args.list:
        sys.stdout.write('\n'.join(eco.list_tools()))
        return

    if args.list_presets:
        sys.stdout.write('\n'.join(eco.list_presets()))
        return

    if args.run is not None:
        if not args.preset and not args.tools:
            parser.error(
                'one of te arguments -t/--tools -p/--presets is required')

        if args.preset:
            preset = eco.get_preset(args.preset)
            preset.run(command=args.run + extra)

        elif args.tools:
            if not args.run:
                parser.error('argument -r/--run requires a value')
            env = eco.get_environment(*args.tools)
            with env:
                subprocess.call(
                    args.run + extra,
                    shell='win' in platform.system().lower(),
                    stdout=subprocess.PIPE,
                    sterr=subprocess.PIPE,
                    stdin=subprocess.PIPE
                )
            raise SystemExit(0)


if __name__ == '__main__':
    main()
