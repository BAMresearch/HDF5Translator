from pathlib import Path
import h5py
import numpy as np
import yaml

# from HDF5Translator.utils.config_reader import read_translation_config
from .translator_elements import TranslationElement
from typing import List
from .utils.hdf5_utils import adjust_data_for_destination, apply_transformation, copy_hdf5_tree, get_data_and_attributes_from_source, perform_unit_conversion, write_dataset
import logging
import shutil


def translate(source_path: Path, dest_path: Path, config_path:Path, template_path: Path = None, overwrite: bool = False):
    """Performs the translation of an HDF5 file based on the given configuration.

    Args:
        source_path (str): Path to the source HDF5 file.
        dest_path (str): Path to the destination HDF5 file.
        translations (List[TranslationElement]): List of translation elements specifying the translation rules.
        template_path (str, optional): Path to a template HDF5 file to use as the base for the destination. Defaults to None.
        overwrite (bool, optional): Whether to overwrite the destination file if it exists. Defaults to False.
    """
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)

    # Optionally use a template file as the basis for the destination
    if template_path:
        # Logic to copy the template HDF5 file to the destination path
        shutil.copy(template_path, dest_path)

    if overwrite:
        logging.warning(f"Overwriting destination file: {dest_path}")
        if dest_path.exists():
            dest_path.unlink()

    # Step 1: Copy trees from source to destination
    for tree in config.get('treecopy', []):
        copy_hdf5_tree(source_path, dest_path, tree['source'], tree['destination'])

    # Step 2: Apply specific dataset translations, transformations, datatype conversions, etc.
    translations = [TranslationElement(**item) for item in config.get('translations',[])]

    with h5py.File(dest_path, "a") as dest_file:
        if source_path:
            with h5py.File(source_path, "r") as source_file:                        
                for element in translations:
                    process_translation_element(source_file, dest_file, element)
        else:
            for element in translations:
                process_translation_element(None, dest_file, element)            

    # Step 3: Update or add attributes as specified in the configuration
    with h5py.File(dest_path, "a") as dest_file:
        for attribute in config.get("attributes", []):
            if attribute.get("path") and attribute.get("key") and attribute.get("value"):
                dest_file[attribute["path"]].attrs[attribute["key"]] = attribute["value"]

    # Step 4: remove (prune) any datasets or groups as specified in the configuration
    with h5py.File(dest_path, "a") as dest_file:
        for prune in config.get("prune", []):
            if prune.get("path"):
                del dest_file[prune["path"]]


def process_translation_element(source_file, dest_file, element: TranslationElement):
    """Processes a single translation element, applying the specified translation to the HDF5 files.

    Args:
        source_file: The source HDF5 file object.
        dest_file: The destination HDF5 file object.
        element (TranslationElement): The translation element specifying the translation rule.
    """
    # Here, you would implement the logic to:
    # - Check if the source dataset/group exists.
    # - Apply any specified transformations.
    # - Create the destination path if it doesn't exist.
    # - Write the data to the destination file, applying any specified datatype conversions or unit changes.
    
    # Example: Read dataset from source
    if source_file:
        data, attributes = get_data_and_attributes_from_source(source_file, element)
    else:
        data = element.default_value
        attributes = element.attributes if element.attributes else {}

    # update translation element units if source_file is specified, and the source_path units attribute exists and is not None
    if 'units' in attributes:
        # specified HDF5 source units take preference over preconfigured element.source_units
        element.source_units = attributes.get('units', element.source_units)

    # adjust the data for the destination, applying transformation, units, and dimensionality adjustments
    data = adjust_data_for_destination(data, element)

    # Optionally apply transformations
    if element.transformation:
        data = apply_transformation(data, element.transformation)    
    # Prepend dimensions to reach minimum dimensionality:
    while data.ndim < element.minimum_dimensionality:
        data = np.expand_dims(data, axis=0)


    # apply units transformation if needed:
    if element.source_units and element.destination_units:
        # Apply unit conversion
        perform_unit_conversion(data, element.source_units, element.destination_units)
        
    write_dataset(dest_file, element, data)
    # Ensure the destination path exists
    # create_path_if_not_exists(dest_file, element.destination)

    # Write data to destination, with optional attributes, compression, etc.
    # dest_file.create_dataset(element.destination, data=data, compression=element.compression)
    # Add or update attributes as specified in the element
    for attr_key, attr_value in element.attributes.items():
        dest_file[element.destination].attrs[attr_key] = attr_value

