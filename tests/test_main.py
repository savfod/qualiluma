from pathlib import Path

import pytest

from qualiluma.checks.base import FileCheckResultBuilder
from qualiluma.main import build_checkers, check, main, visualize_results
from qualiluma.util import Config
from qualiluma.util.logs import init_logging


@pytest.mark.slow
def test_check_smoke_real(tmp_path: Path):
    # run real check on some files to check for any runtime errors
    tmp_path.joinpath("code.py").write_text("a = 1\nb = 0\nprint(a / b)\n")
    assert check(tmp_path, verbose=True) == 1


def test_check(tmp_path: Path):
    filter = "trailing newline"
    (tmp_path / "test_file.py").write_text("print('Hello, World!')\n")
    assert check(tmp_path, filter_checkers=filter) == 0
    assert check(tmp_path, filter_checkers=filter, thorough=True) == 0
    assert check(tmp_path, filter_checkers=filter, thorough=False) == 0
    assert check(tmp_path, filter_checkers=filter, verbose=False) == 0
    assert check(tmp_path, filter_checkers=filter, verbose=True) == 0

    # no newline at end of file
    (tmp_path / "test_file.py").write_text("print('Hello, World!')")
    assert check(tmp_path, filter_checkers=filter) == 1

    # check file, not dir
    assert check(tmp_path / "test_file.py", filter_checkers=filter) == 1

    # check non-existent path
    assert check(tmp_path / "non_existent.py", filter_checkers=filter) == 1

    # check strange extension
    (tmp_path / "test_file.strange_one").write_text("print('Hello, World!')\n")
    assert check(tmp_path / "test_file.strange_one", filter_checkers=filter) == 0
    assert check(tmp_path, filter_checkers=filter) == 1  # still other files


def test_build_checkers():
    config = Config()
    checkers = build_checkers(config, None, False)
    assert len(checkers) > 2

    some_names = [checkers[0].get_name(), checkers[2].get_name()]
    some_checkers = build_checkers(
        config, filter_checkers=",".join(some_names), thorough=True
    )
    assert len(some_checkers) == 2
    assert set(ch.get_name() for ch in some_checkers) == set(some_names)

    with pytest.raises(ValueError):
        build_checkers(config, filter_checkers="non_existent_checker", thorough=True)


def test_visualize_results(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    log_file = tmp_path / "test.log"
    init_logging(str(log_file))

    alpha = FileCheckResultBuilder("CheckerAlpha")
    beta = FileCheckResultBuilder("CheckerBeta")

    good_path = tmp_path / "good.py"
    bad_path = tmp_path / "bad.py"
    skipped_path = tmp_path / "skipped.py"
    ambiguous_path = tmp_path / "ambiguous.py"

    results = {
        "CheckerAlpha": {
            good_path: alpha.passed(),
            bad_path: alpha.failed("boom"),
        },
        "CheckerBeta": {
            skipped_path: beta.skipped(),
            ambiguous_path: beta.ambiguous("unclear status"),
        },
    }
    issues = results["CheckerBeta"][ambiguous_path].issues
    issues.append(issues[0])  # duplicate issue to test multiple issues

    visualize_results(results)

    log_contents = log_file.read_text()

    assert f"❌ {bad_path} - issues found" in log_contents
    assert "    - ERROR: CheckerAlpha - boom" in log_contents
    assert f"⚠️  {ambiguous_path} - not checked: unclear status" in log_contents
    assert "Check status: '❌ Errors found'" in log_contents
    assert "  - ❌ Found issues in 1 files by 'CheckerAlpha'." in log_contents
    assert "  - ✅ No issues found by 'CheckerBeta'" in log_contents

    monkeypatch.setattr("qualiluma.main.contains_errors", lambda x: False)
    visualize_results(results)
    log_contents = log_file.read_text()
    assert "Inconsistent error detection state" in log_contents


def test_main(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("qualiluma.main.sys.argv", ["qualiluma", "--help"])
    with pytest.raises(SystemExit) as _e:
        main()

    (tmp_path / "test_file.py").write_text(
        "print('Hello, World!')"
    )  # no newline at end
    monkeypatch.setattr(
        "qualiluma.main.sys.argv",
        ["qualiluma", str(tmp_path), "--checkers", "trailing newline"],
    )
    assert main() == 1
