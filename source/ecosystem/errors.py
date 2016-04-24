class MissingRequirementError(Exception):
    '''Raised when a tool is unable to meet a requirement.'''


class MissingDependencyError(Exception):
    '''Raised when a variable is unable to meet a dependency.'''


class ToolNotFoundError(Exception):
    '''Raised when attempting to retrieve an non-existing tool'''


class PresetNotFoundError(Exception):
    '''Raised when attempting to retrieve an non-existing preset'''
