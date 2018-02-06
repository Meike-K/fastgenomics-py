import pytest

from pathlib import Path

HERE = Path(__file__).parent
APP_DIR = HERE / 'sample_app'
DATA_ROOT = HERE / 'sample_data'


@pytest.fixture
def app_dir():
    return APP_DIR


@pytest.fixture
def data_root():
    return DATA_ROOT


def get_local_paths():
    return {'app': APP_DIR,
            'data': DATA_ROOT / 'data',
            'config': DATA_ROOT / 'config',
            'summary': DATA_ROOT / 'summary',
            'output': DATA_ROOT / 'output'}


@pytest.fixture
def local(monkeypatch):
    """patches the paths for local testing"""
    monkeypatch.setattr("fastgenomics.common.DEFAULT_APP_DIR", str(APP_DIR))
    monkeypatch.setattr("fastgenomics.common.DEFAULT_DATA_ROOT", str(DATA_ROOT))
    monkeypatch.setattr("fastgenomics.common._PATHS", {})
    monkeypatch.setattr("fastgenomics.common._PARAMETERS", {})
    monkeypatch.setattr("fastgenomics.common._MANIFEST", {})
    monkeypatch.setattr("fastgenomics.common._INPUT_FILE_MAPPING", {})


@pytest.fixture
def fg_env(monkeypatch):
    """sets app_dir and data_root by env-variables"""
    monkeypatch.setenv('FG_APP_DIR', str(APP_DIR))
    monkeypatch.setenv('FG_DATA_ROOT', str(DATA_ROOT))
    monkeypatch.setattr("fastgenomics.common._PATHS", {})
    monkeypatch.setattr("fastgenomics.common._PARAMETERS", {})
    monkeypatch.setattr("fastgenomics.common._MANIFEST", {})
    monkeypatch.setattr("fastgenomics.common._INPUT_FILE_MAPPING", {})


@pytest.fixture
def clear_output():
    """clear everything except of .gitignore"""
    for name in ['output', 'summary']:
        sub_dir = DATA_ROOT / name
        for entry in sub_dir.glob('*.*'):
            if entry.name != '.gitignore':
                entry.unlink()


@pytest.fixture
def fake_docker(monkeypatch):
    """fakes the docker-environment by overriding the running_within_docker-method returning always true"""
    monkeypatch.setattr("fastgenomics.common.running_within_docker", lambda: True)
