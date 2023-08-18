"""TcEx Framework Module"""
# standard library
from tcex_app_testing.render.render import Render
from tcex_app_testing.requests_tc import TcSession
import logging


_logger = logging.getLogger(__name__.split('.', maxsplit=1)[0])


class StagerThreatconnect:
    """Stages the Redis Data"""

    def __init__(self, session: TcSession):
        """Initialize class properties."""
        self.session = session
        self.log = _logger

    def stage(self, threatconnect_data) -> dict:
        staged_data = {}
        for root_key, root_value in threatconnect_data.items():
            for key, data in root_value.items():
                if key in staged_data:
                    raise RuntimeError(f'ThreatConnect variable {key} is already staged.')
                staged_data[f'{key}'] = self.stage_data(root_key, data)

        return staged_data

    def stage_data(self, ioc_type, data):
        """Stage data in ThreatConnect."""
        self.session.log_curl = True
        response = self.session.post(f'/v3/{ioc_type}', json=data)
        if not response.ok:
            error_msg = [
                f'Error staging data: {data}',
                f'Url: {response.request.url}',
                f'Method: {response.request.method}',
                f'Response: {response.text}',
                f'Response: {response.status_code}',
            ]

            error_msg = '\n'.join(error_msg)
            self.log.error(f'step=setup, event=staging-{ioc_type}-data, message={error_msg}')
            Render.panel.warning(error_msg)

        response_json = response.json()
        return response_json.get('data', response_json)
