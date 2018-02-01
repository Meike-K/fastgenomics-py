import fastgenomics.io as fg_io


def test_init_paths(local):
    fg_io.set_paths()


def test_custom_init_paths(local, app_dir, data_root):
    fg_io.set_paths(app_dir, data_root)


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


def test_can_have_different_type(local, monkeypatch):
    monkeypatch.setattr("fastgenomics.io._load_custom_parameters", lambda x: {"StrValue": 1})

    parameters = fg_io.get_parameters()

    assert 1 == parameters["StrValue"]


def test_assert_manifest_is_valid(local):
    fg_io.get_app_manifest()

