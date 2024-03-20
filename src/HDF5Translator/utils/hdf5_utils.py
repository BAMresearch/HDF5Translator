import logging
from pathlib import Path
from typing import Union
import h5py
import numpy as np
from pint import UnitRegistry

from HDF5Translator.translator_elements import TranslationElement

ureg = UnitRegistry(auto_reduce_dimensions=True)
# ureg.define(r"pixels = 1 = px")
Q_ = ureg.Quantity


def apply_transformation(data, transformation):
    """Apply the given transformation function to the data."""
    return transformation(data)


def get_data_and_attributes_from_source(
    source_file: h5py.File, element: TranslationElement
):
    """
    Get data from the source file according to the given translation element.
    """

    # check if source data exists:
    dataLocation = None
    attributes = {}
    data = None

    if element.source is not None:
        dataLocation = source_file.get(element.source, default=None)
    if isinstance(dataLocation, h5py.Dataset):
        data = dataLocation[()]
        attributes = dict(dataLocation.attrs)
    else:
        logging.info(
            f"Path {element.source} does not exist in the input file, using default value {element.default_value} instead"
        )
        data = element.default_value

    if data is None:
        logging.warning(
            f"Path {element.source} does not exist in the input file, and no default value was specified. skipping..."
        )

    return data, attributes


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
            data = element.default

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


def select_source_units(
    element: TranslationElement, attributes: Union[dict | None] = None
):
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
                f"no data or default value specified for {element.destination}, returning None."
            )
            return None
        else:
            logging.warning(
                f"no data specified for {element.destination}, returning default value {element.default_value}."
            )
            data = element.default_value
    return data


def adjust_data_for_destination(data, element: TranslationElement, attributes):
    """
    Adjust the data according to the destination specifications.
    If you have both source_units in the translation configuration,
        and the source hdf5 file has units specified in the attributes,
        the source file attribute units are applied.
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

    # # Optionally apply transformations
    # if element.transformation:
    #     data = apply_transformation(data, element.transformation)

    # # Perform unit conversion if both input and output units are specified
    # if (element.source_units is not None) and element.destination_units:
    #     data = perform_unit_conversion(
    #         data, element.source_units, element.destination_units
    #     )

    # fix string datatypes so h5py can handle them, otherwise it complains about not being able to store '<U4' type
    if isinstance(data, str):
        data = data.encode("utf-8")

    # add dimensions if needed
    data = add_dimensions_if_needed(data, element)

    return data


def write_dataset(
    hdf5_file: h5py.File, path: str, data, compression=None, attributes={}
):
    """
    Write data to the specified path, creating groups as necessary, and setting attributes.
    """

    hdf5_file.require_group(path.rsplit("/", maxsplit=1)[0])
    # check if the dataset exists and is compatible:
    if isinstance(data, np.ndarray):
        shape = data.shape
        dtype = data.dtype
    else:
        shape = None
        dtype = type(data)
    try:  # if it does not exist, fill with new data
        dset = hdf5_file.require_dataset(
            path,
            shape=shape,
            dtype=dtype,
            data=data,
            compression=compression,
            exact=True,
        )
    except TypeError:  # if it exists but is incompatible, delete it and create it again
        if path in hdf5_file:
            del hdf5_file[path]
        dset = hdf5_file.create_dataset(path, data=data, compression=compression)
    # update attributes.
    dset.attrs.update(attributes)


# unused:
# def copy_dataset(
#     source_dataset: h5py.Dataset,
#     dest_file: h5py.File,
#     dest_path: str,
#     input_units=None,
#     output_units=None,
#     minimum_dimensionality=0,
# ):
#     """
#     Copies a dataset from the source to the destination path, including attributes,
#     with optional unit conversion and dimensionality adjustment.

#     Args:
#         source_dataset (h5py.Dataset): The source dataset to copy.
#         dest_file (h5py.File): The destination HDF5 file object.
#         dest_path (str): The destination path in the HDF5 file.
#         input_units (str, optional): The units of the source dataset's data.
#         output_units (str, optional): The units to convert the dataset's data to.
#         minimum_dimensionality (int, optional): The minimum number of dimensions the dataset should have.
#     """
#     data = source_dataset[...]

#     # Perform unit conversion if both input and output units are specified
#     if input_units and output_units:
#         data = perform_unit_conversion(data, input_units, output_units)

#     # Adjust data dimensionality if necessary
#     while data.ndim < minimum_dimensionality:
#         data = np.expand_dims(data, axis=0)

#     # Ensure destination group exists
#     dest_group_path = "/".join(dest_path.split("/")[:-1])
#     if dest_group_path and dest_group_path not in dest_file:
#         dest_file.create_group(dest_group_path)

#     # Copy dataset
#     write_dataset(
#         dest_file,
#         dest_path,
#         data,
#         compression=source_dataset.compression,
#         attributes=attributes,
#     )
#     # dset = dest_file.create_dataset(dest_path, data=data, compression=source_dataset.compression)

#     # Copy attributes
#     dset.attrs[name] = value


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


def copy_hdf5_tree(
    input_file: Path, output_file: Path, input_path: str, output_path: str
):

    with h5py.File(input_file, "r") as h5_in, h5py.File(output_file, "a") as h5_out:
        if not isinstance(
            h5_in.get(input_path, default="NonExistentGroup"), h5py.Group
        ):
            logging.info(f"{input_path=} does not exist in {input_file=}")
            return False
        if output_path in h5_out:
            logging.warning(
                f"Output path {output_path} already exists in {output_file}. Overwriting."
            )
            del h5_out[output_path]
        output_group = h5_out.require_group(output_path)
        h5_in.copy(input_path, output_group, expand_external=True)
        logging.info(
            f"Copied {input_path} from {input_file} to {output_path} in {output_file}."
        )
        return True
