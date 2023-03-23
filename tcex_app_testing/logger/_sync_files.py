"""Sync Shared TcEx Files."""
# standard library
import os
import re

# third-party
import typer

# instantiate typer
app = typer.Typer()


@app.command()
def sync(
    tcex_path: str = typer.Option(
        'tcex_path', help='The path to the latest version of the TcEx Framework.'
    ),
):
    """Sync file from tcex to the testing framework.

    Note: This command needs to run from within the destination directory.

    python _sync_files.py --tcex-path /path/to/tcex
    """
    tcex_testing_path = os.getcwd()
    file_list = [
        'rotating_file_handler_custom.py',
        'sensitive_filter.py',
        'trace_logger.py',
    ]

    for file in file_list:
        source_path = os.path.join(tcex_path, 'tcex', 'logger', file)
        destination_path = os.path.join(tcex_testing_path, file)

        if os.path.isfile(source_path):
            # print(f'Copying {source_path} to {destination_path}')
            print(f'Copying file {file}')

            with open(source_path, encoding='utf-8') as f:
                content = f.read()

            # replace "from tcex." with "from tcex_app_testing."
            content = re.sub(r'from tcex\.', 'from tcex_app_testing.', content)

            # replace "tcex_logger" with "tcex_testing_logger"
            content = re.sub(r'tcex_logger', 'tcex_testing_logger', content)

            # replace "('tcex')" with "('tcex-testing')"
            content = re.sub(r'''\('tcex'\)''', '''('tcex-testing')''', content)

            with open(destination_path, encoding='utf-8', mode='w') as f:
                f.write(content)
        else:
            print(f'File not found: {source_path}')


if __name__ == '__main__':
    app()
