import subprocess


def call_process(command, detached=False, shell=None, **kwargs):

    kwargs.update({'args': command})

    if detached:
        func = subprocess.Popen
        kwargs['stdin'] = subprocess.PIPE
        kwargs['stdout'] = subprocess.PIPE
        kwargs['stderr'] = subprocess.PIPE

    else:
        func = subprocess.call

    return func(**kwargs)
