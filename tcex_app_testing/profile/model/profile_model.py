"""TcEx Framework Module"""
# pylint: disable=no-self-argument
# standard library
import json
from collections.abc import Iterator
from typing import Any

# third-party
from pydantic import BaseModel, Extra, Field, validator

# first-party
from tcex_app_testing.app.config import InstallJson, LayoutJson, Permutation
from tcex_app_testing.env_store import EnvStore
from tcex_app_testing.pleb.cached_property import cached_property
from tcex_app_testing.util import Util

# instantiate EnvStore object
env_store = EnvStore()

# instantiate InstallJson object
ij = InstallJson()

# instantiate LayoutJson object
lj = LayoutJson()

# instantiate Permutation object
permutation = Permutation()

# instantiate Util object
util = Util()


class ExitMessageModel(BaseModel):
    """Exit Message Model"""

    expected_output: str = Field('', description='Expected Output')
    op: str = Field('eq', description='The operator for the output validation.')


class InputsModel(BaseModel):
    """Input Model"""

    defaults: dict[str, bool | str | None] | None = Field({}, description='')
    optional: dict[str, bool | str | None] | None = Field({}, description='')
    required: dict[str, bool | str | None] | None = Field({}, description='')

    class Config:
        """DataModel Config"""

        smart_union = True


class ConfigsModel(BaseModel):
    """Configs Model

    "configs": [
        {
            "config": {
                "optional": {},
                "required": {}
            },
            "trigger_id": "2959" }
    ]
    """

    config: InputsModel = Field(..., description='')
    trigger_id: str = Field(..., description='')


class KvstoreModel(BaseModel):
    """KV Store Model"""

    value: list[dict] | dict | list[str] | str | None = Field(
        ..., description='The value to store in the KV Store for the provided variable.'
    )
    variable: str = Field(
        ..., description='The PB variable value (e.g., #App:0002:string_3!String).'
    )


class StageModel(BaseModel):
    """Stage Model"""

    # kvstore: Optional[Dict[str, Union[bool, List[dict], dict, List[str], str]]] = Field(
    kvstore: dict = Field({}, description='')


class ProfileModel(BaseModel):
    """Profile Model"""

    _comments_: list[str] | None = Field(
        [], description='A list of comment for this specific test profile.'
    )
    custom: dict | None = Field(None, description='Custom data for this profile.')
    environments: list[str] = Field(
        ['build'],
        description='A list of environments in which this profile should run.',
    )
    exit_codes: list[int] = Field([0], description='')
    exit_message: ExitMessageModel = Field(..., description='')
    inputs: InputsModel = Field(..., description='One of more inputs for the App.')
    initialized: bool = Field(
        False,
        description='True, if test profile has been initialized with exit message and outputs.',
    )
    outputs: dict | None = Field(
        {},
        description='One of more output for the App.',
        runtime_levels=['playbook', 'triggerservice', 'webhooktriggerservice'],
    )
    schema_version: str = Field(
        '1.0.0',
        description='The version of the profile schema.',
    )
    stage: StageModel = Field(
        ...,
        description='A StageModel object.',
        runtime_levels=['organization', 'playbook', 'triggerservice', 'webhooktriggerservice'],
    )
    validation_criteria: dict | None = Field(
        {'count': 0, 'percent': 0},
        description='',
        runtime_levels=['organization'],
    )

    @validator('exit_message', always=True, pre=True)
    def _exit_message(cls, v):
        if not v:
            return ExitMessageModel(**{})
        return v

    @validator('inputs', always=True, pre=True)
    def _inputs(cls, v):
        if not v:
            return InputsModel(**{})
        return v

    @validator('stage', always=True, pre=True)
    def _stage(cls, v):
        if not v:
            return StageModel(**{})
        return v

    class Config:
        """DataModel Config"""

        extra = Extra.allow
        keep_untouched = (cached_property,)
        validate_assignment = True

    @staticmethod
    def flatten_inputs(inputs: dict) -> dict[str, Any]:
        """Flatten the inputs dict."""
        inputs_flattened = dict(inputs.get('defaults') or {})
        inputs_flattened.update(inputs.get('optional') or {})
        inputs_flattened.update(inputs.get('required') or {})
        return inputs_flattened

    def get_input(self, name: str) -> dict | str:
        """Return the value of the input."""
        return self.inputs_flattened.get(name) or {}

    def get_input_resolved(self, name: str) -> dict[str, Any]:
        """Return the value of the input."""
        return self.inputs_flattened_staging.get(name) or {}

    def get_output(self, variable: str) -> dict[str, Any]:
        """Return the value of the input."""
        if isinstance(self.outputs, dict):
            return self.outputs.get(variable) or {}
        return {}

    @cached_property
    def inputs_flattened(self) -> dict[str, str]:
        """Flatten the inputs dict."""
        return self.flatten_inputs(self.inputs.dict())

    @cached_property
    def inputs_flattened_staging(self) -> dict[str, Any]:
        """Return inputs data with value from staging data if required.

        For playbook App the inputs are usually referenced as a PB variable. This
        data is defined in the "stage" section of the profile. To get inputs with
        the resolved (original) value, the value is resolved from the staging data.
        """
        _resolved = {}
        for name, value in self.inputs_flattened.items():
            if util.is_playbook_variable(value) is True:
                value = self.stage.kvstore.get(value, value)
            _resolved[name] = value
        return _resolved

    def ordered_json(
        self,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        exclude_unset: bool = False,
        indent: int | None = None,
    ) -> str:
        """Return model ordered."""
        # load dict from model
        model_dict = self.dict(
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            exclude_unset=exclude_unset,
        )
        schema_properties: dict[str, Any] = self.schema()['properties']

        # define output field order
        top_level_order = [
            '_comments_',
            'environments',
            'stage',
            'inputs',
            'custom',
            'exit_message',
            'outputs',
            'exit_codes',
            'schema_version',
        ]

        # reorder data
        _ordered_model = {}
        for key in top_level_order:
            _data = model_dict.pop(key, None)

            # do not include fields that are not intended for the runtime_level of the App
            runtime_levels = schema_properties.get(key, {}).get('runtime_levels')
            if runtime_levels is not None and ij.model.runtime_level.lower() not in runtime_levels:
                continue

            # exclude null values
            if _data is None and exclude_none is True:
                continue

            # excluding none can cause issue for staging and input data. however, there
            # are some fields that if not set, should be excluded in the profile.
            if key in ['custom'] and _data is None:
                continue

            # sort data that is a dict or a list
            if isinstance(_data, dict):
                # sort nested keys
                _data = json.loads(json.dumps(_data, sort_keys=True))
            elif isinstance(_data, list):
                _data = sorted(_data)

            # add data to response
            _ordered_model[key] = _data

        # process any key that was missed
        for key in model_dict:
            runtime_levels = schema_properties.get(key, {}).get('runtime_levels')
            if runtime_levels is not None and ij.model.runtime_level.lower() not in runtime_levels:
                continue

            _ordered_model[key] = model_dict[key]

        return json.dumps(_ordered_model, indent=indent)

    @property
    def profile_inputs(self) -> Iterator[dict[str, dict[str, bool | str]]]:
        """Return the appropriate inputs/config for the current App type.

        Example Response:
        {
          "optional": {},
          "required": {
            "array_data": "#App:1234:array_data!KeyValueArray",
            "tc_action": "Build"
          }
        }
        """
        # InputsModel to dict
        yield self.inputs.dict()

    @property
    def profile_inputs_params(self):
        """Return params for inputs."""
        # handle non-layout and layout based App appropriately
        for profile_inputs in self.profile_inputs:
            if lj.has_layout:
                # using inputs from layout.json since they are required to be in order
                # (display field can only use inputs previously defined)
                params = {}
                for key in lj.model.param_names:
                    # get data from install.json based on name
                    params[key] = ij.model.get_param(key)

                # hidden fields will not be in layout.json so they need to be included manually
                params.update(ij.model.filter_params(hidden=True))
            else:
                # params section of install.json build as dict
                params = ij.model.params_dict

            yield profile_inputs, params
