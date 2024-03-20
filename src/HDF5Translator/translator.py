from pathlib import Path
import h5py
import numpy as np
import yaml

# from HDF5Translator.utils.config_reader import read_translation_config
from .translator_elements import LinkElement, TranslationElement
from typing import List, Union
from .utils.hdf5_utils import (
    adjust_data_for_destination,
    apply_transformation,
    copy_hdf5_tree,
    get_data_and_attributes_from_source,
    perform_unit_conversion,
    write_dataset,
)
import logging
import shutil


def translate(
    source_file: Path,
    dest_file: Path,
    config_file: Path,
    template_file: Path = None,
    overwrite: bool = False,
):
    """Performs the translation of an HDF5 file based on the given configuration.

    Args:
        source_path (str): Path to the source HDF5 file.
        dest_path (str): Path to the destination HDF5 file.
        translations (List[TranslationElement]): List of translation elements specifying the translation rules.
        template_path (str, optional): Path to a template HDF5 file to use as the base for the destination. Defaults to None.
        overwrite (bool, optional): Whether to overwrite the destination file if it exists. Defaults to False.
    """
    with open(config_file, "r") as file:
        config = yaml.safe_load(file)

    if overwrite:
        logging.warning(f"Overwriting destination file: {dest_file}")
        if dest_file.exists():
            dest_file.unlink()

    # Optionally use a template file as the basis for the destination
    if template_file:
        # Logic to copy the template HDF5 file to the destination path
        shutil.copy(template_file, dest_file)

    # Step 1: Copy trees from source to destination
    for tree in config.get("tree_copy", []):
        copy_hdf5_tree(source_file, dest_file, tree["source"], tree["destination"])

    # Step 2: Apply specific dataset translations, transformations, datatype conversions, etc.
    translations = [TranslationElement(**item) for item in config.get("data_copy", [])]

    with h5py.File(dest_file, "a") as h5_out:
        if source_file:
            with h5py.File(source_file, "r") as h5_in:
                for element in translations:
                    logging.info(f"Translating {element=} ")
                    process_translation_element(h5_in, h5_out, element)
        else:
            for element in translations:
                process_translation_element(None, h5_out, element)

    # Step 3: Update or add attributes as specified in the configuration
    attributes = config.get("attributes", [])
    with h5py.File(dest_file, "a") as h5_out:
        for attributeLocation, attributeDict in attributes.items():
            logging.info(f"adding {attributeLocation=}, {attributeDict=}")
            if not attributeLocation in h5_out:
                # create the destination as a group, because I know nothing of a dataset to be created..
                h5_out.require_group(attributeLocation)
            h5_out[attributeLocation].attrs.update(attributeDict)

    # Step 4: remove (prune) any datasets or groups as specified in the configuration
    with h5py.File(dest_file, "a") as h5_out:
        for prune in config.get("prune_list", []):
            if prune.get("path"):
                del dest_file[prune["path"]]

    # Step 5: Add links from the link_list
    link_list = [LinkElement(**item) for item in config.get("link_list", [])]

    with h5py.File(dest_file, "a") as h5_out:
        for element in link_list:
            if element.internal_or_external == "external":
                sf = source_file
                if element.alternate_source_file is not None:
                    sf = element.alternate_source_file
                if sf is None:
                    logging.warning(
                        f"source cannot be none for external link translations... skipping"
                    )
                    continue
                with h5py.File(sf, "r") as h5_in:
                    process_link_element(h5_in, h5_out, element)
            else:
                process_link_element(None, h5_out, element)


def process_link_element(
    h5_in: Union[h5py.File | None], h5_out: h5py.File, element: LinkElement
):

    if element.internal_or_external == "internal":
        if element.soft_or_hard_link == "soft":
            h5_out[element.destination_path] = h5py.SoftLink(element.source_path)
        if element.soft_or_hard_link == "hard":
            h5_out[element.destination_path] = h5_out[element.source_path]

    else:  # external
        # I don't think soft links are possible for external things
        # if element.soft_or_hard_link == 'soft':
        #     h5_out[element.destination_path] = h5py.SoftLink(element.source_path)
        if element.soft_or_hard_link == "soft":
            logging.warning(
                f"Soft external links are not supported, defaulting to hardlink; {element=} "
            )
        h5_out[element.destination_path] = h5_in[element.source_path]


def process_translation_element(
    h5_in: Union[h5py.File | None], h5_out: h5py.File, element: TranslationElement
):
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
    if h5_in:
        data, attributes = get_data_and_attributes_from_source(h5_in, element)
    else:
        data = element.default_value
        attributes = element.attributes if element.attributes else {}

    # update translation element units if source_file is specified, and the source_path units attribute exists and is not None
    if "units" in attributes:
        # specified HDF5 source units take preference over preconfigured element.source_units
        element.source_units = attributes.get("units", element.source_units)

    # adjust the data for the destination, applying transformation, units, and dimensionality adjustments
    data = adjust_data_for_destination(data, element, attributes=attributes)

    # escape clause
    if data is None:
        logging.warning(
            f"Could not find valid data or default for {element.source=}, {element.destination=}, skipping..."
        )
        return

    # Optionally apply transformations
    if element.transformation:
        data = apply_transformation(data, element.transformation)

    # apply units transformation if needed:
    if element.source_units and element.destination_units:
        # Apply unit conversion
        perform_unit_conversion(data, element.source_units, element.destination_units)

    write_dataset(
        h5_out,
        element.destination,
        data,
        compression=element.compression,
        attributes=element.attributes,
    )
    # Ensure the destination path exists
    # create_path_if_not_exists(dest_file, element.destination)

    # Write data to destination, with optional attributes, compression, etc.
    # dest_file.create_dataset(element.destination, data=data, compression=element.compression)
    # Add or update attributes as specified in the element
    for attr_key, attr_value in element.attributes.items():
        h5_out[element.destination].attrs[attr_key] = attr_value
