import subprocess
import platform


def call_process(command, detached=False, shell=None, **kwargs):

    kwargs.update({
        'args': command,
        'shell': shell or 'win' in platform.system().lower()
    })

    if detached:
        func = subprocess.Popen
        kwargs['stdout'] = subprocess.PIPE
        kwargs['stderr'] = subprocess.PIPE
        kwargs['stdin'] = subprocess.PIPE
    else:
        func = subprocess.call

    return func(**kwargs)
