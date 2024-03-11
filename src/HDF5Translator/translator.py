from pathlib import Path
import h5py
import yaml

from HDF5Translator.utils.config_reader import read_translation_config
from .translator_elements import TranslationElement
from typing import List
from .utils.hdf5_utils import apply_transformation, create_path_if_not_exists, copy_hdf5_tree
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
    with h5py.File(source_path, 'r') as source_file, h5py.File(dest_path, "a") as dest_file:
        # # Open or create the destination HDF5 file
        # # mode = 'w' if overwrite else 'a'
        # with h5py.File(dest_path, "a") as dest_file:
        # Iterate through the translation elements and perform the necessary actions

        for element in translations:
            process_translation_element(source_file, dest_file, element)

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
    if element.source in source_file:
        data = source_file[element.source][...]

        # Optionally apply transformations
        if element.transformation:
            data = apply_transformation(data, element.transformation)

        # Ensure the destination path exists
        create_path_if_not_exists(dest_file, element.destination)

        # Write data to destination, with optional attributes, compression, etc.
        dest_file.create_dataset(element.destination, data=data, compression=element.compression)
        # Add or update attributes as specified in the element
        for attr_key, attr_value in element.attributes.items():
            dest_file[element.destination].attrs[attr_key] = attr_value
    else:
        # Handle case where source does not exist, according to specifications
        pass
