#!/usr/bin/env python3
"""
LLMCQR - LLM Code Quality Reviewer
A tool for checking code quality and formatting rules.
"""

import argparse
import sys
from pathlib import Path

from .checks import (
    CheckerABC,
    FunctionAdapter,
    SimpleCheckerAdapter,
    check_trailing_newline,
)
from .checks.llm_checker import LLMCheckerDraft
from .config import Config


def build_checkers(config: Config) -> list[CheckerABC]:
    """Build a list of code quality checks to perform.
    Args:
        config: The configuration object containing settings for the checkers.

    Returns:
        A list of code quality checkers.
    """
    return [
        FunctionAdapter(config, check_trailing_newline, "trailing newline"),
        # FunctionAdapter(config, llm_check_file, "LLM check"),
        SimpleCheckerAdapter(config, LLMCheckerDraft()),
    ]


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        Parsed arguments as Namespace object
    """
    parser = argparse.ArgumentParser(
        description="Check code quality rules for files in a directory", prog="llmcqr"
    )
    parser.add_argument("path", type=Path, help="Path to directory or file to check")
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show verbose output including all checked files",
    )

    return parser.parse_args()


def check(target_path: Path, verbose: bool, config: Config | None = None) -> int:
    """Check the specified file or directory for code quality issues.

    Args:
        target_path: The path to the file or directory to check.
        verbose: Whether to show verbose output.
        config: The configuration object containing settings for the checkers.

    Returns:
        An integer indicating the result of the check (0 for success, 1 for failure).
    """
    if verbose:
        print(f"Checking: {target_path}")

    if config is None:
        config = Config()

    if not target_path.exists():
        print(f"Error: Path '{target_path}' does not exist", file=sys.stderr)
        return 1

    checkers = build_checkers(config)

    if target_path.is_file():
        # Check single file
        print(f"Checking file: {target_path}")
        results = {
            checker.get_name(): {target_path: checker.check_file(target_path)}
            for checker in checkers
        }

    elif target_path.is_dir():
        # Check directory recursively
        print(f"Checking files in: {target_path}")
        results = {
            checker.get_name(): checker.check_directory(target_path)
            for checker in checkers
        }

    else:
        print(
            f"Error: '{target_path}' is neither a file nor a directory", file=sys.stderr
        )
        sys.exit(1)

    # visualize results:
    # todo: fixs
    errors_detected = False
    for checker_name, file_status in results.items():
        print("=" * 80)
        print(f"Checker: {checker_name} result:")
        for file_path, status in file_status.items():
            if not status.was_checked:
                if verbose:
                    print(f"... {file_path} - not checked")

            else:
                if len(status.issues) > 0:
                    errors_detected = True
                    print(f"❌ {file_path} - issues founds:")
                    for issue in status.issues:
                        err_msg = (
                            f"    - {issue.severity.name}:"
                            f" {issue.check_name} - {issue.message}"
                        )
                        print(err_msg)
                else:
                    if verbose:
                        print(f"✅ {file_path} - no issues found")

    print("=" * 80)
    msg = "❌ Errors found" if errors_detected else "✅ No errors found"
    print(f"Check status: '{msg}'")
    return int(errors_detected)


def main() -> int:
    """Main entry point for the script."""
    args = parse_args()
    return check(args.path, args.verbose)


if __name__ == "__main__":
    sys.exit(main())
