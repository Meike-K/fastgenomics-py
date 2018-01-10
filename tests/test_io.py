def test_io_get_parameters_from_manifest(fg_env):
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
    assert parameters["BoolValue"] is True

    assert "ListValue" in parameters
    assert parameters["ListValue"] == [1, 2, 3]

    assert "DictValue" in parameters
    assert parameters["DictValue"] == {"foo": 42, "bar": "answer to everything"}


def test_io_get_parameters_from_manifest_and_parameters(fg_env, app_dir):
    from fastgenomics import io as fg_io

    fg_io._PARAMETERS = None
    fg_io.PARAMETERS_FILE = app_dir / "parameters.json"

    parameters = fg_io.get_parameters()

    assert "BETTER" == parameters["StrValue"]


def test_can_have_different_type(fg_env, app_dir, monkeypatch):
    from fastgenomics import io as fg_io

    fg_io._PARAMETERS = None
    fg_io.PARAMETERS_FILE = app_dir / "parameters.json"
    monkeypatch.setattr(fg_io, "_load_custom_parameters", lambda: {"StrValue": 1})

    parameters = fg_io.get_parameters()

    assert 1 == parameters["StrValue"]


def test_assert_manifest_is_valid(fg_env):
    from fastgenomics import io as fg_io

    fg_io.get_app_manifest()
