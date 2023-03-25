"""TcEx Framework Module"""
# standard library
import os

# first-party
from tcex_app_testing.config_model import config_model
from tcex_app_testing.templates.templates_abc import TemplatesABC


class TemplatesFeature(TemplatesABC):
    """Custom method Template Class"""

    @property
    def _app_class(self) -> str:
        """Return the proper App class based on runtime level."""
        app_type_to_class = {
            'apiservice': 'TestCaseApiService',
            'organization': 'TestCaseJob',
            'playbook': 'TestCasePlaybook',
            'triggerservice': 'TestCaseTriggerService',
            'webhooktriggerservice': 'TestCaseWebhookTriggerService',
        }
        return app_type_to_class[self.ij.model.runtime_level.lower()]

    def custom_feature_py(self):
        """Render the custom.py template."""
        filename = 'custom_feature.py'
        self.log.info(f'Rendering {filename} template to {config_model.test_case_feature_dir}')

        # define template variables
        variables = {'runtime_level': self.ij.model.runtime_level.lower()}

        # render the template
        fqfn = os.path.join(config_model.test_case_feature_dir, filename)
        self.render(f'{filename}.tpl', fqfn, variables)

    def init_py(self):
        """Render template file."""
        filename = '__init__.py'
        self.log.info(f'Rendering {filename} template to {config_model.test_case_feature_dir}')

        # define template variables
        variables = {'type': 'Feature'}

        # render the template
        fqfn = os.path.join(config_model.test_case_feature_dir, filename)
        self.render(f'{filename}.tpl', fqfn, variables, overwrite=True)

    def render_templates(self):
        """Render the templates and write to disk conditionally."""
        self.log.info('render_templates')
        self.custom_feature_py()
        self.init_py()
        self.test_profiles_py()
        self.validate_feature_py()

    def test_profiles_py(self):
        """Render the test_profiles.py template."""
        filename = 'test_profiles.py'
        self.log.info(f'Rendering {filename} template to {config_model.test_case_feature_dir}')

        # define template variables
        variables = {
            'class_name': self._app_class,
            'runtime_level': self.ij.model.runtime_level.lower(),
        }

        # render the template
        fqfn = os.path.join(config_model.test_case_feature_dir, filename)
        self.render(f'{filename}.tpl', fqfn, variables, overwrite=True)

    def validate_feature_py(self):
        """Render the validate_custom.py template."""
        if self.ij.model.runtime_level.lower() in [
            'playbook',
            'triggerservice',
            'webhooktriggerservice',
        ]:
            filename = 'validate_feature.py'
            self.log.info(f'Rendering {filename} template to {config_model.test_case_feature_dir}')

            # define template variables
            variables = {
                'feature': config_model.test_case_feature,
                'output_data': self._output_data(self.ij.tc_playbook_out_variables),
            }

            # render the template
            fqfn = os.path.join(config_model.test_case_feature_dir, filename)
            self.render(f'{filename}.tpl', fqfn, variables)
