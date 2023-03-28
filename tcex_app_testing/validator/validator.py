"""TcEx Framework Module"""
# standard library
import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

# third-party
from redis import Redis

# first-party
from tcex_app_testing.pleb.cached_property import cached_property
from tcex_app_testing.validator.validator_abc import ValidatorABC
from tcex_app_testing.validator.validator_kvstore import ValidatorKvstore

if TYPE_CHECKING:
    # first-party
    from tcex_app_testing.app.playbook import Playbook
    from tcex_app_testing.requests_tc import TcSession

# get logger
_logger = logging.getLogger(__name__.split('.', maxsplit=1)[0])


class Validator(ValidatorABC):
    """Validator"""

    def __init__(
        self,
        playbook: 'Playbook',
        redis_client: Redis,
        session_tc: 'TcSession',
        tc_temp_path: str,
    ):
        """Initialize class properties."""
        super().__init__()
        self.playbook = playbook
        self.redis_client = redis_client
        self.session_tc = session_tc
        self.tc_temp_path = tc_temp_path

        # properties
        self.log = _logger
        self.truncate = 250

    def compare(
        self,
        app_data: dict | list | str,
        test_data: dict | list | str,
        op: str | None = None,
        **kwargs: dict | list | str,
    ) -> tuple:
        """Compare app_data to test data.

        Args:
            app_data: The data from the App.
            test_data: The validation data from the test case.
            op: The comparison operator expression. Defaults to "eq".
        """
        # remove comment field from kwargs if it exists
        if 'comment' in kwargs:
            del kwargs['comment']

        op = op or 'eq'
        if not self.get_operator(op):
            self.log.error(f'step=validate, event=invalid-operator, op={op}')
            return False, None

        # logging header
        title = kwargs.pop('title', app_data)
        self.log.info(title)

        # allow dev to provide formatted data for logging
        log_app_data = kwargs.pop('log_app_data', app_data)
        log_test_data = kwargs.pop('log_test_data', test_data)

        # run operator
        passed, details = self.get_operator(op)(app_data, test_data, **kwargs)

        # log validation data in a readable format
        self.validate_log_output(passed, log_app_data, log_test_data, details.strip(), op)

        # build assert error
        assert_error = (
            f'\n App Data     : {app_data}\n'
            f' Operator     : {op}\n'
            f' Expected Data: {test_data}\n'
            f' Details      : {details}\n'
        )
        return passed, assert_error

    def get_operator(self, op: str) -> Callable:
        """Get the corresponding operator"""
        operators = {
            'date_format': self.operator_date_format,
            'df': self.operator_date_format,
            'dd': self.operator_deep_diff,
            'is_url': self.operator_is_url,
            'is_date': self.operator_is_date,
            'is_number': self.operator_is_number,
            'is_json': self.operator_is_json,
            'length_eq': self.operator_length_eq,
            'leq': self.operator_length_eq,
            'endswith': self.operator_endswith,
            'eq': self.operator_eq,
            'ew': self.operator_endswith,
            '=': self.operator_eq,
            'le': self.operator_le,
            '<=': self.operator_le,
            'lt': self.operator_lt,
            '<': self.operator_lt,
            'ge': self.operator_ge,
            '>=': self.operator_ge,
            'gt': self.operator_gt,
            '>': self.operator_gt,
            'heq': self.operator_hash_eq,
            'hash_eq': self.operator_hash_eq,
            'jeq': self.operator_json_eq,
            'json_eq': self.operator_json_eq,
            'kveq': self.operator_keyvalue_eq,
            'keyvalue_eq': self.operator_keyvalue_eq,
            'ne': self.operator_ne,
            '!=': self.operator_ne,
            'rex': self.operator_regex_match,
            'skip': self.operator_skip,
            'startswith': self.operator_startswith,
            'sw': self.operator_startswith,
        }
        return operators.get(op, None)

    @cached_property
    def kvstore(self) -> ValidatorKvstore:
        """Return instance of ValidatorKvstore"""
        return ValidatorKvstore(self)

    @cached_property
    def redis(self) -> ValidatorKvstore:
        """Return instance of ValidatorKvstore"""
        return ValidatorKvstore(self)

    def remove_excludes(self, dict_1: dict | list, paths: list) -> dict:
        """Remove a list of paths from a given dict

        ex:
            dict_1: {
                'result': {
                    'sys_id': 123,
                    'owner': {
                        'id': 5,
                        'name': 'System'
                    },
                    'name': results
                },
                'status': 'Uploaded
            paths: ['result', 'owner', 'id']

            returns: {
                'result': {
                    sys_id': 123,
                        'owner': {
                            'name': 'System'
                        },
                    'name': results
                },
                'status': 'Uploaded
            }
        """
        if isinstance(dict_1, list):
            for item in dict_1:
                self.remove_excludes(item, paths)
            return {}

        if not isinstance(dict_1, dict):
            raise RuntimeError(f'Provided value ({dict_1}) must be a dict.')

        path_0 = paths[0]
        if len(paths) == 1:
            if path_0 in dict_1:
                del dict_1[path_0]
            return dict_1
        self.remove_excludes(dict_1.get(path_0, {}), paths[1:])
        return dict_1

    def validate_log_output(
        self,
        passed: bool,
        app_data: dict | int | list | str | None,
        test_data: dict | int | list | str | None,
        details: str,
        op: str,
    ):
        """Format the validation log output to be easier to read.

        Args:
            passed: The results of the validation test.
            app_data: The data store in Redis.
            test_data: The user provided data.
            details: The details of the validation test.
            op: The comparison operator.
        """
        truncate = self.truncate

        def _truncate_log_data(
            data: dict | int | list | str | None, passed: bool
        ) -> dict | int | list | str | None:
            """Truncate data before it gets logged."""
            if data is None:
                return data

            if passed is False:
                return data

            if isinstance(data, str) and len(data) > truncate:
                return data[:truncate]

            if isinstance(data, list):
                db_data_truncated = []
                for d in data:
                    if d is not None and isinstance(d, str) and len(d) > truncate:
                        db_data_truncated.append(f'{d[:self.truncate]} ...')
                    else:
                        db_data_truncated.append(d)
                return db_data_truncated

            return data

        # truncate app_data
        app_data = _truncate_log_data(app_data, passed)

        # truncate test_data
        test_data = _truncate_log_data(test_data, passed)

        self.log.info(f'step=validate, app-data={app_data}, type={type(app_data)}')
        self.log.info(f'step=validate, op={op}')
        self.log.info(f'step=validate, exp-data={test_data}, type={type(test_data)}')

        if passed:
            self.log.info('step=validate, results=passed')
        else:
            self.log.info(f'step=validate, results=failed, details={details}')
