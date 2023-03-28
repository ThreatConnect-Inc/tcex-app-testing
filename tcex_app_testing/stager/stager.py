"""TcEx Framework Module"""
# standard library
import logging
from typing import TYPE_CHECKING

# third-party
from redis import Redis

# first-party
from tcex_app_testing.pleb.cached_property import cached_property
from tcex_app_testing.stager.stager_kvstore import StagerKvstore

if TYPE_CHECKING:
    # first-party
    from tcex_app_testing.app.playbook import Playbook
    from tcex_app_testing.requests_tc import TcSession

# get logger
_logger = logging.getLogger(__name__.split('.', maxsplit=1)[0])


class Stager:
    """Stage Data class"""

    def __init__(
        self,
        playbook: 'Playbook',
        redis_client: Redis,
        session_tc: 'TcSession',
    ):
        """Initialize class properties"""
        self.playbook = playbook
        self.redis_client = redis_client
        self.session_tc = session_tc

        # properties
        self.log = _logger

    @cached_property
    def kvstore(self):
        """Get the current instance of Redis for staging data"""
        return StagerKvstore(self.playbook, self.redis_client)

    @cached_property
    def redis(self):
        """Get the current instance of Redis for staging data"""
        return StagerKvstore(self.playbook, self.redis_client)
