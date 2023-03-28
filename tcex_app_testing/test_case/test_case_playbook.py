"""TcEx Framework Module"""
# standard library
import os
import subprocess  # nosec
import sys
from typing import cast

from .test_case_playbook_common import TestCasePlaybookCommon


class TestCasePlaybook(TestCasePlaybookCommon):
    """Playbook TestCase Class"""

    run_method = 'inline'  # run service inline or a as subprocess

    def run(self) -> int:
        """Run the Playbook App."""
        # third-party
        from run import Run  # type: ignore # pylint: disable=import-error,import-outside-toplevel

        # run the app
        exit_code = 0
        try:
            # FIXME need a better "reset tcex" mechanism
            # pylint: disable=protected-access
            if 'tcex.pleb.registry' in sys.modules:
                sys.modules['tcex.registry'].registry._reset()

            run = Run()
            run.setup()
            run.launch()
            run.teardown()
        except SystemExit as e:
            # e.code in actual, is an int "type(e.code) -> <class 'int'>"
            exit_code = cast(int, e.code)

        self.log.info(f'step=run, event=app-exit, exit-code={exit_code}')
        return exit_code

    def run_profile(self) -> int:
        """Run an App using the profile name."""
        # create encrypted config file
        self.aux.create_config(self.aux.profile_runner.inputs)

        if os.getenv('TC_PLAYBOOK_WRITE_NULL') is not None:
            del os.environ['TC_PLAYBOOK_WRITE_NULL']

        if 0 in self.aux.profile_runner.model.exit_codes:
            os.environ['TC_PLAYBOOK_WRITE_NULL'] = 'true'

        # run the service App in 1 of 3 ways
        exit_code = 1
        if self.run_method == 'inline':
            # backup sys.argv
            sys_argv_orig = sys.argv

            # clear sys.argv
            sys.argv = sys.argv[:1]

            # run the App
            exit_code = self.run()

            # restore sys.argv
            sys.argv = sys_argv_orig
        elif self.run_method == 'subprocess':
            # run the Service App as a subprocess
            # pylint: disable=consider-using-with
            app_process = subprocess.Popen(['python', 'run.py'])  # nosec
            exit_code = app_process.wait()

        try:
            # remove env var for encrypted file if there
            del os.environ['TC_APP_PARAM_KEY']
            del os.environ['TC_APP_PARAM_FILE']
        except KeyError:
            pass

        # add context for populating output variables
        self.aux.profile_runner.add_context(self.aux.tc_playbook_kvstore_context)

        return exit_code

    def setup_method(self):
        """Run before each test method runs."""
        super().setup_method()
        self.aux.stager.redis.from_dict(self.redis_staging_data)
