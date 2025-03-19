import os
from pathlib import Path
from typing import Union
import h5py
import hdf5plugin  # noqa: F401
import yaml

from HDF5Translator.utils.data_utils import sanitize_data

# from HDF5Translator.utils.config_reader import read_translation_config
from .translator_elements import LinkElement, TranslationElement
from .utils.hdf5_utils import (
    copy_hdf5_tree,
    get_data_and_attributes_from_source,
    write_dataset,
)
from .utils.data_utils import (
    add_dimensions_if_needed,
    apply_transformation,
    fix_if_array_of_strings,
    parse_link_elements,
    parse_translation_elements,
    perform_unit_conversion,
    resolve_alternate_sourcefile,
    sanitize_attribute,
    select_source_units,
)
import logging
import shutil


def translate(
    source_file: Path,
    dest_file: Path,
    config_file: Path,
    template_file: Union[Path, None] = None,
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

    # Step 0: Optionally use a template file as the basis for the destination
    if template_file:
        # Logic to copy the template HDF5 file to the destination path
        shutil.copyfile(template_file, dest_file)

    # Step 1: Copy trees from source to destination
    for tree in config.get("tree_copy", []):
        copy_hdf5_tree(source_file, dest_file, tree["source"], tree["destination"])

    # Read the data_copy sheet, also add some guardrails in case entries are not properly specified:
    translations = parse_translation_elements(config)

    # Step 2: Apply specific dataset translations, transformations, datatype conversions, etc.
    with h5py.File(dest_file, "a") as h5_out:
        for element in translations:
            if source_file:
                sf = source_file
                if element.alternate_source_file is not None:
                    sf = resolve_alternate_sourcefile(
                        element.alternate_source_file, dest_file
                    )
                if (sf is None) or (not Path(sf).is_file()):
                    logging.warning(
                        f"could not resolve alternate source file for {element=}, skipping"
                    )
                    continue
                with h5py.File(sf, "r") as h5_in:
                    logging.info(f"Translating {element=} ")
                    process_translation_element(h5_in, h5_out, element)
            else:
                process_translation_element(None, h5_out, element)

        # if source_file:
        #     with h5py.File(source_file, "r") as h5_in:
        #         for element in translations:
        #             logging.info(f"Translating {element=} ")
        #             process_translation_element(h5_in, h5_out, element)
        # else:
        #     for element in translations:
        #         process_translation_element(None, h5_out, element)

    # Step 3: Update or add attributes as specified in the configuration
    attributes = config.get("attributes", [])
    with h5py.File(dest_file, "a") as h5_out:
        for attributeLocation, attributeDict in attributes.items():
            ad = {k: sanitize_attribute(v) for k, v in attributeDict.items()}
            logging.info(f"adding {attributeLocation=}, {ad=}")
            if attributeLocation not in h5_out:
                # create the destination as a group, because I know nothing of a dataset to be created..
                h5_out.require_group(attributeLocation)
            h5_out[attributeLocation].attrs.update(ad)

    # Step 4: remove (prune) any datasets or groups as specified in the configuration
    with h5py.File(dest_file, "r+") as h5_out:
        for prune in config.get("prune_list", []):
            logging.info(f"pruning {prune}")
            if prune in h5_out:
                del h5_out[prune]

    # Step 5: Add links from the link_list
    link_list = parse_link_elements(config)

    with h5py.File(dest_file, "a") as h5_out:
        for element in link_list:

            if element.internal_or_external == "external":
                sf = source_file
                if element.alternate_source_file is not None:
                    sf = resolve_alternate_sourcefile(
                        element.alternate_source_file, dest_file
                    )
                if sf is None:
                    logging.warning(
                        f"source cannot be none for external link translations... skipping"
                    )
                    continue
                if element.soft_or_hard_link == "hard":
                    logging.info(
                        "For external links, hard links are not allowed. enforcing soft links."
                    )
                    element.soft_or_hard_link = "soft"
                with h5py.File(sf, "r") as h5_in:
                    process_link_element(h5_in, h5_out, element)
            else:
                process_link_element(None, h5_out, element)


def process_link_element(
    h5_in: h5py.File | None, h5_out: h5py.File, element: LinkElement
):
    """
    Processes a single link element, applying the specified link to the HDF5 files.
    """
    logging.debug(f"processing link {element=}")

    # escape clause
    if element.source_path is None:
        logging.warning(f"source cannot be none for link translations... skipping")
        return

    # check if source exists:
    if element.internal_or_external == "internal":
        if not element.source_path in h5_out:
            logging.warning(
                f"{element.source_path=} does not exist in {h5_out}, skipping..."
            )
            return
    else:
        if not element.source_path in h5_in:
            logging.warning(
                f"{element.source_path=} does not exist in {h5_in}, skipping..."
            )
            return

    # delete destination if it already exists:
    if element.destination_path in h5_out:
        logging.warning(
            f"destination {element.destination_path} already exists, deleting before creating this link"
        )
        del h5_out[element.destination_path]

    if element.internal_or_external == "internal":
        if element.soft_or_hard_link == "soft":
            h5_out[element.destination_path] = h5py.SoftLink(element.source_path)
        if element.soft_or_hard_link == "hard":
            h5_out[element.destination_path] = h5_out[element.source_path]

    else:  # external
        if element.soft_or_hard_link == "hard":
            logging.warning(
                f"Hard external links are not supported, defaulting to softlink; {element=} "
            )
        # get relative path with respect to output file:
        # Todo: Python 3.12+ pathlib supports the "walk_up" boolean to replicate this. When
        # requirements would go for 3.12, this should be enabled, and the os.path disabled:
        # relpath = Path(h5_in.filename).relative_to(Path(h5_out.filename), walk_up = True)
        relpath = Path(
            os.path.relpath(Path(h5_in.filename), Path(h5_out.filename).parent)
        )
        logging.debug(
            f"resolved relative path between {h5_in.filename=} and {h5_out.filename=} for external link: {relpath=}"
        )
        h5_out[element.destination_path] = h5py.ExternalLink(
            relpath.as_posix(), element.source_path
        )


def process_translation_element(
    h5_in: h5py.File | None, h5_out: h5py.File, element: TranslationElement
):
    """Processes a single translation element, applying the specified translation to the HDF5 files.

    Args:
        source_file: The source HDF5 file object.
        dest_file: The destination HDF5 file object.
        element (TranslationElement): The translation element specifying the translation rule.
    """

    # Read dataset and attributes from source if specified, otherwise go for default
    if h5_in and element.source:
        data, attributes = get_data_and_attributes_from_source(h5_in, element)
        logging.debug(
            f"got data {data=} and attributes {attributes=} from source {element.source}"
        )
    else:
        data = element.default_value
        attributes = element.attributes if element.attributes else {}

    # adjust the data for the destination, applying type
    data = sanitize_data(data, element)

    # escape clause
    if data is None:  # adjust_data has already complained about this
        return

    # Optionally apply transformations / lambda functions
    if element.transformation:
        data = apply_transformation(data, element.transformation)

    # get the correct source units to work with:
    source_units = select_source_units(element, attributes)

    # apply units transformation if needed:
    if source_units and element.destination_units:
        # Apply unit conversion
        data = perform_unit_conversion(data, source_units, element.destination_units)

    # add dimensions if needed, and if the data is not a string type
    if not isinstance(data, str):
        data = add_dimensions_if_needed(data, element)

    # Anton Paar data can contain arrays of strings, which h5py has issues with. Concatenating that into a single string if needed.
    data = fix_if_array_of_strings(data)

    # we need to update element.attributes to include source attributes, but element.attributes takes preference as you might have wanted to update some attributes through this mechanism
    if attributes:
        attributes.update(element.attributes)
        element.attributes = attributes  # now replace the source

    # add or update destination_units in attributes
    if source_units is not None:
        element.attributes.update({"units": source_units})
    if element.destination_units is not None:
        element.attributes.update({"units": element.destination_units})
    # somehow we can still end up with None in the attributes, so let's clean that up
    element.attributes = {
        k: sanitize_attribute(v) for k, v in element.attributes.items() if v is not None
    }

    logging.debug(
        f"writing to {h5_out=}, in path {element.destination}, {data=}, using compression {element.compression} and attributes {element.attributes}"
    )

    write_dataset(
        h5_out,
        element.destination,
        data,
        compression=element.compression,
        attributes=element.attributes,
    )

    # Write data to destination, with optional attributes, compression, etc.
    # dest_file.create_dataset(element.destination, data=data, compression=element.compression)
    # Add or update attributes as specified in the element
    # for attr_key, attr_value in element.attributes.items():
    #     h5_out[element.destination].attrs[attr_key] = sanitize_attribute(attr_value)
