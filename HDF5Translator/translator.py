"""Core HDF5 translation workflow."""

from __future__ import annotations

import logging
import os
import shutil
from contextlib import ExitStack
from pathlib import Path
from typing import Any

import h5py
import hdf5plugin  # noqa: F401
import yaml

from .translator_elements import LinkElement, TranslationElement
from .utils.data_utils import (
    add_dimensions_if_needed,
    apply_transformation,
    fix_if_array_of_strings,
    parse_link_elements,
    parse_translation_elements,
    perform_unit_conversion,
    resolve_alternate_sourcefile,
    sanitize_attribute,
    sanitize_data,
    select_source_units,
    summarize_data,
)
from .utils.hdf5_utils import (
    SourceDataCache,
    copy_hdf5_tree,
    get_data_and_attributes_from_source,
    write_dataset,
)


def _source_data_cache_enabled() -> bool:
    """Return whether the optional source dataset cache is enabled for this run."""
    value = os.getenv("HDF5TRANSLATOR_ENABLE_SOURCE_CACHE", "0").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _resolve_source_path_for_element(
    source_file: Path | None,
    alternate_source_file: str | Path | None,
    dest_file: Path,
    alternate_source_cache: dict[str, Path | None],
) -> Path | None:
    """Resolve the source file to use for one element while caching glob resolutions."""
    if alternate_source_file is None:
        return source_file

    normalized_alternate_source = Path(alternate_source_file)
    cache_key = normalized_alternate_source.as_posix()
    if cache_key not in alternate_source_cache:
        alternate_source_cache[cache_key] = resolve_alternate_sourcefile(normalized_alternate_source, dest_file)
    return alternate_source_cache[cache_key]


def _get_open_source_file(
    source_path: Path,
    open_source_files: dict[Path, h5py.File],
    stack: ExitStack,
) -> h5py.File:
    """Open source files lazily and reuse file handles within a translation phase."""
    normalized_path = Path(source_path)
    if normalized_path not in open_source_files:
        open_source_files[normalized_path] = stack.enter_context(h5py.File(normalized_path, "r"))
    return open_source_files[normalized_path]


def translate(
    source_file: Path | None,
    dest_file: Path,
    config_file: Path,
    template_file: Path | None = None,
    overwrite: bool = False,
) -> None:
    """Translate HDF5 file content according to a YAML configuration."""
    with config_file.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file) or {}

    if overwrite and dest_file.exists():
        logging.warning("Overwriting destination file: %s", dest_file)
        dest_file.unlink()

    if template_file is not None:
        shutil.copyfile(template_file, dest_file)

    if source_file is not None:
        for tree in config.get("tree_copy", []):
            copy_hdf5_tree(source_file, dest_file, tree["source"], tree["destination"])

    translations = parse_translation_elements(config)
    alternate_source_cache: dict[str, Path | None] = {}
    source_data_cache: SourceDataCache | None = {} if _source_data_cache_enabled() else None

    with h5py.File(dest_file, "a") as h5_out, ExitStack() as stack:
        open_source_files: dict[Path, h5py.File] = {}
        for element in translations:
            if source_file is None:
                process_translation_element(None, h5_out, element, source_data_cache=source_data_cache)
                continue

            source_path = _resolve_source_path_for_element(
                source_file,
                element.alternate_source_file,
                dest_file,
                alternate_source_cache,
            )
            if source_path is None or not source_path.is_file():
                logging.warning(
                    "Could not resolve source file for destination=%s alternate_source=%s",
                    element.destination,
                    element.alternate_source_file,
                )
                continue

            h5_in = _get_open_source_file(source_path, open_source_files, stack)
            logging.info(
                "Translating destination=%s from source=%s using file=%s",
                element.destination,
                element.source,
                source_path,
            )
            process_translation_element(h5_in, h5_out, element, source_data_cache=source_data_cache)

    attributes = config.get("attributes", {})
    with h5py.File(dest_file, "a") as h5_out:
        for attribute_location, attribute_dict in attributes.items():
            sanitized_attributes = {key: sanitize_attribute(value) for key, value in attribute_dict.items()}
            logging.info("Updating attributes at %s (%d attributes)", attribute_location, len(sanitized_attributes))
            if attribute_location not in h5_out:
                h5_out.require_group(attribute_location)
            h5_out[attribute_location].attrs.update(sanitized_attributes)

    with h5py.File(dest_file, "r+") as h5_out:
        for prune_path in config.get("prune_list", []):
            logging.info("Pruning path %s", prune_path)
            if prune_path in h5_out:
                del h5_out[prune_path]

    link_list = parse_link_elements(config)
    with h5py.File(dest_file, "a") as h5_out, ExitStack() as stack:
        open_source_files: dict[Path, h5py.File] = {}
        for element in link_list:
            if element.internal_or_external == "internal":
                process_link_element(None, h5_out, element)
                continue

            source_path = _resolve_source_path_for_element(
                source_file,
                element.alternate_source_file,
                dest_file,
                alternate_source_cache,
            )
            if source_path is None:
                logging.warning("Source file cannot be None for external link destination=%s", element.destination_path)
                continue

            if element.soft_or_hard_link == "hard":
                logging.info(
                    "External hard links are not supported. Switching to soft link for %s", element.destination_path
                )
                element.soft_or_hard_link = "soft"

            h5_in = _get_open_source_file(source_path, open_source_files, stack)
            process_link_element(h5_in, h5_out, element)


def process_link_element(h5_in: h5py.File | None, h5_out: h5py.File, element: LinkElement) -> None:
    """Create one internal or external HDF5 link from a link element definition."""
    logging.debug(
        "Processing link source_path=%s destination_path=%s mode=%s/%s",
        element.source_path,
        element.destination_path,
        element.internal_or_external,
        element.soft_or_hard_link,
    )

    if element.source_path is None:
        logging.warning("source_path cannot be None for link destination=%s", element.destination_path)
        return

    if element.internal_or_external == "internal":
        if element.source_path not in h5_out:
            logging.warning("Internal source path %s does not exist. Skipping link.", element.source_path)
            return
    else:
        if h5_in is None:
            logging.warning("External link requires an open source file. Skipping %s", element.destination_path)
            return
        if element.source_path not in h5_in:
            logging.warning("External source path %s does not exist. Skipping link.", element.source_path)
            return

    if element.destination_path in h5_out:
        logging.warning("Destination %s exists and will be replaced", element.destination_path)
        del h5_out[element.destination_path]

    if element.internal_or_external == "internal":
        if element.soft_or_hard_link == "soft":
            h5_out[element.destination_path] = h5py.SoftLink(element.source_path)
        else:
            h5_out[element.destination_path] = h5_out[element.source_path]
        return

    assert h5_in is not None
    relative_path = Path(os.path.relpath(Path(h5_in.filename), Path(h5_out.filename).parent))
    logging.debug(
        "Resolved external link file path %s for destination %s",
        relative_path,
        element.destination_path,
    )
    h5_out[element.destination_path] = h5py.ExternalLink(relative_path.as_posix(), element.source_path)


def process_translation_element(
    h5_in: h5py.File | None,
    h5_out: h5py.File,
    element: TranslationElement,
    source_data_cache: SourceDataCache | None = None,
) -> None:
    """Process and write one translation element into the output HDF5 file."""
    if h5_in is not None and element.source is not None:
        data, source_attributes = get_data_and_attributes_from_source(
            h5_in,
            element,
            source_data_cache=source_data_cache,
        )
        logging.debug(
            "Loaded source %s for destination %s: %s with %d attributes",
            element.source,
            element.destination,
            summarize_data(data),
            len(source_attributes),
        )
    else:
        data = element.default_value
        source_attributes: dict[str, Any] = {}

    data = sanitize_data(data, element)
    if data is None:
        return

    if element.transformation is not None:
        data = apply_transformation(data, element.transformation)

    source_units = select_source_units(element, source_attributes)
    if source_units and element.destination_units:
        data = perform_unit_conversion(data, source_units, element.destination_units)

    if not isinstance(data, str):
        data = add_dimensions_if_needed(data, element)

    data = fix_if_array_of_strings(data)

    merged_attributes: dict[str, Any] = dict(source_attributes)
    merged_attributes.update(element.attributes)

    if source_units is not None:
        merged_attributes["units"] = source_units
    if element.destination_units is not None:
        merged_attributes["units"] = element.destination_units

    sanitized_attributes = {
        key: sanitize_attribute(value) for key, value in merged_attributes.items() if value is not None
    }

    logging.debug(
        "Writing destination %s with %s compression=%s attrs=%d",
        element.destination,
        summarize_data(data),
        element.compression,
        len(sanitized_attributes),
    )

    write_dataset(
        h5_out,
        element.destination,
        data,
        compression=element.compression,
        attributes=sanitized_attributes,
    )
