from logging import Logger, StreamHandler
from pathlib import Path
from typing import ContextManager, Callable


def test_check_app_structure(local, app_dir: Path, catch_log_warnings: Callable[[Logger], ContextManager[StreamHandler]]):
    from fastgenomics import app_checker

    with catch_log_warnings(app_checker.logger) as handler:
        app_checker.check_app_structure(app_dir)
        w1, w2, w3 = handler.stream.getvalue().strip().split('\n')

    assert 'please provide LICENSE' in str(w1)
    assert 'No requirements.txt' in str(w2)
    assert 'No sample_data' in str(w3)
