from . import EcosystemPlugin
from .. import environment
import platform
import subprocess
import os
import re


class BuildExtension(EcosystemPlugin):
    name = 'build'

    @staticmethod
    def determineNumberOfCPUs():
        """ Number of virtual or physical CPUs on this system, i.e.
        user/real as output by time(1) when called with an optimally scaling
        userspace-only program"""

        # Python 2.6+
        try:
            import multiprocessing
            return multiprocessing.cpu_count()
        except (ImportError, NotImplementedError):
            pass

        # POSIX
        try:
            res = int(os.sysconf('SC_NPROCESSORS_ONLN'))

            if res > 0:
                return res
        except (AttributeError, ValueError):
            pass

        # Windows
        try:
            res = int(os.environ['NUMBER_OF_PROCESSORS'])

            if res > 0:
                return res
        except (KeyError, ValueError):
            pass

        # jython
        try:
            from java.lang import Runtime
            runtime = Runtime.getRuntime()
            res = runtime.availableProcessors()
            if res > 0:
                return res
        except ImportError:
            pass

        # BSD
        try:
            sysctl = subprocess.Popen(
                ['sysctl', '-n', 'hw.ncpu'],
                stdout=subprocess.PIPE
            )
            scStdout = sysctl.communicate()[0]
            res = int(scStdout)

            if res > 0:
                return res
        except (OSError, ValueError):
            pass

        # Linux
        try:
            res = open('/proc/cpuinfo').read().count('processor\t:')

            if res > 0:
                return res
        except IOError:
            pass

        # Solaris
        try:
            pseudoDevices = os.listdir('/devices/pseudo/')
            expr = re.compile('^cpuid@[0-9]+$')

            res = 0
            for pd in pseudoDevices:
                if expr.match(pd) != None:
                    res += 1

            if res > 0:
                return res
        except OSError:
            pass

        # Other UNIXes (heuristic)
        try:
            try:
                dmesg = open('/var/run/dmesg.boot').read()
            except IOError:
                dmesgProcess = subprocess.Popen(
                    ['dmesg'],
                    stdout=subprocess.PIPE
                )
                dmesg = dmesgProcess.communicate()[0]

            res = 0
            while '\ncpu' + str(res) + ':' in dmesg:
                res += 1

            if res > 0:
                return res
        except OSError:
            pass

        raise Exception('Can not determine number of CPUs on this system')

    def initialize(self, ecosystem):
        self.ecosystem = ecosystem
        list_parser = ecosystem.subparser.add_parser(self.name)

        list_parser.add_argument('-qb', '--quick-build', action='store_true')
        list_parser.add_argument('-fr', '--force-rebuild', action='store_true')
        list_parser.add_argument('-d', '--deploy', action='store_true')
        list_parser.add_argument('-t', '--tools', nargs='*')

    def execute(self, args):
        versions = self.ecosystem.get_versions()
        _versions = [x.tool + x.version for x in versions]

        if platform.system().lower() == 'windows':
            make_command = ['jom']
            make_target = 'NMake Makefiles'
        else:
            make_target = 'Unix Makefiles'
            make_command = ['make', '-j', str(self.number_of_processors())]

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
            build_type = os.getenv('PG_BUILD_TYPE')
            if not args.quick_build:
                if args.force_rebuild:
                    try:
                        open('CMakeCache.txt')
                        os.remove('CMakeCache.txt')
                    except IOError:
                        print 'Cache doesnt exist...'

                call_process([
                    'cmake',
                    '-DCMAKE_BUILD_TYPE='+build_type,
                    '-G',
                    make_target,
                    '..']
                )

            if args.deploy:
                make_command.append("package")
            call_process(make_command)


def call_process(arguments):
    if platform.system().lower() == 'windows':
        subprocess.call(arguments, shell=True)
    else:
        subprocess.call(arguments)


def register(ecosystem):
    run_extension = BuildExtension()
    ecosystem.register_extension(run_extension)
