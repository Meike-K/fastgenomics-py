"""
FASTGenomics IO helper: Wraps input/output of input_file_mapping and parameters given by the FASTGenomics runtime.

If you want to work without docker, you can set two environment variables to ease testing:

``APP_ROOT_DIR``: This path should contain manifest.json, normally this is /app.
``DATA_ROOT_DIR``: This path should contain you test data - normally, this is /fastgenomics.
"""

import os
import pathlib
import json
import jsonschema

from logging import getLogger
import pkg_resources

__version__ = pkg_resources.get_distribution('fastgenomics')

logger = getLogger('fastgenomics.io')

# set paths
RESOURCES_PATH = pathlib.Path(__file__).parent
SCHEMA_DIR = RESOURCES_PATH / 'schemes'

APP_ROOT_DIR = pathlib.Path(os.environ.get("FG_APP_DIR", "/app"))
DATA_ROOT_DIR = pathlib.Path(os.environ.get("FG_DATA_ROOT", "/fastgenomics"))

logger.info(f"Using {APP_ROOT_DIR} as app directory")
logger.info(f"Using {DATA_ROOT_DIR} as data root")

DATA_DIR = DATA_ROOT_DIR / pathlib.Path('data')
CONFIG_DIR = DATA_ROOT_DIR / pathlib.Path('config')
OUTPUT_DIR = DATA_ROOT_DIR / pathlib.Path('output')
SUMMARY_DIR = DATA_ROOT_DIR / pathlib.Path('summary')
PARAMETERS_FILE = CONFIG_DIR / 'parameters.json'

_PARAMETERS = None


class NotSupportedError(Exception):
    pass


def assert_manifest_is_valid(config: dict):
    """
    Asserts that the manifest (``manifest.json``) matches our JSON-Schema.
    If not a ``jsonschema.ValidationError`` will be raised.
    """
    with open(SCHEMA_DIR / 'manifest_schema.json') as f:
        schema = json.load(f)
    jsonschema.validate(config, schema)

    parameters = config["FASTGenomicsApplication"]["Parameters"]
    if parameters is not None:
        for name, properties in parameters.items():
            expected_type = properties["Type"]
            default_value = properties["Default"]
            if not _value_is_of_type(expected_type, default_value):
                logger.warning(f"The default parameter {name} has a different value than expected. "
                               f"It should be {expected_type} but is {type(default_value)}. "
                               f"The value is accessible but beware!")


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
    Gets the location of a input file and returns it as pathlib object.
    Keep in mind that you have to define your input files in your ``manifest.json`` in advance!
    """
    # try to get input file mapping from environment
    input_file_mapping = json.loads(os.environ.get('INPUT_FILE_MAPPING', '{}'))
    source_str = "environment 'INPUT_FILE_MAPPING'"

    # else use input_file_mapping file
    if not input_file_mapping:
        with open(CONFIG_DIR / 'input_file_mapping.json') as f:
            input_file_mapping = json.load(f)
            source_str = "file 'input_file_mapping.json'"

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
    Gets the location of the output file and returns it as a ``pathlib.Path``.
    Keep in mind that you have to define your output files in your ``manifest.json`` in advance!

    You can use this path-object to write your output as follows::

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
    Please write your summary as CommonMark-compatible Markdown into this file.
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
    global _PARAMETERS

    if _PARAMETERS is None:
        parameters = _load_parameters()
        _PARAMETERS = parameters

    return _PARAMETERS


def _load_parameters():
    parameters = _get_default_parameters_from_manifest()

    if not PARAMETERS_FILE.exists():
        logger.info(f"No custom parameters found - {PARAMETERS_FILE} does not exist")
        return parameters

    custom_parameters = _load_custom_parameters()

    _check_all_custom_parameters_are_in_manifest(custom_parameters, parameters)

    parameter_types = _get_parameter_types_from_manifest()
    _check_parameter_types(custom_parameters, parameters, parameter_types)

    _overwrite_manifest_parameters_with_custom_parameters(custom_parameters, parameters)

    return parameters


def _load_custom_parameters():
    try:
        custom_parameters = json.loads(PARAMETERS_FILE.read_text())
    except Exception as ex:
        logger.exception(
            f"Could not read {PARAMETERS_FILE} due to an unexpected error. "
            f"Please report this at https://github.com/FASTGenomics/fastgenomics-py/issues")
        raise ex
    return custom_parameters


def _overwrite_manifest_parameters_with_custom_parameters(custom_parameters, parameters):
    for parameter in parameters:
        if parameter not in custom_parameters:
            continue

        parameters[parameter] = custom_parameters[parameter]


def _value_is_of_type(expected_type: str, value) -> bool:
    # known types from json schema
    return {
        'float': lambda x: isinstance(x, (int, float)),
        'integer': lambda x: isinstance(x, int),
        'bool': lambda x: isinstance(x, bool),
        'string': lambda x: isinstance(x, str),
    }[expected_type](value)


def _check_parameter_types(custom_parameters, parameters, parameter_types):
    for parameter in parameters:
        if parameter not in custom_parameters:
            continue
            # this is ok, just no custom value specified
        custom_value = custom_parameters[parameter]

        expected_type = parameter_types[parameter]
        # parameter types see manifest_schema.json
        if not _value_is_of_type(expected_type, custom_value):
            # we do not throw an exception because having multi-value parameters is
            #  common in some libraries, e.g. specify "red" or 24342
            logger.warning(f"The custom parameter {parameter} has a different value than expected. "
                           f"It should be {expected_type} but is {type(custom_value)}. "
                           f"The value is accessible but beware!")


def _check_all_custom_parameters_are_in_manifest(custom_parameters, parameters):
    manifest_parameter_keys = set(parameters.keys())
    custom_parameter_keys = set(custom_parameters.keys())
    extra_custom_keys = custom_parameter_keys.difference(manifest_parameter_keys)
    if len(extra_custom_keys) > 0:
        logger.warning(
            f"{PARAMETERS_FILE} contains extra keys which are net specified in the manifest, "
            f"We are ignoring them. Keys {extra_custom_keys}")


def _get_default_parameters_from_manifest():
    temp = get_app_manifest()['Parameters']
    parameters = {param: value.get('Default') for param, value in temp.items()}
    return parameters


def _get_parameter_types_from_manifest():
    temp = get_app_manifest()['Parameters']
    parameters = {param: value.get('Type') for param, value in temp.items()}
    return parameters


def get_parameter(param_key: str):
    """Returns the parameter 'param_key' from the parameters file or manifest.json"""
    parameters = get_parameters()

    # check for existence
    if param_key not in parameters:
        raise ValueError(f"Parameter {param_key} not defined in {PARAMETERS_FILE}")
    return parameters[param_key]
