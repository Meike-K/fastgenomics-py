"""
FASTGenomics IO helper: Wraps input/output of input_file_mapping and parameters given by the FASTGenomics runtime.

If you want to work without docker, you can set two environment variables to ease testing:

``APP_ROOT_DIR``: This path should contain manifest.json, normally this is /app.
``DATA_ROOT_DIR``: This path should contain you test data - normally, this is /fastgenomics.

You can set them by environment variables or just call ``fg_io.set_paths(path_to_app, path_to_data_root)``
"""

import os
import pathlib
import json
import jsonschema
import typing as ty
import pkg_resources

from logging import getLogger

__version__ = pkg_resources.get_distribution('fastgenomics')

logger = getLogger('fastgenomics.io')


# get package paths
RESOURCES_PATH = pathlib.Path(__file__).parent
SCHEMA_DIR = RESOURCES_PATH / 'schemes'

# set default paths
DEFAULT_APP_DIR = '/app'
DEFAULT_DATA_ROOT = '/fastgenomics'

# init cache
_PATHS = None
_MANIFEST = None
_PARAMETERS = None


class NotSupportedError(Exception):
    pass


def _running_within_docker() -> bool:
    """
    detects, if module is running within docker and returns the result as bool
    """
    if pathlib.Path('/.dockerenv').exists():
        logger.debug("Running within docker")
        return True
    else:
        logger.info("Running locally")
        return False


def _check_paths(paths: ty.Dict[str, pathlib.Path], raise_error: bool = True):
    """
    checks, if main paths are existing along with the manifest.json and input_file_mapping.json
    """
    for to_check in ['app', 'config', 'data']:
        path_entry = paths.get(to_check)
        if path_entry is None or not path_entry.exists():
            err_msg = f"Path to {path_entry} not found! Check paths!"
            if raise_error is True:
                raise RuntimeError(err_msg)
            else:
                logger.warning(err_msg)

    for to_check in [paths['app'] / 'manifest.json', paths['config'] / 'input_file_mapping.json']:
        if not to_check.exists():
            err_msg = f"`{to_check}` does not exist! Please check paths and existence!"
            if raise_error is True:
                raise FileNotFoundError(err_msg)
            else:
                logger.warning(err_msg)


def set_paths(app_dir: str = None, data_root: str = None) -> ty.Dict[str, pathlib.Path]:
    """
    sets the paths for the module to search for the manifest.json and IO/files

    The following strategy is used
    - use variables provided to function, but warn, if running within docker
    - else: if set, use environment-variables FG_APP_DIR and FG_DATA_ROOT
    - else: if running within docker use defaults /app and /fastgenomics
    - else: raise exception

    Parameters:
    ===========
    app_dir: str, optional
      path to root directory of the application (must contain manifest.json)
    data_root: str, optional
      path to root directory of input/output/config/summary
    """
    global _PATHS
    if _running_within_docker() is True:
        if any([app_dir, data_root, os.environ.get("FG_APP_DIR"), os.environ.get("FG_DATA_ROOT")]):
            logger.warning("Running within docker - non-default paths may result in errors!")

    if app_dir is None:
        app_dir_path = pathlib.Path(os.environ.get("FG_APP_DIR", DEFAULT_APP_DIR)).absolute()
    else:
        app_dir_path = pathlib.Path(app_dir).absolute()

    if data_root is None:
        data_root_path = pathlib.Path(os.environ.get("FG_DATA_ROOT", DEFAULT_DATA_ROOT)).absolute()
    else:
        data_root_path = pathlib.Path(data_root).absolute()

    logger.info(f"Using {app_dir_path} as app directory")
    logger.info(f"Using {data_root_path} as data root")

    # set paths
    paths = {'app': app_dir_path,
             'data': data_root_path / pathlib.Path('data'),
             'config': data_root_path / pathlib.Path('config'),
             'output': data_root_path / pathlib.Path('output'),
             'summary': data_root_path / pathlib.Path('summary')}

    # check and set
    _check_paths(paths)
    _PATHS = paths


def _get_paths():
    """
    safe getter for the runtime paths

    if paths are not initialized, it runs ``set_paths(DEFAULT_APP_DIR, DEFAULT_DATA_ROOT)``
    """
    global _PATHS
    if _PATHS is None:
        _PATHS = set_paths(DEFAULT_APP_DIR, DEFAULT_DATA_ROOT)
    return _PATHS


def _assert_manifest_is_valid(config: dict):
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


def _get_app_manifest() -> dict:
    """
    Parses and returns the app manifest.json

    Raises a RuntimeError of manifest.json does not exist.
    """
    global _MANIFEST

    # use cache
    if _MANIFEST is not None:
        return _MANIFEST

    manifest_file = _get_paths()['app'] / 'manifest.json'
    if not manifest_file.exists():
        err_msg = (f"App manifest {manifest_file} not found! "
                   "Please provide a manifest.json in the application's root-directory.")
        raise RuntimeError(err_msg)
    with open(manifest_file) as f:
        try:
            config = json.load(f)
            _assert_manifest_is_valid(config)
            # update cache
            _MANIFEST = config['FASTGenomicsApplication']
        except json.JSONDecodeError:
            err_msg = f"App manifest {manifest_file} not a valid JSON-file - check syntax!"
            raise RuntimeError(err_msg)

    return _MANIFEST


def get_input_path(input_key: str) -> pathlib.Path:
    """
    Gets the location of a input file and returns it as pathlib object.
    Keep in mind that you have to define your input files in your ``manifest.json`` in advance!
    """
    manifest = _get_app_manifest()['Input']

    if input_key not in manifest:
        err_msg = f"Key '{input_key}' not defined in manifest.json!"
        logger.error(err_msg)
        raise ValueError(err_msg)

    # try to get input file mapping from environment
    input_file_mapping = json.loads(os.environ.get('INPUT_FILE_MAPPING', '{}'))
    source_str = "environment 'INPUT_FILE_MAPPING'"

    # else use input_file_mapping file
    if not input_file_mapping:
        with open(_get_paths()['config'] / 'input_file_mapping.json') as f:
            input_file_mapping = json.load(f)
            source_str = "file 'input_file_mapping.json'"

    # check for key in mapping
    if input_key not in input_file_mapping:
        err_msg = f"Key '{input_key}' not defined in {source_str}! Please check your manifest.json and code."
        logger.error(err_msg)
        raise ValueError(err_msg)

    input_file = _get_paths()['data'] / input_file_mapping[input_key]

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
    manifest = _get_app_manifest()

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

    output_file = _get_paths()['output'] / output_file_mapping[output_key]['FileName']

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
    manifest = _get_app_manifest()

    # check application type
    if manifest['Type'] != 'Calculation':
        err_msg = f"File output for '{manifest['Type']}' applications not supported!"
        raise NotSupportedError(err_msg)

    output_file = _get_paths()['summary'] / 'summary.md'

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
    parameters_file = _get_paths()['config'] / 'parameters.json'

    if not parameters_file.exists():
        logger.info(f"No custom parameters {parameters_file} found - using defaults.")
        return parameters

    # else:
    # get and check custom parameters
    custom_parameters = _load_custom_parameters(parameters_file)
    _check_all_custom_parameters_are_in_manifest(custom_parameters, parameters)

    # merge with defaults
    parameters.update(custom_parameters)

    # check types
    _check_parameter_types(parameters)

    return parameters


def _load_custom_parameters(parameters_file):
    try:
        custom_parameters = json.loads(parameters_file.read_text())
    except Exception as ex:
        logger.exception(
            f"Could not read {parameters_file} due to an unexpected error. "
            f"Please report this at https://github.com/FASTGenomics/fastgenomics-py/issues")
        raise ex
    return custom_parameters


def _value_is_of_type(expected_type: str, value) -> bool:
    # known types from json schema
    return {
        'float': lambda x: isinstance(x, (int, float)),
        'integer': lambda x: isinstance(x, int),
        'bool': lambda x: isinstance(x, bool),
        'list': lambda x: isinstance(x, list),
        'dict': lambda x: isinstance(x, dict),
        'string': lambda x: isinstance(x, str),
    }[expected_type](value)


def _check_parameter_types(parameters):
    """checks the correct type of parameters as specified in the manifest.json"""
    parameter_types = _get_parameter_types_from_manifest()

    for param_name, param_value in parameters.items():
        expected_type = parameter_types[param_name]
        # parameter types see manifest_schema.json
        if not _value_is_of_type(expected_type, param_value):
            # we do not throw an exception because having multi-value parameters is
            #  common in some libraries, e.g. specify "red" or 24342
            logger.warning(f"The parameter {param_name} has a different type than expected. "
                           f"It should be {expected_type} but is {type(param_value)}. "
                           f"The value is accessible but beware!")


def _check_all_custom_parameters_are_in_manifest(custom_parameters, parameters):
    manifest_parameter_keys = set(parameters.keys())
    custom_parameter_keys = set(custom_parameters.keys())
    extra_custom_keys = custom_parameter_keys.difference(manifest_parameter_keys)
    if len(extra_custom_keys) > 0:
        logger.warning(
            f"Ignoring parameter {extra_custom_keys}, defined in parameters.json as it is not defined in manifest")


def _get_default_parameters_from_manifest():
    temp = _get_app_manifest()['Parameters']
    parameters = {param: value.get('Default') for param, value in temp.items()}
    return parameters


def _get_parameter_types_from_manifest():
    temp = _get_app_manifest()['Parameters']
    parameters = {param: value.get('Type') for param, value in temp.items()}
    return parameters


def get_parameter(param_key: str):
    """Returns the parameter 'param_key' from the parameters file or manifest.json"""
    # trigger parameter_caching
    parameters = get_parameters()

    # get value or raise exception
    parameter = parameters.get(param_key)

    # check for existence and return
    if parameter is None:
        raise ValueError(f"Parameter {param_key} not defined in manifest.json!")
    return parameter
