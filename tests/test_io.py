import fastgenomics.io as fg_io
import pytest


def test_paths_are_initialized(local):
    fg_io._get_paths()


def test_custom_init_paths(app_dir, data_root):
    fg_io.set_paths(app_dir, data_root)
    fg_io._get_paths()


def test_custom_init_path_within_docker(fake_docker, app_dir, data_root):
    with pytest.warns(None):
        fg_io.set_paths(app_dir, data_root)
        fg_io._get_paths()


def test_assert_manifest_is_valid(local):
    fg_io._get_app_manifest()


def test_io_get_parameters(local):
    parameters = fg_io.get_parameters()
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
    assert fg_io.get_parameter("IntValue") == 150


def test_can_have_different_type(local, monkeypatch):
    # patch custom parameter load function
    monkeypatch.setattr("fastgenomics.io._load_custom_parameters", lambda x: {"StrValue": 1})

    # get parameters and compare parameters of different types
    with pytest.warns(None):
        parameters = fg_io.get_parameters()
        assert 1 == parameters["StrValue"]


def test_can_read_input_file(local):
    # can get path
    to_test = fg_io.get_input_path("some_input")

    # path exists
    assert to_test.exists()


def test_cannot_read_undefined_input(local):
    with pytest.raises(ValueError):
        fg_io.get_input_path("i_dont_exist")


def test_can_write_summary(local, clear_output):
    sum_file = fg_io.get_summary_path()
    with sum_file.open('w') as sum:
        sum.write('test')
    assert sum_file.exists()


def test_can_write_output(local, clear_output):
        out_path = fg_io.get_output_path("some_output")
        assert out_path.name == 'some_output.csv'
        with out_path.open('w') as out:
            out.write('test')
        assert out_path.exists()


def test_cannot_write_undefined_output(local):
    with pytest.raises(ValueError):
        fg_io.get_output_path("i_dont_exist")