class MissingRequirementError(Exception):
    '''Raised when a tool is unable to meet a requirement.'''


class MissingDependencyError(Exception):
    '''Raised when a variable is unable to meet a dependency.'''


class InvalidTool(Exception):
    '''Raised when attempting to retrieve an invalid/non-existing tool'''
