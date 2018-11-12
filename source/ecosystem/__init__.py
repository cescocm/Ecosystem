import logging
from .eco import Ecosystem, Environment
from .errors import MissingDependencyError, MissingRequirementError
from .errors import ToolNotFoundError, PresetNotFoundError

logging.basicConfig(
    format='%(levelname)-8s - %(name)-18s:  %(message)s',
    level=logging.INFO
)

__version__ = '0.6.4'
