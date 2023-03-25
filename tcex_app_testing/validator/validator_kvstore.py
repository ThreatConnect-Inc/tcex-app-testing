"""TcEx Framework Module"""
# standard library
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    # first-party
    from tcex_app_testing.validator import Validator  # CIRCULAR-IMPORT


class ValidatorKvstore:
    """Validates Redis data"""

    def __init__(self, validator: 'Validator'):
        """Initialize class properties."""
        self.playbook = validator.playbook
        self.redis_client = validator.redis_client
        self.validator = validator

        # Properties
        self.log = self.validator.log

    def _read_variable(self, variable: str) -> Any:
        if variable.endswith('Binary'):
            app_data = self.playbook.read.binary(variable, False, False)
        elif variable.endswith('BinaryArray'):
            app_data = self.playbook.read.binary_array(variable, False, False)
        else:
            app_data = self.playbook.read.variable(variable)
        return app_data

    def data(
        self, variable: str, test_data: dict | int | list | str, op: str | None = None, **kwargs
    ) -> tuple:
        """Validate Redis data <operator> test_data.

        Args:
            variable: The variable to read from REDIS.
            test_data: The validation data.
            op: The comparison operator expression. Defaults to "eq".
        """
        # remove comment field from kwargs if it exists
        kwargs.pop('comment', None)

        # log skipped validations here so that variable can be logged
        if op == 'skip':
            self.log.warning(f'step=validate, event=skipped-validation variable={variable}')

        op = op or 'eq'
        if not variable:
            self.log.error('step=validate, event=kvstore-variable-not-provided')
            return False, None

        if not self.validator.get_operator(op):
            self.log.error(f'step=validate, event=invalid-operator-provided, operator={op}')
            return False, None

        app_data = self._read_variable(variable)

        # run operator
        passed, details = self.validator.get_operator(op)(app_data, test_data, **kwargs)

        # log validation data in a readable format
        self.validator.validate_log_output(passed, app_data, test_data, details.strip(), op)

        # build assert error
        assert_error = (
            f'\n Variable      : {variable}\n'
            f' App Data      : {app_data}\n'
            f' Operator      : {op}\n'
            f' Expected Data : {test_data}\n'
        )
        if details:
            assert_error += f' Details       : {details}\n'
        return passed, assert_error

    def not_null(self, variable: str) -> bool:
        """Validate that a variable is not empty/null"""
        # Could do something like self.ne(variable, None), but want to be pretty specific on
        # the errors on this one
        variable_data = self.playbook.read.variable(variable)
        self.log.info(
            f'step=validate, event=not-null, variable={variable}, db-data={variable_data}'
        )
        if not variable:
            self.log.error('step=validate, event=kvstore-variable-not-provided')
            return False

        if not variable_data:
            self.log.error(
                f'step=validate, event=kvstore-variable-not-provided, variable={variable}'
            )
            return False

        return True

    def type(self, variable: str) -> bool:
        """Validate the type of a redis variable"""
        variable_data = self.playbook.read.variable(variable)
        self.log.info(
            f'step=validate, event=validate-type, variable={variable}, db-data={variable_data}'
        )
        variable_type = self.playbook.get_variable_type(variable)
        if variable_type.endswith('Array'):
            variable_type = list
        elif variable_type.startswith('String'):
            variable_type = str
        elif variable_type.startswith('KeyValuePair'):
            variable_type = dict
        else:
            variable_type = str

        if not variable_data:
            self.log.error(
                f'step=validate, event=kvstore-variable-not-provided, variable={variable}'
            )
            return False
        if not isinstance(variable_data, variable_type):
            self.log.error(
                f'step=validate, event=variable-type-mismatch, '
                f'variable-type={variable_type}, variable={variable}'
            )
            return False

        return True

    #
    # Operators
    #

    def eq(self, variable: str, data: Any) -> tuple:
        """Validate test data equality"""
        return self.data(variable, data)

    def dd(self, variable: str, data: Any, **kwargs) -> tuple:
        """Validate test data equality"""
        return self.data(variable, data, op='dd', **kwargs)

    def ge(self, variable: str, data: int | str) -> tuple:
        """Validate test data equality"""
        return self.data(variable, data, op='ge')

    def gt(self, variable: str, data: int | str) -> tuple:
        """Validate test data equality"""
        return self.data(variable, data, op='gt')

    def jeq(self, variable: str, data: dict | list | str, **kwargs) -> tuple:
        """Validate JSON data equality"""
        return self.data(variable, data, op='jeq', **kwargs)

    def json_eq(self, variable: str, data: dict | list | str, **kwargs) -> tuple:
        """Validate JSON data equality"""
        return self.data(variable, data, op='jeq', **kwargs)

    def kveq(self, variable: str, data: dict | list, **kwargs) -> tuple:
        """Validate JSON data equality"""
        return self.data(variable, data, op='kveq', **kwargs)

    def keyvalue_eq(self, variable: str, data: dict | list, **kwargs) -> tuple:
        """Validate KeyValue JSON data equality"""
        return self.data(variable, data, op='kveq', **kwargs)

    def lt(self, variable: str, data: int | str) -> tuple:
        """Validate test data less than"""
        return self.data(variable, data, op='lt')

    def le(self, variable: str, data: int | str) -> tuple:
        """Validate test data less than or equal"""
        return self.data(variable, data, op='le')

    def ne(self, variable: str, data: Any) -> tuple:
        """Validate test data non equality"""
        return self.data(variable, data, op='ne')

    def rex(self, variable: str, data: str) -> tuple:
        """Test App data with regex"""
        return self.data(variable, fr'{data}', op='rex')

    def skip(self, variable: str, data: Any) -> tuple:
        """Test App data with regex"""
        return self.data(variable, data, op='skip')
