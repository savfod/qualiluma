import os
from pathlib import Path

from ..util.llm import get_llm_client
from .base import FileCheckResult, FileIssue, Severity, SimpleCheckerABC
from .variable_consistency import _load_numbered

# TODO find better debug method. Maybe file logging.
DEBUG = os.getenv("DEBUG", "False").lower() == "true"


class CaseConsistencyChecker(SimpleCheckerABC):
    """Checker for case consistency."""

    def __init__(self):
        self.llm_client = get_llm_client()

    def _check_file(self, file_path: Path, checker_config: dict) -> FileCheckResult:
        """Check a single file for issues."""
        if self.llm_client is None:
            return FileCheckResult(was_checked=False)

        code_numbered: str = _load_numbered(file_path)
        prompt_detect: str = checker_config["prompt_detect_variables"].format(
            code=code_numbered
        )
        list_variables = self.llm_client(prompt_detect)
        if DEBUG:
            print("prompt_detect:", prompt_detect)
            print("list_variables:", list_variables)

        prompt_check: str = checker_config["prompt_check_case"].format(
            variables=list_variables
        )
        result: str = self.llm_client(prompt_check)

        if result.lstrip(".").lower().startswith("good"):
            return FileCheckResult(was_checked=True, issues=[])

        elif result.lstrip(".").lower().startswith("bad"):
            return FileCheckResult(
                was_checked=True,
                issues=[
                    FileIssue(
                        check_name="CaseConsistencyChecker",
                        message=f"Case consistency check failed: {result}",
                        severity=Severity.ERROR,
                    )
                ],
            )
        else:
            # unknown response format
            return FileCheckResult(
                was_checked=False,
                issues=[
                    FileIssue(
                        check_name="CaseConsistencyChecker",
                        message=f"Unknown response format: {result}",
                        severity=Severity.WARNING,
                    )
                ],
            )
