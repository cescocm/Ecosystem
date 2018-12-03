import sys
import argparse
import logging

from ecosystem import Ecosystem
from ecosystem import utils
from ecosystem import presets

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
    run_grp.add_argument('--run-detached', action='store_true')
    run_grp.add_argument('--normalize-paths', action='store_true')
    run_grp.add_argument('--from-previous', action='store_true')

    source_subgrp = run_grp.add_mutually_exclusive_group()
    source_subgrp.add_argument('-t', '--tools', nargs='+')
    source_subgrp.add_argument('-p', '--preset', nargs='+')

    common_grp = parser.add_argument_group('common')
    common_grp.add_argument('--verbosity', type=str, default='info')

    args, extra = parser.parse_known_args(args)
    logger.setLevel(levels.get(args.verbosity, logging.INFO))

    eco = Ecosystem(normalize_paths=args.normalize_paths)

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

        command = args.run + extra

        if args.preset:
            if len(args.preset) == 1:
                preset = eco.get_preset(args.preset[0])
                environment = preset.get_environment()
            else:
                environment = presets.merge(*[eco.get_preset(x)
                                              for x in args.preset])
                environment.remove_duplicates()

            if not command:
                command = preset.default_command
                if not command:
                    raise ValueError('Preset does not have a default command')

        elif args.tools:
            if not args.run:
                parser.error('argument -r/--run requires a value')

            environment = eco.get_environment(*args.tools)

        kwargs = {}
        if args.from_previous:
            env = utils.retrieve_environment()
            kwargs['env'] = env

        with environment:
            code = utils.call_process(command,
                                      detached=args.run_detached,
                                      **kwargs)

        raise SystemExit(code)


if __name__ == '__main__':
    main()
