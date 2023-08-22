"""TcEx Framework Module"""
# standard library
import json
import logging
from collections import OrderedDict
from typing import Any

# third-party
from pydantic import ValidationError

# first-party
from tcex_app_testing.app.config.install_json import InstallJson
from tcex_app_testing.app.config.layout_json import LayoutJson
from tcex_app_testing.app.config.permutation import Permutation
from tcex_app_testing.config_model import config_model
from tcex_app_testing.env_store import EnvStore
from tcex_app_testing.pleb.cached_property import cached_property
from tcex_app_testing.profile.model.profile_model import ProfileModel
from tcex_app_testing.profile.profile_populate import ProfilePopulate
from tcex_app_testing.render.render import Render
from tcex_app_testing.requests_tc import TcSession
from tcex_app_testing.requests_tc.auth.tc_auth import TcAuth
from tcex_app_testing.util import Util

# get logger
_logger = logging.getLogger(__name__.split('.', maxsplit=1)[0])


class Profile:
    """Testing Profile Class.

    Args:
        app_inputs: The default Args for the profile.
        monkeypatch: Pytest monkeypatch object.
        pytestconfig: Pytest config object.
        redis_client: An instance of Redis client.
        tcex_testing_context: The current context for this profile.
    """

    def __init__(self):
        """Initialize instance properties."""

        # properties
        self._context_tracker = []
        self._data = None
        self.env_store = EnvStore()
        self.ij = InstallJson(logger=_logger)
        self.lj = LayoutJson(logger=_logger)
        self.log = _logger
        self.permutation = Permutation()
        self.populate = ProfilePopulate(self)
        self.util = Util()

    @staticmethod
    def _flatten_inputs(inputs):
        """Flatten the inputs dict."""
        inputs_flattened = dict(inputs.get('defaults', {}))
        inputs_flattened.update(inputs.get('optional', {}))
        inputs_flattened.update(inputs.get('required', {}))
        return inputs_flattened

    def add(self, contents: dict | None = None):
        """Add a profile."""
        contents = contents or {}

        # get input permutations when a permutation_id is passed
        input_permutations = None

        # this should not hit since tctest also check for duplicates
        self.check_existing_profile()

        profile = OrderedDict()
        profile['_comments_'] = []
        profile['environments'] = contents.get('environments', ['build'])
        profile['stage'] = contents.get('stage', {'kvstore': {}})
        profile['inputs'] = {}  # add inputs here and remove later to ensure proper order
        profile['outputs'] = contents.get('outputs', {})
        profile['schema_version'] = contents.get('schema_version', '1.0.0')

        if self.ij.model.runtime_level.lower() in ['organization', 'playbook']:
            profile['exit_codes'] = contents.get('exit_codes', [0])
            profile['exit_message'] = None
            profile['inputs'].update(
                contents.get(
                    'inputs',
                    {
                        'optional': self.ij.params_to_args(
                            required=False, input_permutations=input_permutations
                        ),
                        'required': self.ij.params_to_args(
                            required=True, input_permutations=input_permutations
                        ),
                    },
                )
            )

        # write the new profile to disk
        self.rewrite_contents(contents=profile)

        return '[green]Success[/green]'

    def check_existing_profile(self):
        """Check if profile is existing."""
        if config_model.test_case_profile_filename.is_file():
            Render.panel.failure(
                f'Profile file {config_model.test_case_profile_filename} already exists.'
            )

    @cached_property
    def contents(self) -> dict:
        """Return the contents of the current profile file.

        Any time the rewrite_contents method is called, this cached property will be
        reset so that the next time it's accessed the latest data is pulled from file.
        """
        contents = json.loads(self.contents_raw)
        self.log.debug('event=contents-loaded')

        return contents

    @property
    def contents_raw(self) -> str:
        """Load contents from file.

        Used to create _contents property and to hunt for
        variable in profile_validate._file_link method.
        """
        contents_raw = ''
        if config_model.test_case_profile_filename.is_file():
            try:
                with config_model.test_case_profile_filename.open(encoding='utf-8') as fh:
                    contents_raw = fh.read()
            except (OSError, ValueError):  # pragma: no cover
                self.log.error(
                    'event=load-profile-contents, exception=failed-reading-file, '
                    f'filename={config_model.test_case_profile_filename}'
                )
        else:
            self.log.error(
                'feature=load-profile-contents, exception=file-not-found, '
                f'filename={config_model.test_case_profile_filename}'
            )
            Render.panel.failure(
                f'Profile file {config_model.test_case_profile_filename} not found.'
            )
        return contents_raw

    @property
    def data(self) -> dict:
        """Return all profile data with env vars replaced.

        The data object is used in the test suite and updated in the aux.init_profile method.
        """
        if self._data is None:
            _contents = self.model.dict()
            self._data = self.populate.replace_env_variables(_contents)

            # used in test cases
            self._data['name'] = config_model.test_case_profile_name
        return self._data

    @data.setter
    def data(self, contents: dict):
        """Set profile_data dict.

        The data object needs to be updated after TC variables are resolved. The order of
        operations requires that the TC data be staged first, then TC variables can be resolved.
        """
        self._data = ProfileModel(**contents).dict()

    def fix_profile(self):
        """Fix any issues with the profile."""
        _contents = self.contents
        _updated = False

        # fix null or empty environments
        if not _contents.get('environments'):
            _contents['environments'] = ['build']
            _updated = True

        # fix null exit message
        if _contents.get('exit_message') is None:
            _contents['exit_message'] = {}
            _updated = True

        # fix null or empty outputs
        if not _contents.get('outputs'):
            _contents['outputs'] = {}
            _updated = True

        # remove options
        if _contents.get('options'):
            del _contents['options']
            _updated = True

        # update inputs, converting array to dict
        for input_type in ['defaults', 'optional', 'required']:
            for _, v in _contents.get('inputs', {}).get(input_type, {}).items():
                if isinstance(v, list):
                    v = f'{self.ij.model.list_delimiter}'.join(v)

        if _updated is True:
            self.rewrite_contents(contents=_contents)

    @property
    def inputs(self) -> dict[str, Any]:
        """Return profile inputs.

        The is the main data property for the run_profile methods in the test_case classes.
        """
        return self.model.flatten_inputs(self.data.get('inputs', {}))

    @cached_property
    def model(self) -> ProfileModel:
        """Return the data model.

        Any time the rewrite_contents method is called, this cached property will be
        reset so that the next time it's accessed the latest data is pulled from file.
        """
        return ProfileModel(**self.contents)

    @property
    def model_resolved(self) -> ProfileModel:
        """Return the data model with all ENV and TC variables resolved."""
        return ProfileModel(**self.data)

    @cached_property
    def session(self):
        """Return a instance of the session manager."""
        auth = TcAuth(
            tc_api_access_id=config_model.tc_api_access_id,
            tc_api_secret_key=config_model.tc_api_secret_key,
        )
        return TcSession(auth, config_model.tc_api_path)

    @property
    def outputs_calculated(self) -> list[str]:
        """Return calculated output variables data."""
        if self.ij.model.playbook is None:
            raise RuntimeError('playbook is not defined in install.json model.')

        output_variables = self.ij.model.playbook.output_variables
        if self.lj.has_layout:
            output_variables = list(
                self.permutation.outputs_by_inputs(self.model.inputs_flattened_staging)
            )

        # take OutputVariablesModel and create variables (e.g. #App:0002:string_3!String)
        output_variables = self.ij.create_output_variables(output_variables)

        return output_variables

    @property
    def outputs_dynamic(self) -> list[str]:
        """Return dynamic output variables based on inputs with exposePlaybookKeyAs defined."""
        output_variables = []
        for name, value in self.model.inputs_flattened.items():
            # get full input data from install.json
            input_data = self.ij.model.params_dict.get(name)
            if input_data is None:
                continue

            # check to see if it support dynamic output variables
            if input_data.expose_playbook_key_as is None:
                continue

            # staged data for this dynamic input must be a KeyValueArray
            for data in self.model.stage.kvstore.get(value, []):
                # create a variable using key value
                variable = self.ij.create_variable(
                    data.get('key'), input_data.expose_playbook_key_as, job_id=9876
                )
                output_variables.append(variable)

        return output_variables

    def rewrite_contents(self, contents: dict, clear_cache: bool = True):
        """Rewrite app_spec.yml file."""
        try:
            contents_ = ProfileModel(**contents).ordered_json(
                exclude_defaults=False,
                exclude_none=False,
                exclude_unset=False,
                indent=2,
            )
        except ValidationError as e:
            self.log.error(
                f'event=validation-error, error={e}, '
                f'filename={config_model.test_case_profile_filename_rel}'
            )
            Render.panel.failure(
                f'Invalid profile: filename="{config_model.test_case_profile_filename_rel}"'
            )

        # write the new contents to the file
        self.write(contents_)

        # clear cache
        if clear_cache is True:
            for cache in ['contents', 'model']:
                if cache in self.__dict__:
                    del self.__dict__[cache]

    @property
    def tc_playbook_out_variables(self) -> list[str]:
        """Return calculated and dynamic output variables."""
        output_variables = self.outputs_calculated
        output_variables.extend(self.outputs_dynamic)

        return output_variables

    def write(self, contents: str):
        """Write json to file."""
        with config_model.test_case_profile_filename.open(mode='w', encoding='utf-8') as fh:
            fh.write(contents.strip())
            fh.write('\n')

    #
    # Context Manager
    #

    def add_context(self, context: str):
        """Add a context to the context tracker for this profile.

        Context gets added during execution of playbook test cases in the run_profile method.
        """
        self._context_tracker.append(context)
