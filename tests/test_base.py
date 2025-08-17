from pathlib import Path

from llmcqr.checks.base import (
    CheckerABC,
    FunctionAdapter,
    SimpleCheckerABC,
    SimpleCheckerAdapter,
)
from llmcqr.checks.llm_checker import LLMCheckerDraft
from llmcqr.config import Config


class TestCheckers:
    def test_simple_checker_adapter(self):
        config = Config()
        checker = LLMCheckerDraft()
        adapter = SimpleCheckerAdapter(
            config,
            checker,
        )

        file_path = Path(__file__).parent / "file.py"
        result = adapter.check_file(file_path)

        assert result.was_checked is True
        assert len(result.issues) == 0
