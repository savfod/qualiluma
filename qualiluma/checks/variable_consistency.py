import os
from pathlib import Path

from ..util.llm import get_llm_client
from .base import (
    FileCheckResult,
    FileCheckResultBuilder,
    SimpleCheckerABC,
)

# TODO find better debug method. Maybe file logging.
DEBUG = os.getenv("DEBUG", "False").lower() == "true"


def _load_numbered(file_path: Path) -> str:
    """Load a file and return its content with line numbers.

    Args:
        file_path (Path): The path to the file to load.

    Returns:
        str: The content of the file with line numbers.
    """
    with file_path.open("r") as f:
        lines = f.readlines()
    return "\n".join(f"{i + 1}: {line.strip()}" for i, line in enumerate(lines))


class VariablesConsistencyChecker(SimpleCheckerABC):
    def __init__(self):
        self.llm_client = get_llm_client()

    def _check_file(self, file_path: Path, checker_config: dict) -> FileCheckResult:
        """Check a single file for issues."""
        file_res = FileCheckResultBuilder(checker_name="VariablesConsistencyChecker")

        if self.llm_client is None:
            return file_res.ambiguous("LLM client not initialized")

        code_numbered = _load_numbered(file_path)
        prompt_detect = checker_config["prompt_detect_variables"].format(
            code=code_numbered
        )
        list_variables = self.llm_client(prompt_detect)
        if DEBUG:
            print("prompt_detect:", prompt_detect)
            print("list_variables:", list_variables)

        prompt_check = checker_config["prompt_check_consistency"].format(
            variables=list_variables
        )
        result = self.llm_client(prompt_check)

        normalized = result.lstrip(".").lower()
        if normalized.startswith("good"):
            return file_res.passed()
        elif normalized.startswith("bad"):
            return file_res.failed(f"Variables consistency check failed: {result}")
        else:
            # unknown response format
            return file_res.ambiguous(f"Unknown response format: {result}")
