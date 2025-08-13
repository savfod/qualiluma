"""
End-of-line checking functionality for LLMCQR.
"""

import sys
from pathlib import Path

from ..config import CONFIG_PATH, yaml_read


def check_trailing_newline(file_path: Path) -> bool:
    """
    Check if a file ends with a newline character.

    Args:
        file_path: Path to the file to check

    Returns:
        True if file ends with newline, False otherwise
    """
    try:
        with open(file_path, "rb") as f:
            if f.seek(0, 2) == 0:  # Empty file
                return True
            f.seek(-1, 2)
            last_char = f.read(1)
            return last_char == b"\n"
    except (IOError, OSError) as e:
        print(f"Error reading file {file_path}: {e}", file=sys.stderr)
        return False


def should_check_file(file_path: Path) -> bool:
    """
    Determine if a file should be checked based on its extension and properties.

    Args:
        file_path: Path to the file

    Returns:
        True if file should be checked, False otherwise
    """
    # Skip binary files and common non-text files
    skip_extensions: list[str] = yaml_read(CONFIG_PATH)["skip_extensions"]

    # Skip hidden files and directories
    if file_path.name.startswith("."):
        return False

    # Skip files with extensions we know are binary
    if file_path.suffix.lower() in skip_extensions:
        return False

    # Check if file appears to be text by trying to read a small portion
    try:
        with open(file_path, "rb") as f:
            sample = f.read(1024)
            # If file contains null bytes, it's likely binary
            if b"\x00" in sample:
                return False
    except (IOError, OSError):
        return False

    return True
