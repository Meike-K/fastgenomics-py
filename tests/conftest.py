from pathlib import Path

import pytest
import sys

HERE = Path(__file__).parent
APP_DIR = HERE / 'data'


@pytest.fixture
def fg_env(monkeypatch):
    # Don’t use the preloaded module so the environment can provide the paths
    for key in list(sys.modules.keys()):
        if key.startswith('fastgenomics'):
            del sys.modules[key]
    monkeypatch.setenv('FG_APP_DIR', str(APP_DIR))


@pytest.fixture
def app_dir():
    return APP_DIR

