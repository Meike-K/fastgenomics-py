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


class Parameter(ty.NamedTuple):
    """Parameter entry"""
    name: str
    type: str
    value: ty.Any  # uses default for initialization or None
    default: ty.Any
    optional: bool
    enum: ty.Optional[ty.List[ty.Any]]
    description: str


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


def check_input_file_mapping(input_file_mapping: FileMapping):
    """checks the keys in input_file_mapping and existence of the files

    raises a KeyError on missing Key and FileNotFoundError on missing file
    """
    manifest = get_app_manifest()['Input']

    not_in_manifest = set(input_file_mapping.keys()) - set(manifest.keys())
    not_in_ifm = set(manifest.keys()) - set(input_file_mapping.keys())

    optional = set()  # not implemented yet
    missing = not_in_ifm - optional

    # check keys
    if not_in_manifest:
        logger.warning(f"Ignoring Keys defined in input_file_mapping: {not_in_manifest}")

    if optional:   # not implemented yet
        logger.warning(f"Non-optional keys not defined in input_file_mapping: {missing}")

    if missing:
        raise KeyError(f"Non-optional keys not defined in input_file_mapping: {missing}")

    # check for existence
    for entry in input_file_mapping.values():
        if not entry.exists():
            raise FileNotFoundError(f"{entry}, defined in input_file_mapping, not found!")


def str_to_path_file_mapping(relative_mapping: ty.Dict[str, str]) -> FileMapping:
    """maps the relative string paths given in input_file_mapping to absolute paths"""
    data_path = get_paths()['data']

    absolute_mapping = {key: data_path / mapped_file
                        for key, mapped_file in relative_mapping.items()}
    return absolute_mapping


def load_input_file_mapping() -> ty.Dict[str, str]:
    """helper function loading the input_file_mapping either from environment or from file"""
    # try to get input file mapping from environment
    empty_str = '{}'
    ifm_str = os.environ.get('INPUT_FILE_MAPPING', empty_str)
    source_str = "`INPUT_FILE_MAPPING` environment"

    # else use input_file_mapping file
    if ifm_str == empty_str:
        ifm_path = get_paths()['config'] / 'input_file_mapping.json'
        if not ifm_path.exists():
            raise FileNotFoundError(f"Input file mapping {ifm_path} not found!")

        with open(get_paths()['config'] / 'input_file_mapping.json', encoding='utf-8') as f:
            ifm_str = f.read()
            source_str = ifm_path.name
    logger.info(f"Input file mapping loaded from {source_str}.")

    # decode json:
    try:
        ifm_dict = json.loads(ifm_str)
    except json.JSONDecodeError:
        raise RuntimeError(f"{source_str} is not valid JSON!")
    return ifm_dict


def get_input_file_mapping(check_mapping: bool = True) -> FileMapping:
    """returns the input_file_mapping either from environment `INPUT_FILE_MAPPING` or from config file"""
    global _INPUT_FILE_MAPPING

    if _INPUT_FILE_MAPPING:
        return _INPUT_FILE_MAPPING

    # load mapping
    ifm_dict = load_input_file_mapping()

    # convert into paths
    input_file_mapping = str_to_path_file_mapping(ifm_dict)

    # check existence
    if check_mapping:
        check_input_file_mapping(input_file_mapping)

    # update cache and return
    _INPUT_FILE_MAPPING = input_file_mapping
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
            enum = properties.get("Enum")
            default_value = properties["Default"]
            optional = properties.get("Optional", False)
            warn_if_not_of_type(name, expected_type, enum, default_value, optional, is_default=True)


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
    """Returns a dict of all parameters along with it's current value provided by parameters.json
    or defaults defined in manifest.json"""
    global _PARAMETERS

    # use cache and return dict of {param: current value}
    if _PARAMETERS:
        return {name: param.value for name, param in _PARAMETERS.items()}

    # else: load parameters
    parameters = load_parameters_from_manifest()
    runtime_parameters = load_runtime_parameters()

    # merge with defaults
    for name, current_value in runtime_parameters.items():
        if name not in parameters:
            logger.warning(f"Ignoring runtime parameter {name}, as it is not defined in manifest.json!")
            continue
        parameters[name] = _update_param_value(parameters[name], current_value)

    # check types
    check_parameter_types(parameters)

    # update cache and return
    _PARAMETERS = parameters
    return get_parameters()


def _update_param_value(param: Parameter, new_value: ty.Any):
    """helper function for updating the value of a Parameter instance"""
    return Parameter(name=param.name,
                     type=param.type,
                     value=new_value,
                     default=param.default,
                     optional=param.optional,
                     enum=param.enum,
                     description=param.description)


def get_parameter(param_key: str):
    """Returns the specific parameter 'param_key' from the parameters"""
    parameters = get_parameters()

    # check for existence and return or raise exception
    if param_key not in parameters:
        raise ValueError(f"Parameter {param_key} not defined in manifest.json!")
    return parameters[param_key]


def get_default_parameters() -> Parameters:
    """returns the default parameters defined in the manifest.json"""
    parameters = get_parameters()
    return {param: value.default for param, value in parameters.items()}


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

    return runtime_parameters


def load_parameters_from_manifest() -> ty.Dict[str, Parameter]:
    """returns the parameters section defined in the manifest.json as dict of Parameter
    """
    param_section = get_app_manifest()['Parameters']

    return {name: Parameter(name=name,
                            type=value['Type'],
                            value=value.get('Default'),
                            default=value.get('Default'),
                            optional=value.get('Optional', False),
                            enum=value.get('Enum'),
                            description=value['Description'])

            for name, value in param_section.items()}


def value_is_of_type(expected_type: str, enum: ty.Optional[list], value: ty.Any, optional: bool) -> bool:
    """tests, of a value is an instance of a given an expected type"""
    type_mapping = {
        'float': (int, float),
        'integer': int,
        'bool': bool,
        'list': list,
        'dict': dict,
        'string': str,
        'enum': object,
    }
    mapped_type = type_mapping.get(expected_type)
    if mapped_type is None:
        raise ValueError(f"Unknown type to check: {expected_type}")

    if optional and value is None:
        return True
    if enum is not None:
        if expected_type != 'enum':
            raise ValueError(f"Enum provided but type is {expected_type}")
        return value in enum
    return isinstance(value, mapped_type)


def check_parameter_types(parameters: Parameters):
    """checks the correct type of parameters as specified in the manifest.json"""
    manifest_parameters = load_parameters_from_manifest()

    for param_name, current_value in parameters.items():
        manifest_param = manifest_parameters[param_name]
        # parameter types see manifest_schema.json
        # we do not throw an exception because having multi-value parameters is
        #  common in some libraries, e.g. specify "red" or 24342
        warn_if_not_of_type(name=param_name, expected_type=manifest_param.type, enum=manifest_param.enum,
                            value=current_value, optional=manifest_param.optional)


def warn_if_not_of_type(name, expected_type, enum, value, optional, is_default=False):
    if value_is_of_type(expected_type, enum, value, optional):
        return

    msg = f"The {'default ' if is_default else ''}parameter {name} has a different value than expected. "
    if enum is None:
        msg += f"It should be a {expected_type} but is a {type(value)}. "
    else:
        msg += f"It should be one of {enum!r} but is {value!r}. "
    logger.warning(msg + f"The value is accessible but beware!")
