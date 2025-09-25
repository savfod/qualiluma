"""
End-of-line checking functionality for Qualiluma.
"""

from pathlib import Path

from ..util import get_logger

logger = get_logger(__name__)


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
        logger.error(f"Error reading file {file_path}: {e}")
        return False
