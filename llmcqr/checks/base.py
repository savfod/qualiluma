# checks/base.py
from abc import ABC, abstractmethod
from enum import IntEnum
from pathlib import Path
from typing import List, Dict, Any, Callable
from dataclasses import dataclass
from ..config import Config
import os


class Severity(IntEnum):
    """Severity levels for issues."""

    INFO = 1
    WARNING = 2
    ERROR = 3


@dataclass
class FileIssue:
    """Represents an issue found in a file."""

    check_name: str
    message: str
    severity: Severity
    # line: int = 0
    # column: int = 0
    # suggestion: str = ""


@dataclass
class FileCheckResult:
    was_checked: bool  # some files may be ignored
    issues: List[FileIssue]


class CheckerABC(ABC):
    def __init__(self, config: Config):
        self.config = config
        self.statistics: list[Any] = []  # any info saved between file checks

    @abstractmethod
    def _check_file_impl(self, file_path: Path) -> FileCheckResult:
        """Implement the file checking logic."""
        pass

    def get_name(self) -> str:
        """Get the name of the checker."""
        return self.__class__.__name__

    def check_file(self, file_path: Path) -> FileCheckResult:
        """Check a single file for issues.
        Args:
            file_path (Path): The path to the file to check.

        Returns:
            FileCheckResult: The result of the file check.
        """
        res = self._check_file_impl(file_path)
        self._clear_statistics()
        return res

    def check_directory(self, directory_path: Path) -> Dict[Path, FileCheckResult]:
        """Check all files in a directory for issues.
        Args:
            directory_path (Path): The path to the directory to check.

        Returns:
            Dict[Path, FileCheckResult]:
                A dictionary mapping file paths to their check results.
        """
        results: Dict[Path, FileCheckResult] = {}

        # todo: follow_symlink = True with saving to avoid recursion
        for dirpath, dirnames, filenames in os.walk(
            directory_path, topdown=True, onerror=None, followlinks=False
        ):
            dirnames[:] = [d for d in dirnames if self._filter_dir(Path(dirpath) / d)]
            for file_name in filenames:
                file_path = Path(dirpath) / file_name
                if file_path.is_file() and self._filter_file(file_path):
                    results[file_path] = self._check_file_impl(file_path)

        return results

    def _clear_statistics(self) -> None:
        """Delete statistics"""
        self.statistics = []

    def _filter_file(self, file_path: Path) -> bool:
        """Process the file during checks."""
        labels = self.config.get_labels(file_path.suffix)
        return ("code" in labels) or ("docs" in labels)

    def _filter_dir(self, dir_path: Path) -> bool:
        """Process the directory during checks."""
        return dir_path.name not in self.config.get_ignored_directories()


class SimpleCheckerABC(ABC):
    def __init__(self):
        self.checker_config = {}

    @abstractmethod
    def _check_file(self, file_path: Path) -> FileCheckResult:
        """Check a single file for issues."""
        pass

    def _set_checker_config(self, config: dict) -> None:
        """Set the checker-specific configuration."""
        self.checker_config = config


class SimpleCheckerAdapter(CheckerABC):
    """Adapter to make a complex checker from a simple one."""

    def __init__(self, config: Config, checker: SimpleCheckerABC):
        super().__init__(config)
        self.checker = checker
        self.checker._set_checker_config(self.config.get_checker_extra(self.get_name()))

    def _check_file_impl(self, file_path: Path) -> FileCheckResult:
        return self.checker._check_file(file_path)

    def get_name(self) -> str:
        return self.checker.__class__.__name__


class FunctionAdapter(CheckerABC):
    """Deprecated interface to support functions checks"""

    def __init__(
        self, config: Config, function: Callable[[Path], bool | None], check_name: str
    ):
        super().__init__(config)
        self.function = function
        self.check_name = check_name

    def _check_file_impl(self, file_path: Path) -> FileCheckResult:
        """Implement the file checking logic."""
        result = self.function(file_path)
        if result is None:
            return FileCheckResult(was_checked=False, issues=[])
        elif result is False:
            return FileCheckResult(
                was_checked=True,
                issues=[
                    FileIssue(
                        check_name=self.check_name,
                        message=f"Check {self.check_name} - failed.",
                        severity=Severity.ERROR,
                    )
                ],
            )
        else:
            return FileCheckResult(was_checked=True, issues=[])

    def get_name(self) -> str:
        return self.check_name
