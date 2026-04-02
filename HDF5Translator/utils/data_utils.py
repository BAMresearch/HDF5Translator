"""Utility helpers for data sanitization, conversion, and configuration parsing."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
from pint import UnitRegistry

from HDF5Translator.translator_elements import LinkElement, TranslationElement

ureg = UnitRegistry(auto_reduce_dimensions=True)
ureg.define(r"eigerpixels = 0.075 mm = eigerpixel = eigerpx")
ureg.define(r"pilatuspixels = 0.172 mm = pilatuspixel = pilatuspx")
Q_ = ureg.Quantity

AttributeValue = str | float | int | np.ndarray | None


def summarize_data(data: Any) -> str:
    """Return a compact textual description of a data payload for logging."""
    if isinstance(data, np.ndarray):
        return f"ndarray(shape={data.shape}, dtype={data.dtype})"
    return f"{type(data).__name__}({data!r})"


def apply_transformation(data: Any, transformation: Callable[[Any], Any]) -> Any:
    """Apply a custom transformation and keep original data on failure."""
    try:
        return transformation(data)
    except Exception as error:
        logging.warning(
            "Could not apply transformation %s to %s: %s",
            transformation,
            summarize_data(data),
            error,
        )
        return data


def resolve_alternate_sourcefile(alternate_source_file: str | Path, dest_file: Path) -> Path | None:
    """Resolve an alternate source file path relative to the destination file path."""
    resolved_source_file = Path(alternate_source_file)
    logging.info("Resolving alternate source file %s relative to %s", resolved_source_file, dest_file.parent)

    if any(char in resolved_source_file.as_posix() for char in ["?", "*", "["]):
        source_matches = sorted(Path(dest_file.parent).glob(resolved_source_file.as_posix()))
        if len(source_matches) == 0:
            logging.warning(
                "Could not find a file matching %s relative to %s",
                resolved_source_file,
                dest_file.parent,
            )
            return None
        resolved_source_file = source_matches[-1]
        logging.info("Resolved alternate source file glob to %s", resolved_source_file)

    if not resolved_source_file.is_file():
        logging.warning("Resolved alternate source %s is not a file", resolved_source_file)
        return None
    return resolved_source_file


def cast_to_datatype(data: Any, element: TranslationElement) -> Any:
    """Cast data to the destination datatype declared in a translation element."""
    if element.data_type is None:
        return data

    if not isinstance(element.data_type, type):
        logging.warning(
            "Type conversion requires element.data_type to be a type. Received %s for %s",
            element.data_type,
            element.destination,
        )
        return data

    if data is None:
        return None

    logging.debug(
        "Casting %s to %s for destination %s",
        summarize_data(data),
        element.data_type,
        element.destination,
    )

    try:
        if isinstance(data, np.ndarray):
            target_dtype = np.dtype(element.data_type)
            if data.dtype == target_dtype:
                return data
            return data.astype(target_dtype, copy=False)

        if isinstance(data, element.data_type):
            return data
        return element.data_type(data)
    except (TypeError, ValueError) as error:
        logging.info(
            "Failed to cast %s to %s for %s (%s). Falling back to default value %r",
            summarize_data(data),
            element.data_type,
            element.destination,
            error,
            element.default_value,
        )
        return element.default_value


def add_dimensions_if_needed(data: Any, element: TranslationElement) -> Any:
    """Prepend singleton dimensions until data reaches the configured minimum dimensionality."""
    if element.minimum_dimensionality is None:
        return data

    if data is None:
        return data

    minimum_dimensionality = int(element.minimum_dimensionality)
    if minimum_dimensionality <= 0:
        return data

    try:
        if isinstance(data, np.ndarray):
            if data.ndim >= minimum_dimensionality:
                return data
            extra_dims = (1,) * (minimum_dimensionality - data.ndim)
            return data.reshape(extra_dims + data.shape)

        return np.array(data, ndmin=minimum_dimensionality)
    except (TypeError, ValueError) as error:
        logging.debug(
            "Failed to add dimensions for %s to minimum dimensionality %s (%s)",
            element.destination,
            minimum_dimensionality,
            error,
        )
        return data


def fix_if_array_of_strings(data: Any) -> Any:
    """Convert numpy string arrays to a single whitespace-joined string for HDF5 compatibility."""
    if not isinstance(data, np.ndarray):
        return data
    if data.dtype.kind not in ["U", "S"]:
        return data
    return " ".join(data.tolist())


def select_source_units(element: TranslationElement, attributes: dict[str, Any] | None = None) -> str | None:
    """Resolve source units, preferring source attributes over configured defaults."""
    if attributes is not None and "units" in attributes:
        return attributes["units"]
    return element.source_units


def parse_translation_elements(config: dict[str, Any]) -> list[TranslationElement]:
    """Parse translation element dictionaries from the loaded configuration."""
    translations: list[TranslationElement] = []
    for item in config.get("data_copy", []):
        try:
            translations.append(TranslationElement(**item))
        except TypeError as error:
            logging.warning(
                "Could not parse translation element entry %s (%s). Skipping entry.",
                item,
                error,
            )
    return translations


def parse_link_elements(config: dict[str, Any]) -> list[LinkElement]:
    """Parse link element dictionaries from the loaded configuration."""
    links: list[LinkElement] = []
    for item in config.get("link_list", []):
        try:
            links.append(LinkElement(**item))
        except TypeError as error:
            logging.warning(
                "Could not parse link element entry %s (%s). Skipping entry.",
                item,
                error,
            )
    return links


def if_data_is_none(data: Any, element: TranslationElement) -> Any | None:
    """Replace missing data with default value if configured."""
    if data is not None:
        return data

    if element.default_value is None:
        logging.warning(
            "No data or default value specified for destination %s. Skipping dataset.",
            element.destination,
        )
        return None

    logging.warning(
        "No data specified for destination %s. Falling back to default value %r.",
        element.destination,
        element.default_value,
    )
    return element.default_value


def sanitize_attribute(value: str | bytes | None, default_type: type = float) -> AttributeValue:
    """Convert textual attributes to arrays or scalar numeric values where appropriate."""
    if value is None:
        return None

    if isinstance(value, bytes):
        value = value.decode("utf-8")

    sanitized_value = try_string_as_array(value)
    if isinstance(sanitized_value, str):
        try:
            sanitized_value = default_type(sanitized_value)
        except ValueError:
            pass
    return sanitized_value


def try_string_as_array(value: Any, data_type: type | None = None) -> Any:
    """Parse JSON-style list strings into numpy arrays."""
    if not isinstance(value, str):
        return value

    stripped_value = value.strip()
    if len(stripped_value) == 0 or stripped_value[0] != "[":
        return stripped_value

    try:
        return np.array(json.loads(stripped_value), dtype=data_type)
    except (TypeError, ValueError, json.JSONDecodeError):
        return stripped_value


def sanitize_data(data: Any, element: TranslationElement) -> Any | None:
    """Apply defaulting and datatype conversion rules for a translation payload."""
    sanitized_data = if_data_is_none(data, element)
    if sanitized_data is None:
        logging.warning(
            "Could not find valid data or default for source=%s destination=%s",
            element.source,
            element.destination,
        )
        return None

    if isinstance(sanitized_data, bytes):
        sanitized_data = sanitized_data.decode("utf-8")

    sanitized_data = try_string_as_array(sanitized_data, data_type=element.data_type)
    sanitized_data = cast_to_datatype(sanitized_data, element)
    return sanitized_data


def getFromKeyVals(
    item: str,
    keyvals: dict[str, Any] | None,
    default: str | int | float | None = None,
) -> str | int | float | np.ndarray | None:
    """Read and sanitize values from key-value dictionaries used by post-processing scripts."""
    if keyvals is None:
        return default

    value = keyvals.get(item, default)
    if value is None:
        return default

    return sanitize_attribute(value)


def perform_unit_conversion(data: Any, input_units: str, output_units: str) -> Any:
    """Convert values between units using Pint while returning original data on conversion errors."""
    logging.debug(
        "Converting %s from input_units=%s to output_units=%s",
        summarize_data(data),
        input_units,
        output_units,
    )

    try:
        quantity = Q_(data, input_units)
    except (TypeError, ValueError) as error:
        logging.warning(
            "Could not create quantity for %s with input_units=%s (%s)",
            summarize_data(data),
            input_units,
            error,
        )
        return data

    try:
        converted = quantity.to(output_units).magnitude
    except (TypeError, ValueError) as error:
        logging.warning(
            "Could not convert %s from %s to %s (%s)",
            summarize_data(data),
            input_units,
            output_units,
            error,
        )
        return data

    logging.debug("Converted value summary: %s", summarize_data(converted))
    return converted
