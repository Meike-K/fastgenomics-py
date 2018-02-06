import pytest
from fastgenomics import common


def test_paths_are_initialized(local):
    common.get_paths()


def test_custom_init_paths(app_dir, data_root):
    common.set_paths(app_dir, data_root)
    common.get_paths()


def test_paths_from_env(fg_env):
    common.get_paths()


def test_cannot_init_nonexisting_paths():
    with pytest.raises(RuntimeError):
        common.set_paths("i_don't_exist", "me_neither")


def test_custom_init_path_within_docker(fake_docker, app_dir, data_root):
    with pytest.warns(None):
        common.set_paths(app_dir, data_root)
        common.get_paths()


def test_get_app_manifest(local):
    common.get_app_manifest()


def test_assert_manifest_is_valid(local):
    manifest = common.get_app_manifest()
    common.assert_manifest_is_valid({'FASTGenomicsApplication': manifest})


def test_can_get_parameters(local):
    parameters = common.get_parameters()
    assert len(parameters) > 0


def test_parameters(local):
    parameters = common.get_parameters()

    assert "StrValue" in parameters
    assert parameters["StrValue"] == "hello from parameters.json"

    assert "IntValue" in parameters
    assert parameters["IntValue"] == 150

    assert "FloatValue" in parameters
    assert parameters["FloatValue"] == float(100)

    assert "BoolValue" in parameters
    assert parameters["BoolValue"] is True

    assert "ListValue" in parameters
    assert parameters["ListValue"] == [1, 2, 3]

    assert "DictValue" in parameters
    assert parameters["DictValue"] == {"foo": 42, "bar": "answer to everything"}


def test_can_get_specific_parameter(local):
    assert common.get_parameter("IntValue") == 150


def test_can_have_different_type(local, monkeypatch):
    # patch custom parameter load function
    monkeypatch.setattr("fastgenomics.common.load_runtime_parameters", lambda: {"StrValue": 1})

    # get parameters and compare parameters of different types
    with pytest.warns(None):
        parameters = common.get_parameters()
        assert 1 == parameters["StrValue"]


def test_input_file_mapping(local):
    input_file_mapping = common.get_input_file_mapping()
    assert "some_input" in input_file_mapping
    assert input_file_mapping['some_input'].exists()