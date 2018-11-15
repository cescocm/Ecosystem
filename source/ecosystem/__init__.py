import logging
from .eco import Ecosystem, Environment
from .errors import MissingDependencyError, MissingRequirementError
from .errors import ToolNotFoundError, PresetNotFoundError
from ._version import __version__, VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH

logging.basicConfig(
    format='%(levelname)-8s - %(name)-18s:  %(message)s',
    level=logging.INFO
)

__all__ = ['Ecosystem', 'Environment', 'MissingDependencyError',
           'MissingRequirementError', 'ToolNotFoundError',
           'PresetNotFoundError', '__version__', 'VERSION_MAJOR',
           'VERSION_MINOR', 'VERSION_PATCH']
