"""TcEx Framework Module"""
# standard library
import os

# first-party
from tcex_app_testing.cli.cli_common import CliCommon
from tcex_app_testing.config_model import config_model
from tcex_app_testing.profile.profile import Profile


class Update(CliCommon):
    """CLI Test Update Class"""

    def is_feature_directory(self, feature: str) -> bool:
        """Check if feature directory exists."""
        feature_path = os.path.join('tests', feature)

        if not os.path.isdir(feature_path) or not os.path.isdir(
            os.path.join(feature_path, 'profiles.d')
        ):
            # not a feature directory
            return False

        self.log.info(f'event=found-feature-directory, feature-path={feature_path}')
        return True

    def update_feature_files(self):
        """Update all JSON profiles."""
        for feature in os.listdir('tests'):
            # validate the feature dir
            if self.is_feature_directory(feature) is False:
                continue

            # set environment variable for test case (used to determine all name and paths)
            self.create_profile_env_var(feature=feature, profile_name='')

            # render all templates in the features directory
            self.templates_feature.render_templates()

            # update all profiles in the profiles.d directory
            self.update_profiles(feature)

    def update_profiles(self, feature: str):
        """Update all JSON profiles."""
        # iterate over all profiles in the profiles.d directory
        for profile_filename in os.listdir(config_model.test_case_feature_profile_dir):
            self.log.debug(f'event=update-profile, profile-filename={profile_filename}')

            # strip the .json extension
            profile_name = profile_filename.replace('.json', '')

            # set environment variable for test case (used to determine all name and paths)
            self.create_profile_env_var(feature=feature, profile_name=profile_name)

            # get a new instance of profile since contents is a cached property
            profile = Profile()

            # run fix profile method
            profile.fix_profile()
