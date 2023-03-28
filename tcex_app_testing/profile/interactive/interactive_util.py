"""TcEx Framework Module"""

# first-party
from tcex_app_testing.app.config.model.install_json_model import ParamsModel
from tcex_app_testing.config_model import config_model
from tcex_app_testing.pleb.cached_property import cached_property
from tcex_app_testing.requests_tc import TcSession
from tcex_app_testing.requests_tc.auth.tc_auth import TcAuth


class InteractiveUtil:
    """TcEx App Testing Module."""

    def _expand_valid_values_artifact_types(self, valid_values: list):
        """Expand ${ARTIFACT_TYPES} variable to full list."""
        valid_values.remove('${ARTIFACT_TYPES}')
        valid_values.extend(
            [
                'ASN',
                'Asset Group ID',
                'Certificate File',
                'CIDR',
                'Credential ID',
                'Document Metadata',
                'Email Address',
                'Email Attachment File',
                'Email Attachment File Name',
                'Email Body',
                'Email Message File',
                'Email Subject',
                'Event File',
                'Exploit ID',
                'File Hash',
                'Filter ID',
                'Hashtag',
                'Host',
                'Image File',
                'IP Address',
                'Log File',
                'MutEx',
                'PCAP File',
                'Policy ID',
                'Registry Key',
                'Results ID',
                'Screenshot File',
                'Tactic ID',
                'Technique ID',
                'Ticket ID',
                'Timestamp',
                'URL',
                'User Agent',
                'Vulnerability Detection ID',
                'Vulnerability ID',
            ]
        )

    def _expand_valid_values_group_types(self, valid_values: list):
        """Expand ${GROUP_TYPES} variable to full list."""
        valid_values.remove('${GROUP_TYPES}')
        valid_values.extend(
            [
                'Adversary',
                'Attack Pattern',
                'Campaign',
                'Course of Action',
                'Document',
                'Email',
                'Event',
                'Incident',
                'Intrusion Set',
                'Malware',
                'Report',
                'Signature',
                'Tactic',
                'Task',
                'Threat',
                'Tool',
                'Vulnerability',
            ]
        )

    def _expand_valid_values_indicator_types(self, valid_values: list):
        """Expand ${INDICATOR_TYPES} variable to full list."""
        valid_values.remove('${INDICATOR_TYPES}')
        r = self.session.get('/v2/types/indicatorTypes')
        if r.ok:
            valid_values.extend(
                [t.get('name') for t in r.json().get('data', {}).get('indicatorType', {})]
            )

    def _expand_valid_values_owners(self, valid_values: list):
        """Expand ${OWNERS} variable to full list."""
        valid_values.remove('${OWNERS}')
        r = self.session.get('/v2/owners')
        if r.ok:
            valid_values.extend([o.get('name') for o in r.json().get('data', {}).get('owner', {})])

    def _expand_valid_values_users(self, valid_values: list):
        """Expand ${USERS} variable to full list."""
        valid_values.remove('${USERS}')
        r = self.session.get('/v2/owners/mine/members')
        if r.ok:
            valid_values.extend(
                [o.get('userName') for o in r.json().get('data', {}).get('user', {})]
            )

    def _expand_valid_values_users_groups(self, valid_values: list):
        """Expand ${USERS} variable to full list."""
        valid_values.remove('${USER_GROUPS}')
        valid_values.extend(['User Group 1', 'User Group 1'])

    def expand_valid_values(self, valid_values: list) -> list:
        """Expand supported playbook variables to their full list."""
        valid_values = list(valid_values)
        if '${ARTIFACT_TYPES}' in valid_values:
            self._expand_valid_values_artifact_types(valid_values)
        elif '${GROUP_TYPES}' in valid_values:
            self._expand_valid_values_group_types(valid_values)
        elif '${INDICATOR_TYPES}' in valid_values:
            self._expand_valid_values_indicator_types(valid_values)
        elif '${OWNERS}' in valid_values:
            self._expand_valid_values_owners(valid_values)
        elif '${USERS}' in valid_values:
            self._expand_valid_values_users(valid_values)
        elif '${USER_GROUPS}' in valid_values:
            self._expand_valid_values_users_groups(valid_values)
        return valid_values

    def get_default(self, data: ParamsModel) -> int | list | str | None:
        """Return the best option for default.

        Args:
            data: The install.json params object.
        """
        if data.type.lower() == 'boolean':
            default = str(data.default or False).lower()
        elif data.type.lower() == 'choice':
            default = 0
            valid_values: list = self.expand_valid_values(data.valid_values)
            if data.name == 'tc_action':
                for vv in valid_values:
                    if config_model.test_case_feature.lower() == vv.replace(' ', '_').lower():
                        default = vv
                        break
            else:
                default = data.default
        elif data.type.lower() == 'multichoice':
            default = data.default
            if default is not None and isinstance(default, str):
                default = default.split('|')
        else:
            default = data.default
        return default

    @cached_property
    def session(self):
        """Return a instance of the session manager."""
        auth = TcAuth(
            tc_api_access_id=config_model.tc_api_access_id,
            tc_api_secret_key=config_model.tc_api_secret_key,
        )
        return TcSession(auth, config_model.tc_api_path)
