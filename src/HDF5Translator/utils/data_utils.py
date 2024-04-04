import json
import logging
from pathlib import Path
from typing import Callable, List, Type, Union
import numpy as np
from pint import UnitRegistry

from HDF5Translator.translator_elements import LinkElement, TranslationElement

ureg = UnitRegistry(auto_reduce_dimensions=True)
ureg.define(r"eigerpixels = 0.075 mm = eigerpixel = eigerpx")
ureg.define(r"pilatuspixels = 0.172 mm = pilatuspixel = pilatuspx")
Q_ = ureg.Quantity

doc = """
This module contains utility functions for data manipulation, such as casting to a specific datatype, adding dimensions, and unit conversion.
"""


def apply_transformation(data, transformation: Callable):
    """Apply the given transformation function to the data."""
    try:
        data = transformation(data)
    except Exception as e:
        logging.warning(
            f"Could not apply custom transformation {transformation} to {data=}, received exception {e}. skipping transformation..."
        )
    return data


def resolve_alternate_sourcefile(alternate_source_file: str | Path, dest_file: Path):
    alternate_source_file = Path(alternate_source_file)
    logging.info(
        f"trying to resolve {alternate_source_file=} relative to {dest_file.parent=}"
    )
    if any([c in alternate_source_file.as_posix() for c in ["?", "*", "["]]):
        sourceFile = sorted(
            Path(dest_file.parent).glob(alternate_source_file.as_posix())
        )
        if len(sourceFile) == 0:
            logging.warning(
                f"a file matching {alternate_source_file=} could not be found relative to the output file. Skipping link"
            )
            return
        logging.info(f"Source file globbed: {sourceFile[-1]}")
        alternate_source_file = sourceFile[-1]
    if not alternate_source_file.is_file():
        logging.warning(f"{alternate_source_file=} is not a file. Skipping link")
        return None
    return alternate_source_file


def cast_to_datatype(data, element: TranslationElement):
    """determines the datatype we need the data to be, recasting it if needed"""
    if element.data_type is not None:
        logging.debug(
            f"attempting to cast value {data} into data_type: {element.data_type}"
        )
        if not isinstance(element.data_type, type):
            logging.warning(
                "Type conversion must be supplied with a data type in element.data_type, something must have gone wrong. returning data as is without conversion"
            )
            return data

        if data is None:
            # can't do anything, return none
            return None

        try:
            if isinstance(data, np.ndarray):
                data = data.astype(element.data_type)
            else:
                data = element.data_type(data)
        except ValueError:
            logging.info(
                f"could not cast value {data} into data_type {element.data_type}, defaulting to {element.default_value} for {element.destination}"
            )
            data = element.default_value

    return data


def add_dimensions_if_needed(data, element: TranslationElement):

    if element.minimum_dimensionality is None:
        # no change needed
        return data

    if data is None or element.minimum_dimensionality == 0:
        return data  # nothing I can do.

    dtype = type(data)
    if isinstance(data, np.ndarray):
        dtype = data.dtype
    try:
        logging.debug(
            f"trying to add {element.minimum_dimensionality} dimensions to {data=} of dtype {dtype=} for {element.destination=}"
        )
        data = np.array(data, dtype=dtype, ndmin=int(element.minimum_dimensionality))
    except:  # didn't work...
        logging.debug("failure to add dimensions. Skipping")

    return data


def fix_if_array_of_strings(data):
    if not isinstance(data, np.ndarray):
        return data  # leave unchanged
    if not data.dtype.kind in ["U", "S"]:  # if not one of the string datatypes
        return data  # leave unchanged
    else:
        return " ".join(data.tolist())


def select_source_units(element: TranslationElement, attributes: [dict | None] = None):
    """
    This singular function dictates what takes precedence: the units specified in the source file, or the units specified in the translation configuration.
    If both are none, result remains none. If both are set, the source file units are chosen.
    """
    if attributes is not None:
        if "units" in attributes.keys():
            return attributes["units"]

    if element.source_units is None:
        return None
    else:
        return element.source_units


def parse_translation_elements(config) -> List:
    translations = []
    for item in config.get("data_copy", []):
        try:
            translations += [TranslationElement(**item)]
        except TypeError as e:
            logging.warning(
                f"Could not properly interpret the following entry as a TranslationElement (skipping...): {item=}. it raised the following error: {e}"
            )
    return translations


def parse_link_elements(config) -> List:
    links = []
    for item in config.get("link_list", []):
        try:
            links += [LinkElement(**item)]
        except TypeError as e:
            logging.warning(
                f"Could not properly interpret the following entry as a LinkElement (skipping...): {item=}. it raised the following error: {e}"
            )
    return links


def if_data_is_none(data, element):

    if data is None:
        if element.default_value is None:
            logging.warning(
                f"no data or default value specified for {element.destination}, returning None and skipping.."
            )
            return None
        else:
            logging.warning(
                f"no data specified for {element.destination}, returning default value {element.default_value}."
            )
            data = element.default_value
    return data


def sanitize_attribute(
    value: str | bytes | None, default_type: Type = float
) -> Union[str, float, np.ndarray]:
    """
    Tries to convert the attribute to:
      - numpy array
      - value
      - leave as string
    """
    if value is None:
        return None

    if isinstance(value, bytes):
        value = value.decode("utf-8")

    value = try_string_as_array(value)
    if isinstance(value, str):  # conversion did not succeed
        try:
            value = default_type(value)
        except ValueError:
            pass
    return value


def try_string_as_array(value: str, data_type: Type = None) -> Union[str, np.ndarray]:
    """
    Tries to convert the value to a numpy array
    """
    if isinstance(value, str):
        value = value.strip()
        if len(value) > 0:
            if value[0] == "[":  # sign it's an array
                value = np.array(json.loads(value), dtype=data_type)
    return value


def sanitize_data(data, element: TranslationElement):
    """
    Adjust the data according to the destination specifications.
    This applies default value from the translation element if data is none,
    casts to the datatype if specified in the translation element,
    """

    # apply default value if data is None
    data = if_data_is_none(data, element)

    if data is None:
        logging.warning(
            f"Could not find valid data or default for {element.source=}, {element.destination=}, skipping..."
        )
        return None

    # convert bytes to string:
    if isinstance(data, bytes):
        data = data.decode("utf-8")

    # check if it is an array by checking the first character, and try to interpret it as such
    data = try_string_as_array(data, data_type=element.data_type)

    # cast to datatype
    data = cast_to_datatype(data, element)

    # # fix string datatypes so h5py can handle them, otherwise it complains about not being able to store '<U4' type
    # if isinstance(data, str):
    #     print(f'{data=}') # strings can be "1"
    #     data = data.encode("utf-8")
    #     print(f'{data=}') # and now they are b"1".. ugh.

    return data


def getFromKeyVals(
    item: str, keyvals: dict | None, default: str | int | float | None = None
) -> str | int | float | None:
    """
    Helper function to get a value from the keyvals dictionary, with a default value if not present.
    """
    if keyvals is None:
        return default
    val = keyvals.get(item, default)
    if val is None:
        return default
    val = sanitize_attribute(val)
    return val


def perform_unit_conversion(data, input_units, output_units):
    """
    Converts the data from input units to output units using pint.

    Args:
        data (np.ndarray): The data to convert.
        input_units (str): The units of the input data.
        output_units (str): The units to convert the data to.

    Returns:
        np.ndarray: The data converted to the output units.
    """
    logging.debug(
        f"Converting {data=} of type {type(data)} from {input_units=} to {output_units=}"
    )
    try:
        quantity = Q_(data, input_units)
    except:
        logging.warning(
            f"Could not convert {data=} to a quantity with {input_units=}, skipping unit conversion"
        )
        return data
    try:
        converted = quantity.to(output_units).magnitude
    except:
        logging.warning(
            f"Could not convert {data=} from {input_units=} to {output_units=}, skipping unit conversion"
        )
        return data
    logging.debug(f"converted value: {converted}")
    return converted
