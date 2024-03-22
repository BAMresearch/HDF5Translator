from pathlib import Path
import logging

def file_exists_and_is_file(file_path: Path):
    """Check if the file exists and is a file."""
    assert file_path.exists() and file_path.is_file(), logging.error(
        f"{file_path} does not exist or is not a file."
    )

def file_check_extension(file_path: Path, valid_extensions: list):
    """Check if the file has a valid extension."""
    assert file_path.suffix in valid_extensions, logging.error(
        f"{file_path} should have a valid extension of {valid_extensions}."
    )