"""TcEx Framework Module"""
# standard library
import copy

# first-party
from tcex_app_testing.cli.cli_common import CliCommon
from tcex_app_testing.config_model import config_model
from tcex_app_testing.profile import Profile


class Negative(CliCommon):
    """CLI Test Create Class"""

    def __init__(self, feature: str | None = None, profile_name: str | None = None):
        """Initialize class properties."""
        super().__init__(feature, profile_name)

        # properties
        self.results = []

    def add_negative_profile(
        self, profile_name: str, inputs: dict, fail_on_error: bool | None = None
    ):
        """Create a negative profile."""
        # build profile name
        exit_code = 1  # default exit code is 1
        if fail_on_error is not None:
            if fail_on_error is False:
                exit_code = 0
            profile_name = f'{profile_name}_foe_{str(fail_on_error).lower()}'

        # get profile data and update with new inputs
        contents = self.profile.contents
        contents['exit_codes'] = [exit_code]
        contents['exit_message'] = None
        contents['inputs'] = inputs
        contents['outputs'] = None
        contents['environments'] = [*self.profile.model.environments, 'negative']

        # create a meaningful profile name
        self.create_profile_env_var(self.feature, profile_name)
        profile = Profile()
        status = profile.add(contents)

        # add entry to results to display on CLI when negative action is executed
        self.results.append([profile_name, config_model.test_case_profile_filename_rel, status])

    def create_negative_profiles(self):
        """Create negative profiles using interactive profile base."""
        # pylint: disable=too-many-nested-blocks
        for inputs in self.profile.model.profile_inputs:
            for name, value in inputs.get('required', {}).items():
                ij_data = self.profile.ij.model.params_dict[name]
                # create a profile for each pb data type
                for pb_data_type in ij_data.playbook_data_type:
                    for negative_type in self.negative_inputs.get(pb_data_type.lower(), []):
                        # the value is pre-staged in test_case_playbook_common.py
                        value = f'#App:1234:{negative_type}!{pb_data_type}'
                        profile_name = f'negative_{name}_{pb_data_type.lower()}_{negative_type}'
                        # modify copy so original is preserved for next interaction
                        new_inputs = copy.deepcopy(inputs)
                        new_inputs['required'][name] = value

                        if 'fail_on_error' in inputs.get('optional', {}):
                            # handle fail on error
                            for b in [False, True]:
                                new_inputs['optional']['fail_on_error'] = b
                                self.add_negative_profile(profile_name, new_inputs, b)
                        else:
                            self.add_negative_profile(profile_name, new_inputs)

    @property
    def negative_inputs(self):
        """Return dict of negative inputs."""
        return {
            'binary': ['empty', 'null'],
            'binaryarray': ['empty', 'null'],
            'keyvalue': ['null'],
            'keyvaluearray': ['null'],
            'string': ['empty', 'null'],
            'stringarray': ['empty', 'null'],
            'tcentity': ['null'],
            'tcentityarray': ['null'],
        }
