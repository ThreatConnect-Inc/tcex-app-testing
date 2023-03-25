"""TcEx Framework Module"""
# standard library
import os

# first-party
from tcex_app_testing.config_model import config_model
from tcex_app_testing.templates.templates_abc import TemplatesABC


class TemplatesTests(TemplatesABC):
    """Template Tests Module."""

    def conftest_py(self):
        """Render template file."""
        filename = 'conftest.py'
        self.log.info(f'Rendering {filename} template to {config_model.test_case_dir}')

        # render the template
        fqfn = os.path.join(config_model.test_case_dir, filename)
        self.render(f'{filename}.tpl', fqfn, overwrite=True)

    def custom_py(self):
        """Render the custom.py template."""
        filename = 'custom.py'
        self.log.info(f'Rendering {filename} template to {config_model.test_case_dir}')

        # define template variables
        variables = {'runtime_level': self.ij.model.runtime_level.lower()}

        # render the template
        fqfn = os.path.join(config_model.test_case_dir, filename)
        self.render(f'{filename}.tpl', fqfn, variables)

    def init_py(self):
        """Render template file."""
        filename = '__init__.py'
        self.log.info(f'Rendering {filename} template to {config_model.test_case_dir}')

        # define template variables
        variables = {'type': 'Suite'}

        # render the template
        fqfn = os.path.join(config_model.test_case_dir, filename)
        self.render(f'{filename}.tpl', fqfn, variables, overwrite=True)

    def render_templates(self):
        """Render all templates"""
        self.init_py()
        self.conftest_py()
        self.custom_py()
        self.test_global_py()
        self.validate_py()
        self.validate_custom_py()

    def test_global_py(self):
        """Render template file."""
        filename = 'test_global.py'
        self.log.info(f'Rendering {filename} template to {config_model.test_case_dir}')

        # render the template
        fqfn = os.path.join(config_model.test_case_dir, filename)
        self.render(f'{filename}.tpl', fqfn, overwrite=True)

    def validate_py(self):
        """Render the validate.py template."""
        if self.ij.model.runtime_level.lower() in [
            'playbook',
            'triggerservice',
            'webhooktriggerservice',
        ]:
            filename = 'validate.py'
            self.log.info(f'Rendering {filename} template to {config_model.test_case_dir}')

            # define template variables
            variables = {
                'feature': config_model.test_case_feature,
                'output_data': self._output_data(self.ij.tc_playbook_out_variables),
            }

            # render the template
            fqfn = os.path.join(config_model.test_case_dir, filename)
            self.render(f'{filename}.tpl', fqfn, variables, overwrite=True)

    def validate_custom_py(self):
        """Render the validate_custom.py template."""
        if self.ij.model.runtime_level.lower() in [
            'playbook',
            'triggerservice',
            'webhooktriggerservice',
        ]:
            filename = 'validate_custom.py'
            self.log.info(f'Rendering {filename} template to {config_model.test_case_dir}')

            # define template variables
            variables = {
                'feature': config_model.test_case_feature,
                'output_data': self._output_data(self.ij.tc_playbook_out_variables),
            }

            # render the template
            fqfn = os.path.join(config_model.test_case_dir, filename)
            self.render(f'{filename}.tpl', fqfn, variables)
