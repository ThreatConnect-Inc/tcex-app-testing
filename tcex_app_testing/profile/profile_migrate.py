"""TcEx Framework Module"""
# standard library
import logging

# first-party
from tcex_app_testing.app.config import InstallJson
from tcex_app_testing.config_model import config_model
from tcex_app_testing.util import Util

# get logger
_logger = logging.getLogger(__name__.split('.', maxsplit=1)[0])


class ProfileMigrate:
    """Class for profile Migration methods management."""

    def __init__(self):
        """Initialize Class properties."""

        # properties
        self.ij = InstallJson()
        self.log = _logger
        self.migrated = False
        self.util = Util()

    def migrate_schema(self, contents: dict) -> tuple[dict, bool]:
        """Migrate profile schema."""
        # migrate any default inputs that are mistakenly in required or optional sections
        self._migrate_schema_default_inputs(contents)

        # migrate any inputs that are not using variable when variable are supported. using variable
        # is the preferred method of passing data to the App during testing.
        self._migrate_schema_inputs_to_stage_kvstore(contents)

        return contents, self.migrated

    def _add_staging_data(self, contents: dict, name: str, type_: str, value: str) -> str:
        """Create staging data and return variable value.

        Args:
            contents: The profile to update with new staging data.
            name: The name of the input.
            type_: The type of input (Binary, StringArray, etc.)
            value: The value to write in the staging data.

        Returns:
            str: The variable for the staged data.
        """
        contents.setdefault('stage', {}).setdefault('kvstore', {})
        variable: str = self.ij.create_variable(name, type_)
        contents['stage']['kvstore'][variable] = value

        return variable

    def _migrate_schema_default_inputs(self, contents: dict):
        """Move any default args from optional or required inputs to defaults section.

        Args:
            contents: The profile data dict.
        """
        for input_type in ['optional', 'required']:
            for k in dict(contents.get('inputs', {}).get(input_type, {})):
                if k in config_model.schema().get('properties'):
                    contents['inputs'].setdefault('defaults', {})
                    contents['inputs']['defaults'][k] = contents['inputs'][input_type].pop(k)

                    # set migrated flag so profile will be rewritten
                    self.migrated = True

    def _migrate_schema_inputs_to_stage_kvstore(self, contents: dict):
        """Stage any non-staged profile data.

        Args:
            contents: The profile data dict.
        """
        # staging is only required for PB Apps
        if self.ij.model.runtime_level.lower() != 'playbook':
            return

        for input_type in ['optional', 'required']:
            for k, v in dict(contents.get('inputs', {}).get(input_type, {})).items():
                # skip staging inputs that are null are already use a variable
                if v is None or self.util.contains_playbook_variable(v):
                    continue

                # get ij data for key/field
                param_data = self.ij.model.get_param(k)

                # skip staging inputs that are not defined in install.json (possibly default args)
                if param_data is None:
                    continue

                # skip staging for input types that don't support playbookDataType
                if param_data.type.lower() in [
                    'boolean',
                    'choice',
                    'multichoice',
                ]:
                    continue

                # only stage String input types
                if 'String' not in param_data.playbook_data_type and not isinstance(v, str):
                    continue

                # convert input value to staged data
                v = self._add_staging_data(contents, k, 'String', v)

                # update input with new variable
                contents['inputs'][input_type][k] = v

                # set migrated flag so profile will be rewritten
                self.migrated = True
