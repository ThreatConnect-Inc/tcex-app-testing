"""TcEx Framework Module"""

# standard library
from base64 import b64encode
from collections.abc import Callable
from typing import TYPE_CHECKING, cast

# first-party
from tcex_app_testing.pleb.cached_property import cached_property
from tcex_app_testing.profile.interactive.model.interactive_params_model import (
    InteractiveParamsModel,
)
from tcex_app_testing.render.render import Render
from tcex_app_testing.util import Util

if TYPE_CHECKING:
    from .interactive import Interactive  # CIRCULAR-IMPORT


class InteractiveCollect:
    """TcEx App Testing Module."""

    def __init__(self, present: 'Interactive'):
        """Initialize instance properties."""
        self.present = present

        # properties
        self._no_selection_text = 'No Selection'
        self.accent = 'dark_orange'

    def _input_value(
        self, label: str, array_type: bool = False, option_text: str | None = None
    ) -> str:
        """Return user input.

        Args:
            label: The label to display to the user.
            option_text: the Option text to display to the user.
            array_type: If the input is an array type.
        """
        prompt_default = option_text or ''
        if prompt_default:
            prompt_default = (
                f' (default: [bold {self.accent}]{prompt_default}[/bold {self.accent}])'
            )
        else:
            prompt_default = ''

        subtitle = f'[dim {self.accent}]? for help[/dim {self.accent}]'
        if array_type is True:
            subtitle = (
                f'[dim italic {self.accent}]array input - hit enter on a '
                f'blank input to end collection[/dim italic {self.accent}]'
            )

        # collect response
        response = Render.prompt.input(label, prompt_default, subtitle)

        # handle special user inputs
        if response == '?':
            Render.panel_help()
            return self._input_value(label, array_type=array_type, option_text=option_text)

        return response

    @cached_property
    def type_map(self) -> dict[str, Callable]:
        """Return a map of collect type to collect method."""
        return {
            'Any': self.string,
            'Binary': self.binary,
            'BinaryArray': self.binary_array,
            'KeyValue': self.key_value,
            'KeyValueArray': self.key_value_array,
            'String': self.string,
            'StringArray': self.string_array,
            'TCEntity': self.tcentity,
            'TCEntityArray': self.tcentity_array,
        }

    def binary(self, input_data_model: InteractiveParamsModel) -> str:
        """Collect binary data."""
        # collect input value
        input_value: str = self._input_value(
            (
                f'Collecting [bold {self.accent}]Binary[/bold {self.accent}] input '
                f'for [bold {self.accent}]"{input_data_model.label}"[/bold {self.accent}]'
            ),
            array_type=input_data_model.array_type,
            option_text=input_data_model.option_text,
        )
        if not input_value:
            # if no default value and required force user to input again
            if input_data_model.default is None and input_data_model.required is True:
                Render.panel.error('This input is required, please enter an appropriate value.')
                return self.binary(input_data_model)

        if input_value not in [None, '']:
            input_value = b64encode(input_value.encode()).decode()

        return input_value

    def binary_array(self, input_data_model: InteractiveParamsModel) -> list | None:
        """Collect binary array data."""
        input_values = []
        while True:
            input_value = self.binary(input_data_model)
            if not input_value:
                break
            input_values.append(input_value)

            input_data_model.required = False  # only the first input is required

        if not input_values:
            # return None to ensure data doesn't get added to inputs
            input_values = None

        return input_values

    def boolean(self, input_data_model: InteractiveParamsModel) -> bool:
        """Collect binary data."""
        input_value = self._input_value(
            (
                f'Collecting [bold {self.accent}]Boolean[/bold {self.accent}] input '
                f'for [bold {self.accent}]"{input_data_model.label}"[/bold {self.accent}]'
            ),
            option_text=input_data_model.option_text,
        )
        if input_value == '':
            input_value = input_data_model.default

        if str(input_value).lower() not in ['0', 'f', 'false', '1', 't', 'true']:
            Render.panel.invalid_value(
                'The provided value is not a boolean value (true/false).',
                title='Invalid Boolean Value',
            )
            return self.boolean(input_data_model)

        input_value = cast(str, input_value)

        # convert input value to a proper boolean
        input_value = Util.to_bool(input_value)

        return input_value

    def editchoice(self, input_data_model: InteractiveParamsModel) -> str | None:
        """Collect edit choice data."""
        # collect input value from user and set default if required
        input_value = self._input_value(
            (
                f'Collecting [bold {self.accent}]EditChoice[/bold {self.accent}] input '
                f'for [bold {self.accent}]"{input_data_model.label}"[/bold {self.accent}]'
            ),
            option_text=input_data_model.option_text,
        )
        if not input and isinstance(input_data_model.default, str):
            input_value = input_data_model.default

        # ensure input value is provided when input is required
        if input_value is None and input_data_model.required is True:
            Render.panel.error('This input is required, please enter an appropriate value.')
            return self.editchoice(input_data_model)

        # if input value is None then there is not need to continue
        if input_value is None:
            return input_value

        # convert to int or recollect input
        try:
            input_value_ = int(input_value)
            is_between = 0 <= input_value_ <= (len(input_data_model.valid_values) - 1)
            if not is_between:
                Render.panel.invalid_value(
                    (
                        f'The provided index value is not valid, please select a '
                        f'valid value between 0-{len(input_data_model.valid_values) - 1}.'
                    ),
                    title='Invalid Index Value',
                )
                return self.editchoice(input_data_model)
            input_value = input_data_model.valid_values[input_value_]
            if input_value == self._no_selection_text:
                # special case for when user select no selection
                input_value = None

        except ValueError:
            Render.panel.info(f'Using custom input {input_value}.', title='Custom Input')

        if input_value is None:
            return None

        return input_value

    def choice(self, input_data_model: InteractiveParamsModel) -> str | None:
        """Collect choice data."""
        # collect input value from user and set default if required
        input_value = self._input_value(
            (
                f'Collecting [bold {self.accent}]Choice[/bold {self.accent}] input '
                f'for [bold {self.accent}]"{input_data_model.label}"[/bold {self.accent}]'
            ),
            array_type=input_data_model.array_type,
            option_text=input_data_model.option_text,
        )

        # set default value if no input provided (default can only be int or str)
        if not input_value and (
            input_data_model.default is None or isinstance(input_data_model.default, (int, str))
        ):
            input_value = input_data_model.default

        # ensure input value is provided when input is required
        if input_value is None and input_data_model.required is True:
            Render.panel.error('This input is required, please enter an appropriate value.')
            return self.choice(input_data_model)

        # if input value is None then there is not need to continue
        if input_value is None:
            return input_value

        # convert to int or recollect input
        try:
            input_value = int(input_value)
        except ValueError:
            Render.panel.invalid_value(
                (
                    f'The provided index value is not valid, please select a '
                    f'valid value between 0-{len(input_data_model.valid_values) - 1}.'
                ),
                title='Invalid Index Value',
            )
            return self.choice(input_data_model)

        # ensure input value is valid
        valid_index_values = [i for i, _ in enumerate(input_data_model.valid_values)]
        if input_value not in valid_index_values:
            Render.panel.invalid_value(
                (
                    f'The provided index value is not valid, please select a '
                    f'valid value between 0-{len(input_data_model.valid_values) - 1}.'
                ),
                title='Invalid Index Value',
            )
            return self.choice(input_data_model)

        # using index value provided by user, set value to valid value
        input_value = input_data_model.valid_values[input_value]
        if input_value == self._no_selection_text:
            # special case for when user select no selection
            input_value = None

        return input_value

    def exit_code(self, **kwargs) -> int | None:
        """Collect exit codes.

        Args:
            array_type (bool, kwargs): If True the user can provide multiple values.
            option_text (str, kwargs): The text shown to the user.
        """
        array_type = kwargs.get('array_type', False)
        option_text = kwargs.get('option_text')

        input_value = self._input_value(
            f'Collection [bold {self.accent}]Exit Code[/bold {self.accent}]',
            array_type=array_type,
            option_text=option_text,
        )

        if input_value != '':
            try:
                input_value = int(input_value)
            except ValueError:
                Render.panel.invalid_value(
                    'The provided value is not a valid exit code (0, 1).', title='Invalid Exit Code'
                )
                return self.exit_code(**kwargs)

            if input_value not in [0, 1, 3, 4]:
                Render.panel.invalid_value(
                    'The provided value is not a valid exit code (0, 1).', title='Invalid Exit Code'
                )
                return self.exit_code(**kwargs)

        return input_value  # type: ignore

    def exit_codes(self, **kwargs) -> list:
        """Collect exit codes."""
        input_values = []
        while True:
            input_value = self.exit_code(array_type=True, **kwargs)
            if input_value == '':
                break
            input_values.append(input_value)

        if not input_values:
            # return None to ensure data doesn't get added to inputs
            input_values = [0]

        return input_values

    def key_value(self, input_data_model: InteractiveParamsModel) -> dict | None:
        """Collect key value data."""
        input_value = None
        key = self._input_value(
            (
                f'Collecting [bold {self.accent}]Key[/bold {self.accent}]Value input '
                f'for [bold {self.accent}]"{input_data_model.label}"[/bold {self.accent}]'
            ),
            array_type=input_data_model.array_type,
            option_text=input_data_model.option_text,
        )

        # ensure input value is provided when input is required
        if key == '' and input_data_model.required is True:
            Render.panel.error('This input is required, please enter an appropriate value.')
            return self.key_value(input_data_model)

        if key != '':
            value = self._input_value(
                (
                    f'Collecting Key[bold {self.accent}]Value[/bold {self.accent}] input '
                    f'for [bold {self.accent}]"{input_data_model.label}"[/bold {self.accent}]'
                ),
                array_type=input_data_model.array_type,
            )
            input_value = {'key': key, 'value': value}

        return input_value

    def key_value_array(self, input_data_model: InteractiveParamsModel) -> list | None:
        """Collect key value array data."""
        input_values = []
        while True:
            input_value = self.key_value(input_data_model)
            if not input_value:
                break
            input_values.append(input_value)

            # unset required after collecting the first value
            input_data_model.required = False

        if not input_values:
            # return None to ensure data doesn't get added to inputs
            input_values = None

        return input_values

    def multichoice(self, input_data_model: InteractiveParamsModel) -> str | None:
        """Collect multichoice data."""
        input_values = []
        while True:
            input_value = self.choice(input_data_model)
            if not input_value:
                break
            input_values.append(input_value)

            # unset required after collecting the first value
            input_data_model.required = False

        input_values = list(set(input_values))
        if input_values:
            # format multichoice value as pipe delimited string
            input_values = '|'.join(input_values)
        else:
            # return None to ensure data doesn't get added to inputs
            input_values = None

        return input_values

    def string(self, input_data_model: InteractiveParamsModel) -> str | None:
        """Collect string data."""
        input_value = self._input_value(
            label=(
                f'Collecting [bold {self.accent}]String[/bold {self.accent}] input '
                f'for [bold {self.accent}]"{input_data_model.label}"[/bold {self.accent}]'
            ),
            array_type=input_data_model.array_type,
            option_text=input_data_model.option_text,
        )
        if not input_value and (
            input_data_model.default is None or isinstance(input_data_model.default, str)
        ):
            input_value = input_data_model.default

        if input_value is None and input_data_model.required is True:
            Render.panel.error('This input is required, please enter an appropriate value.')
            return self.string(input_data_model)

        # APP-622 - handle null/None values
        if input_value == 'null':
            input_value = None
        elif input_value in ['"null"', "'null'"]:
            input_value = 'null'

        # default for String type will always be None or str
        return input_value

    def string_array(self, input_data_model: InteractiveParamsModel) -> list | None:
        """Collect string array data."""
        # reset default/option_text values to None. these fields can't be used with array_type.
        input_data_model.default = None
        input_data_model.option_text = None

        input_values = []
        while True:
            input_value = self.string(input_data_model)
            if not input_value:
                break
            input_values.append(input_value)

            # unset required after collecting the first value
            input_data_model.required = False

        if not input_values:
            # return None to ensure data doesn't get added to inputs
            input_values = None

        return input_values

    def tcentity(self, input_data_model: InteractiveParamsModel) -> dict | None:
        """Collect tcentity data."""
        input_value = None
        id_ = self._input_value(
            (
                f'Collecting [bold {self.accent}]TCEntity Id[/bold {self.accent}] input '
                f'for [bold {self.accent}]"{input_data_model.label}"[/bold {self.accent}]'
            ),
            array_type=input_data_model.array_type,
        )
        if id_:
            value = self._input_value(
                (
                    f'Collecting [bold {self.accent}]TCEntity Value[/bold {self.accent}] input '
                    f'for [bold {self.accent}]"{input_data_model.label}"[/bold {self.accent}]'
                ),
                array_type=input_data_model.array_type,
            )
            type_ = self._input_value(
                (
                    f'Collecting [bold {self.accent}]TCEntity Type[/bold {self.accent}] input '
                    f'for [bold {self.accent}]"{input_data_model.label}"[/bold {self.accent}]'
                ),
                array_type=input_data_model.array_type,
            )
            input_value = {'id': id_, 'value': value, 'type': type_}

        if input_value is None and input_data_model.required is True:
            Render.panel.error('This input is required, please enter an appropriate value.')
            return self.tcentity(input_data_model)

        return input_value

    def tcentity_array(self, input_data_model: InteractiveParamsModel) -> list | None:
        """Collect tcentity array data."""
        input_values = []
        while True:
            input_value = self.tcentity(input_data_model)
            if not input_value:
                break
            input_values.append(input_value)

            # unset required after collecting the first value
            input_data_model.required = False

        if not input_values:
            # return None to ensure data doesn't get added to inputs
            input_values = None

        return input_values
