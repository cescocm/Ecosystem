from . import EcosystemPlugin
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
        self.parser = ecosystem.subparser.add_parser(self.name)

        self.parser.add_argument('-q', '--quick-build', action='store_true')
        self.parser.add_argument('-f', '--force-rebuild', action='store_true')
        self.parser.add_argument('-d', '--deploy', action='store_true')
        self.parser.add_argument('-t', '--tools', nargs='*')

    def execute(self, args):
        if platform.system().lower() == 'windows':
            make_command = ['jom']
            make_target = 'NMake Makefiles'
        else:
            make_target = 'Unix Makefiles'
            make_command = ['make', '-j', str(self.number_of_processors())]

        env = self.get_environment(args)
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
                    '-DCMAKE_BUILD_TYPE=%s' % build_type,
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
