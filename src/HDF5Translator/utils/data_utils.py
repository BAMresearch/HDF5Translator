import logging
from typing import Union
import numpy as np
from pint import UnitRegistry

from HDF5Translator.translator_elements import TranslationElement

ureg = UnitRegistry(auto_reduce_dimensions=True)
# ureg.define(r"pixels = 1 = px")
Q_ = ureg.Quantity

doc = """
This module contains utility functions for data manipulation, such as casting to a specific datatype, adding dimensions, and unit conversion.
"""


def apply_transformation(data, transformation):
    """Apply the given transformation function to the data."""
    return transformation(data)


def cast_to_datatype(data, element: TranslationElement):
    """determines the datatype we need the data to be, recasting it if needed"""
    if element.data_type is not None:
        logging.debug(
            f"attempting to cast value {data} into data_type: {element.data_type}"
        )
        if not isinstance(element.data_type, type):
            print(
                "Type conversion must be supplied with a data type in element.data_type, something must have gone wrong. returning data as is without conversion"
            )
            return data

        if data is None:
            # can't do anything, return none
            return None

        try:
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

    # cast to datatype
    data = cast_to_datatype(data, element)

    # fix string datatypes so h5py can handle them, otherwise it complains about not being able to store '<U4' type
    if isinstance(data, str):
        data = data.encode("utf-8")

    return data


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
    logging.debug(f"Converting {data=} from {input_units=} to {output_units=}")
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
    return converted
