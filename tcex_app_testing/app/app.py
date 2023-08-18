"""TcEx Framework Module"""

# first-party
from tcex_app_testing.registry import registry

from ..input.model.module_app_model import ModuleAppModel
from ..pleb.cached_property import cached_property
from ..pleb.scoped_property import scoped_property
from ..util.file_operation import FileOperation
from .config.install_json import InstallJson
from .key_value_store.key_value_store import KeyValueStore
from .playbook.playbook import Playbook


class App:
    """TcEx Module"""

    def __init__(self, model: ModuleAppModel, proxies: dict[str, str]):
        """Initialize instance properties."""
        self.model = model
        self.proxies = proxies

    @cached_property
    def file_operation(self) -> FileOperation:
        """Include the Utils module."""
        return FileOperation(
            out_path=self.model.tc_out_path,
            temp_path=self.model.tc_temp_path,
        )

    def get_playbook(
        self, context: str | None = None, output_variables: list | None = None
    ) -> Playbook:
        """Return a new instance of playbook module.

        Args:
            context: The KV Store context/session_id. For PB Apps the context is provided on
                startup, but for service Apps each request gets a different context.
            output_variables: The requested output variables. For PB Apps outputs are provided on
                startup, but for service Apps each request gets different outputs.
        """
        return Playbook(self.key_value_store, context, output_variables)

    @scoped_property
    def key_value_store(self) -> KeyValueStore:
        """Return the correct KV store for this execution.

        The TCKeyValueAPI KV store is limited to two operations (create and read),
        while the Redis kvstore wraps a few other Redis methods.
        """
        return KeyValueStore(
            registry.session_tc,
            self.model.tc_kvstore_host,
            self.model.tc_kvstore_port,
            self.model.tc_kvstore_type,
        )

    @cached_property
    def ij(self) -> InstallJson:
        """Return the install.json file as a dict."""
        return self.install_json

    @cached_property
    def install_json(self) -> InstallJson:
        """Return the install.json file as a dict."""
        return InstallJson()

    @scoped_property
    def playbook(self) -> Playbook:
        """Return an instance of Playbooks module.

        This property defaults context and output variables to arg values.
        """
        return self.get_playbook(
            context=self.model.tc_playbook_kvstore_context,
            output_variables=self.model.tc_playbook_out_variables,
        )

    @cached_property
    def user_agent(self) -> dict[str, str]:
        """Return a User-Agent string."""
        return {
            'User-Agent': (
                f'TcExAppTesting/{__import__(__name__).__version__}, '
                f'{self.ij.model.display_name}/{self.ij.model.program_version}'
            )
        }
