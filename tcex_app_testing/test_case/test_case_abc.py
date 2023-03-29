"""TcEx Framework Module"""
# standard library
import logging
import os
import sys
import traceback
from abc import ABC
from datetime import datetime

# third-party
import urllib3

# first-party
from tcex_app_testing.config_model import config_model
from tcex_app_testing.test_case.aux import Aux

# disable ssl warning message
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  # type: ignore

# get logger (self.log can't be used in setup_class and teardown_class)
_logger = logging.getLogger(__name__.split('.', maxsplit=1)[0])


class TestCaseABC(ABC):
    """Base TestCase Class"""

    # an instance of the App when running in threaded mode
    app = None

    # aid/helper methods and properties
    aux = Aux()

    # this flag is set to True in the test_profile.py setup_class method, which
    # allow for the update of the profile. then it's set to false in the
    # teardown_method to prevent skipped profiles from being updated.
    enable_update_profile = False

    # main logger with title and data feature
    log = _logger

    # flag that allows the App developer to control if a TC API token should be used.
    use_token = True

    @property
    def app_inputs(self) -> dict[str, int | list | str | None]:
        """Return current inputs, updated in child classes."""
        return self.aux.app_inputs_default

    def run(self):
        """Implement in Child Class"""
        raise NotImplementedError('Child class must implement this method.')

    def run_app_method(self, app, method):
        """Run the provided App method."""
        try:
            getattr(app, method)()
        except SystemExit as e:
            self.log.info(f'step=run, event=app-exit, exit-code={e.code}')
            if (
                e.code != 0
                and self.aux.profile_runner
                and e.code not in self.aux.profile_runner.model.exit_codes
            ):
                self.log.error(f'step=run, event=app-failed, exit-code={e.code}, method={method}')
            app.tce.log.info(f'Exit Code: {e.code}')
            return e.code
        except Exception:
            self.log.error(
                'step=run, event=app-method-encountered-exception, '
                f'method={method}, exception={traceback.format_exc()}'
            )
            return 1
        return 0

    @classmethod
    def setup_class(cls):
        """Run once before all test cases."""

        cls.initialized = True
        cls.log.info('Setup Class')
        cls.log.info(f'step=setup-class, event=started, datetime={datetime.now().isoformat()}')

    # pylint: disable=protected-access
    def setup_method(self):
        """Run before each test method runs."""

        self.log.info(config_model.current_test)
        self.log.info(f'step=setup-method, event=started, datetime={datetime.now().isoformat()}')

        # create and log current context
        self.aux.tc_playbook_kvstore_context = self.aux._get_tc_playbook_kvstore_context
        self.log.info(
            f'step=setup-method, event=get-context, context={self.aux.tc_playbook_kvstore_context}'
        )

        # clear cache, etc between test cases in tcex
        if 'tcex.pleb.cached_property' in sys.modules:
            sys.modules['tcex.pleb.cached_property'].cached_property._reset()
        if 'tcex.pleb.scoped_property' in sys.modules:
            sys.modules['tcex.pleb.scoped_property'].scoped_property._reset()
        if 'tcex.registry' in sys.modules:
            sys.modules['tcex.registry'].registry._reset()

        # Adding this for batch to created the -batch and errors files
        os.makedirs(os.path.join(config_model.test_case_log_test_dir, 'DEBUG'), exist_ok=True)

    @classmethod
    def teardown_class(cls):
        """Run once before all test cases."""
        cls.initialized = False
        cls.log.info('Teardown Class')
        cls.log.info(f'step=teardown-class, event=finished, datetime={datetime.now().isoformat()}')

    def teardown_method(self):
        """Run after each test method runs."""
        if self.aux.skip is False:
            if self.enable_update_profile:
                self.aux.profile_runner.update.exit_message()

            # the "initialized" property is used to determine if the profile was run previously
            # and the exit message and outputs have been updated. if the profile is not
            # initialized, then validations are skipped and the test will intentionally fail.
            # on future runs of the test profile the validations will run.
            self.aux.profile_runner.update.initialized()

            self.log.info(
                f'step=teardown-method, event=finished, datetime={datetime.now().isoformat()}'
            )

        # clear cache for playbook, stager, validator property
        self.aux.clear_cache()
