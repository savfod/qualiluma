import os
from pathlib import Path

import dotenv
from langchain_openai import ChatOpenAI

from ..config import CONFIG_PATH, yaml_read
from .base import FileCheckResult, FileIssue, Severity, SimpleCheckerABC

CONFIG = yaml_read(CONFIG_PATH)
AVAILABLE_EXTENSIONS: list[str] = CONFIG["available_extensions"]


AVAILABLE_EXTENSIONS = [
    ".py",
    ".java",
    ".js",
    ".ts",
    ".c",
    ".cpp",
    ".h",
    ".css",
    ".json",
    ".md",
    ".txt",
]

# Limit for LLM processing,
# mostly to avoid running on wrong files accidentally.
LENGTH_LIMIT: int = CONFIG["llm_length_limit"]
TEMPLATE: str = CONFIG["llm_template"]


class Checker:
    def __init__(self):
        dotenv.load_dotenv(Path(__file__).parents[2] / ".env")
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", None)

        if not OPENAI_API_KEY:
            print("OPENAI_API_KEY is not set. Please set it to use the LLM checker.")
            self.llm = None
        else:
            self.llm = ChatOpenAI(
                model="gpt-5-nano",
                # temperature=0,
                # max_tokens=None,
                timeout=None,
                max_retries=2,
                # api_key="...",  # if you prefer to pass api key in directly instaed of using env vars
                # base_url="...",
                # organization="...",
                # other params...
            )

    def check_code(self, code: str, verbose: bool = True) -> bool | None:
        """
        Check the code for some obvious errors with an LLM.

        Args:
            code: The code to check
            verbose: Whether to print verbose output

        Returns:
            True if the code passes the checks, False otherwise
        """
        if not self.llm:
            return None

        if len(code) > LENGTH_LIMIT:
            if verbose:
                print("Code length exceeds the limit for LLM processing, ignoring.")
            return None

        response = self.llm.invoke([("system", TEMPLATE.format(code=code))])
        response = response.content.strip().lstrip(".").lstrip()

        if response.lower().startswith("good"):
            return True
        elif response.lower().startswith("bad"):
            if verbose:
                print(f"LLM found issues in the code: {response}")
            return False
        else:
            if verbose:
                print(f"LLM response is unclear: {response[:100]}...")
            return None


global_checker = Checker()


def llm_check_file(file_path: Path, verbose: bool = True) -> bool | None:
    """
    Check if a file for some obvious errors with an llm with llamaindex

    Args:
        file_path: Path to the file to check
        verbose: Whether to print verbose output

    Returns:
        False if some issues were found (errors will be printed),
        True if everything is ok,
        None if file is not a supported type
    """
    if file_path.suffix not in AVAILABLE_EXTENSIONS:
        if verbose:
            print(f"Skipping unsupported file type: {file_path.suffix}")
        return None
    code = file_path.read_text()

    if verbose:
        print(f"Checking file {file_path} with LLM...")
    return global_checker.check_code(code, verbose=verbose)


class LLMCheckerDraft(SimpleCheckerABC):
    def _check_file(self, file_path: Path, checker_config: dict) -> FileCheckResult:
        result = llm_check_file(file_path, verbose=True)

        if result is None:
            return FileCheckResult(was_checked=False, issues=[])
        elif result is False:
            return FileCheckResult(
                was_checked=True,
                issues=[
                    FileIssue(
                        check_name=checker_config["check_name"],
                        message=f"LLM found issues in file {file_path.name}",
                        severity=Severity.ERROR,
                    )
                ],
            )
        else:
            return FileCheckResult(was_checked=True, issues=[])
