"""TcEx Framework Module"""
# standard library
import logging
import os

# third-party
import hvac
from hvac.exceptions import InvalidPath, VaultError

# first-party
from tcex_app_testing.pleb.cached_property import cached_property
from tcex_app_testing.pleb.singleton import Singleton
from tcex_app_testing.render.render import Render

# init logger
_logger = logging.getLogger(__name__.split('.', maxsplit=1)[0])


class EnvStore(metaclass=Singleton):
    """TcEx Key Value API Module."""

    def __init__(self):
        """Initialize the Class properties."""

        # properties
        self.cache = {}
        self.log = _logger
        self.tcex_test_vault_base_path = os.getenv('TCEX_TEST_VAULT_BASE_PATH', '').rstrip('/')
        self.vault_token = os.getenv('VAULT_TOKEN')
        self.vault_addr = os.getenv('VAULT_ADDR') or os.getenv('VAULT_URL')

    def _convert_env(self, env_variable: str) -> str:
        """Convert an a vault path to env variable, removing first 2 parts of path

        Vault path need to be updated to be looked up as env variables.

        non-tc variable expect the path to be /<company>/<product>/<key> or /<company>/<key>

        input (w/ product)  -> <tcex_testing_vault_base_path>/cisco/umbrella/token
        output              -> CISCO_UMBRELLA_TOKEN

        input (w/o product) -> <tcex_testing_vault_base_path>/zoom/user_id
        output              -> ZOOM_USER_ID
        """
        if '/' in env_variable:
            paths = env_variable.lstrip('/').split('/')

            if env_variable.startswith(f'{self.tcex_test_vault_base_path}/threatconnect/tc/tc_'):
                # threatconnect variables are treated special
                # input  -> <tcex_testing_vault_base_path>/threatconnect/tc/tc_api_access_id
                # output -> TC_API_ACCESS_ID
                env_variable = paths[-1]
            else:
                trim_count = 0
                if self.tcex_test_vault_base_path:
                    trim_count = len(self.tcex_test_vault_base_path.lstrip('/').split('/'))

                # remove first to parts of path for env variable and leading '/'
                env_variable = '_'.join(paths[trim_count:])
        return env_variable.replace(' ', '_').upper()

    def _has_base_path(self, env_variable: str) -> bool:
        """Return True if the env variable has base path."""
        return env_variable.startswith(self.tcex_test_vault_base_path)

    @staticmethod
    def _is_path_variable(env_variable: str) -> bool:
        """Return True if the env variable is a path variable."""
        return env_variable.startswith('/')

    def getenv(
        self, env_variable: str, env_type: str | None = 'env', default: str | None = None
    ) -> str:
        """Return the value for the provide environment variable.

        Args:
            env_variable: The env variable name or env store path.
            env_type: The type of environment variable to look up. Defaults to 'env'.
            default: The default value if no value is found.
        """
        # only prepend if current path doesn't already start with this value
        if not self._has_base_path(env_variable) and self._is_path_variable(env_variable):
            env_variable = f'{self.tcex_test_vault_base_path}{env_variable}'

        cache_key = f'{env_type}-{env_variable}'
        cache_value = self.cache.get(cache_key)
        if cache_value is not None:
            return cache_value

        # only log when not retrieving from cache
        self.log.info(
            f'step=config, event=getenv, env-variable={env_variable}, env-type={env_type}'
        )

        # convert path (e.g. /threatconnect/tc/tc_api_access_id) to env variable [TC_API_ACCESS_ID]
        env_var_updated = self._convert_env(env_variable)
        value = default

        env_value = os.getenv(env_var_updated)
        if env_type in ['env', 'envs', 'local'] and env_value is not None:
            # return value from OS environ
            value = env_value
        elif env_type in ['env', 'envs', 'remote', 'vault'] and self.vault_client is not None:
            # return value from Vault
            value = self.read_from_vault(env_variable, default)

        # provide an error so dev/qa engineer knows that
        # an env var they provide could not be found
        if value is None:
            Render.panel.failure(
                f'Could not resolve env variable {env_variable} ({env_var_updated}).'
            )

        # update cache
        if env_type not in ['local']:
            self.cache[cache_key] = value
        return value

    def read_from_vault(self, full_path: str, default: str | None = None) -> str | None:
        """Read data from Vault for the provided path.

        Args:
            full_path: The path to the vault data including the key (e.g. myData/mySecret/myKey).
            default: The default value if no value is found.
        """
        if self.vault_client is None:
            return None

        # self.log.debug(f'step=config, event=read-from-vault, full-path={full_path}')
        paths = full_path.lstrip('/').split('/')

        # the key stored in data object at the provided path
        # (e.g., "/myData/myResource/token" -> "token")
        key = paths[-1].strip('/')

        # the path with the key and mount point removed
        # (e.g., "/myData/myResource/token/" -> "myResource")
        path = '/'.join(paths[1:-1])

        # the mount point from the path
        # (e.g., "/myData/myResource/token/" -> "myData")
        mount_point = paths[0]

        data = {}
        try:
            data = self.vault_client.secrets.kv.read_secret_version(
                path=path, mount_point=mount_point
            )
        except InvalidPath:
            Render.panel.warning(f'Error reading from Vault for path {path}. Path was not found.')
            self.log.error(f'step=setup, event=env-store-invalid-path, path={path}')
        except VaultError as e:
            Render.panel.warning(
                f'Error reading from Vault for path {path}. Check access and credentials.'
            )
            self.log.error(
                f'step=setup, event=env-store-error-reading-path, path={path}, error={e}'
            )
        except Exception:
            Render.panel.warning(f'Error reading from Vault for path {path}.')
            self.log.error('step=setup, event=env-store-generic-failure')

        return data.get('data', {}).get('data', {}).get(key) or default

    @cached_property
    def vault_client(self) -> hvac.Client | None:
        """Return configured vault client."""
        if self.vault_addr is not None and self.vault_token is not None:
            return hvac.Client(url=self.vault_addr, token=self.vault_token)
        return None
