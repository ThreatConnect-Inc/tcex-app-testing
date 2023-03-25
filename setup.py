"""TcEx Framework Module"""
# standard library
import os

# third-party
from setuptools import find_packages, setup

metadata = {}
metadata_file = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), 'tcex_app_testing', '__metadata__.py'
)
with open(
    metadata_file,
    encoding='utf-8',
) as f:
    exec(f.read(), metadata)  # nosec; pylint: disable=exec-used

if not metadata:
    raise RuntimeError(f'Could not load metadata file ({metadata_file}).')

with open('README.md', encoding='utf-8') as f:
    readme = f.read()

dev_packages = [
    'bandit',
    'codespell',
    'flake8',
    'pre-commit',
    'pydocstyle',
    'pylint',
    'pyright',
    'pytest-html',
    'pytest-xdist',
    'pyupgrade',
]


setup(
    author=metadata['__author__'],
    author_email=metadata['__author_email__'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Security',
    ],
    description=metadata['__description__'],
    download_url=metadata['__download_url__'],
    entry_points={
        'console_scripts': ['tcex-app-test=tcex_app_testing.cli.cli:app'],
    },
    extras_require={'dev': dev_packages},
    include_package_data=True,
    install_requires=[
        'arrow',
        'astunparse',
        'black',
        'deepdiff',
        'hvac',
        'inflect',
        'isort',
        'jmespath',
        'mako',
        'paho-mqtt',
        'pyaes',
        'pydantic',
        'pytest',
        'pytest-cov',
        'python-dateutil',
        'redis',
        'requests',
        'rich',
        'semantic_version',
        'typer',
    ],
    license=metadata['__license__'],
    long_description=readme,
    long_description_content_type='text/markdown',
    name=metadata['__package_name__'],
    packages=find_packages(exclude=['tests', 'test.*']),
    package_data={'': ['*.json', '*.tpl']},
    package_dir={'tcex_app_testing': 'tcex_app_testing'},
    project_urls={
        'Documentation': 'https://github.com/ThreatConnect-Inc/tcex-app-testing',
        'Source': 'https://github.com/ThreatConnect-Inc/tcex-app-testing',
    },
    python_requires='>=3.11',
    url=metadata['__url__'],
    version=metadata['__version__'],
    zip_safe=True,
)
