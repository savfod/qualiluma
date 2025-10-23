"""Utility functions for file operations."""

from pathlib import Path


def load_numbered(file_path: Path) -> str:
    """Load a file and return its content with line numbers.

    This function preserves the original indentation of the code by using
    rstrip() instead of strip(), which is important for Python code.

    Args:
        file_path (Path): The path to the file to load.

    Returns:
        str: The content of the file with line numbers.
    """
    with file_path.open("r") as f:
        return "\n".join(f"{i}: {line.rstrip()}" for i, line in enumerate(f, start=1))