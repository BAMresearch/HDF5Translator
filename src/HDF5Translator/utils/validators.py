from pathlib import Path
import logging
from typing import List

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

def validate_file(file_path: str | Path, extension_list: List = [".h5", ".hdf5", ".nxs", ".H5", ".HDF5", ".NXS"]) -> Path:
    """
    Validates that the file exists and has a valid extension.

    Args:
        file_path (str): Path to the file to validate.

    Returns:
        Path: Path object of the file.
    """
    file_path = Path(file_path)
    file_exists_and_is_file(file_path)
    file_check_extension(file_path, extension_list)
    return file_path