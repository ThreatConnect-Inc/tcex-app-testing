"""TcEx Framework Module"""

# third-party
from rich import print  # pylint: disable=redefined-builtin
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# first-party
from tcex_app_testing.app.config.model.install_json_model import ParamsModel
from tcex_app_testing.util.render.render import Render as RenderUtil


class Render(RenderUtil):
    """Render CLI Output"""

    @classmethod
    def panel_help(cls):
        """Render the help information for the prompt"""
        text = Text(style=f'italic {cls.accent}')
        text.append('For String type inputs: \n')
        text.append(' • A value of null will be treated as an actual null value.\n')
        text.append(' • Using "null" or \'null\' to insert a string of null.')
        print(Panel(text, title='Help', title_align=cls.title_align))

    @classmethod
    def table_file_results(cls, row_data: list[list[str]], title: str):
        """Render template create results in a table."""
        table = Table(
            border_style='dim',
            expand=True,
            show_edge=False,
            show_header=False,
        )

        table.add_column(
            'Filename',
            max_width=20,
            min_width=20,
            no_wrap=True,
            style=cls.accent2,
        )
        table.add_column(
            'Destination',
            max_width=70,
            min_width=70,
            style='',
        )
        table.add_column(
            'Status',
            max_width=10,
            min_width=10,
            style='',
        )

        for row in row_data:
            table.add_row(*row)

        print(Panel(table, title=title, title_align=cls.title_align))

    @classmethod
    def table_input_data(cls, data: ParamsModel):
        """Render template create results in a table."""
        table = Table(
            border_style='',
            expand=True,
            show_edge=False,
            show_header=False,
        )

        table.add_column('Field', justify='left', style=cls.accent2, no_wrap=True)
        table.add_column('Value', justify='left', style='bold')

        table.add_row('Label', data.label)
        table.add_row('Type', data.type)

        if data.default is not None:
            table.add_row('Default', str(data.default))

        if data.note is not None:
            table.add_row('Note', data.note)

        table.add_row('Required', str(data.required).lower())

        if data.hidden:
            table.add_row('Hidden', 'true')

        pbt = ','.join(data.playbook_data_type)
        if pbt:
            table.add_row('Playbook Data Types', pbt)

        vv = ','.join(data.valid_values)
        if vv:
            table.add_row('Valid Values', vv)

        print(Panel(table, title=f'Collecting {data.type} Input', title_align=cls.title_align))

    @classmethod
    def table_profile(cls, inputs: dict, staged_data: dict):
        """Render template create results in a table."""
        table = Table(
            border_style='dim',
            expand=True,
            show_edge=False,
            show_header=False,
            # show_lines=False,
            style='dim',
        )

        table.add_column('Field', header_style=cls.accent, justify='left', style=cls.accent)
        table.add_column('Value', header_style=cls.accent, justify='left', style=cls.accent)
        table.add_column('Variable', header_style=cls.accent, justify='left', style=cls.accent)

        for key, input_value in inputs.items():
            # lookup the real value from the staged data, if not found use the input value
            value = staged_data.get(input_value)
            if value is None:
                value = input_value
                input_value = 'N/A'

            table.add_row(key, str(value), input_value)

        console = Console(emoji=False)
        console.print(Panel(table, title='Profile Data', title_align=cls.title_align))
