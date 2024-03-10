import logging
from pathlib import Path
import h5py
import numpy as np
from pint import UnitRegistry

ureg = UnitRegistry()
Q_ = ureg.Quantity

def create_path_if_not_exists(hdf5_file: h5py.File, path: str):
    """Ensure that the HDF5 path exists, creating groups as necessary."""
    current = hdf5_file
    for group in path.strip('/').split('/'):
        if group not in current:
            current = current.create_group(group)
        else:
            current = current[group]

def apply_transformation(data, transformation):
    """Apply the given transformation function to the data."""
    return transformation(data) 

def read_dataset(hdf5_file: h5py.File, path: str, transformation=None):
    """Read dataset from the given path and apply an optional transformation."""
    if path in hdf5_file:
        data = hdf5_file[path][...]
        if transformation:
            data = apply_transformation(data, transformation)
        return data
    else:
        return None  # or raise an error/exception as appropriate
    
def write_dataset(hdf5_file: h5py.File, path: str, data, compression=None, attributes={}):
    """Write data to the specified path, creating groups as necessary, and setting attributes."""
    create_path_if_not_exists(hdf5_file, '/'.join(path.split('/')[:-1]))  # Ensure the group exists
    dset = hdf5_file.create_dataset(path, data=data, compression=compression)
    for attr_name, attr_value in attributes.items():
        dset.attrs[attr_name] = attr_value

def copy_dataset(source_dataset: h5py.Dataset, dest_file: h5py.File, dest_path: str,
                 input_units=None, output_units=None, minimum_dimensionality=0):
    """
    Copies a dataset from the source to the destination path, including attributes,
    with optional unit conversion and dimensionality adjustment.

    Args:
        source_dataset (h5py.Dataset): The source dataset to copy.
        dest_file (h5py.File): The destination HDF5 file object.
        dest_path (str): The destination path in the HDF5 file.
        input_units (str, optional): The units of the source dataset's data.
        output_units (str, optional): The units to convert the dataset's data to.
        minimum_dimensionality (int, optional): The minimum number of dimensions the dataset should have.
    """
    data = source_dataset[...]

    # Perform unit conversion if both input and output units are specified
    if input_units and output_units:
        data = perform_unit_conversion(data, input_units, output_units)

    # Adjust data dimensionality if necessary
    while data.ndim < minimum_dimensionality:
        data = np.expand_dims(data, axis=0)

    # Ensure destination group exists
    dest_group_path = '/'.join(dest_path.split('/')[:-1])
    if dest_group_path and dest_group_path not in dest_file:
        dest_file.create_group(dest_group_path)

    # Copy dataset
    dset = dest_file.create_dataset(dest_path, data=data, compression=source_dataset.compression)

    # Copy attributes
    for name, value in source_dataset.attrs.items():
        dset.attrs[name] = value

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
    quantity = Q_(data, input_units)
    converted = quantity.to(output_units).magnitude
    return converted

def copy_hdf5_tree(input_file:Path, output_file:Path, input_path:str, output_path:str):
    # generates the name from a logbook entry row
    
    assert input_file.exists(), logging.error(f"input file {input_file} does not exist")
    # assert output_file.exists(), f"output file {output_file} does not exist"

    with h5py.File(input_file, 'r') as h5_in, h5py.File(output_file, 'a') as h5_out:
        if output_path in h5_out:
            logging.warning(f"Output path {output_path} already exists in {output_file}. Overwriting.")
            del h5_out[output_path]
        h5_in.copy(input_path, h5_out, name=output_path)
        logging.info(f"Copied {input_path} from {input_file} to {output_path} in {output_file}.")


# def copy_subtree(source_file: h5py.File, dest_file: h5py.File, source_path: str, dest_path: str):
#     """
#     Recursively copies a subtree from a source HDF5 file to a destination path in another HDF5 file.

#     Args:
#         source_file (h5py.File): The source HDF5 file object.
#         dest_file (h5py.File): The destination HDF5 file object.
#         source_path (str): The path within the source file to start copying from.
#         dest_path (str): The path within the destination file to copy to.
#     """
#     # Ensure the source exists
#     if source_path not in source_file:
#         raise ValueError(f"Source path {source_path} not found in source file.")

#     source_obj = source_file[source_path]

#     # If the source is a group, recursively copy its contents
#     if isinstance(source_obj, h5py.Group):
#         for name, item in source_obj.items():
#             if isinstance(item, h5py.Dataset):
#                 # Copy dataset
#                 copy_dataset(item, dest_file, f"{dest_path}/{name}")
#             elif isinstance(item, h5py.Group):
#                 # Recursively copy group
#                 new_dest_path = f"{dest_path}/{name}"
#                 if new_dest_path not in dest_file:
#                     dest_file.create_group(new_dest_path)
#                 copy_subtree(source_file, dest_file, f"{source_path}/{name}", new_dest_path)
                
#         # After copying items, copy the attributes of the group
#         copy_attributes(source_obj, dest_file[dest_path])

#     elif isinstance(source_obj, h5py.Dataset):
#         # Directly copy dataset if the source path is a dataset
#         copy_dataset(source_obj, dest_file, dest_path)

def copy_dataset(source_dataset: h5py.Dataset, dest_file: h5py.File, dest_path: str):
    """
    Copies a dataset from the source to the destination path, including attributes.

    Args:
        source_dataset (h5py.Dataset): The source dataset to copy.
        dest_file (h5py.File): The destination HDF5 file object.
        dest_path (str): The destination path in the HDF5 file.
    """
    # Ensure destination group exists
    dest_group_path = '/'.join(dest_path.split('/')[:-1])
    if dest_group_path and dest_group_path not in dest_file:
        dest_file.create_group(dest_group_path)
    
    # Copy dataset
    dest_file.copy(source_dataset, dest_path)

    # Copy attributes (handled automatically by h5py's copy method if entire dataset is copied)

def copy_attributes(source_obj, dest_obj):
    """
    Copies attributes from a source object (group or dataset) to a destination object.

    Args:
        source_obj: The source object to copy attributes from.
        dest_obj: The destination object to copy attributes to.
    """
    for name, value in source_obj.attrs.items():
        dest_obj.attrs[name] = value

def apply_attributes(hdf5_file_path: str, attributes_config: dict):
    """
    Applies attributes to nodes (groups/datasets) within an HDF5 file based on the provided configuration.

    Args:
        hdf5_file_path (str): Path to the HDF5 file.
        attributes_config (dict): A dictionary containing the attribute configurations.
    """
    with h5py.File(hdf5_file_path, 'a') as hdf5_file:
        for path, attributes in attributes_config.items():
            # Use require_group to ensure the group exists; does nothing if the group already exists.
            # Note: h5py doesn't have a generic "require_dataset" similar to "require_group",
            # so dataset existence needs additional logic if datasets are to be created.
            node = hdf5_file.require_group(path) if not isinstance(hdf5_file.get(path), h5py.Dataset) else hdf5_file[path]

            # Apply attributes
            for attr_name, attr_value in attributes.items():
                node.attrs[attr_name] = attr_value