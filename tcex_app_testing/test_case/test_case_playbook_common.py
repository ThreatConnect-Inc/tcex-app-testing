"""TcEx Framework Module"""
# standard library
import time
import uuid

from .test_case_abc import TestCaseABC


class TestCasePlaybookCommon(TestCaseABC):
    """Playbook TestCase Class"""

    redis_staging_data = {
        '#App:1234:empty!Binary': '',
        '#App:1234:empty!BinaryArray': [],
        # tcex won't let these be staged
        # '#App:1234:empty!KeyValue': {},
        # '#App:1234:empty!KeyValueArray': [],
        '#App:1234:empty!String': '',
        '#App:1234:empty!StringArray': [],
        # tcex won't let these be staged
        # '#App:1234:empty!TCEntity': {},
        # '#App:1234:empty!TCEntityArray': [],
        '#App:1234:non-ascii!String': 'ドメイン.テスト',
        # staging this data is not required
        # '#App:1234:null!Binary': None,
        # '#App:1234:null!BinaryArray': None,
        # '#App:1234:null!KeyValue': None,
        # '#App:1234:null!KeyValueArray': None,
        # '#App:1234:null!String': None,
        # '#App:1234:null!StringArray': None,
        # '#App:1234:null!TCEntity': None,
        # '#App:1234:null!TCEntityArray': None,
    }

    @property
    def app_inputs(self):
        """Return App inputs."""
        _app_inputs = super().app_inputs.copy()
        _app_inputs.update(
            {
                # already included in Config
                # 'tc_kvstore_host': os.getenv('TC_PLAYBOOK_DB_PATH', 'localhost'),
                # 'tc_kvstore_port': os.getenv('TC_PLAYBOOK_DB_PORT', '6379'),
                # 'tc_kvstore_type': os.getenv('TC_PLAYBOOK_DB_TYPE', 'Redis'),
                'tc_playbook_kvstore_context': self.aux.tc_playbook_kvstore_context,
                'tc_playbook_out_variables': '',
            }
        )
        return _app_inputs

    def setup_method(self):
        """Run before each test method runs."""
        super().setup_method()
        # APP-78 - The unique redis data that will be regenerated each test method.
        redis_unique_staged_data = {
            '#App:1234:epoch!String': str(int(time.time())),
            '#App:1234:uuid!String': str(uuid.uuid4()),
        }
        self.redis_staging_data.update(redis_unique_staged_data)

    def run(self):
        """Implement in Child Class"""
        raise NotImplementedError('Child class must implement this method.')

    def stage_data(self, staged_data):
        """Stage the data in the profile."""
        for key, value in list(staged_data.get('redis', {}).items()):
            self.aux.stager.redis.stage(key, value)

    def teardown_method(self):
        """Run after each test method runs."""
        # APP-1212 - fix issue where outputs were being deleted when profile was skipped
        if self.enable_update_profile and self.aux.skip is False:
            self.log.info('Update Outputs')

            # validate outputs first
            self.aux.profile_runner.validate()

            # update outputs if required
            self.aux.profile_runner.update.outputs()

        # clear context tracker
        self.aux.profile_runner._context_tracker = []  # pylint: disable=protected-access

        # run test_case teardown_method
        super().teardown_method()
