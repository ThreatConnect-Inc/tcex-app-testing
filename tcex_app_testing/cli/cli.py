"""TcEx Framework Module"""
# standard library
import logging
import os
import traceback

# third-party
import typer

# first-party
from tcex_app_testing.cli import Create, Negative, Update
from tcex_app_testing.config_model import config_model
from tcex_app_testing.render.render import Render

# initialize typer
app = typer.Typer()

# get logger
_logger = logging.getLogger(__name__.split('.', maxsplit=1)[0])


@app.command()
def create(
    feature: str = typer.Option(
        ...,
        help=(
            'The testing feature name (e.g., RetrieveAlerts). Multiple '
            'profiles/test cases can live in a feature directory. For services '
            'the App is launched once per feature.'
        ),
    ),
    profile_name: str = typer.Option(
        ...,
        help=('The name of the testing profile (e.g. negative_retrieve_alerts_null_id_input).'),
    ),
    interactive: bool = typer.Option(False, help='When set to True, interactive mode is enabled.'),
):
    """Create a test case or negative test cases."""

    try:
        tcc = Create(feature, profile_name, interactive)

        if config_model.test_case_profile_filename.is_file():
            Render.panel.failure(f'A profile with name ({profile_name}) already exists.')

        # generates the tests and feature dir
        tcc.create_dirs()

        # render all templates in the features directory
        tcc.templates_feature.render_templates()

        # render all templates in the tests directory
        tcc.templates_tests.render_templates()

        if interactive is True:
            # adds the profile to the json
            profile_status = tcc.interactive_profile()
        else:
            # adds the profile to the json
            profile_status = tcc.profile.add()

        # build table row data
        row_data = []
        row_data.extend(tcc.templates_feature.results)
        row_data.append(
            [
                os.path.basename(config_model.test_case_profile_filename),
                str(config_model.test_case_profile_filename),
                profile_status,
            ]
        )
        row_data.extend(tcc.templates_tests.results)

        # render results table
        Render.table_file_results(row_data, 'Test Case Create Results')
    except Exception as ex:
        _logger.error(traceback.format_exc())
        Render.panel.failure(f'Exception: {ex}')


@app.command()
def negative(
    feature: str = typer.Option(
        ...,
        help=(
            'The testing feature name (e.g., RetrieveAlerts). Multiple '
            'profiles/test cases can live in a feature directory. For services '
            'the App is launched once per feature.'
        ),
    ),
    profile_name: str = typer.Option(
        ...,
        help=('The name of the testing profile (e.g. negative_retrieve_alerts_null_id_input).'),
    ),
):
    """Create negative test cases."""
    try:
        tcn = Negative(feature, profile_name)

        # create the negative test cases
        tcn.create_negative_profiles()

        # render results table
        Render.table_file_results(tcn.results, 'Test Case Create Negative Results')
    except Exception as ex:
        _logger.error(traceback.format_exc())
        Render.panel.failure(f'Exception: {ex}')


@app.command()
def update():
    """Update all existing test cases."""
    try:
        tcu = Update()
        _logger.info('Updating test cases.')

        if os.path.isdir('tests'):
            # render all templates in the feature directory
            tcu.update_feature_files()

            # render all templates in the tests directory
            tcu.templates_tests.render_templates()

            # build table row data
            row_data = []
            row_data.extend(tcu.templates_feature.results)
            row_data.extend(tcu.templates_tests.results)

            # render results table
            Render.table_file_results(row_data, 'Test Case Update Results')
    except Exception as ex:
        _logger.error(traceback.format_exc())
        Render.panel.failure(f'Exception: {ex}')


if __name__ == '__main__':
    app()
