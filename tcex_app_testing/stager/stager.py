"""TcEx Framework Module"""
# standard library
import logging
from typing import TYPE_CHECKING

# third-party
from redis import Redis

# first-party
from tcex_app_testing.pleb.cached_property import cached_property
from tcex_app_testing.stager.stager_env import StagerEnv
from tcex_app_testing.stager.stager_kvstore import StagerKvstore
from tcex_app_testing.stager.stager_request import StagerRequest
from tcex_app_testing.stager.stager_threatconnect import StagerThreatconnect
from tcex_app_testing.stager.stager_vault import StagerVault

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
        tc_session: 'TcSession',
    ):
        """Initialize class properties"""
        self.playbook = playbook
        self.redis_client = redis_client
        self.tc_session = tc_session

        # properties
        self.log = _logger

    @cached_property
    def redis(self):
        """Get the current instance of Redis for staging data"""
        return StagerKvstore(self.playbook, self.redis_client)

    @cached_property
    def threatconnect(self):
        """Get the current instance of ThreatConnect for staging data"""
        return StagerThreatconnect(self.tc_session)

    @cached_property
    def vault(self):
        """Get the current instance of Vault for staging data"""
        return StagerVault()

    @cached_property
    def env(self):
        """Get the current instance of Env for staging data"""
        return StagerEnv()

    @cached_property
    def request(self):
        """Get the current instance of Env for staging data"""
        return StagerRequest()
