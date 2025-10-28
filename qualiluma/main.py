#!/usr/bin/env python3
"""
Qualiluma - LLM Code Quality Reviewer
A tool for checking code quality and formatting rules.
"""

import argparse
import sys
from collections import defaultdict
from pathlib import Path

from .checks import (
    CheckerABC,
    FileCheckResult,
    FunctionAdapter,
    LLMSimpleChecker,
    PepChecker,
    SimpleCheckerAdapter,
    VariablesConsistencyChecker,
    check_trailing_newline,
)
from .util import Config, get_logger, init_logging
from .util.llm import log_llm_pricing

logger = get_logger(__name__)
results_logger = get_logger(__name__, results_mode=True)  # for cleaner output


def build_checkers(
    config: Config, filter_checkers: str | None = None, thorough: bool = False
) -> list[CheckerABC]:
    """Build a list of code quality checks to perform.
    Args:
        config: The configuration object containing settings for the checkers.
        filter_checkers: comma separated list of checkers to run if provided.
        thorough: Whether to use more thorough (but slower) checks.

    Returns:
        A list of code quality checkers.
    """
    checkers = [
        FunctionAdapter(config, check_trailing_newline, "trailing newline"),
        SimpleCheckerAdapter(config, LLMSimpleChecker(thorough)),
        SimpleCheckerAdapter(config, VariablesConsistencyChecker(thorough)),
        SimpleCheckerAdapter(config, PepChecker(thorough)),
    ]

    if filter_checkers:
        filter_list = filter_checkers.split(",")
        checkers_dict = {checker.get_name().lower(): checker for checker in checkers}

        checkers = []
        for name in filter_list:
            if name.lower() in checkers_dict:
                checkers.append(checkers_dict[name.lower()])

            else:
                raise ValueError(
                    f"Invalid checker: {name}. "
                    f"Available checkers are: {[c.get_name() for c in checkers_dict.values()]}"
                )

    return checkers


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        Parsed arguments as Namespace object
    """
    parser = argparse.ArgumentParser(
        description="Check code quality rules for files in a directory",
        prog="qualiluma",
    )
    parser.add_argument("path", type=Path, help="Path to directory or file to check")
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show verbose output including all checked files",
    )
    parser.add_argument(
        "-c",
        "--checkers",
        type=str,
        default=None,
        help="Comma-separated list of checkers to run (or all if not specified)",
    )
    parser.add_argument(
        "-t",
        "--thorough",
        action="store_true",
        help="Use more thorough (but slower) checks",
    )

    return parser.parse_args()


def check_path(
    target_path: Path, checkers: list[CheckerABC]
) -> dict[str, dict[Path, FileCheckResult]]:
    """Calculate the results of the code quality checks.

    Args:
        target_path: The path to the file or directory to check.
        checkers: A list of code quality checkers to apply.

    Returns:
        A dictionary mapping checker names to file paths and their check status.
    """
    if target_path.is_file():
        # Check single file
        logger.info(f"Checking file: {target_path}")
        results = {
            checker.get_name(): {target_path: checker.check_file(target_path)}
            for checker in checkers
        }

    else:
        assert target_path.is_dir(), "Target path is neither file nor directory"
        # Check directory recursively
        logger.info(f"Checking files in: {target_path}")
        results = {
            checker.get_name(): checker.check_directory(target_path)
            for checker in checkers
        }

    return results


def contains_errors(results: dict[str, dict[Path, FileCheckResult]]) -> bool:
    """Check if any errors are in the checks results.

    Args:
        results: A dictionary mapping checker names to file paths and their check status.

    Returns:
        True if errors were detected, False otherwise.
    """
    for _checker_name, file_status in results.items():
        for _file_path, status in file_status.items():
            if status.was_checked and len(status.issues) > 0:
                return True
    return False


def visualize_results(results: dict[str, dict[Path, FileCheckResult]]) -> None:
    """Visualize the results of the code quality checks.

    Args:
        results: A dictionary mapping checker names to file paths and their check status.
    """
    problems_by_checker = defaultdict(list)
    for checker_name, file_status in results.items():
        results_logger.info("")
        results_logger.info(f" Checker {checker_name} ".center(80, "="))
        for file_path, status in file_status.items():
            if not status.was_checked:
                if len(status.issues) == 0:
                    results_logger.debug(f"⏭️  {file_path} - not checked")
                else:
                    results_logger.warning(
                        f"⚠️  {file_path} - not checked: {status.issues[0].message}"
                    )
                    if len(status.issues) > 1:
                        results_logger.warning(
                            f"    (and {len(status.issues) - 1} more issues)"
                        )

            else:
                if len(status.issues) > 0:
                    problems_by_checker[checker_name].append(file_path)
                    results_logger.info(f"❌ {file_path} - issues found:")
                    for issue in sorted(status.issues, key=lambda x: (x.line or 0)):
                        line = issue.line if issue.line is not None else "unknown"
                        err_msg = (
                            f"    - {file_path}:{line}: {issue.severity.name}:"
                            f" {issue.check_name} - {issue.message}"
                        )
                        results_logger.info(err_msg)
                    results_logger.info("")

                else:
                    results_logger.info(f"✅ {file_path} - no issues found")

    errs = contains_errors(results)
    # sanity check
    if errs != (len(problems_by_checker) > 0):
        logger.error("Inconsistent error detection state!")

    msg = "❌ Errors found" if errs else "✅ No errors found"
    results_logger.info("")
    results_logger.info(" Summary ".center(80, "="))
    results_logger.info(f"Check status: '{msg}'")
    for checker_name in results:
        if checker_name not in problems_by_checker:
            results_logger.info(f"  - ✅ No issues found by '{checker_name}'")
        else:
            results_logger.info(
                "  - ❌ Found issues in"
                f" {len(problems_by_checker[checker_name])}"
                f" files by '{checker_name}'."
            )
    results_logger.info("")


def check(
    target_path: Path,
    filter_checkers: str | None = None,
    verbose: bool = True,
    thorough: bool = False,
    config: Config | None = None,
) -> int:
    """Check the specified file or directory for code quality issues.

    Args:
        target_path: The path to the file or directory to check.
        filter_checkers: Comma-separated list of checkers to run (or no filtering).
        verbose: Whether to show verbose output.
        thorough: Whether to use more thorough (but slower) checks.
        config: The configuration object containing settings for the checkers.

    Returns:
        An integer indicating the result of the check (0 for success, 1 for failure).
    """
    if config is None:
        config = Config()

    if not target_path.exists():
        logger.error(f"Path '{target_path}' does not exist")
        return 1

    checkers = build_checkers(config, filter_checkers, thorough)
    check_results = check_path(target_path, checkers)
    visualize_results(check_results)
    log_llm_pricing()
    return int(contains_errors(check_results))


def main() -> int:
    """Main entry point for the script."""
    args = parse_args()
    # Set console log level based on verbose flag
    console_level = "DEBUG" if args.verbose else "INFO"
    init_logging("qualiluma.log", console_log_level=console_level)
    return check(args.path, args.checkers, args.verbose, args.thorough)


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
