"""TcEx Framework Module"""

# standard library
import logging

# first-party
from tcex_app_testing.__metadata__ import (
    __author__,
    __author_email__,
    __description__,
    __license__,
    __package_name__,
    __url__,
    __version__,
)
from tcex_app_testing.logger.trace_logger import TraceLogger  # pylint: disable=no-name-in-module


def initialize_logger():
    """Initialize logger TraceLogger."""
    logging.setLoggerClass(TraceLogger)
    _logger = logging.getLogger(__name__.split('.', maxsplit=1)[0])
    _logger.setLevel(logging.TRACE)  # type: ignore


# init logger before instantiating tcex
initialize_logger()
