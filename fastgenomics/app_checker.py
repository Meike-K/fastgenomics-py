"""
FASTGenomics Test-Suite:

Provides methods to check your app-structure, manifest.json and create an docker-compose.yml for testing
"""
import pathlib
import jinja2


from fastgenomics import io as fg_io

from logging import getLogger

__version__ = fg_io.__version__

# set paths
RESOURCES_PATH = pathlib.Path(__file__).parent
TEMPLATE_DIR = RESOURCES_PATH / 'templates'

# registry
DOCKER_REGISTRY = 'apps.fastgenomics.org'

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
    manifest = fg_io.common.get_app_manifest()
    # This is already done in get_app_manifest, but let’s make sure this is tested
    fg_io.common.assert_manifest_is_valid(dict(FASTGenomicsApplication=manifest))

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

    # check input_file_mapping
    ifm = fg_io.common.get_input_file_mapping()
    fg_io.common.check_input_file_mapping(ifm)


def create_docker_compose(app_dir: pathlib.Path, app_name: pathlib.Path, sample_dir: pathlib.Path,
                          docker_registry: str = DOCKER_REGISTRY):
    """
    creates an docker-compose.yml for testing
    """
    docker_compose_file = app_dir / 'docker-compose.yml'

    if docker_compose_file.exists():
        logger.warning(f"{docker_compose_file.name} already existing! Aborting.")
        return

    # get app type
    manifest = fg_io.common.get_app_manifest()
    app_type = manifest['Type']

    logger.info("Loading docker-compose.yml template")
    with open(TEMPLATE_DIR / 'docker-compose.yml.j2') as f_temp:
        template = jinja2.Template(f_temp.read())

    logger.info(f"Writing {docker_compose_file}")
    with docker_compose_file.open('w') as f_out:
        temp = template.render(app_name=app_name, sample_dir=sample_dir.relative_to(app_dir),
                               docker_registry=docker_registry, app_type=app_type)
        f_out.write(temp)


def check_input_file_mapping(app_dir: pathlib.Path):
    """checks the input_file_mapping"""
    sample_dir = app_dir / 'sample_data'
    fg_io.set_paths(app_dir, sample_dir)
    fg_io.common.get_input_file_mapping(check_mapping=True)


def create_file_mapping(sample_dir: pathlib.Path):
    """
    creates a base input_file_mapping.json
    """
    sample_output_dir = sample_dir / 'data' / 'other_app_uuid' / 'output'
    file_mapping_file = sample_dir / 'config' / 'input_file_mapping.json'

    if file_mapping_file.exists():
        logger.warning(f"{file_mapping_file} already existing! Aborting.")
        return

    # creating output directories
    sample_output_dir.mkdir(parents=True, exist_ok=True)
    file_mapping_file.parent.mkdir(parents=True, exist_ok=True)

    # create file_mappings
    manifest = fg_io.common.get_app_manifest()
    input_keys = manifest['Input'].keys()
    file_mapping = {key: sample_output_dir / 'fix_me.txt' for key in input_keys}

    # write file_mappings
    logger.info("Loading input_file_mapping.json template")
    with open(TEMPLATE_DIR / 'input_file_mapping.json.j2') as f_temp:
        template = jinja2.Template(f_temp.read())

    logger.info(f"Writing {file_mapping_file}")
    with file_mapping_file.open('w') as f_out:
        temp = template.render(file_mapping=file_mapping)
        f_out.write(temp)

    print()
    print(f"Please edit {file_mapping_file} and provide the following files:")
    for key in input_keys:
        print(f" - {key}: {manifest['Input'][key]['Usage']} ({manifest['Input'][key]['Type']})")
    print()

