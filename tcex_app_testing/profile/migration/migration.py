"""TcEx Framework Module"""
# standard library
import logging
from abc import ABC, abstractmethod

# first-party
from tcex_app_testing.util import Util

# get logger
_logger = logging.getLogger(__name__.split('.', maxsplit=1)[0])


class MigrationABC(ABC):
    """Class for profile Migration methods management."""

    def __init__(self, content, start_version, end_version):
        """Initialize Class properties."""
        self.util = Util()
        self.content = content
        self.start_version = start_version
        self.end_version = end_version
        self.log = _logger

        if start_version >= end_version:
            raise RuntimeError('Migration start version must be less than end version.')

    @abstractmethod
    def migrate(self, contents: dict) -> dict:
        """Migrate profile schema."""

    def update_schema_version(self, contents: dict) -> dict:
        """Update the schema version in the profile."""
        contents['schema_version'] = str(self.end_version)
        return contents
