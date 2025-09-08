import os
from pathlib import Path

from ..util.llm import get_llm_client
from .base import FileCheckResult, FileCheckResultBuilder, Severity, SimpleCheckerABC
from .variable_consistency import _load_numbered

# TODO find better debug method. Maybe file logging.
DEBUG = os.getenv("DEBUG", "False").lower() == "true"


class CaseConsistencyChecker(SimpleCheckerABC):
    """Checker for case consistency."""

    def __init__(self):
        self.llm_client = get_llm_client()

    def _check_file(self, file_path: Path, checker_config: dict) -> FileCheckResult:
        """Check a single file for issues."""
        file_res = FileCheckResultBuilder(checker_name="CaseConsistencyChecker")

        if self.llm_client is None:
            return file_res.ambiguous("LLM client not initialized")

        code_numbered: str = _load_numbered(file_path)
        prompt_check: str = checker_config["prompt_check_case"].format(
            code=code_numbered,
        )
        result: str = self.llm_client(prompt_check)

        if self._starts_with(result, "good"):
            return file_res.passed()

        elif self._starts_with(result, "bad"):
            return file_res.failed(f"Case consistency check failed: {result}")

        else:
            return file_res.ambiguous(
                f"Unknown response format: {result}"
            )

    def _starts_with(self, string: str, prefix: str) -> bool:
        return string.lstrip(".").lower().startswith(prefix)
