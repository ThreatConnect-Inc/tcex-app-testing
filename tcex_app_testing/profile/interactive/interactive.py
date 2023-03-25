"""TcEx Framework Module"""
# pylint: disable=too-many-lines

# standard library
import json
import re
from collections import OrderedDict
from collections.abc import Iterator
from typing import Any

# first-party
from tcex_app_testing.app.config.install_json import InstallJson
from tcex_app_testing.app.config.layout_json import LayoutJson
from tcex_app_testing.app.config.model.install_json_model import ParamsModel
from tcex_app_testing.app.config.model.layout_json_model import ParametersModel
from tcex_app_testing.app.config.permutation import Permutation
from tcex_app_testing.pleb.cached_property import cached_property
from tcex_app_testing.profile.interactive.interactive_collect import InteractiveCollect
from tcex_app_testing.profile.interactive.interactive_util import InteractiveUtil
from tcex_app_testing.profile.interactive.model.interactive_params_model import (
    InteractiveParamsModel,
)
from tcex_app_testing.render.render import Render


class Interactive:
    """Testing Profile Interactive Class."""

    def __init__(self):
        """Initialize instance properties."""

        # properties
        self._no_selection_text = 'No Selection'
        self._inputs = {
            'optional': {},
            'required': {},
        }
        self._staging_data = {'kvstore': {}}
        self._no_selection_text = 'No Selection'
        self.accent = 'dark_orange'
        self.collect = InteractiveCollect(self)
        self.exit_codes = []
        self.ij = InstallJson()
        self.lj = LayoutJson()
        self.permutation = Permutation()
        self.util = InteractiveUtil()

    def add_staging_data(self, name: str, type_: str, value: str | None) -> str | None:
        """Create staging data and return variable value.

        Args:
            name: The name of the input.
            type_: The type of input (Binary, StringArray, etc.)
            value: The value to write in the staging data.
        """
        arg_value = value
        if (
            self.ij.model.runtime_level.lower() not in ['triggerservice', 'webhooktriggerservice']
            and value is not None
        ):
            arg_value = self.ij.create_variable(name, type_)
            self._staging_data['kvstore'].setdefault(arg_value, value)

        return arg_value

    @staticmethod
    def layout_inputs(model: ParametersModel) -> dict[str, Any]:
        """Return the list of input names from the list of layout parameters"""

        result = OrderedDict()
        inputs = model.dict().get('inputs', [])
        for section in inputs:
            for input_ in section.get('parameters', []):
                name = input_.get('name')
                result[name] = input_

        return result

    @property
    def staging_data(self):
        """Return staging data dict."""
        return self._staging_data

    def add_input(self, name: str, data: ParamsModel, value: bool | str | None):
        """Add an input to inputs.

        Args:
            name: The name of the input.
            data: The install.json params object.
            value: The value for the input.
        """
        if data.required:
            self._inputs['required'].setdefault(name, value)
        else:
            self._inputs['optional'].setdefault(name, value)

    @cached_property
    def input_type_map(self):
        """Return a map of input types to presentation methods."""
        return {
            'boolean': self.present_boolean,
            'choice': self.present_choice,
            'keyvaluelist': self.present_key_value_list,
            'multichoice': self.present_multichoice,
            'string': self.present_string,
            'editchoice': self.present_editchoice,
        }

    @property
    def inputs(self) -> dict:
        """Return inputs dict."""
        return self._inputs

    def present(self):
        """Present interactive menu to build profile."""

        Render.panel.rule(f'[{self.accent}]Interactive Profile Creation[{self.accent}]')

        def params_data() -> Iterator[tuple[str, ParamsModel]]:
            # handle non-layout and layout based App appropriately
            install_inputs = self.ij.model.params_dict
            if self.lj.has_layout:
                # using inputs from layout.json since they are required to be in order
                # (display field can only use inputs previously defined)
                for name in self.layout_inputs(self.lj.model).keys():  # type: ignore
                    # get data from install.json based on name
                    data = install_inputs[name]
                    yield name, data

                # hidden fields will not be in layout.json so they need to be include manually
                for name, data in self.ij.model.filter_params(hidden=True).items():
                    yield name, data
            else:
                for name, data in install_inputs.items():
                    yield name, data

        inputs = {}
        for name, data in params_data():
            if data.service_config:
                # inputs that are serviceConfig are not applicable for profiles
                continue

            if not data.hidden:
                # each input will be checked for permutations if the App has layout and not hidden
                if not self.permutation.validate_input_variable(name, inputs):
                    continue

            # present the input
            value = self.input_type_map[data.type.lower()](name, data)

            # update inputs
            inputs[name] = value

            # render a table with the current profile values
            Render.table_profile(inputs, self.staging_data.get('kvstore', {}))

        self.present_exit_code()
        inputs['<exit_code>'] = str(self.exit_codes)

        # render a table with the current profile values
        Render.table_profile(inputs, self.staging_data.get('kvstore', {}))

    def present_boolean(self, name: str, data: ParamsModel) -> bool:
        """Build a question for boolean input.

        Args:
            name: The name of the input field.
            data: The install.json input param object.
        """
        # render header information
        Render.table_input_data(data)

        default = self.util.get_default(data)
        valid_values = ['true', 'false']

        option_default = 'false'
        option_text = ''
        options = []
        for v in valid_values:
            # in install.json all default values should be a string (e.g., "true" or "false")
            if v.lower() == str(default).lower():
                option_default = v
                v = f'[{v}]'
            options.append(v)
        option_text = f'''({'/'.join(options)})'''

        input_data_dict = data.dict()
        input_data_dict['default'] = option_default
        input_data_dict['option_text'] = option_text
        input_data_model = InteractiveParamsModel(**input_data_dict)

        value = self.collect.boolean(input_data_model)

        # add input
        self.add_input(name, data, value)

        return value

    def present_editchoice(self, name: str, data: ParamsModel) -> str | None:
        """Build a question for editchoice input.

        Args:
            name: The name of the input field.
            data: The install.json input param object.
        """
        # render header information
        Render.table_input_data(data)

        default = self.util.get_default(data)
        option_index = 0
        valid_values = self.util.expand_valid_values(data.valid_values)
        if not data.required:
            # add option to invalidate defaults
            valid_values.insert(0, self._no_selection_text)

        # default value needs to be converted to index
        if default:
            try:
                option_index = valid_values.index(default)
            except ValueError:
                # if "magic" variable (e.g., ${GROUP_TYPES}) was not expanded then use index 0.
                # there is no way to tell if the default value will be part of the expansion.
                if any(re.match(r'^\${.*}$', v) for v in valid_values):
                    option_index = 0
                else:
                    Render.panel.failure(
                        f'Invalid value of ({default}) for {data.name}, check that '
                        'default value and validValues match in install.json.'
                    )
        option_text = f'[{option_index}]'

        Render.panel.column_index(valid_values, 'Options')

        input_data_dict = data.dict()
        input_data_dict['default'] = option_index
        input_data_dict['option_text'] = option_text
        input_data_dict['valid_values'] = valid_values
        input_data_model = InteractiveParamsModel(**input_data_dict)

        # collect user input
        value = self.collect.editchoice(input_data_model)

        # add input
        self.add_input(name, data, value)

        return value

    def present_choice(self, name: str, data: ParamsModel) -> str | None:
        """Build a question for choice input.

        Args:
            name: The name of the input field.
            data: The install.json input param object.
        """
        # render header information
        Render.table_input_data(data)

        default = self.util.get_default(data)
        option_index = 0
        valid_values = self.util.expand_valid_values(data.valid_values)
        if not data.required:
            # add option to invalidate defaults
            valid_values.insert(0, self._no_selection_text)

        # default value needs to be converted to index
        if default:
            try:
                option_index = valid_values.index(default)
            except ValueError:
                # if "magic" variable (e.g., ${GROUP_TYPES}) was not expanded then use index 0.
                # there is no way to tell if the default value is be part of the expansion.
                if any(re.match(r'^\${.*}$', v) for v in valid_values):
                    option_index = 0
                else:
                    Render.panel.failure(
                        f'Invalid value of ({default}) for {data.name}, check'
                        'that default value and validValues match in install.json.'
                    )
        option_text = f'{option_index}'

        Render.panel.column_index(valid_values, 'Options')

        input_data_dict = data.dict()
        input_data_dict['default'] = option_index
        input_data_dict['option_text'] = option_text
        input_data_dict['valid_values'] = valid_values
        input_data_model = InteractiveParamsModel(**input_data_dict)

        # collect user input
        value = self.collect.choice(input_data_model)

        # add input
        self.add_input(name, data, value)

        return value

    def present_data_types(self, data_types: list, required: bool = False) -> str:
        """Present data types options.

        Args:
            data_types: A list of optional data types.
            required: If False the no selection option will be added.
        """
        if 'Any' in data_types:
            data_types = [
                'Binary',
                'BinaryArray',
                'KeyValue',
                'KeyValueArray',
                'String',
                'StringArray',
                'TCEntity',
                'TCEntityArray',
            ]

        # add option to not select an index value if input is not required
        if required is False:
            data_types.insert(0, self._no_selection_text)

        Render.panel.column_index(data_types, 'Options')

        data_type = None
        while not data_type:
            index = (
                self.collect._input_value(  # pylint: disable=protected-access
                    label=f'Select a [{self.accent}]Data Type[/{self.accent}]', option_text='0'
                )
                or 0
            )

            try:
                data_type = data_types[int(index)]
            except (IndexError, TypeError, ValueError):
                Render.panel.invalid_value(
                    (
                        f'The provided index value is not valid, please select a '
                        f'valid value between 0-{len(data_types) - 1}.'
                    ),
                    title='Invalid Index Value',
                )
                return self.present_data_types(data_types, required)

        return data_type

    def present_exit_code(self):
        """Provide user input for exit code."""
        self.exit_codes = list(set(self.collect.exit_codes(default=[0], option_text='[0]')))

    def present_key_value_list(self, name: str, data: ParamsModel):
        """Build a question for key value list input.

        Args:
            name: The name of the input field.
            data: The install.json input param object.
        """
        # render header information
        Render.table_input_data(data)

        # the default value from install.json or user_data
        default = self.util.get_default(data)  # array of default values

        input_data_dict = data.dict()
        input_data_dict['default'] = default
        input_data_model = InteractiveParamsModel(**input_data_dict)

        # collect input
        input_data = self.collect.key_value_array(input_data_model)

        # create variable
        variable = self.add_staging_data(name, 'KeyValueArray', input_data)  # type: ignore

        # add input to args
        self.add_input(name, data, variable)

        # user feedback
        feedback_data = input_data
        if input_data is not None:
            feedback_data = json.dumps(feedback_data)

        return variable

    def present_multichoice(self, name: str, data: ParamsModel) -> str | None:
        """Build a question for multichoice input.

        Args:
            name: The name of the input field.
            data: The install.json input param object.
        """
        # render header information
        Render.table_input_data(data)

        default = self.util.get_default(data)  # array of default values
        if not isinstance(default, list):
            raise RuntimeError(f'Invalid default value for {name} ({default}).')

        option_indexes = [0]
        valid_values = self.util.expand_valid_values(data.valid_values)
        if not data.required:
            # add option to invalidate defaults
            valid_values.insert(0, self._no_selection_text)

        # default values will be return as an array (e.g., one|two -> ['one'. 'two']).
        # using the valid values array we can look up these values to show as default in input.
        if default:
            option_indexes = []
            for d in default:
                try:
                    option_indexes.append(valid_values.index(d))
                except ValueError:
                    # if "magic" variable (e.g., ${GROUP_TYPES}) was not expanded then skip value.
                    # there is no way to tell if the default value is be part of the expansion.
                    if any(re.match(r'^\${.*}$', v) for v in valid_values):
                        continue

                    Render.panel.failure(
                        f'''Invalid value of ({d}) for {data.name}, check that '''
                        'default value(s) and validValues match in install.json.'
                    )
        option_text = f''' [{','.join([str(v) for v in option_indexes])}]'''

        Render.panel.column_index(valid_values, 'Options')

        input_data_dict = data.dict()
        input_data_dict['default'] = option_indexes
        input_data_dict['option_text'] = option_text
        input_data_dict['valid_values'] = valid_values
        input_data_model = InteractiveParamsModel(**input_data_dict)

        # collect user input
        values = self.collect.multichoice(input_data_model)

        # add input
        self.add_input(name, data, values)

        return values

    def present_string(self, name: str, data: ParamsModel) -> str | None:
        """Build a question for string input.

        Args:
            name: The name of the input field.
            data: The install.json input param object.
        """
        # display header information
        Render.table_input_data(data)

        # use playbook data types to determine what input to provide (default to String)
        data_type = 'String'
        if len(data.playbook_data_type) > 1 or 'any' in data.playbook_data_type:
            data_type = self.present_data_types(data.playbook_data_type, required=data.required)

        # no need to proceed if there is not valid data type selected.
        if data_type == self._no_selection_text:
            self.add_input(name, data, None)
            return None

        # the default value from install.json or user_data
        default = self.util.get_default(data)

        option_text = ''
        if default is not None:
            option_text = f'{default}'

        input_data_dict = data.dict()
        input_data_dict['data_type'] = data_type
        input_data_dict['default'] = default
        input_data_dict['option_text'] = option_text
        input_data_model = InteractiveParamsModel(**input_data_dict)

        # collect input from user
        input_value = self.collect.type_map[data_type](input_data_model)

        # add staging data and get variable name
        variable = self.add_staging_data(name, data_type, input_value)

        # add input
        self.add_input(name, data, variable)

        return variable
