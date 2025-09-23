from pathlib import Path

import pytest

# filepath: /Users/savmac/proj/llm_qa/llmcqr/tests/test_base.py
from qualiluma.checks.base import (
    CheckerABC,
    FileCheckResult,
    FileCheckResultBuilder,
    FileIssue,
    FunctionAdapter,
    Severity,
    SimpleCheckerABC,
    SimpleCheckerAdapter,
)
from qualiluma.checks.llm_simple_checker import LLMSimpleChecker
from qualiluma.config import Config


class TestSimpleCheckerAdapter:
    def test_real_checker(self):
        config = Config()
        checker = LLMSimpleChecker()
        adapter = SimpleCheckerAdapter(
            config,
            checker,
        )

        file_path = Path(__file__).parent / "examples" / "file.py"
        result = adapter.check_file(file_path)

        assert result.was_checked is True
        assert len(result.issues) == 0

    def test_synthetic_checker(self, tmp_path):
        # todo: replace with endsline checker
        # custom simple checker that fails on files containing "fail"
        class MySimpleChecker(SimpleCheckerABC):
            def _check_file(
                self, file_path: Path, checker_config: dict
            ) -> FileCheckResult:
                text = file_path.read_text()
                if "fail" in text:
                    return FileCheckResult(
                        was_checked=True,
                        issues=[
                            FileIssue(
                                "MySimpleChecker", "contains fail", Severity.ERROR
                            )
                        ],
                    )
                return FileCheckResult(was_checked=True, issues=[])

        class FakeConfig:
            def get_labels(self, suffix):
                return ["code"]

            def get_checker_extra(self, name):
                return {"dummy": True}

            def get_ignored_directories(self):
                return []

        cfg = FakeConfig()
        checker = MySimpleChecker()
        adapter = SimpleCheckerAdapter(cfg, checker)

        ok = tmp_path / "ok.py"
        ok.write_text("everything fine")
        fail = tmp_path / "bad.py"
        fail.write_text("this should fail")

        res_ok = adapter.check_file(ok)
        assert res_ok.was_checked is True
        assert res_ok.issues == []

        res_fail = adapter.check_file(fail)
        assert res_fail.was_checked is True
        assert len(res_fail.issues) == 1
        assert res_fail.issues[0].message == "contains fail"


class TestFileIssueAndCheckResultBuilder:
    def test_file_issue_and_result_builder(self):
        b = FileCheckResultBuilder("MyChecker")

        skipped = b.skipped("not needed")
        assert skipped.was_checked is False
        assert skipped.issues == []

        passed = b.passed()
        assert passed.was_checked is True
        assert passed.issues == []

        failed = b.failed()  # default message
        assert failed.was_checked is True
        assert len(failed.issues) == 1
        assert failed.issues[0].check_name == "MyChecker"
        assert "Check failed" in failed.issues[0].message

        ambiguous = b.ambiguous("unclear")
        assert ambiguous.was_checked is False
        assert ambiguous.issues[0].severity == Severity.INFO
        assert ambiguous.issues[0].message == "unclear"


class TestSeverity:
    def test_severity_enum_values(self):
        assert Severity.INFO < Severity.WARNING < Severity.ERROR


class TestSimpleCheckerABC:
    def test_simple_checker_abc_abstract_method(self):
        class IncompleteChecker(SimpleCheckerABC):
            pass

        with pytest.raises(TypeError):
            _checker = IncompleteChecker()

        IncompleteChecker._check_file(None, None, None)


class TestCheckerABC:
    def test_checkerabc_check_file_and_directory_and_statistics_and_error_handling(
        self, tmp_path
    ):
        # CheckerABC subclass that records statistics and raises for a particular filename
        class MyChecker(CheckerABC):
            def __init__(self, config):
                super().__init__(config)
                self.statistics = ["keep"]

            def _check_file_impl(self, file_path: Path) -> FileCheckResult:
                if file_path.name == "raise.py":
                    raise RuntimeError("boom")
                # simple warning issue for other files
                return FileCheckResult(
                    was_checked=True,
                    issues=[FileIssue(self.get_name(), "warn", Severity.WARNING)],
                )

        class FakeConfig:
            def get_labels(self, suffix):
                return ["code"]

            def get_ignored_directories(self):
                return ["ignored_dir"]

        cfg = FakeConfig()
        checker = MyChecker(cfg)
        CheckerABC._check_file_impl(checker, Path())

        # create files and directories
        d = tmp_path
        f1 = d / "a.py"
        f1.write_text("ok")
        f2 = d / "raise.py"
        f2.write_text("boom")
        ign_dir = d / "ignored_dir"
        ign_dir.mkdir()
        (ign_dir / "skip.py").write_text("skipme")

        results = checker.check_directory(d)
        # should have entries for a.py and raise.py but not for ignored file
        assert (f1 in results) and (f2 in results)
        assert all(isinstance(v, FileCheckResult) for v in results.values())

        # a.py should have one warning issue
        assert results[f1].was_checked is True
        assert len(results[f1].issues) == 1
        assert results[f1].issues[0].severity == Severity.WARNING

        # raise.py should be caught and marked was_checked False
        assert results[f2].was_checked is False

        # check_file should clear statistics after invocation
        checker.statistics = ["something"]
        res = checker.check_file(f1)
        assert checker.statistics == []
        assert res.was_checked is True


class TestFunctionAdapter:
    def test_function_adapter(self, tmp_path):
        # function returns None -> skipped
        def fun_none(p: Path):
            return None

        # function returns False -> failed
        def fun_false(p: Path):
            return False

        # function returns True -> passed
        def fun_true(p: Path):
            return True

        class FakeConfig:
            pass

        cfg = FakeConfig()
        fa_none = FunctionAdapter(cfg, fun_none, "none_check")
        fa_false = FunctionAdapter(cfg, fun_false, "false_check")
        fa_true = FunctionAdapter(cfg, fun_true, "true_check")
        assert fa_none.get_name() == "none_check"

        p = tmp_path / "x.py"
        p.write_text("x")

        r_none = fa_none.check_file(p)
        assert r_none.was_checked is False

        r_false = fa_false.check_file(p)
        assert r_false.was_checked is True
        assert len(r_false.issues) == 1
        assert r_false.issues[0].check_name == "false_check"

        r_true = fa_true.check_file(p)
        assert r_true.was_checked is True
        assert r_true.issues == []
