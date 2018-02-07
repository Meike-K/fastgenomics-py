"""
FASTGenomics IO helper: Wraps input/output of input_file_mapping and parameters given by the FASTGenomics runtime.

If you want to work without docker, you can set two environment variables to ease testing:

``APP_ROOT_DIR``: This path should contain manifest.json, normally this is /app.
``DATA_ROOT_DIR``: This path should contain you test data - normally, this is /fastgenomics.

You can set them by environment variables or just call ``fg_io.set_paths(path_to_app, path_to_data_root)``
"""
import pathlib
from logging import getLogger
from . import common

# imported for interface
# noinspection PyUnresolvedReferences
from .common import set_paths, get_parameters, get_parameter


logger = getLogger('fastgenomics.io')
__version__ = common.__version__


def get_input_path(input_key: str) -> pathlib.Path:
    """
    Gets the location of a input file and returns it as pathlib object.
    Keep in mind that you have to define your input files in your ``manifest.json`` in advance!
    """
    manifest = common.get_app_manifest()['Input']
    input_file_mapping = common.get_input_file_mapping()

    # check for key in manifest
    if input_key not in manifest:
        err_msg = f"Input '{input_key}' not defined in manifest.json!"
        logger.error(err_msg)
        raise ValueError(err_msg)

    # check for key in mapping
    if input_key not in input_file_mapping:
        err_msg = f"Input '{input_key}' not defined in input_file_mapping!"
        logger.error(err_msg)
        raise ValueError(err_msg)

    # check existence
    input_file = input_file_mapping[input_key]
    if not input_file.exists():
        err_msg = f"Input-file '{input_file}' not found! Please check your input_file_mapping."
        logger.error(err_msg)
        raise FileNotFoundError(err_msg)

    return input_file


def get_output_path(output_key: str) -> pathlib.Path:
    """
    Gets the location of the output file and returns it as a ``pathlib.Path``.
    Keep in mind that you have to define your output files in your ``manifest.json`` in advance!

    You can use this path-object to write your output as follows::

        my_path_object = get_output_path('my_output_key')
        with my_path_object.open('w', encoding='utf-8') as f_out:
            f_out.write("something")
    """
    manifest = common.get_app_manifest()

    # check application type
    if manifest['Type'] != 'Calculation':
        err_msg = f"File output for '{manifest['Type']}' applications not supported!"
        raise common.NotSupportedError(err_msg)

    # get output_file_mapping
    output_file_mapping = manifest['Output']
    if output_key not in output_file_mapping:
        err_msg = f"Key '{output_key}' not defined in manifest.json!"
        logger.error(err_msg)
        raise ValueError(err_msg)

    output_file = common.get_paths()['output'] / output_file_mapping[output_key]['FileName']

    # check for existence
    if output_file.exists():
        err_msg = f"Output-file '{output_file}' already exists!"
        logger.warning(err_msg)

    return output_file


def get_summary_path() -> pathlib.Path:
    """
    Gets the location of the summary file and returns it as a pathlib object.
    Please write your summary as CommonMark-compatible Markdown into this file.
    """
    manifest = common.get_app_manifest()

    # check application type
    if manifest['Type'] != 'Calculation':
        err_msg = f"File output for '{manifest['Type']}' applications not supported!"
        raise common.NotSupportedError(err_msg)

    output_file = common.get_paths()['summary'] / 'summary.md'

    # check for existence
    if output_file.exists():
        err_msg = f"Summary-file '{output_file}' already exists!"
        logger.warning(err_msg)

    return output_file
