import os
import sys
import argparse
import logging
import platform

from ecosystem import Ecosystem
from ecosystem import utils
from ecosystem import presets

logger = logging.getLogger('ecosystem')
levels = {
    'info': logging.INFO,
    'warning': logging.WARNING,
    'debug': logging.DEBUG
}


def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def main(args=sys.argv[1:]):

    # Pre-parse
    runcmd = []
    if ('-r' in args or '--run' in args):
        index = args.index('-r') if '-r' in args else args.index('--run')
        runcmd += [args.pop(x) for x in reversed(range(index, len(args)))]
        runcmd = list(reversed(runcmd))[1:]

    extra = []
    if ('-h' in args or '--help' in args) and len(args) != 1:
        index = args.index('-h') if '-h' in args else args.index('--help')
        extra.append(args.pop(index))

    parser = argparse.ArgumentParser(prog='ecosystem')

    list_grp = parser.add_argument_group('list')
    list_subgrp = list_grp.add_mutually_exclusive_group()
    list_subgrp.add_argument(
        '-l', '--list', action='store_true', default=False)
    list_subgrp.add_argument(
        '-L', '--list-presets', action='store_true', default=False)

    run_grp = parser.add_argument_group('run')
    run_grp.add_argument('-r', '--run', nargs='?', default=[''])
    run_grp.add_argument('--run-detached', action='store_true')
    run_grp.add_argument('--run-shell', type=str2bool,
                         default=platform.system() == 'Windows')
    run_grp.add_argument('--normalize-paths', action='store_true')
    run_grp.add_argument('--from-previous', action='store_true')

    source_subgrp = run_grp.add_mutually_exclusive_group()
    source_subgrp.add_argument('-t', '--tools', nargs='+')
    source_subgrp.add_argument('-p', '--preset', nargs='+')

    common_grp = parser.add_argument_group('common')
    common_grp.add_argument('--verbosity', type=str, default='info')

    args, extra_ = parser.parse_known_args(args)
    extra += extra_
    logger.setLevel(levels.get(args.verbosity, logging.INFO))

    eco = Ecosystem(normalize_paths=args.normalize_paths)

    if args.list:
        sys.stdout.write('\n'.join(eco.list_tools()))
        return

    if args.list_presets:
        sys.stdout.write('\n'.join(eco.list_presets()))
        return

    if runcmd is not None:
        if not args.preset and not args.tools:
            parser.error(
                'one of te arguments -t/--tools -p/--presets is required')

        if args.preset:
            if len(args.preset) == 1:
                preset = eco.get_preset(args.preset[0])
                environment = preset.get_environment()
            else:
                environment = presets.merge(*[eco.get_preset(x)
                                              for x in args.preset])
                environment.remove_duplicates()

            if not runcmd:
                runcmd = preset.default_command
                if not runcmd:
                    raise ValueError('Preset does not have a default runcmd')

        elif args.tools:
            if not args.run:
                parser.error('argument -r/--run requires a value')

            environment = eco.get_environment(*args.tools)

        prev_env = None
        if args.from_previous:
            env = utils.retrieve_environment()
            prev_env = os.environment
            os.environ = env

        with environment:
            code = utils.call_process(runcmd,
                                      detached=args.run_detached,
                                      shell=args.run_shell)

        if prev_env:
            os.environ = prev_env

        raise SystemExit(code)


if __name__ == '__main__':
    main()
