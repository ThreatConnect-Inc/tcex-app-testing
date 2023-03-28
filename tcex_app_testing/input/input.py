"""TcEx Framework Module"""
# standard library
import logging
import re
from base64 import b64decode

# first-party
from tcex_app_testing.input.field_type.sensitive import Sensitive
from tcex_app_testing.logger.trace_logger import TraceLogger
from tcex_app_testing.registry import registry
from tcex_app_testing.util import Util

# get tcex logger
_logger: TraceLogger = logging.getLogger(__name__.split('.', maxsplit=1)[0])  # type: ignore


class Input:
    """Module to handle inputs for all App types."""

    def __init__(self, config: dict | None = None, config_file: str | None = None):
        """Initialize instance properties."""

        self.config = config
        self.config_file = config_file

        # properties
        self.log = _logger
        self.util = Util()

    def resolve_variable(self, variable: str) -> bytes | str | Sensitive:
        """Resolve FILE/KEYCHAIN/TEXT variables.

        Feature: PLAT-2688

        Data Format:
        {
                "data": "value"
        }
        """
        match = re.match(self.util.variable_tc_match, variable)
        if not match:
            raise RuntimeError(f'Could not parse variable: {variable}')

        key = match.group('key')
        provider = match.group('provider')
        type_ = match.group('type')

        # retrieve value from API
        data = None
        r = registry.session_tc.get(f'/internal/variable/runtime/{provider}/{key}')
        if r.ok:
            try:
                data = r.json().get('data')

                if type_.lower() == 'file':
                    data = b64decode(data)  # returns bytes
                elif type_.lower() == 'keychain':
                    data = Sensitive(data)
            except Exception as ex:
                raise RuntimeError(
                    f'Could not retrieve variable: provider={provider}, key={key}, type={type_}.'
                ) from ex
        else:
            raise RuntimeError(
                f'Could not retrieve variable: provider={provider}, key={key}, type={type_}.'
            )

        return data
