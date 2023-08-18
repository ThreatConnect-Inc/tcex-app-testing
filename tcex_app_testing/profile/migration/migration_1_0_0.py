"""TcEx Framework Module"""
import json
# standard library
import logging
import os
import re
from typing import Callable

# first-party
from tcex_app_testing.profile.migration.migration import MigrationABC
from packaging import version
from tcex_app_testing.render.render import Render
from tcex_app_testing.pleb.cached_property import cached_property

# get logger
_logger = logging.getLogger(__name__.split('.', maxsplit=1)[0])


class Migration_1_0_0(MigrationABC):
    """Class for profile Migration methods management."""

    def __init__(self, content):
        """Initialize Class properties."""
        super().__init__(content, version.parse('1.0.0'), version.parse('1.0.1'))

    def migrate(self, contents: dict) -> dict:
        # The order of these migrations sadly matter since vault variables can be env variables
        migrations: list[Callable[[dict], dict]] = [
            self.env_migration, self.tc_migration, self.vault_migration
        ]

        for migration in migrations:
            contents = migration(contents)
        return contents

    def vault_migration(self, contents: dict) -> dict:
        """Migrate vault variable format to stage the vault values and transform the syntax."""
        contents_str = json.dumps(contents)
        transformation_tracker = {}
        for m in re.finditer(r'\${(env|envs|remote|vault):(.*?)}', contents_str):
            full_match = m.group(0)
            key_ = m.group(2).lower()
            if self._check_default_value_unsupported(key_, full_match):
                continue
            if not key_.startswith('/'):
                continue

            contents.setdefault('stage', {}).setdefault('vault', {})
            transformed_key, value, path = self._vault_path_parsed(key_)
            contents['stage']['vault'][transformed_key] = path
            transformation_tracker[full_match] = {'key': transformed_key, 'value': value}

        contents_str = json.dumps(contents)
        for full_match, transformation in transformation_tracker.items():
            transformed_key = transformation.get('key')
            value = transformation.get('value')
            transformation_pattern = f'${{vault.{transformed_key}.{value}}}'
            contents_str = contents_str.replace(full_match, transformation_pattern)

        return json.loads(contents_str)

    @staticmethod
    def _vault_path_parsed(path):
        path = path.split('/')
        key_ = path[-2].replace(' ', '_').lower()
        value = path[-1]
        path = '/'.join(path[:-1])
        return key_, value, path

    def tc_migration(self, contents: dict) -> dict:
        """Migrate staged tc data and its variable references"""

        contents.setdefault('stage', {}).setdefault('threatconnect', {})
        original_tc_staged_data = contents['stage']['threatconnect'].copy()
        transformed_tc_staged_data = {}
        for key_, value in original_tc_staged_data.items():
            root_type = self._determine_tc_root_type(value)
            if root_type in ['victims', 'cases', 'notes', 'artifacts']:
                value.pop('type')
            transformed_tc_staged_data.setdefault(root_type, {})
            transformed_tc_staged_data[root_type][key_] = value
        contents['stage']['threatconnect'] = transformed_tc_staged_data

        contents = json.dumps(contents)
        for m in re.finditer(r'\${tcenv:(.*?):(.*?)}', contents):
            transformed_pattern = f'${{tc.{m.group(1)}.{m.group(2)}}}'
            contents = contents.replace(m.group(0), transformed_pattern)

        return json.loads(contents)

    def _determine_tc_root_type(self, data) -> str:
        type_ = data.get('type')
        if not type_:
            Render.panel.warning(f'Unable to determine root type for TC data: {data}')
        type_ = type_.lstrip('ti_').lstrip('cm_')

        match type_.lower():
            case type_ if type_ in self._tc_groups:
                return 'groups'
            case type_ if type_ in self._tc_indicators:
                return 'indicators'
            case 'task':
                if 'name' in data:
                    return 'tasks'
                return 'groups'
            case type_ if type_ in ['artifact', 'case', 'note', 'victim']:
                return f'{type_}s'
            case _:
                Render.panel.warning(
                    f'Unable to determine root type for TC data: {data}, assuming Indicator due to '
                    'custom indicator types.'
                )
                return 'indicators'

    @property
    def _tc_groups(self):
        return [
            'adversary', 'attack pattern', 'campaign', 'course of action', 'document', 'email',
            'event', 'incident', 'intrusion set', 'report', 'signature', 'tactic', 'threat', 'tool',
            'vulnerability'
        ]

    @property
    def _tc_indicators(self):
        return [
            'address', 'email address', 'file', 'host', 'url', 'asn', 'cidr',
            'email subject', 'hashtag', 'mutex', 'registry key', 'user agent'
        ]

    @staticmethod
    def _check_default_value_unsupported(key_, full_match):
        if '=' in key_:
            Render.panel.warning(
                f'Setting a default value for {full_match} is no longer supported, '
                'please manually update this value'
            )
            return True
        return False

    def env_migration(self, contents: dict) -> dict:
        """Migrate env variable references"""
        contents = json.dumps(contents)
        for m in re.finditer(r'\${(env|envs|local|remote):(.*?)}', contents):
            full_match = m.group(0)
            key_ = m.group(2).lower()
            if self._check_default_value_unsupported(key_, full_match):
                continue
            if key_.startswith('/'):
                continue

            transformed_key = f'${{env.{key_}}}'
            contents = contents.replace(full_match, transformed_key)
        return json.loads(contents)

    @cached_property
    def _vault_base_path(self):
        return os.getenv('TCEX_TEST_VAULT_BASE_PATH', '').rstrip('/').lstrip('/')

