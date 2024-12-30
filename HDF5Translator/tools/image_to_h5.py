"""
The python scripts dumps all the metadata and image data from 
a fabIO-compatibe image file (such as EDF, TIFF, etc) into an
HDF5 file. The metadata is stored in the root of the HDF5 file
while the image data is stored in a group called "image_data".
"""

import argparse
import fabio
import h5py
import logging
import sys

from pathlib import Path


def image_to_h5(source_file_location: Path, destination_file_location: Path | None=None):
    """
    source_file_location: str
                          image file location. The file should be fabIO-compatible

    destination_file_location: optional, str
                               .h5 output file location including .h5 extension. 
                               if not supplied, it's the source file with .h5 extension
    """

    for source_file in source_file_location:

        if destination_file_location is None:
            destination_file_location = source_file.with_suffix(".h5")

        with fabio.open(source_file) as s_file:
            two_d_data = s_file.data
            metadata = s_file.header

        with h5py.File(destination_file_location, "w") as dest_file:

            image_grp = dest_file.create_group("image_data")
            image_grp.create_dataset("data", data=two_d_data)

            for key, value in metadata.items():

                subgroup = dest_file.create_group(key)

                subgroup.create_dataset(key, data=value)

            dest_file.close()

        destination_file_location = None


def main(args=None):

    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description="Translates a (fabIO-compatibe) image file \
                                     into a basic h5 file structure which can be \
                                     translated with HDF5Translator"
    )
    parser.add_argument(
        "-O",
        "--destination_file",
        required=False,
        type=Path,
        help="Path to the destination .h5 file, can be left out \
                            if h5 extension file with same name is required",
    )
    parser.add_argument(
        "-I",
        "--source_file",
        nargs="+",
        required=True,
        type=Path,
        help="Path to the source (fabIO-compatible) image file such as TIFF, EDF, etc.",
    )

    args = parser.parse_args(args)


    if args.destination_file:
        if args.destination_file.exists():
            logging.warning(f"Overwriting destination file: {args.destination_file}")
            args.destination_file.unlink()

    logging.info("image to HDF5 translation started")

    image_to_h5(args.source_file, args.destination_file)


if __name__ == "__main__":
    """
    source_file_location: str
                          image file location including the image extension

    destination_file_location: str
                               .nxs output file location including .nxs extension
    """
    main()
