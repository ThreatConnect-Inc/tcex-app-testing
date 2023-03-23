"""TcEx App Testing Module"""

# standard library
import sys
from typing import NoReturn

# third-party
from rich import print  # pylint: disable=redefined-builtin
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

# first-party
from tcex_app_testing.app.config.model.install_json_model import ParamsModel


class Render:
    """TcEx App Testing Module"""

    @staticmethod
    def render_failure_message(message: str) -> NoReturn:
        """Print Failure."""
        print(Panel(f'[bold red]{message}[/bold red]', title='Failure'))
        sys.exit(1)

    @staticmethod
    def render_feedback(feedback_value: bool | dict | int | list | str | None):
        """Print the value used."""
        print(Panel(f'Using [bold green]{feedback_value}[/bold green]', title='Feedback'))

    @staticmethod
    def render_input_data_table(data: ParamsModel):
        """Render template create results in a table."""
        table = Table(
            expand=True,
            show_header=False,
            show_lines=False,
            title=f'Collecting {data.type} Input',
        )

        table.add_column('Field', justify='left', style='dodger_blue2', no_wrap=True)
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

        console = Console()
        console.print(table)

    @staticmethod
    def render_invalid_bool():
        """Print a invalid bool error."""
        message = 'The provided value is not a boolean value (true/false).'
        print(Panel(message, style='bold yellow', title='Invalid Bool Value'))

    @staticmethod
    def render_invalid_exit_code():
        """Print a invalid exit code error."""
        message = 'The provided value is not a valid exit code (0, 1).'
        print(Panel(message, style='bold yellow', title='Invalid Exit Code'))

    @staticmethod
    def render_invalid_index_warning(range_: str):
        """Print Failure."""
        message = (
            f'The provided index value is not valid, please select a valid value between {range_}.'
        )
        print(Panel(message, style='bold yellow', title='Invalid Index'))

    @staticmethod
    def render_options(
        options: list[str],
        title: str = 'Options',
        subtitle: str | None = None,
        equal: bool = False,
        expand: bool = True,
    ):
        """Render template create results in a table."""
        options = [
            f'[dark_orange]{i}.[/dark_orange] [white]{o}[/white]' for i, o in enumerate(options)
        ]
        options_column = Columns(options, equal=equal, expand=expand)
        print(Panel(options_column, title=title, subtitle=subtitle))

    @staticmethod
    def render_profile(inputs: dict, staged_data: dict):
        """Render template create results in a table."""
        table_color = 'dark_orange'
        table = Table(
            expand=True,
            show_lines=False,
            style=table_color,
            title='Profile Data',
            title_style=table_color,
        )

        table.add_column('Field', header_style=table_color, justify='left', style=table_color)
        table.add_column('Value', header_style=table_color, justify='left', style=table_color)
        table.add_column('Variable', header_style=table_color, justify='left', style=table_color)

        for key, input_value in inputs.items():
            # lookup the real value from the staged data, if not found use the input value
            value = staged_data.get(input_value)
            if value is None:
                value = input_value
                input_value = 'N/A'

            table.add_row(key, str(value), input_value)

        console = Console(emoji=False)
        console.print(table)
        console.print('\n')

    @staticmethod
    def render_prompt(
        text: str, choices: list[str] | None = None, default: str | None = None
    ) -> str | None:
        """Render a prompt"""
        return Prompt.ask(text, choices=choices, default=default)

    @staticmethod
    def render_prompt_text(
        prompt_text: str, prompt_default: str | None, array_type: bool = False
    ) -> str | None:
        """Render a prompt"""
        if prompt_default:
            prompt_default = f' (default: [bold dark_orange]{prompt_default}[/bold dark_orange])'
        else:
            prompt_default = ''

        prompt_text = f'[white]{prompt_text}[/white][bold white]{prompt_default}[/bold white]'

        subtitle = '[dim dark_orange]<? for help>[/dim dark_orange]'
        if array_type is True:
            subtitle = (
                '[dim italic dark_orange]array input - hit enter on a '
                'blank input to end collection[/dim italic dark_orange]'
            )

        print(Panel(prompt_text, title='Input', subtitle=subtitle))
        # if array_type is True:
        #     array_type_text = (
        #         'array input - one entry at a time type, hit enter on a blank line to end input'
        #     )
        #     print(f'[dim italic medium_purple1]{array_type_text}[/dim italic medium_purple1]')

    @staticmethod
    def render_prompt_help():
        """Render the help information for the prompt"""
        text = Text(style='italic dark_orange')
        text.append('For String type inputs: \n')
        text.append(' • A value of null will be treated as an actual null value.\n')
        text.append(' • Using "null" or \'null\' to insert a string of null.')
        print(Panel(text, title='Help'))

    @staticmethod
    def render_required_input():
        """Render required error."""
        print('[red]This input is required, please enter an appropriate value.[/red]')

    @staticmethod
    def render_rule(message: str):
        """Render a horizontal rule."""
        console = Console()
        print('\n')
        console.rule(f'[bold dark_orange]{message}[/bold dark_orange]', style='dark_orange')
        print('\n')

    @staticmethod
    def render_template_create_results(row_data: list[list[str]], title: str):
        """Render template create results in a table."""
        table = Table(title=title, expand=True)

        table.add_column('Filename', justify='right', style='cyan', no_wrap=True)
        table.add_column('Destination', style='magenta')
        table.add_column('Status', justify='left')

        for row in row_data:
            table.add_row(*row)

        console = Console()
        console.print(table)

    @staticmethod
    def render_tip(message: str):
        """Render a tip."""
        print(Panel(message, style='dim white', title='Tip'))

    @staticmethod
    def render_warning_message(message: str):
        """Print Failure."""
        print(Panel(f'[bold yellow]{message}[/bold yellow]', title='Warning'))
