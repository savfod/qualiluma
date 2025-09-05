import os
from pathlib import Path

from ..config import CONFIG_PATH, _yaml_read
from ..util.llm import get_llm_client
from .base import (
    FileCheckResult,
    FileCheckResultBuilder,
    Severity,
    SimpleCheckerABC,
)

CONFIG = _yaml_read(CONFIG_PATH)
LENGTH_LIMIT: int = CONFIG["llm_length_limit"]

# TODO: find a better debug method (file logger?).
DEBUG = os.getenv("DEBUG", "False").lower() == "true"


class LLMSimpleChecker(SimpleCheckerABC):
    """LLM-based simple checker.

    Gets a prompt from config, and processes file-wise.
    """

    def __init__(self):
        self.llm_client = get_llm_client()

    def _check_file(self, file_path: Path, checker_config: dict) -> FileCheckResult:
        # If there's no initialized LLM client, indicate the file wasn't checked
        file_res = FileCheckResultBuilder(checker_name="LLMSimpleChecker")

        if self.llm_client is None:
            return file_res.ambiguous("LLM client not initialized")

        # Skip unsupported extensions early
        # TODO: do on the wrapper level
        if file_path.suffix not in checker_config["available_extensions"]:
            if DEBUG:
                print(f"Skipping unsupported file type: {file_path.suffix}")
            return file_res.ambiguous(f"Unsupported file type {file_path.suffix}")

        code = file_path.read_text()

        # Enforce length limit to avoid sending huge files to the LLM
        if len(code) > LENGTH_LIMIT:
            if DEBUG:
                print("Code length exceeds the limit for LLM processing, ignoring.")
            return file_res.ambiguous(
                "Code length exceeds the limit for LLM processing"
            )

        # Use the prompt from checker_config if present, otherwise fall back to
        # global template from config (keeps compatibility with previous behavior).
        prompt_template = checker_config.get("prompt") or CONFIG.get("llm_template")
        assert isinstance(prompt_template, str), "Prompt template must be a string."
        prompt = prompt_template.format(code=code)

        result = self.llm_client(prompt)

        # Interpret response
        normalized = result.lstrip(".").lower()
        if normalized.startswith("good"):
            return file_res.passed()
        elif normalized.startswith("bad"):
            return file_res.failed(f"LLM found issues: {result}")
        else:
            if DEBUG:
                print("Ambiguous LLM result:", result[:200])

            # Unknown response format
            return file_res.ambiguous(
                f"Failed to parse LLM response: {result}", severity=Severity.WARNING
            )
