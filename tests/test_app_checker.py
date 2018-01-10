def test_check_app_structure(app_dir):
    from fastgenomics.app_checker import check_app_structure

    check_app_structure(app_dir)
