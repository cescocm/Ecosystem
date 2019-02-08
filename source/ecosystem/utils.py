import os
import json
import subprocess
import logging

logger = logging.getLogger(__name__)


def retrieve_environment():
    environment = os.getenv('ECO_PREVIOUS_ENV')

    if not environment:
        return None

    if not os.path.isfile(environment):
        raise ValueError('ECO_PREVIOUS_ENV does not point to a file')

    with open(environment, 'r') as f:
        data = json.load(f)

    return {str(x): str(y) for x, y in data.items()}


def call_process(command, detached=False, **kwargs):

    kwargs.update({'args': command})

    if detached:
        func = subprocess.Popen
        kwargs['stdin'] = subprocess.PIPE
        kwargs['stdout'] = subprocess.PIPE
        kwargs['stderr'] = subprocess.PIPE

    else:
        func = subprocess.call

    return func(**kwargs)
