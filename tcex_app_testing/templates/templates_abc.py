"""TcEx Framework Module"""
# standard library
import logging
import os
import zipfile

# third-party
from mako.template import Template

# first-party
from tcex_app_testing.app.config.install_json import InstallJson
from tcex_app_testing.util import Util
from tcex_app_testing.util.code_operation import CodeOperation

# get logger
_logger = logging.getLogger(__name__.split('.', maxsplit=1)[0])


class TemplatesABC:
    """Base class for template module."""

    def __init__(self):
        """Initialize class properties."""

        # properties
        self._base_dir = os.path.abspath(os.path.dirname(__file__))
        self.ij = InstallJson()
        self.log = _logger
        self.results = []
        self.util = Util()

    def _output_data(self, output_variables: list | None):
        """Return formatted output data.

        variable format: #App:9876:http.content!Binary
        """
        output_data = []
        for ov in output_variables or []:
            output_data.append({'method': self._variable_method_name(ov), 'variable': ov})
        return sorted(output_data, key=lambda i: i['method'])

    def _variable_method_name(self, variable: str) -> str:
        """Convert #App:1234:variable!type -> variable_type"""
        variable_model = self.util.get_playbook_variable_model(variable)
        if variable_model is None:
            raise RuntimeError(f'Invalid variable {variable}')
        return f'''{variable_model.key.replace('.', '_')}_{variable_model.type.lower()}'''

    def get_template(self, filename: str) -> str:
        """Get the specified file, optionally out of an egg in the path."""
        fqfn = os.path.join(self._base_dir, filename)
        self.log.info(f'get_template: {fqfn}')

        egg_path = []
        internal_path = []

        in_egg = False
        for part in fqfn.split('/'):
            if not in_egg:
                egg_path.append(part)
                if part.endswith('.zip') or part.endswith('.egg'):
                    in_egg = True
            else:
                internal_path.append(part)

        if not in_egg:
            with open(fqfn, encoding='utf-8') as fh:
                return fh.read()

        egg = zipfile.ZipFile('/'.join(egg_path), mode='r')  # pylint: disable=consider-using-with
        internal_name = '/'.join(internal_path)

        if internal_name not in egg.namelist():
            self.log.error(f'{internal_name} not found in egg.')
            raise FileNotFoundError(internal_name)

        return egg.read(internal_name).decode('utf-8')

    def render(
        self,
        template_name: str,
        destination: str,
        variables: dict | None = None,
        overwrite: bool = False,
    ):
        """Render the provided template"""
        variables = variables or {}

        status = '[red]Failed[/red]'
        if not os.path.isfile(destination) or overwrite:
            template_data = self.get_template(template_name)
            template = Template(template_data)  # nosec
            rendered_template = template.render(**variables)
            self.log.debug(f'template-destination={destination}')
            with open(destination, 'w', encoding='utf-8') as f:
                f.write(CodeOperation.format_code(rendered_template))
            status = '[green]Success[/green]'
        else:
            status = '[yellow]Skipped[/yellow]'

        self.results.append([template_name.replace('.tpl', ''), destination, status])
