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

This example determines a beam center and flux from a beamstopless measurement.
requires scikit-image
"""

import argparse
from ctypes import Union
import logging
from pathlib import Path
import hdf5plugin # loaded BEFORE h5py
import h5py
import numpy as np
from skimage.measure import regionprops
from HDF5Translator.utils.validators import file_check_extension, file_exists_and_is_file
from HDF5Translator.utils.configure_logging import configure_logging
from HDF5Translator.translator_elements import TranslationElement
from HDF5Translator.translator import process_translation_element

def main(filename: Path, auxilary_files: list[Path] = None):
    """
    We do a three-step process here: 
      1. read from the main HDF5 file (and optionally the auxilary files), 
      2. perform an operation, 
      3. and write back to the file

    In this template, we have the example of determining the beam parameters (center location, flux) from 
    the detector data of a beamstopless measurement, and writing it back to the HDF5 file.
    """

    ROI_SIZE = 25  # Size of the region of interest (ROI) for beam center determination. your beam center should be at least this far from the edge

    # Example of reading from the main HDF5 file
    with h5py.File(filename, 'r') as h5_in:
        # Read necessary information (this is just a placeholder, adapt as needed)
        imageData = h5_in['/entry/data/data_000001'][()]
        recordingTime = h5_in['/entry/instrument/detector/count_time'][()]
    
    # reduce the dimensionality of the imageData by averaging until we have a 2D array:
    while imageData.ndim > 2:
        imageData = np.mean(imageData, axis=0)

    # get rid of masked or pegged pixels
    labeled_foreground = (np.logical_and(imageData >= 0, imageData <= 1e6)).astype(int)
    maskedTwoDImage = imageData * labeled_foreground # apply mask
    threshold_value = np.maximum(1, 0.0001 * maskedTwoDImage.max()) # filters.threshold_otsu(maskedTwoDImage) # ignore zero pixels
    labeled_peak = (maskedTwoDImage > threshold_value).astype(int) # label peak
    properties = regionprops(labeled_peak, imageData) # calculate region properties
    center_of_mass = properties[0].centroid # center of mass (unweighted by intensity)
    weighted_center_of_mass = properties[0].weighted_centroid # center of mass (weighted)

    ITotal_region = np.sum(maskedTwoDImage[
            np.maximum(int(weighted_center_of_mass[0] - 25), 0): np.minimum(int(weighted_center_of_mass[0] + 25), maskedTwoDImage.shape[0]), 
            np.maximum(int(weighted_center_of_mass[1] - 25), 0): np.minimum(int(weighted_center_of_mass[1] + 25), maskedTwoDImage.shape[1])
        ])

    logging.debug(f'{center_of_mass=}')
    logging.debug(f'{ITotal_region=}, flux = {ITotal_region / recordingTime} counts/s')

    # configure how you want the output to look like in the HDF5 file:
    TElements = []
    TElements += [
        TranslationElement(
            # source is none since we're storing derived data
            destination='/entry/sample/beam/beamAnalysis/centerOfMass',
            minimum_dimensionality=1,
            data_type='float32',
            default_value=center_of_mass,
            destination_units='px',
            attributes={'note': 'Determined by a post-translation processing script.'}
        ),
        TranslationElement(
            # source is none since we're storing derived data
            destination='/entry/sample/beam/beamAnalysis/flux',
            default_value=ITotal_region / recordingTime,
            data_type='float',
            destination_units='counts/s',
            minimum_dimensionality=1,
            attributes={'note': 'Determined by a post-translation processing script.'}
        )
    ]

    # Example of writing back to the main HDF5 file
    with h5py.File(filename, 'r+') as h5_out:
        for element in TElements:
            process_translation_element(None, h5_out, element)

    logging.info("Post-translation processing complete.")

### in principle, the code below does not need changing for use of the tremplate. ###

def validate_file(file_path: str| Path) -> Path:
    """
    Validates that the file exists and has a valid extension.

    Args:
        file_path (str): Path to the file to validate.

    Returns:
        Path: Path object of the file.
    """
    file_path = Path(file_path)
    file_exists_and_is_file(file_path)
    file_check_extension(file_path, ['.h5', '.hdf5', '.nxs','.H5', '.HDF5', '.NXS'])
    return file_path


def setup_argparser():
    """
    Sets up command line argument parser using argparse.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Perform post-translation operations on HDF5 files.")
    parser.add_argument('-f', '--filename', type=validate_file, required=True, help="Input measurement HDF5 file.")
    parser.add_argument('-a', '--auxilary_files', type=validate_file, nargs='*', help="Optional additional HDF5 files needed for processing. (read-only)")
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
    return parser.parse_args()


if __name__ == "__main__":

    args = setup_argparser()
    configure_logging(args.verbose, args.very_verbose, log_to_file=args.logging, log_file_prepend="PostTranslationProcessor_")

    logging.info(f"Processing input file: {args.filename}")
    if args.auxilary_files:
        for auxilary_file in args.auxilary_files:
            logging.info(f"using auxilary file: {auxilary_file}")
    
    main(args.filename, args.auxilary_files)