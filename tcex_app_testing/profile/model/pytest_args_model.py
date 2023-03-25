"""TcEx Framework Module"""


# third-party
from pydantic import BaseModel, Field


class PytestArgsModel(BaseModel):
    """Model Definition"""

    merge_inputs: bool = Field(
        False,
        description='Merge inputs from profile with inputs from PB execution.',
    )
    replace_exit_message: bool = Field(
        False, description='Replace exit message from profile with exit message from PB execution.'
    )
    replace_outputs: bool = Field(
        False, description='Replace outputs from profile with outputs from PB execution.'
    )

    @property
    def updated(self) -> bool:
        """Return True if profile should be updated."""
        return any(
            [
                self.merge_inputs,
                self.replace_exit_message,
                self.replace_outputs,
            ]
        )
