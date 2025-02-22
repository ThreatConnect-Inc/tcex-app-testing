"""Pytest configuration for App testing."""

# standard library
import contextlib
import os
import shutil
import socket
import sys
from importlib.metadata import version
from pathlib import Path
from threading import Thread

# third-party
from _pytest.config import Config
from _pytest.config.argparsing import Parser
from _pytest.python import Metafunc
from dotenv import load_dotenv
from fakeredis import TcpFakeServer

load_dotenv()


def validate_deps(deps_dir: Path):
    """Validate deps directory exists."""
    if deps_dir.is_dir():
        deps_dir_str = str(deps_dir)
        if deps_dir in sys.path:
            # remove and ensure path is at the front of the list
            sys.path.remove(deps_dir_str)

        # insert deps directory at the front of the path
        sys.path.insert(0, deps_dir_str)
    else:
        print(  # noqa: T201
            f'Running an App requires a "{deps_dir.name}" directory.'
            '\n\nTry running "tcex deps" to install dependencies.'
        )
        sys.exit(1)


# validate deps directory and update sys path
validate_deps(Path.cwd() / 'deps_tests')
# insert deps module last, so that it's at the front of the path. this matters for ensuring the
# App runs with the correct dependencies in the deps directory, not the deps_tests directory.
validate_deps(Path.cwd() / 'deps')

try:
    # first-party
    from tcex_app_testing.util.render.render import Render
except ImportError:
    print(  # noqa: T201
        'Running an App test requires the tcex-app-testing package.'
        '\n\nPlease run "pip install tcex-app-testing".'
    )
    sys.exit(1)

# display tcex app testing framework version
Render.panel.info(f'Using tcex-app-testing version {version("tcex-app-testing")}', 'Version')


def clear_log_directory():
    """Clear the App log directory.

    The tests.log file is create before conftest load and therefore would
    delete immediately after being created. This would prevent the log file
    from being viewed, so the log is cleaned up in the __init__.py of tcex-testing.
    """
    log_directory = Path.cwd() / 'log'

    if log_directory.is_dir():
        print('Clearing log directory.')  # noqa: T201
        for log_file in log_directory.iterdir():
            if log_file.is_dir():
                shutil.rmtree(log_file)
            if log_file.is_file() and 'tests.log' not in log_file.name:
                log_file.unlink()


def profiles(profiles_path: Path) -> list:
    """Get all testing profile names for current feature.

    Args:
        profiles_path: The profile.d directory for the current test.

    Returns:
        list: All profile names for the current test case.
    """
    profile_names = []
    for profile_file in sorted(profiles_path.glob('*.json')):
        profile_names.append(profile_file.stem)
    return profile_names


def pytest_addoption(parser: Parser):
    """Add arg flag to control replacement of outputs.

    Args:
        parser: Pytest argparser instance.
    """
    parser.addoption('--merge_inputs', action='store_true')
    parser.addoption('--replace_exit_message', action='store_true')
    parser.addoption('--replace_outputs', action='store_true')
    parser.addoption('--record', action='store_true')
    parser.addoption(
        '--environment',
        action='append',
        help='Sets the TCEX_TEST_ENVS environment variable',
    )


def pytest_generate_tests(metafunc: Metafunc):
    """Generate parametrize values for test_profiles.py::test_profiles tests case.

    Replacing "@pytest.mark.parametrize('profile_name', profile_names)"

    Skip functions that do not accept "profile_name" as an input, specifically this should
    only be used for the test_profiles method in test_profiles.py.
    """
    # we don't add automatic parameterization to anything that doesn't request profile_name
    if 'profile_name' not in metafunc.fixturenames:
        return

    # get the profile.d directory containing JSON profile files
    profile_dir = Path(metafunc.module.__file__).parent / 'profiles.d'  # type: ignore

    # decorate 'test_profiles()' method with parametrize profiles
    metafunc.parametrize('profile_name,', profiles(profile_dir))


def pytest_configure(config: Config):  # pylint: disable=unused-argument
    """Execute configure logic before test is started."""
    config.tcp_fake_server = None  # type: ignore
    server_address = 'localhost'
    server_port = 6379

    def is_port_in_use() -> bool:
        """Check if a port is in use."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex((server_address, server_port)) == 0

    if not is_port_in_use():
        tcp_fake_server = TcpFakeServer((server_address, server_port), server_type='redis')
        tcp_fake_server.daemon_threads = True
        t = Thread(target=tcp_fake_server.serve_forever, daemon=True)
        t.start()
        config.tcp_fake_server = tcp_fake_server  # type: ignore

        print('Starting fake Redis server.')  # noqa: T201


def pytest_unconfigure(config: Config):  # pylint: disable=unused-argument
    """Execute unconfigure logic before test process is exited."""
    if config.tcp_fake_server:  # type: ignore
        config.tcp_fake_server.server_close()  # type: ignore
        config.tcp_fake_server.shutdown()  # type: ignore
    log_directory = Path.cwd() / 'log'

    # remove any 0 byte files from log directory
    for log_file in log_directory.rglob('*'):
        try:
            if log_file.is_file() and log_file.stat().st_size == 0:
                log_file.unlink()
        except OSError:
            continue

    # display any Errors or Warnings in tests.log
    test_log_file = log_directory / 'tests.log'
    errors_count = {'ERROR': 0, 'WARNING': 0}
    if test_log_file.is_file():
        with test_log_file.open(encoding='utf-8') as fh:
            for line in fh:
                if '- ERROR - ' in line:
                    errors_count['ERROR'] += 1
                elif '- WARNING - ' in line:
                    errors_count['WARNING'] += 1
        print(f'Error/Warning Count: {errors_count}')  # noqa: T201
        if any((errors_count['ERROR'], errors_count['WARNING'])):
            print('Please check your log/tests.log file')  # noqa: T201

    # remove service started file
    with contextlib.suppress(FileNotFoundError):
        Path('./SERVICE_STARTED').unlink()


clear_log_directory()
