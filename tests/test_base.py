from pathlib import Path

from qualiluma.checks.base import SimpleCheckerAdapter
from qualiluma.checks.llm_based_checker import LLMSimpleChecker
from qualiluma.config import Config


class TestCheckers:
    def test_simple_checker_adapter(self):
        config = Config()
        checker = LLMSimpleChecker()
        adapter = SimpleCheckerAdapter(
            config,
            checker,
        )

        file_path = Path(__file__).parent / "examples" / "file.py"
        result = adapter.check_file(file_path)

        assert result.was_checked is True
        assert len(result.issues) == 0
