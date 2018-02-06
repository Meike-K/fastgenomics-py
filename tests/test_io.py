import fastgenomics.io as fg_io
import pytest


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


# test things, imported from fastgenomics.common, are available
def test_import_from_common(app_dir, data_root):
    fg_io.set_paths(app_dir=app_dir, data_root=data_root)
    assert len(fg_io.get_parameters()) > 0
    fg_io.get_parameter('IntValue')

