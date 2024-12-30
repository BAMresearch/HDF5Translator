import logging
from pathlib import Path
import h5py
import numpy as np

from HDF5Translator.translator_elements import TranslationElement
from HDF5Translator.utils.data_utils import sanitize_attribute

doc = """
This module contains utility functions for working with HDF5 files, such as copying trees, reading data, and writing data.
"""


def get_data_and_attributes_from_source(
    source_file: h5py.File, element: TranslationElement
):
    """
    Get data and attributes from the source file according to the given translation element.
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
        # sanitize attributes
        attributes = {k: sanitize_attribute(v) for k, v in attributes.items()}
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
        dset[...] = data
    except (
        TypeError,
        ValueError,
    ):  # if it exists but is incompatible, delete it and create it again
        if path in hdf5_file:
            del hdf5_file[path]
        dset = hdf5_file.create_dataset(path, data=data, compression=compression)
    # update attributes.
    dset.attrs.update(attributes)


def copy_hdf5_tree(
    input_file: Path, output_file: Path, input_path: str, output_path: str
):
    """
    Copy a tree from one HDF5 file to another. This should behave like rsync when it comes to slashes etc.
    """

    with h5py.File(input_file, "r") as h5_in, h5py.File(output_file, "a") as h5_out:
        if not isinstance(
            h5_in.get(input_path, default="NonExistentGroup"), h5py.Group
        ):
            logging.info(f"{input_path=} does not exist in {input_file=}")
            return False

        # check if we need to copy the source element(s) to inside a group
        copy_to_inside = False
        if output_path[-1] == "/":
            copy_to_inside = True
            output_path = output_path[:-1]
        # check if we need to copy multiple elements from inside the source
        copy_from_inside = False
        if input_path[-1] == "/":
            copy_from_inside = True
            input_path = input_path[:-1]

        # deal with the case where we need to copy multiple elements from inside the source or to inside a group
        if copy_to_inside and copy_from_inside:
            for group in h5_in[input_path].keys():
                copy_hdf5_tree(
                    input_file,
                    output_file,
                    f"{input_path}/{group}",
                    f"{output_path}/{group}",
                )
            return True
        elif copy_to_inside:
            copy_hdf5_tree(input_file, output_file, input_path, output_path)
            return True
        elif copy_from_inside:
            logging.error(
                f"Cannot copy multiple entries from inside a group to a single output destination. Did you forget a trailing slash in the destination? Skipping {input_path}"
            )
            return False

        # This is the actual copying functionality. If we reach this point, we are copying a single element to a single destination.
        name = input_path.rsplit("/", maxsplit=1)[-1]
        if (output_path + "/" + name) in h5_out:
            logging.warning(
                f"Output path {output_path + '/' + name} already exists in {output_file}. Overwriting."
            )
            del h5_out[output_path + "/" + name]
        output_group = h5_out.require_group(output_path)
        h5_in.copy(
            input_path,
            output_group,
            expand_external=True,
            name=name,
        )
        logging.info(
            f"Copied {input_path} from {input_file} to {output_path} in {output_file}."
        )
        return True
