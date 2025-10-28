import os
from pathlib import Path

from ..util import load_numbered
from ..util.llm import get_llm_client
from .base import FileCheckResult, FileCheckResultBuilder, SimpleCheckerABC

# TODO find better debug method. Maybe file logging.
DEBUG = os.getenv("DEBUG", "False").lower() == "true"


class PepChecker(SimpleCheckerABC):
    """Checker for PEP 8 compliance."""

    def __init__(self, thorough: bool = False):
        self.llm_client = get_llm_client("fast" if not thorough else "thorough")

    def _check_file(self, file_path: Path, checker_config: dict) -> FileCheckResult:
        """Check a single file for issues."""
        file_res = FileCheckResultBuilder(checker_name="PepChecker")

        if self.llm_client is None:
            return file_res.ambiguous("LLM client not initialized")

        code_numbered: str = load_numbered(file_path)
        prompt_check: str = checker_config["prompt_check_case"].format(
            code=code_numbered,
        )
        return self.llm_client.structured_output(prompt_check, FileCheckResult)
