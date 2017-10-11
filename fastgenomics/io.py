"""
FASTGenomics IO helper: Wraps input/output of input_file_mapping and parameters given by the FASTGenomics runtime.
"""
import os
import pathlib
import json
import jsonschema

from logging import getLogger
from pkg_resources import get_distribution

__version__ = get_distribution('fastgenomics')

# set paths
RESOURCES_PATH = pathlib.Path(__file__).parent
SCHEMA_DIR = RESOURCES_PATH / 'schemes'
APP_ROOT_DIR = pathlib.Path('/app')
DATA_DIR = pathlib.Path('/fastgenomics/data')
CONFIG_DIR = pathlib.Path('/fastgenomics/config')
OUTPUT_DIR = pathlib.Path('/fastgenomics/output')
SUMMARY_DIR = pathlib.Path('/fastgenomics/summary')

logger = getLogger('fastgenomics.io')


class NotSupportedError(Exception):
    pass


def assert_manifest_is_valid(config: dict):
    """
    Asserts that the manifest (manifest.json) matches our JSON-Schema.
    If not a jsonschema.ValidationError will be raised.
    """
    with open(SCHEMA_DIR / 'manifest_schema.json') as f:
        schema = json.load(f)
    jsonschema.validate(config, schema)


def get_app_manifest(app_dir: pathlib.Path = APP_ROOT_DIR) -> dict:
    """
    Parses and returns the app manifest.json

    Raises a RuntimeError of manifest.json does not exist.
    """
    manifest_file = app_dir / 'manifest.json'
    if not manifest_file.exists():
        err_msg = (f"App manifest {manifest_file} not found! "
                   "Please provide a manifest.json in the application's root-directory.")
        raise RuntimeError(err_msg)
    with open(manifest_file) as f:
        try:
            config = json.load(f)
            assert_manifest_is_valid(config)
            return config['FASTGenomicsApplication']
        except json.JSONDecodeError:
            err_msg = f"App manifest {manifest_file} not a valid JSON-file - check syntax!"
            raise RuntimeError(err_msg)


def get_input_path(input_key: str) -> pathlib.Path:
    """
    Gets the location of a input file and returns it as pathlib object
    Keep in mind, that you have to define your input files in your manifest.json in advance!
    """
    # try to get input file mapping from environment
    input_file_mapping = json.loads(os.environ.get('INPUT_FILE_MAPPING', '{}'))
    source_str = "environment 'INPUT_FILE_MAPPING'"

    # else use input_file_mapping file
    if not input_file_mapping:
        with open(CONFIG_DIR / 'input_file_mapping.json') as f:
            input_file_mapping = json.load(f)
            source_str = f"file '{input_file_mapping}'"

    # check for key in mapping
    if input_key not in input_file_mapping:
        err_msg = f"Key '{input_key}' not defined in {source_str}. Please check your manifest.json and code."
        logger.error(err_msg)
        raise ValueError(err_msg)

    input_file = DATA_DIR / input_file_mapping[input_key]

    # check existence
    if not input_file.exists():
        err_msg = f"Input-file '{input_file}' not found! Please check your input_file_mapping."
        logger.error(err_msg)
        raise FileNotFoundError(err_msg)

    return input_file


def get_output_path(output_key: str) -> pathlib.Path:
    """
    Gets the location of the output file and returns it as a pathlib object.
    Keep in mind, that you have to define your output files in your manifest.json in advance!

    You can use this path-object to write your output as follows:

        my_path_object = get_output_path('my_output_key')
        with my_path_object.open('w') as f_out:
            f_out.write("something")
    """
    manifest = get_app_manifest()

    # check application type
    if manifest['Type'] != 'Calculation':
        err_msg = f"File output for '{manifest['Type']}' applications not supported!"
        raise NotSupportedError(err_msg)

    # get output_file_mapping
    output_file_mapping = manifest['Output']
    if output_key not in output_file_mapping:
        err_msg = f"Key '{output_key}' not defined in manifest.json!"
        logger.error(err_msg)
        raise ValueError(err_msg)

    output_file = OUTPUT_DIR / output_file_mapping[output_key]['FileName']

    # check for existence
    if output_file.exists():
        err_msg = f"Output-file '{output_file}' already exists!"
        logger.warning(err_msg)

    return output_file


def get_summary_path() -> pathlib.Path:
    """
    Gets the location of the summary file and returns it as a pathlib object.
    Please store your summary as commonMark into this file
    """
    manifest = get_app_manifest()

    # check application type
    if manifest['Type'] != 'Calculation':
        err_msg = f"File output for '{manifest['Type']}' applications not supported!"
        raise NotSupportedError(err_msg)

    output_file = SUMMARY_DIR / 'summary.md'

    # check for existence
    if output_file.exists():
        err_msg = f"Summary-file '{output_file}' already exists!"
        logger.warning(err_msg)

    return output_file


def get_parameters() -> dict:
    """Returns a dict of all parameters provided by parameters.json or defaults in manifest.json"""
    params_file = CONFIG_DIR / 'parameters.json'

    # load parameters from parameters.json:
    if params_file.exists():
        raise NotImplementedError("We don't have parameters yet")

    # use defaults from manifest.json:
    else:
        # TODO: change to warning when parameters are implemented
        logger.debug("parameters.json not provided - using defaults")

        temp = get_app_manifest()['Parameters']
        parameters = {param: value.get('Default') for param, value in temp.items()}
    return parameters


def get_parameter(param_key: str):
    """Returns the parameter 'param_key' from the parameters file or manifest.json"""
    parameters = get_parameters()
    params_file = CONFIG_DIR / 'parameters.json'

    # check for existence
    if param_key not in parameters:
        raise ValueError(f"Parameter {param_key} not defined in {params_file}")
    return parameters[param_key]
