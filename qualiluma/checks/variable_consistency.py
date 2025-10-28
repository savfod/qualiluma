from pathlib import Path

from pydantic import BaseModel

from ..util import get_llm_client, get_logger, load_numbered
from .base import (
    FileCheckResult,
    FileCheckResultBuilder,
    SimpleCheckerABC,
)

logger = get_logger(__name__)


class _Identifier(BaseModel):
    name: str
    line_defined: int
    description: str


class _IdentifiersList(BaseModel):
    variables: list[_Identifier]


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
        list_variables = self.llm_client.structured_output(
            prompt_detect, _IdentifiersList
        )
        logger.debug(f"prompt_detect: {prompt_detect}")
        logger.debug(f"list_variables: {list_variables}")

        if len(list_variables.variables) == 0:
            return file_res.ambiguous(
                "No variables detected"
            )  # no variables found, strange

        list_variables_str = "\n".join(
            f"- {var.name} (line {var.line_defined}): {var.description}"
            for var in list_variables.variables
        )
        logger.debug(f"list_variables_str: {list_variables_str}")
        prompt_check = checker_config["prompt_check_consistency"].format(
            variables=list_variables_str
        )
        return self.llm_client.structured_output(prompt_check, FileCheckResult)
