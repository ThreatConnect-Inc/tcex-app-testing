"""TcEx Framework Module"""

# first-party
from tcex_app_testing.cli.cli_common import CliCommon
from tcex_app_testing.config_model import config_model


class Create(CliCommon):
    """CLI Test Create Class"""

    def __init__(
        self,
        feature: str,
        profile_name: str,
        interactive: bool = False,
    ):
        """Initialize instance properties."""
        super().__init__(feature, profile_name)
        self.interactive = interactive

    def create_dirs(self):
        """Create tcex.d directory and sub directories."""
        for d in [
            config_model.test_case_dir,
            config_model.test_case_feature_dir,
            config_model.test_case_feature_profile_dir,
        ]:
            if not d.is_dir():
                d.mkdir()

    def interactive_profile(self):
        """Present interactive profile inputs."""
        self.profile_interactive.present()
        contents = {
            'exit_codes': self.profile_interactive.exit_codes,
            'inputs': self.profile_interactive.inputs,
            'stage': self.profile_interactive.staging_data,
        }
        return self.profile.add(contents)
