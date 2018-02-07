"""
FASTGenomics common IO helpers: Wraps manifest.json, input_file_mapping.json and parameters.json given by the
FASTGenomics runtime.

If you want to work without docker, you can set two environment variables to ease testing:

``APP_ROOT_DIR``: This path should contain manifest.json, normally this is /app.
``DATA_ROOT_DIR``: This path should contain you test data - normally, this is /fastgenomics.

You can set them by environment variables or just call ``fastgenomics.common.set_paths(path_to_app, path_to_data_root)``
"""
import os
import pathlib
import json
import jsonschema
import typing as ty
import pkg_resources

from logging import getLogger

logger = getLogger('fastgenomics.common')

# get / set version
VERSION = __version__ = pkg_resources.get_distribution('fastgenomics')

# get package paths
RESOURCES_PATH = pathlib.Path(__file__).parent
SCHEMA_DIR = RESOURCES_PATH / 'schemes'

# set default paths
DEFAULT_APP_DIR = '/app'
DEFAULT_DATA_ROOT = '/fastgenomics'

# init cache
_PATHS = {}
_MANIFEST = {}
_PARAMETERS = {}
_INPUT_FILE_MAPPING = {}


class NotSupportedError(Exception):
    pass


Parameters = ty.Dict[str, ty.Any]
PathsDict = ty.Dict[str, pathlib.Path]
FileMapping = ty.Dict[str, pathlib.Path]


def running_within_docker() -> bool:
    """
    detects, if module is running within docker and returns the result as bool
    """
    if pathlib.Path('/.dockerenv').exists():
        logger.debug("Running within docker")
        return True
    else:
        logger.info("Running locally")
        return False


def check_paths(paths: PathsDict, raise_error: bool = True):
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


def set_paths(app_dir: str = None, data_root: str = None):
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
    if running_within_docker() is True:
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
    check_paths(paths)
    _PATHS = paths


def get_input_file_mapping() -> FileMapping:
    """returns the input_file_mapping either from environment `INPUT_FILE_MAPPING` or from config file"""
    global _INPUT_FILE_MAPPING

    if _INPUT_FILE_MAPPING:
        return _INPUT_FILE_MAPPING

    # try to get input file mapping from environment
    input_file_mapping = json.loads(os.environ.get('INPUT_FILE_MAPPING', '{}'))
    source_str = "`INPUT_FILE_MAPPING` environment"

    # else use input_file_mapping file
    if not input_file_mapping:
        ifm_path = get_paths()['config'] / 'input_file_mapping.json'
        if not ifm_path.exists():
            raise FileNotFoundError("Input file mapping %s not found!", ifm_path)

        with open(get_paths()['config'] / 'input_file_mapping.json', encoding='utf-8') as f:
            input_file_mapping = json.load(f)
            source_str = ifm_path.name

    logger.info(f"Input file mapping loaded from {source_str}.")

    # convert into paths and update cache
    _INPUT_FILE_MAPPING = {key: get_paths()['data'] / mapped_file
                           for key, mapped_file in input_file_mapping.items()}
    return _INPUT_FILE_MAPPING


def get_paths() -> PathsDict:
    """
    safe getter for the runtime paths

    if paths are not initialized, it runs ``set_paths(DEFAULT_APP_DIR, DEFAULT_DATA_ROOT)``
    """
    if not _PATHS:
        set_paths()
    return _PATHS


def assert_manifest_is_valid(config: dict):
    """
    Asserts that the manifest (``manifest.json``) matches our JSON-Schema.
    If not a ``jsonschema.ValidationError`` will be raised.
    """
    with open(SCHEMA_DIR / 'manifest_schema.json', encoding='utf-8') as f:
        schema = json.load(f)
    jsonschema.validate(config, schema)

    parameters = config["FASTGenomicsApplication"]["Parameters"]
    if parameters is not None:
        for name, properties in parameters.items():
            expected_type = properties["Type"]
            default_value = properties["Default"]
            if not value_is_of_type(expected_type, default_value):
                logger.warning(f"The default parameter {name} has a different value than expected. "
                               f"It should be {expected_type} but is {type(default_value)}. "
                               f"The value is accessible but beware!")


def get_app_manifest() -> dict:
    """
    Parses and returns the app manifest.json

    Raises a RuntimeError of manifest.json does not exist.
    """
    global _MANIFEST

    # use cache
    if _MANIFEST:
        return _MANIFEST

    manifest_file = get_paths()['app'] / 'manifest.json'
    if not manifest_file.exists():
        err_msg = (f"App manifest {manifest_file} not found! "
                   "Please provide a manifest.json in the application's root-directory.")
        raise RuntimeError(err_msg)
    with open(manifest_file, encoding='utf-8') as f:
        try:
            config = json.load(f)
            assert_manifest_is_valid(config)
            # update cache
            _MANIFEST = config['FASTGenomicsApplication']
        except json.JSONDecodeError:
            err_msg = f"App manifest {manifest_file} not a valid JSON-file - check syntax!"
            raise RuntimeError(err_msg)

    return _MANIFEST


def get_parameters() -> Parameters:
    """Returns a dict of all parameters provided by parameters.json or defaults in manifest.json"""
    global _PARAMETERS

    # use cache
    if _PARAMETERS:
        return _PARAMETERS

    # else: load parameters
    parameters = get_default_parameters_from_manifest()
    runtime_parameters = load_runtime_parameters()

    # merge with defaults
    parameters.update(runtime_parameters)

    # check types
    check_parameter_types(parameters)
    return parameters


def get_parameter(param_key: str):
    """Returns the specific parameter 'param_key' from the parameters"""
    parameters = get_parameters()

    # get value or raise exception
    parameter = parameters.get(param_key)

    # check for existence and return
    if parameter is None:
        raise ValueError(f"Parameter {param_key} not defined in manifest.json!")
    return parameter


def get_default_parameters_from_manifest() -> Parameters:
    """returns the default parameters defined in the manifest.json"""
    temp = get_app_manifest()['Parameters']
    parameters = {param: value.get('Default') for param, value in temp.items()}
    return parameters


def load_runtime_parameters() -> Parameters:
    """loads and returns the runtime parameters from parameters.json"""

    parameters_file = get_paths()['config'] / 'parameters.json'

    if not parameters_file.exists():
        logger.info(f"No runtime parameters {parameters_file} found - using defaults.")
        return {}

    try:
        runtime_parameters = json.loads(parameters_file.read_text())
    except json.JSONDecodeError:
        logger.error(
            f"Could not read {parameters_file} due to an unexpected error. "
            f"Please report this at https://github.com/FASTGenomics/fastgenomics-py/issues")
        return {}

    check_all_runtime_parameters_are_in_manifest(runtime_parameters)
    return runtime_parameters


def get_parameter_types_from_manifest() -> ty.Dict[str, str]:
    """returns the types of parameters defined in the manifest.json"""
    temp = get_app_manifest()['Parameters']
    parameters = {param: value.get('Type') for param, value in temp.items()}
    return parameters


def value_is_of_type(expected_type: str, value: ty.Any) -> bool:
    """tests, of a value is an instance of a given an expected type"""
    type_mapping = {
        'float': (int, float),
        'integer': int,
        'bool': bool,
        'list': list,
        'dict': dict,
        'string': str,
    }
    mapped_type = type_mapping.get(expected_type)
    if mapped_type is None:
        raise ValueError(f"Unknown type to check: {expected_type}")

    return isinstance(value, mapped_type)


def check_parameter_types(parameters: Parameters):
    """checks the correct type of parameters as specified in the manifest.json"""
    parameter_types = get_parameter_types_from_manifest()

    for param_name, param_value in parameters.items():
        expected_type = parameter_types[param_name]
        # parameter types see manifest_schema.json
        if not value_is_of_type(expected_type, param_value):
            # we do not throw an exception because having multi-value parameters is
            #  common in some libraries, e.g. specify "red" or 24342
            logger.warning(f"The parameter {param_name} has a different type than expected. "
                           f"It should be {expected_type} but is {type(param_value)}. "
                           f"The value is accessible but beware!")


def check_all_runtime_parameters_are_in_manifest(runtime_parameters: Parameters):
    """checks, if all runtime parameters are defined in the manifest"""
    parameters = get_default_parameters_from_manifest()
    manifest_params_keys = set(parameters.keys())
    runtime_params_keys = set(runtime_parameters.keys())
    additional_runtime_params = runtime_params_keys.difference(manifest_params_keys)
    if len(additional_runtime_params) > 0:
        logger.warning(f"Ignoring parameter {additional_runtime_params} "
                       f"defined in parameters.json, as it is not defined in manifest.json")