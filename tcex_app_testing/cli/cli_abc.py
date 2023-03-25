"""TcEx Framework Module"""
# standard library
import logging
import os
from abc import ABC
from pathlib import Path

# first-party
from tcex_app_testing.logger.rotating_file_handler_custom import (  # pylint: disable=no-name-in-module
    RotatingFileHandlerCustom,
)
from tcex_app_testing.logger.trace_logger import TraceLogger
from tcex_app_testing.pleb.cached_property import cached_property


class CliABC(ABC):
    """Base Class for ThreatConnect command line tools."""

    @cached_property
    def cli_out_path(self) -> Path:
        """Return the path to the tcex cli command out directory."""
        _out_path = Path(os.path.expanduser('~/.tcex'))
        _out_path.mkdir(exist_ok=True, parents=True)
        return _out_path

    @cached_property
    def log(self) -> logging.Logger:
        """Return the configured logger."""
        # create logger based on custom TestLogger
        logging.setLoggerClass(TraceLogger)

        # init logger
        logger_name = __name__.split('.', maxsplit=1)[0]
        logger = logging.getLogger(logger_name)

        # set logger level
        logger.setLevel(logging.TRACE)  # type: ignore

        # create rotation filehandler
        filename = self.cli_out_path / f'{logger_name}.log'
        lfh = RotatingFileHandlerCustom(
            backupCount=3,
            filename=str(filename),
            maxBytes=1_000_000,
        )

        # get logging level from OS env or default to debug
        logging_level = logging.getLevelName('TRACE')

        # set handler logging level
        lfh.setLevel(logging_level)

        # create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)'
        )
        if logging_level <= logging.DEBUG:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s '
                '(%(filename)s:%(funcName)s:%(lineno)d:%(threadName)s)'
            )

        # set formatter
        lfh.setFormatter(formatter)

        # add handler
        logger.addHandler(lfh)

        # logger
        logger.info('Logger initialized.')

        return logger
