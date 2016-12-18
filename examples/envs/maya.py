import os
import re
import platform


TEMPLATE = {
    "tool": "maya",
    "platforms": [
        "windows"
    ],
    "version": "",
    "requires": [],
    "environment": {
        "PATH": {
            "windows": "${MAYA_LOCATION}/bin",
            "darwin": "${MAYA_LOCATION}/bin",
            "linux": "${MAYA_LOCATION}/bin"
        },
        "MAYA_VERSION": "",
        "DYLD_LIBRARY_PATH": {
            "darwin": "${MAYA_LOCATION}/MacOS"
        },
        "MAYA_LOCATION": {
            "windows": "C:/Program Files/Autodesk/Maya${MAYA_VERSION}",
            "darwin": "/Applications/Autodesk/maya${MAYA_VERSION}/Maya.app/Contents",
            "linux": "/usr/autodesk/maya${MAYA_VERSION}-x64"
        }
    }
}

SEARCH_PATHS = {
    'windows': {
        'path': r'C:\Program Files\Autodesk',
        'regex': 'Maya(.+)'
    },
    'linux': {
        'path': '/usr/autodesk/',
        'regex': 'maya(.+)-x64'
    },
    'darwin': {
        'path': '/Applications/Autodesk',
        'regex': 'maya(.+)'
    }
}


def get_tools():
    paths = SEARCH_PATHS.get(platform.system().lower())
    if not paths:
        return []

    regex = re.compile(paths['regex'])
    versions = []
    for item in os.listdir(paths['path']):
        result = regex.match(item)
        if result:
            versions.append(result.group(1))

    versions = sorted(versions)
    tools = []
    for version in versions:
        tool = dict()
        tool.update(TEMPLATE)
        tool['version'] = version
        tool['environment']['MAYA_VERSION'] = version
        tools.append(tool)

    tool = dict()
    tool.update(TEMPLATE)
    tool['version'] = ':latest'
    tool['environment']['MAYA_VERSION'] = versions[-1]
    tools.append(tool)

    return tools
