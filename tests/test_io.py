import pathlib

import pkg_resources
import os

APP_DIR = os.path.join(os.path.dirname(__file__), "data/")


def test_io_get_parameters_from_manifest(monkeypatch):
    _setup_env(monkeypatch)

    from fastgenomics import io as fg_io
    fg_io._PARAMETERS = None

    parameters = fg_io.get_parameters()
    assert "StrValue" in parameters
    assert parameters["StrValue"] == "batch_id"

    assert "IntValue" in parameters
    assert parameters["IntValue"] == 150

    assert "FloatValue" in parameters
    assert parameters["FloatValue"] == float(100)

    assert "BoolValue" in parameters
    assert parameters["BoolValue"] == True

    del fg_io


def _setup_env(monkeypatch):
    monkeypatch.setattr(pkg_resources, 'get_distribution', lambda x: "-1")
    monkeypatch.setenv("FG_APP_DIR", APP_DIR)


def test_io_get_parameters_from_manifest_and_parameters(monkeypatch):
    _setup_env(monkeypatch)

    from fastgenomics import io as fg_io

    fg_io._PARAMETERS = None
    fg_io.PARAMETERS_FILE = pathlib.Path(APP_DIR) / "parameters.json"

    parameters = fg_io.get_parameters()

    assert "BETTER" == parameters["StrValue"]


def test_can_have_different_type(monkeypatch):
    _setup_env(monkeypatch)

    from fastgenomics import io as fg_io

    fg_io._PARAMETERS = None

    monkeypatch.setattr(fg_io, "_load_custom_parameters", lambda: {"StrValue": 1})

    parameters = fg_io.get_parameters()

    assert 1 == parameters["StrValue"]


def test_assert_manifest_is_valid(monkeypatch):
    _setup_env(monkeypatch)

    from fastgenomics import io as fg_io

    fg_io.get_app_manifest()