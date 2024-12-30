from pathlib import Path
import logging
from typing import List

def file_exists_and_is_file(file_path: Path):
    """Assert that the file exists and is a file."""
    assert file_path.exists() and file_path.is_file(), logging.error(
        f"{file_path} does not exist or is not a file."
    )

def delete_file_if_exists(file_path:Path):
    """removes the file if it exists already."""
    if (file_path.exists() and file_path.is_file()):
        file_path.unlink()

def file_check_extension(file_path: Path, valid_extensions: list):
    """Check if the file has a valid extension."""
    assert file_path.suffix in valid_extensions, logging.error(
        f"{file_path} should have a valid extension of {valid_extensions}."
    )

def validate_file_delete_if_exists(file_path: str | Path) -> Path:
    return validate_file(file_path, delete_if_exists=True, must_exist=False)

def validate_yaml_file(file_path):
    return validate_file(file_path, extension_list=[".yaml", ".YAML"])

def validate_file(file_path: str | Path, must_exist=True, delete_if_exists=False, extension_list: List = [".h5", ".hdf5", ".nxs", ".H5", ".HDF5", ".NXS"]) -> Path:
    """
    Validates that the file exists and has a valid extension.

    Args:
        file_path (str): Path to the file to validate.

    Returns:
        Path: Path object of the file.
    """
    file_path = Path(file_path)
    if must_exist:
        file_exists_and_is_file(file_path)
    if delete_if_exists:
        delete_file_if_exists(file_path)
    file_check_extension(file_path, extension_list)
    return file_path