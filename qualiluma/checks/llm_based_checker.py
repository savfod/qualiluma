import os
from pathlib import Path

from ..config import CONFIG_PATH, _yaml_read
from ..util.llm import get_llm_client
from .base import FileCheckResult, FileIssue, Severity, SimpleCheckerABC

CONFIG = _yaml_read(CONFIG_PATH)
AVAILABLE_EXTENSIONS: list[str] = CONFIG["available_extensions"]
LENGTH_LIMIT: int = CONFIG["llm_length_limit"]

# TODO: find a better debug method (file logger?).
DEBUG = os.getenv("DEBUG", "False").lower() == "true"


class LLMSimpleChecker(SimpleCheckerABC):
    """LLM-based simple checker implemented in the same style as VariablesConsistencyChecker.

    Gets a prompt from config, and processes file-wise.
    """

    def __init__(self):
        self.llm_client = get_llm_client()

    def _check_file(self, file_path: Path, checker_config: dict) -> FileCheckResult:
        # If there's no initialized LLM client, indicate the file wasn't checked
        if self.llm_client is None:
            return FileCheckResult(was_checked=False)

        # Skip unsupported extensions early
        if file_path.suffix not in AVAILABLE_EXTENSIONS:
            if DEBUG:
                print(f"Skipping unsupported file type: {file_path.suffix}")
            return FileCheckResult(was_checked=False)

        code = file_path.read_text()

        # Enforce length limit to avoid sending huge files to the LLM
        if len(code) > LENGTH_LIMIT:
            if DEBUG:
                print("Code length exceeds the limit for LLM processing, ignoring.")
            return FileCheckResult(was_checked=False)

        # Use the prompt from checker_config if present, otherwise fall back to
        # global template from config (keeps compatibility with previous behavior).
        prompt_template = checker_config.get("prompt") or CONFIG.get("llm_template")
        assert isinstance(prompt_template, str), "Prompt template must be a string."
        prompt = prompt_template.format(code=code)

        result = self.llm_client(prompt)

        # Interpret response
        normalized = result.lstrip(".").lower()
        if normalized.startswith("good"):
            return FileCheckResult(was_checked=True, issues=[])

        elif normalized.startswith("bad"):
            return FileCheckResult(
                was_checked=True,
                issues=[
                    FileIssue(
                        check_name=checker_config.get("check_name", "LLMSimpleChecker"),
                        message=f"LLM found issues: {result}",
                        severity=Severity.ERROR,
                    )
                ],
            )
        else:
            if DEBUG:
                print("Ambiguous LLM result:", result[:200])

            # Unknown response format
            return FileCheckResult(
                was_checked=False,
                issues=[
                    FileIssue(
                        check_name=checker_config.get("check_name", "LLMSimpleChecker"),
                        message=f"Unknown response format: {result}",
                        severity=Severity.WARNING,
                    )
                ],
            )
