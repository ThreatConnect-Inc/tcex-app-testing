"""TcEx Framework Module"""

# third-party
from pydantic import Field

# first-party
from tcex_app_testing.app.config.model.install_json_model import ParamsModel


class InteractiveParamsModel(ParamsModel):
    """Interactive Params Model"""

    data_type: str | None = Field(None, description='The data type for the profile input.')
    default: bool | int | list | str | None = Field(
        None, description='The default for the interactive profile.'
    )
    option_text: str | None = Field(None, description='The text to display for the option.')
    valid_values: list[str] = Field(
        [],
        description=(
            'Optional property to be used with the Choice, MultiChoice, and String input '
            'types to provide pre-defined inputs for the user selection.'
        ),
    )

    @property
    def array_type(self):
        """Return array type."""
        if self.data_type is not None and self.data_type.endswith('Array'):
            return True
        return False

    class Config:
        """DataModel Config"""

        alias_generator = None
