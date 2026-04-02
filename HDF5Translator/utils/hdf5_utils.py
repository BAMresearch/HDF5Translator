"""Utilities for reading, writing, and copying HDF5 structures."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import h5py
import numpy as np

from HDF5Translator.translator_elements import TranslationElement
from HDF5Translator.utils.data_utils import AttributeValue, sanitize_attribute

SourceDataCache = dict[tuple[str, str], tuple[Any, dict[str, AttributeValue]]]


def _clone_cached_data(data: Any) -> Any:
    """Return an isolated copy of cached data when needed to avoid mutation side effects."""
    if isinstance(data, np.ndarray):
        return data.copy()
    return data


def get_data_and_attributes_from_source(
    source_file: h5py.File,
    element: TranslationElement,
    source_data_cache: SourceDataCache | None = None,
) -> tuple[Any, dict[str, AttributeValue]]:
    """Load source data and sanitized attributes for one translation element."""
    attributes: dict[str, AttributeValue] = {}
    data: Any = None

    if element.source is None:
        return element.default_value, attributes

    cache_key: tuple[str, str] | None = None
    if source_data_cache is not None:
        cache_key = (str(source_file.filename), element.source)
        cached_payload = source_data_cache.get(cache_key)
        if cached_payload is not None:
            cached_data, cached_attributes = cached_payload
            return _clone_cached_data(cached_data), dict(cached_attributes)

    data_location = source_file.get(element.source, default=None)
    if isinstance(data_location, h5py.Dataset):
        data = data_location[()]
        attributes = {key: sanitize_attribute(value) for key, value in dict(data_location.attrs).items()}
        if source_data_cache is not None and cache_key is not None:
            source_data_cache[cache_key] = (_clone_cached_data(data), dict(attributes))
    else:
        logging.info(
            "Path %s does not exist in input file %s, using default value %r",
            element.source,
            source_file.filename,
            element.default_value,
        )
        data = element.default_value

    if data is None:
        logging.warning(
            "Path %s does not exist in input file %s and no default value was specified",
            element.source,
            source_file.filename,
        )

    return data, attributes


def _calculate_chunking_shape(data: Any) -> tuple[int, ...] | None:
    """Determine a chunk shape that preserves the two slowest dimensions for arrays."""
    if not isinstance(data, np.ndarray):
        return None
    if len(data.shape) > 1:
        return (1,) * (len(data.shape) - 2) + data.shape[-2:]
    return data.shape


def _dataset_is_compatible(existing_dataset: h5py.Dataset, data: Any) -> bool:
    """Check whether an existing dataset can be updated in place with the provided payload."""
    if isinstance(data, np.ndarray):
        return existing_dataset.shape == data.shape and existing_dataset.dtype == data.dtype

    if np.isscalar(data):
        return existing_dataset.shape == ()

    return False


def write_dataset(
    hdf5_file: h5py.File,
    path: str,
    data: Any,
    compression: str | None = None,
    attributes: dict[str, Any] | None = None,
) -> None:
    """Write a dataset and attributes while avoiding redundant physical writes."""
    parent_path = path.rsplit("/", maxsplit=1)[0] if "/" in path else ""
    if parent_path:
        hdf5_file.require_group(parent_path)

    chunking_shape = _calculate_chunking_shape(data)
    dataset = hdf5_file.get(path)

    if isinstance(dataset, h5py.Dataset) and _dataset_is_compatible(dataset, data):
        try:
            dataset[...] = data
            target_dataset = dataset
        except (TypeError, ValueError):
            del hdf5_file[path]
            target_dataset = hdf5_file.create_dataset(path, data=data, compression=compression, chunks=chunking_shape)
    else:
        if path in hdf5_file:
            del hdf5_file[path]
        target_dataset = hdf5_file.create_dataset(path, data=data, compression=compression, chunks=chunking_shape)

    if attributes is not None:
        target_dataset.attrs.update(attributes)


def _copy_hdf5_tree_open_files(
    h5_in: h5py.File,
    h5_out: h5py.File,
    input_path: str,
    output_path: str,
) -> bool:
    """Recursively copy trees using open file handles to avoid repeated file open/close overhead."""
    if not isinstance(h5_in.get(input_path, default="NonExistentGroup"), h5py.Group):
        logging.info("Input path %s does not exist in %s", input_path, h5_in.filename)
        return False

    copy_to_inside = output_path.endswith("/")
    copy_from_inside = input_path.endswith("/")

    if copy_to_inside:
        output_path = output_path[:-1]
    if copy_from_inside:
        input_path = input_path[:-1]

    if copy_to_inside and copy_from_inside:
        for group in h5_in[input_path].keys():
            _copy_hdf5_tree_open_files(
                h5_in,
                h5_out,
                f"{input_path}/{group}",
                f"{output_path}/{group}",
            )
        return True

    if copy_to_inside:
        return _copy_hdf5_tree_open_files(h5_in, h5_out, input_path, output_path)

    if copy_from_inside:
        logging.error(
            "Cannot copy multiple entries from %s to destination %s without trailing slash",
            input_path,
            output_path,
        )
        return False

    name = input_path.rsplit("/", maxsplit=1)[-1]
    destination_path = f"{output_path}/{name}"
    if destination_path in h5_out:
        logging.warning("Output path %s already exists in %s. Overwriting.", destination_path, h5_out.filename)
        del h5_out[destination_path]

    output_group = h5_out.require_group(output_path)
    h5_in.copy(
        input_path,
        output_group,
        expand_external=True,
        name=name,
    )
    logging.info("Copied %s from %s to %s in %s", input_path, h5_in.filename, output_path, h5_out.filename)
    return True


def copy_hdf5_tree(input_file: Path, output_file: Path, input_path: str, output_path: str) -> bool:
    """Copy a tree from source file to destination file with rsync-like slash semantics."""
    with h5py.File(input_file, "r") as h5_in, h5py.File(output_file, "a") as h5_out:
        return _copy_hdf5_tree_open_files(h5_in, h5_out, input_path, output_path)
