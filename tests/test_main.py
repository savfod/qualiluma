import argparse
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from llmcqr.checks import CheckerABC
from llmcqr.config import Config
from llmcqr.main import build_checkers, check, main, parse_args


def test_check(tmp_path):
    tmp_path.joinpath("test_file.py").write_text("print('Hello, World!')\n")
    assert check(tmp_path, verbose=True) == 0

    # no newline at end of file
    tmp_path.joinpath("test_file.py").write_text("print('Hello, World!')")
    assert check(tmp_path, verbose=True) == 1
