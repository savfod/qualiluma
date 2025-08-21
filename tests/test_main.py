from pathlib import Path

from llmcqr.main import check


def test_check(tmp_path: Path):
    tmp_path.joinpath("test_file.py").write_text("print('Hello, World!')\n")
    assert check(tmp_path, verbose=True) == 0

    # no newline at end of file
    tmp_path.joinpath("test_file.py").write_text("print('Hello, World!')")
    assert check(tmp_path, verbose=True) == 1
