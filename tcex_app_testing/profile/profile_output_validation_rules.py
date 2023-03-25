"""TcEx Framework Module"""
# standard library
import hashlib
import json
import re
from typing import Any

# first-party
from tcex_app_testing.util import Util


class ProfileOutputValidationRules:
    """TcEx testing profile Class.

    This module will generate profile output validation rules.
    """

    def __init__(self):
        """Initialize instance properties."""

        # properties
        self.util = Util()

    @staticmethod
    def _hash_value(value):
        """Return the SHA256 hash of the given value."""
        if isinstance(value, (bytes, bytearray)):
            return hashlib.sha256(value).hexdigest()
        if isinstance(value, str):
            return hashlib.sha256(value.encode('utf-8')).hexdigest()
        raise RuntimeError(f'Tried to hash unsupported type: {type(value)}')

    def _matches_date_rule(self, outputs: Any) -> bool:
        """Return if output should use the is_date operator."""
        if not isinstance(outputs, list):
            outputs = [outputs]

        for output in outputs:
            # date_to_datetime will take int/floats and convert to date.
            # if the value can be converted to int/float then it will
            # not be considered a date for this rule.
            try:
                is_float = True
                float(output)
            except Exception:
                is_float = False
            else:
                if is_float:
                    return False

            try:
                is_int = True
                int(output)
            except Exception:
                is_int = False
            else:
                if is_int:
                    return False

            try:
                if self.util.any_to_datetime(output) is None:
                    return False
            except RuntimeError:
                return False

        return True

    @staticmethod
    def _matches_dd_rule(outputs):
        """Return if output should use the dd operator."""
        return isinstance(outputs, (dict, list))

    @staticmethod
    def _matches_heq_rule(outputs):
        """Determine if an output should use hash_eq.

        Use hash_eq operator for the following scenarios:
            1) The type is Binary
            2) The type is String and the length is > 1024
        """
        return outputs is not None and (
            isinstance(outputs, (bytes, bytearray))
            or (isinstance(outputs, str) and len(outputs) > 1024)
        )

    @staticmethod
    def _matches_jeq_rule(outputs):
        """Return if output should use the jeq operator."""
        # TODO: APP-674 - revisit this with Ben
        if not isinstance(outputs, list):
            outputs = [outputs]
        try:
            for output in outputs:
                if not isinstance(output, str):
                    return False
                if not isinstance(json.loads(output), (dict, list)):
                    return False
        except Exception:
            return False
        return True

    @staticmethod
    def _matches_number_rule(outputs: Any) -> bool:
        """Return if output should use the is_number operator."""
        if not isinstance(outputs, list):
            outputs = [outputs]
        try:
            for output in outputs:
                int(output)
        except Exception:
            return False
        return True

    @staticmethod
    def _matches_url_rule(outputs):
        """Return if output should use the is_url operator."""
        if not isinstance(outputs, list):
            outputs = [outputs]

        regex = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$',
            re.IGNORECASE,
        )
        try:
            for output in outputs:
                matched = re.match(regex, output)
                if not matched:
                    return False
        except Exception:
            return False
        return True

    def generate_rule(self, data: Any) -> dict:  # pylint: disable=too-many-return-statements
        """Return the default output data for a given variable"""

        _rule = {'expected_output': data, 'op': 'eq'}

        # IMPORTANT: The order of these if statements matter.
        if data is None:
            _rule = {'expected_output': data, 'op': 'eq'}
        elif isinstance(data, list) and not data:
            _rule = {
                'expected_output': data,
                'op': 'dd',
                'ignore_order': False,
                'exclude_paths': [],
            }
        elif self._matches_url_rule(data):
            _rule = {'expected_output': data, 'op': 'is_url'}
        elif self._matches_number_rule(data):
            _rule = {'expected_output': data, 'op': 'is_number'}
        elif self._matches_jeq_rule(data):
            _rule = {
                'expected_output': data,
                'op': 'jeq',
                'ignore_order': False,
                'exclude_paths': [],
            }
        elif self._matches_date_rule(data):
            _rule = {'expected_output': data, 'op': 'is_date'}
        elif self._matches_dd_rule(data):
            _rule = {
                'expected_output': data,
                'op': 'dd',
                'ignore_order': False,
                'exclude_paths': [],
            }
        elif self._matches_heq_rule(data):
            _rule = {'expected_output': self._hash_value(data), 'op': 'heq'}
            if isinstance(data, str):
                _rule['encoding'] = 'utf-8'
        return _rule
