from pathlib import Path

from ..util import get_llm_client, get_logger, load_numbered
from ..util.config import CONFIG_PATH, _yaml_read
from .base import (
    FileCheckResult,
    FileCheckResultBuilder,
    SimpleCheckerABC,
)

CONFIG = _yaml_read(CONFIG_PATH)

logger = get_logger(__name__)


class LLMSimpleChecker(SimpleCheckerABC):
    """LLM-based simple checker.

    Gets a prompt from config, and processes file-wise.
    """

    def __init__(self, thorough: bool = False):
        self.llm_client = get_llm_client("fast" if not thorough else "thorough")

    def _check_file(self, file_path: Path, checker_config: dict) -> FileCheckResult:
        # If there's no initialized LLM client, indicate the file wasn't checked
        file_res = FileCheckResultBuilder(checker_name="LLMSimpleChecker")

        if self.llm_client is None:
            return file_res.ambiguous("LLM client not initialized")

        # Skip unsupported extensions early
        # TODO: do on the wrapper level
        if file_path.suffix not in checker_config["available_extensions"]:
            logger.debug(f"Skipping unsupported file type: {file_path.suffix}")
            return file_res.ambiguous(f"Unsupported file type {file_path.suffix}")

        code = load_numbered(file_path)

        # Enforce length limit to avoid sending huge files to the LLM
        if len(code) > checker_config["length_limit"]:
            logger.warning(
                "Code length exceeds the limit for LLM processing, ignoring."
            )
            return file_res.ambiguous(
                "Code length exceeds the limit for LLM processing"
            )

        # Use the prompt from checker_config if present, otherwise fall back to
        # global template from config (keeps compatibility with previous behavior).
        prompt_template = checker_config.get("prompt") or CONFIG.get("llm_template")
        assert isinstance(prompt_template, str), "Prompt template must be a string."
        prompt = prompt_template.format(code=code)

        logger.debug(f"Sending prompt {prompt}")
        return self.llm_client.structured_output(prompt, FileCheckResult)
