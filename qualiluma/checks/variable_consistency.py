from pathlib import Path

from ..util import get_llm_client, get_logger, load_numbered
from .base import (
    FileCheckResult,
    FileCheckResultBuilder,
    SimpleCheckerABC,
)

logger = get_logger(__name__)


class VariablesConsistencyChecker(SimpleCheckerABC):
    def __init__(self, thorough: bool = False):
        self.llm_client = get_llm_client("fast" if not thorough else "thorough")

    def _check_file(self, file_path: Path, checker_config: dict) -> FileCheckResult:
        """Check a single file for issues."""
        file_res = FileCheckResultBuilder(checker_name="VariablesConsistencyChecker")

        if self.llm_client is None:
            return file_res.ambiguous("LLM client not initialized")

        code_numbered = load_numbered(file_path)
        prompt_detect = checker_config["prompt_detect_variables"].format(
            code=code_numbered
        )
        list_variables = self.llm_client(prompt_detect)
        logger.debug(f"prompt_detect: {prompt_detect}")
        logger.debug(f"list_variables: {list_variables}")

        if len(list_variables.strip()) == 0:
            return file_res.ambiguous(
                "No variables detected"
            )  # no variables found, strange

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
