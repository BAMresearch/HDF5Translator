#!/usr/bin/env python
# coding: utf-8

"""
Post-Translation HDF5 Processor

This script performs post-translation steps on HDF5 files, including reading information,
performing calculations (e.g. for determining beam centers, transmission factors and other 
derived information), and writes the result back into the HDF5 structure of the original file.

Usage:
    python post_translation_processor.py --input measurement.h5 [--auxilary_files file2.h5 ...] [-v]

Replace the calculation and file read/write logic according to your specific requirements.

See the MOUSE_beamanalysis script for a working example of post-translation processing.
"""

import argparse
from ctypes import Union
import logging
from pathlib import Path
import hdf5plugin  # loaded BEFORE h5py
import h5py
import numpy as np
from HDF5Translator.utils.validators import (
    file_check_extension,
    file_exists_and_is_file,
)
from HDF5Translator.utils.configure_logging import configure_logging
from HDF5Translator.translator_elements import TranslationElement
from HDF5Translator.translator import process_translation_element
from HDF5Translator.utils.data_utils import getFromKeyVals


description = """
This script is an example on how to perform post-translation operations on HDF5 files.
Ths example includes all the necessary steps, such as including reading information,
performing calculations (e.g. for determining beam centers, transmission factors and other
derived information), and writes the result back into the HDF5 structure of the original file.

The example includes universal command-line arguments for specifying the input file,
auxilary files, and verbosity level. It includes validators and a logging engine. There is also 
the option of supplying key-value pairs for additional parameters to your operation.

You can replace the calculation and file read/write logic according to your specific requirements.
"""


# If you are adjusting the template for your needs, you probably only need to touch the main function:
def main(
    filename: Path,
    auxilary_files: list[Path] | None = None,
    keyvals: dict | None = None,
):
    """
    We do a three-step process here:
      1. read from the main HDF5 file (and optionally the auxilary files),
      2. perform an operation, in this example determining the beam center and flux,
      3. and write back to the file

    In this template, we have the example of determining the beam parameters (center location, flux) from
    the detector data of a beamstopless measurement, and writing it back to the HDF5 file. The example
    also shows how you can add command-line inputs to your process as well.
    """
    # Process input parameters, these are some examples for getting an int and a string:
    ROI_SIZE = getFromKeyVals(
        "roi_size", keyvals, 25
    )  # Size of the region of interest (ROI) for beam center determination. your beam center should be at least this far from the edge
    imageType = getFromKeyVals("image_type", keyvals, "direct_beam")

    # read some information from the main HDF5 file
    with h5py.File(filename, "r") as h5_in:
        # Read necessary information (this is just a placeholder, adapt as needed)
        imageData = h5_in["/entry/data/data_000001"][()]
        recordingTime = h5_in["/entry/instrument/detector/count_time"][()]

    # Now you can do operations, such as determining a beam center and flux. For that, we need to

    # enter your operations here.

    # Now we start the write-back to the HDF5 file, using the TranslationElement class
    # This class lets you configure exactly what the output should look like in the HDF5 file. These are two examples:

    TElements = []  # we want to add two elements, so I make a list
    TElements += [
        TranslationElement(
            # source is none since we're storing derived data
            destination="/entry/sample/beam/beamAnalysis/centerOfMass",
            minimum_dimensionality=1,
            data_type="float32",
            default_value=center_of_mass,
            source_units="px",
            destination_units="px",
            attributes={"note": "Determined by a post-translation processing script."},
        ),
        TranslationElement(
            # source is none since we're storing derived data
            destination="/entry/sample/beam/beamAnalysis/flux",
            default_value=ITotal_region / recordingTime,
            data_type="float",
            source_units="counts/s",
            destination_units="counts/s",
            minimum_dimensionality=1,
            attributes={"note": "Determined by a post-translation processing script."},
        ),
    ]

    # lastly, these elements are interpreted to write the resulting metadata back to the main HDF5 file
    with h5py.File(filename, "r+") as h5_out:
        for element in TElements:  # iterate over the two elements and write them back
            process_translation_element(None, h5_out, element)

    logging.info("Post-translation processing complete.")
    # and now you're done! the rest of the code probably doesn't need updating.


### The code below probably does not need changing for use of the tremplate. ###


def validate_file(file_path: str | Path) -> Path:
    """
    Validates that the file exists and has a valid extension.

    Args:
        file_path (str): Path to the file to validate.

    Returns:
        Path: Path object of the file.
    """
    file_path = Path(file_path)
    file_exists_and_is_file(file_path)
    file_check_extension(file_path, [".h5", ".hdf5", ".nxs", ".H5", ".HDF5", ".NXS"])
    return file_path


# for handling the optional keyval arguments for feeding additional parameters to your operation
class KeyValueAction(argparse.Action):
    """
    Custom action for argparse to parse key-value pairs from the command line.
    """

    def __call__(self, parser, namespace, values, option_string=None):
        keyvals = {}
        for item in values:
            # Split on the first equals sign
            key, value = item.split("=", 1)
            keyvals[key.strip()] = value.strip()
        setattr(namespace, self.dest, keyvals)


def setup_argparser():
    """
    Sets up command line argument parser using argparse.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description=description, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "-f",
        "--filename",
        type=validate_file,
        required=True,
        help="Input measurement HDF5 file.",
    )
    parser.add_argument(
        "-a",
        "--auxilary_files",
        type=validate_file,
        nargs="*",
        help="Optional additional HDF5 files needed for processing. (read-only)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Increase output verbosity to INFO level.",
    )
    parser.add_argument(
        "-vv",
        "--very_verbose",
        action="store_true",
        help="Increase output verbosity to DEBUG level.",
    )
    parser.add_argument(
        "-l",
        "--logging",
        action="store_true",
        help="Write log out to a timestamped file.",
    )
    parser.add_argument(
        "-k",
        "--keyvals",
        nargs="+",
        action=KeyValueAction,
        help="Optional key-value pairs (key=value)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    """
    Entry point for the script. Parses command line arguments and calls the main function.
    """
    args = setup_argparser()
    configure_logging(
        args.verbose,
        args.very_verbose,
        log_to_file=args.logging,
        log_file_prepend="PostTranslationProcessor_",
    )

    logging.info(f"Processing input file: {args.filename}")
    if args.auxilary_files:
        for auxilary_file in args.auxilary_files:
            logging.info(f"using auxilary file: {auxilary_file}")

    main(args.filename, args.auxilary_files, args.keyvals)
