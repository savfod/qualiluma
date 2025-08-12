#!/usr/bin/env python3
"""
LLMCQR - LLM Code Quality Reviewer
A tool for checking code quality and formatting rules.
"""

import argparse
import sys
from pathlib import Path

from .checks.base import CheckerABC, FunctionAdapter, SimpleCheckerAdapter
from .checks import check_trailing_newline
from .checks.llm_checker import LLMCheckerDraft
from .config import Config


def build_checkers(config: Config) -> list[CheckerABC]:
    """Build a list of code quality checks to perform."""
    return [
        FunctionAdapter(config, check_trailing_newline, "trailing newline"),
        # FunctionAdapter(config, llm_check_file, "LLM check"),
        SimpleCheckerAdapter(config, LLMCheckerDraft()),
    ]


# def check_file(file_path: Path, verbose: bool) -> bool | None:
#     """
#     Check a single file for code quality issues.

#     Args:
#         file_path: Path to the file to check
#         verbose: Whether to print verbose output

#     Returns:
#         True if the file passes all checks, False otherwise
#     """
#     if not should_check_file(file_path):
#         return None

#     has_newline = check_trailing_newline(file_path)
#     llm_result = None
#     if has_newline:
#         llm_result = llm_check_file(file_path, verbose=verbose)

#     if verbose:
#         if has_newline is False:
#             print(f"❌ {file_path} does not end with a newline")
#         elif llm_result is False:
#             print(f"❌ {file_path} has issues detected by LLM")
#         else:
#             print(f"✅ {file_path} passes all checks")

#     return (has_newline is True) and (llm_result is not False)


# def check_directory(directory_path: Path, verbose: bool) -> dict[Path, bool | None]:
#     """
#     Recursively check all files in a directory.

#     Args:
#         directory_path: Path to the directory to check
#         verbose: Whether to print verbose output

#     Returns:
#         Dictionary mapping file paths to their check status
#     """
#     file_status: dict[Path, bool | None] = {}

#     for root, dirs, files in os.walk(directory_path):
#         # Skip common build/cache directories
#         dirs[:] = [
#             d
#             for d in dirs
#             if not d.startswith(".")
#             and d
#             not in {
#                 "__pycache__",
#                 "node_modules",
#                 "venv",
#                 "env",
#                 ".venv",
#                 ".env",
#                 "build",
#                 "dist",
#                 ".git",
#                 ".svn",
#                 ".hg",
#             }
#         ]

#         for file_name in files:
#             file_path = Path(root) / file_name
#             file_status[file_path] = check_file(file_path, verbose)

#     return file_status


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
    """Check the specified file or directory for code quality issues."""
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

    # problems_count = sum(1 for status in file_status.values() if status is False)
    # checked_files_count = sum(
    #     1 for status in file_status.values() if status is not None
    # )
    # passed_files_count = sum(1 for status in file_status.values() if status is True)
    # skipped_files_count = sum(
    #     1 for status in file_status.values() if status is None
    # )
    # if skipped_files_count > 0:
    #     print(f"ℹ️  Skipped {skipped_files_count} files (not code files)")

    # if problems_count > 0:
    #     print(
    #         f"⚠️  Checked {checked_files_count} files"
    #         f", found {problems_count} problems."
    #     )
    #     return 1
    # else:
    #     print(f"✅ All {passed_files_count} checked files end with newline!")

    # else:
    #     print(
    #         f"Error: '{target_path}' is neither a
    # file nor a directory", file=sys.stderr
    #     )
    #     return 1

    return int(errors_detected)


def main() -> int:
    """Main entry point for the script."""
    args = parse_args()
    return check(args.path, args.verbose)


if __name__ == "__main__":
    sys.exit(main())
