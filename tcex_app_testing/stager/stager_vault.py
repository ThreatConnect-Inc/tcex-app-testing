"""TcEx Framework Module"""
# standard library
import logging
import os

import hvac
from hvac.exceptions import InvalidPath, VaultError

from tcex_app_testing.pleb.cached_property import cached_property
# first-party
from tcex_app_testing.render.render import Render

# get logger
_logger = logging.getLogger(__name__.split('.', maxsplit=1)[0])


class VaultTokenError(Exception):
    """Exception raised for errors in the Vault Token."""

    def __init__(self):
        self.message = 'VAULT_TOKEN or (VAULT_ADDR or VAULT_URL) env variables not set.'
        super().__init__(self.message)


class StagerVault:
    """Stages the Redis Data"""

    def __init__(self):
        """Initialize class properties."""
        self.log = _logger

    def stage(self, vault_data) -> dict:
        """Stage redis data from dict"""
        staged_data = {}
        for key, url in vault_data.items():
            if key in staged_data:
                raise RuntimeError(f'Vault variable {key} is already staged.')
            staged_data[key] = self.read_from_vault(url)

        return staged_data

    @cached_property
    def vault_client(self):
        vault_token = os.getenv('VAULT_TOKEN')
        vault_addr = os.getenv('VAULT_ADDR') or os.getenv('VAULT_URL')

        if any(value is None for value in [vault_token, vault_addr]):
            raise VaultTokenError()

        return hvac.Client(url=vault_addr, token=vault_token)

    def read_from_vault(self, url: str) -> dict | str:
        """Read data from Vault for the provided path.

        Args:
            url: The url to the vault data including the key (e.g. myData/mySecret).
        """
        url = url.lstrip('/').split('/')

        # the mount point from the path
        # (e.g., "/myData/myResource/token/" -> "myData")
        mount_point = url[0]

        # the path with the key and mount point removed
        # (e.g., "/myData/myResource/token/" -> "myResource")
        url = '/'.join(url[1:])

        data = {}
        try:
            data = self.vault_client.secrets.kv.read_secret_version(
                path=url, mount_point=mount_point
            )
        except InvalidPath:
            Render.panel.warning(f'Error reading from Vault for path {url}. Path was not found.')
            self.log.error(f'step=setup, event=env-store-invalid-path, path={url}')
        except VaultError as e:
            Render.panel.warning(
                f'Error reading from Vault for path {url}. Check access and credentials.'
            )
            self.log.error(
                f'step=setup, event=env-store-error-reading-path, path={url}, error={e}'
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            Render.panel.warning(f'Error reading from Vault for path {url}: {e}.')
            self.log.error('step=setup, event=env-store-generic-failure')

        return data.get('data', data).get('data', data)
