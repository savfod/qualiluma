from pathlib import Path
import dotenv
import os
from langchain_openai import OpenAI


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
LENGTH_LIMIT = 10000
TEMPLATE = """Please check the code for errors.
Start your answer with "good" if there are no problems, with "bad" otherwise.
Please provide a brief description of the problems afterwards.
The code is here: <<<{code}>>>.
(Start your answer with "good" if there are no problems, with "bad" otherwise.)
"""


class Checker:
    def __init__(self):
        dotenv.load_dotenv(Path(__file__).parents[2] / ".env")
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", None)

        if not OPENAI_API_KEY:
            print("OPENAI_API_KEY is not set. Please set it to use the LLM checker.")
            self.llm = None
        else:
            self.llm = OpenAI(
                model="gpt-3.5-turbo-instruct",
                temperature=0,
                max_retries=2,
                # api_key="...",
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

        if len(code) > 10000:
            if verbose:
                print("Code length exceeds the limit for LLM processing, ignoring.")
            return None

        response = self.llm.invoke(TEMPLATE.format(code=code))
        response = response.strip().lstrip(".").lstrip()

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
        True if file ends with newline, False otherwise (errors will be printed)
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
