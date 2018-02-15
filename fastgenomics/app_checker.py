"""
FASTGenomics Test-Suite:

Provides methods to check your app-structure, manifest.json and input_file_mapping.json
"""
import pathlib
from logging import getLogger


from fastgenomics import io as fg_io
from ._common import get_app_manifest, assert_manifest_is_valid, get_input_file_mapping

__version__ = fg_io.__version__

logger = getLogger('fastgenomics.testing')


def check_app_structure(app_dir: pathlib.Path):
    """checks the structure of your app - only checks for mandatory files and directories"""

    # check app structure
    logger.info(f"Checking app-structure in {app_dir}")
    to_check = ['manifest.json', 'README.md', 'LICENSE', 'Dockerfile', 'requirements.txt']
    warn_only = ['requirements.txt']

    for entry in to_check:
        entry_path = app_dir / entry
        if not entry_path.exists():
            err_msg = f"{entry_path} is missing!"
            if entry in warn_only:
                logger.warning(err_msg)
            else:
                logger.error(err_msg)

    # check manifest.json
    logger.info(f"Checking manifest.json in {app_dir}")
    manifest = get_app_manifest()
    # This is already done in get_app_manifest, but let’s make sure this is tested
    assert_manifest_is_valid(dict(FASTGenomicsApplication=manifest))

    # checking for sample_data
    logger.info(f"Checking for sample_data in {app_dir}")
    sample_dir = app_dir / 'sample_data'

    valid_sample_data_sub_dirs = ['data', 'config']
    if manifest['Type'] == 'Calculation':
        valid_sample_data_sub_dirs += ['output', 'summary']

    if not sample_dir.exists():
        logger.warning("No sample_data found - please provide sample data!")
    else:
        for sub_dir in valid_sample_data_sub_dirs:
            assert (sample_dir / sub_dir).exists(), f"sample_data subdirectory {sub_dir} is missing!"


def check_input_file_mapping(app_dir: pathlib.Path):
    """checks the input_file_mapping"""
    sample_dir = app_dir / 'sample_data'
    fg_io.set_paths(str(app_dir), str(sample_dir))
    get_input_file_mapping(check_mapping=True)
