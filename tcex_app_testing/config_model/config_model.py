"""TcEx Framework Module"""
# standard library
import json
import logging
import os
import re
from pathlib import Path

# third-party
from pydantic import BaseModel, Field, validator
from pydantic.fields import ModelField

# first-party
from tcex_app_testing.app.config import InstallJson
from tcex_app_testing.env_store import EnvStore
from tcex_app_testing.input.field_type.sensitive import Sensitive

# get logger
_logger = logging.getLogger(__name__.split('.', maxsplit=1)[0])

# initialize env store
env_store = EnvStore()

# instantiate InstallJson object
ij = InstallJson()

# define JSON encoders
json_encoders = {Sensitive: lambda v: v.value}  # pylint: disable=unnecessary-lambda


def env_store_getenv(v: str, field: ModelField) -> str | None:
    """Get environment variables."""
    if v is None:
        default = field.field_info.extra.get('env_default')
        env = field.field_info.extra['env']
        v = env_store.getenv(env, default=default)

    return v


class ConfigModel(BaseModel):
    """Model Definition"""

    #
    # API Inputs
    #

    tc_api_access_id: str = Field(
        None,
        app_input=True,
        description='The API Access ID for the TC Exchange Admin API.',
        env='/threatconnect/tc/tc_api_access_id',
    )
    tc_api_default_org: str = Field(
        None,
        app_input=True,
        description='The default organization for the TC Exchange Admin API.',
        env='/threatconnect/tc/tc_api_default_org',
    )
    tc_api_secret_key: Sensitive = Field(
        None,
        app_input=True,
        description='The API Secret Key for the TC Exchange Admin API.',
        env='/threatconnect/tc/tc_api_secret_key',
    )
    tc_api_path: str = Field(
        env_store.getenv('TC_API_PATH', env_type='local'),
        app_input=True,
        description='The API path for the TC Exchange Admin API.',
    )
    tc_verify: bool = Field(
        env_store.getenv('TC_VERIFY', env_type='local', default='true').lower() == 'true',
        app_input=True,
        description='Verify SSL certificate.',
    )

    _getenv_api_inputs = validator(
        'tc_api_access_id',
        'tc_api_default_org',
        'tc_api_secret_key',
        allow_reuse=True,
        always=True,
        pre=True,
    )(env_store_getenv)

    #
    # Logging Inputs
    #

    tc_log_backup_count: int = Field(
        25,
        app_input=True,
        description='The maximum number of log files to retain for an App.',
    )
    tc_log_curl: bool = Field(
        env_store.getenv('TC_LOG_CURL', env_type='local', default='false').lower() == 'true',
        app_input=True,
        description='Flag to enable logging curl commands.',
    )
    tc_log_file: str = Field(
        'app.log',
        app_input=True,
        description='The default name of the App\'s log file.',
    )
    tc_log_level: str = Field(
        env_store.getenv('TC_LOG_LEVEL', env_type='local', default='trace'),
        app_input=True,
        description='The logging level for the App.',
    )
    tc_log_max_bytes: int = Field(
        10_485_760,
        app_input=True,
        description='The maximum size of the App log file before rotation.',
    )
    tc_log_to_api: bool = Field(
        env_store.getenv('TC_LOG_TO_API', env_type='local', default='false').lower() == 'true',
        app_input=True,
        description='Flag to enable API logging for the App.',
    )

    #
    # Path Inputs
    #

    tc_in_path: str = Field(
        env_store.getenv('TC_OUT_PATH', env_type='local', default='log'),
        app_input=True,
        description='The path to the Apps "in" directory.',
    )
    tc_log_path: str = Field(
        env_store.getenv('TC_LOG_PATH', env_type='local', default='log'),
        app_input=True,
        description='The path to the Apps "log" directory.',
    )
    tc_out_path: str = Field(
        env_store.getenv('TC_OUT_PATH', env_type='local', default='log'),
        app_input=True,
        description='The path to the Apps "out" directory.',
    )
    tc_temp_path: str = Field(
        env_store.getenv('TC_OUT_PATH', env_type='local', default='log'),
        app_input=True,
        description='The path to the Apps "tmp" directory.',
    )

    #
    # Playbook Common Config Inputs (shared with services)
    #

    tc_cache_kvstore_id: int = Field(
        10,
        app_input=True,
        description='The KV Store cache DB Id.',
    )
    tc_kvstore_host: str = Field(
        env_store.getenv('TC_KVSTORE_HOST', env_type='local', default='localhost'),
        app_input=True,
        description='The KV Store hostname.',
    )
    tc_kvstore_port: int = Field(
        env_store.getenv('TC_KVSTORE_PORT', env_type='local', default='6379'),
        app_input=True,
        description='The KV Store port number.',
    )
    tc_kvstore_type: str = Field(
        'Redis',
        app_input=True,
        description='The KV Store type (Redis or TCKeyValueAPI).',
    )
    tc_playbook_kvstore_id: int = Field(
        0,
        app_input=True,
        description='The KV Store playbook DB Id.',
    )

    #
    # Playbook Config Inputs
    #

    # this value is overwritten when create_config -> create_config_update runs
    tc_playbook_kvstore_context: str | None = Field(
        None,
        app_input=True,
        description='The KV Store context for the current App execution.',
    )
    # this value is overwritten when create_config -> create_config_update runs
    tc_playbook_out_variables: list | None = Field(
        None,
        app_input=True,
        description='The list of requested output variables.',
    )

    #
    # Proxy Inputs
    #

    tc_proxy_external: bool | None = Field(
        env_store.getenv('TC_PROXY_EXTERNAL', env_type='local', default='false').lower() == 'true',
        app_input=True,
        description='Flag to enable proxy for external connections.',
    )
    tc_proxy_host: str | None = Field(
        None,
        app_input=True,
        env='/threatconnect/tc/tc_proxy_host',
        env_default='localhost',
        description='The proxy hostname.',
    )
    tc_proxy_password: Sensitive | None = Field(
        None,
        app_input=True,
        env='/threatconnect/tc/tc_proxy_password',
        env_default='',
        description='The proxy password',
    )
    tc_proxy_port: int | None = Field(
        None,
        app_input=True,
        env='/threatconnect/tc/tc_proxy_port',
        env_default='4242',
        description='The proxy port number.',
    )
    tc_proxy_tc: bool | None = Field(
        env_store.getenv('TC_PROXY_TC', env_type='local', default='false').lower() == 'true',
        app_input=True,
        description='Flag to enable proxy for ThreatConnect connection.',
    )
    tc_proxy_username: str | None = Field(
        None,
        app_input=True,
        env='/threatconnect/tc/tc_proxy_username',
        description='The proxy username.',
    )

    _getenv_proxy_input = validator(
        'tc_proxy_host',
        'tc_proxy_password',
        'tc_proxy_port',
        'tc_proxy_username',
        allow_reuse=True,
        always=True,
        pre=True,
    )(env_store_getenv)

    #
    # Service Config Inputs
    #

    tc_svc_broker_conn_timeout: int = Field(
        60,
        app_input=True,
        description='The broker connection startup timeout in seconds.',
    )
    tc_svc_broker_jks_file: str = Field(
        'Unused',
        app_input=True,
        description='The JKS file for the TC Service Broker.',
    )
    tc_svc_broker_jks_pwd: str = Field(
        'Unused',
        app_input=True,
        description='The JKS password for the TC Service Broker.',
    )
    tc_svc_broker_timeout: int = Field(
        60,
        app_input=True,
        description='The broker service timeout in seconds.',
    )
    tc_svc_hb_timeout_seconds: int = Field(
        20,
        app_input=True,
        description='The heartbeat timeout interval in seconds.',
    )

    class Config:
        """DataModel Config"""

        validate_assignment = True
        json_encoders = json_encoders

    @property
    def inputs(self) -> dict[str, int | list | str | None]:
        """Return a list of all input fields."""
        return json.loads(self.json())

    #
    # Additional Config Items
    #

    @property
    def app_path(self) -> str:
        """Return the path to the App."""
        return os.getcwd()

    @property
    def current_test(self) -> str:
        """Return properly formatted value for current test."""
        pytest_current_test = os.getenv('PYTEST_CURRENT_TEST', '').split(' ')[0]
        # _logger.debug(f'PYTEST_CURRENT_TEST={pytest_current_test}')
        return pytest_current_test

    @property
    def os_environments(self) -> set[str]:
        """Return the locally defined env values."""
        return set(os.getenv('TCEX_TEST_ENVS', 'build').split(','))

    @property
    def runtime_level_service_apps(self) -> list[str]:
        """Return runtime level service apps."""
        return ['apiservice', 'triggerservice', 'webhooktriggerservice']

    @property
    def runtime_level_trigger_service_apps(self) -> list[str]:
        """Return runtime level trigger service apps."""
        return ['triggerservice', 'webhooktriggerservice']

    @property
    def tcex_testing_vault_base_path(self) -> str:
        """Return the base path for the vault."""
        return os.getenv('TCEX_TESTING_VAULT_BASE_PATH', '').rstrip('/')

    @property
    def test_case_data(self) -> list[str]:
        """Return partially parsed test case data."""
        return self.current_test.split('::')

    @property
    def test_case_dir(self) -> Path:
        """Return profile fully qualified filename."""
        return Path(os.path.join(self.app_path, 'tests'))

    @property
    def test_case_feature(self) -> str:
        """Return partially parsed test case data."""
        return self.test_case_data[0].split('/')[1].replace('/', '-')

    @property
    def test_case_feature_dir(self) -> Path:
        """Return profile fully qualified filename."""
        return Path(os.path.join(self.test_case_dir, self.test_case_feature))

    @property
    def test_case_feature_profile_dir(self) -> Path:
        """Return profile fully qualified filename."""
        return Path(os.path.join(self.test_case_feature_dir, 'profiles.d'))

    @property
    def test_case_log_feature_dir(self) -> Path:
        """Return profile fully qualified filename."""
        return Path(os.path.join(self.app_path, self.tc_log_path, self.test_case_feature))

    @property
    def test_case_log_test_dir(self) -> Path:
        """Return profile fully qualified filename."""
        return Path(os.path.join(self.test_case_log_feature_dir, self.test_case_name))

    @property
    def test_case_message_tc_filename(self) -> Path:
        """Return profile fully qualified filename."""
        return Path(os.path.join(self.test_case_tc_out_path, 'message.tc'))

    @property
    def test_case_name(self) -> str:
        """Return partially parsed test case data."""
        return self.test_case_data[-1].replace('/', '-').replace('[', '-').replace(']', '')

    @property
    def test_case_profile_name(self) -> str:
        """Return profile fully qualified filename."""
        name_pattern = r'^test_[a-zA-Z0-9_]+\[(.+)\]$'
        _profile_name = re.search(name_pattern, self.test_case_data[-1])
        if _profile_name is None:
            raise RuntimeError(f'Unable to parse profile name from {self.test_case_data[-1]}')
        return _profile_name.group(1)

    @property
    def test_case_profile_filename(self) -> Path:
        """Return profile fully qualified filename."""
        return Path(
            os.path.join(self.test_case_feature_profile_dir, f'{self.test_case_profile_name}.json')
        )

    @property
    def test_case_profile_filename_rel(self) -> str:
        """Return profile fully qualified filename."""
        return f'./{self.test_case_profile_filename.relative_to(os.getcwd())}'

    @property
    def test_case_tc_in_path(self) -> Path:
        """Return profile fully qualified filename."""
        fqfn = os.path.join(self.app_path, self.tc_in_path, self.test_case_feature)
        if ij.model.runtime_level.lower() not in self.runtime_level_service_apps:
            fqfn = os.path.join(fqfn, self.test_case_name)
        return Path(fqfn)

    @property
    def test_case_tc_log_path(self) -> Path:
        """Return profile fully qualified filename."""
        fqfn = os.path.join(self.app_path, self.tc_log_path, self.test_case_feature)
        if ij.model.runtime_level.lower() not in self.runtime_level_service_apps:
            fqfn = os.path.join(fqfn, self.test_case_name)
        return Path(fqfn)

    @property
    def test_case_tc_out_path(self) -> Path:
        """Return profile fully qualified filename."""
        fqfn = os.path.join(self.app_path, self.tc_out_path, self.test_case_feature)
        if ij.model.runtime_level.lower() not in self.runtime_level_service_apps:
            fqfn = os.path.join(fqfn, self.test_case_name)
        return Path(fqfn)

    @property
    def test_case_tc_temp_path(self) -> Path:
        """Return profile fully qualified filename."""
        fqfn = os.path.join(self.app_path, self.tc_temp_path, self.test_case_feature)
        if ij.model.runtime_level.lower() not in self.runtime_level_service_apps:
            fqfn = os.path.join(fqfn, self.test_case_name)
        return Path(fqfn)
