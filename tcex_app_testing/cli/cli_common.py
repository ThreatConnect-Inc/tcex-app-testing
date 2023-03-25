"""TcEx Framework Module"""
# standard library
import os

# first-party
from tcex_app_testing.cli.cli_abc import CliABC
from tcex_app_testing.profile import Profile
from tcex_app_testing.profile.interactive import Interactive
from tcex_app_testing.templates import TemplatesFeature, TemplatesTests


class CliCommon(CliABC):
    """CLI Common Class"""

    def __init__(self, feature: str | None = None, profile_name: str | None = None):
        """Initialize instance properties."""
        super().__init__()
        self.feature = feature
        self.profile_name = profile_name

        # properties
        self.profile = Profile()
        self.profile_interactive = Interactive()
        self.templates_feature = TemplatesFeature()
        self.templates_tests = TemplatesTests()

        # create the env variable
        self.create_profile_env_var(self.feature, self.profile_name)

    @staticmethod
    def create_profile_env_var(feature: str | None, profile_name: str | None):
        """Create profile environment variable.

        The config_model module is required to get the profile name from the
        environment variable that python sets. To be consistent with the
        current functionality the env var is set here instead of passing
        in the feature name and profile name.

        tests/Build/test_profiles.py::TestProfiles::test_profiles[string-array]
        """
        if feature is not None and profile_name is not None:
            pytest_current_test = os.path.join(
                'tests',
                feature,
                f'tests_profile.py::TestProfile::test_profile[{profile_name}]',
            )
            os.environ['PYTEST_CURRENT_TEST'] = pytest_current_test
