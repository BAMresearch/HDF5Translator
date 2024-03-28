"""
The python scripts dumps all the metadata and image data from the .edf file
into .h5 format

"""

import argparse
import fabio
import h5py
import logging
import sys

from pathlib import Path


def edf_to_h5(source_file_location: Path, destination_file_location: Path | None=None):
    """
    source_file_location: str
                          edf file location including the .edf extension

    destination_file_location: str
                               .nxs output file location including .nxs extension
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
        description="Translates the edf file \
                                     into the h5 file structure which can be \
                                     opened into the DAWN Science"
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
        help="Path to the source .edf file",
    )

    args = parser.parse_args(args)


    if args.destination_file:
        if args.destination_file.exists():
            logging.warning(f"Overwriting destination file: {args.destination_file}")
            args.destination_file.unlink()

    logging.info(".edf into .h5 translation started")

    edf_to_h5(args.source_file, args.destination_file)


if __name__ == "__main__":
    """
    source_file_location: str
                          edf file location including the .edf extension

    destination_file_location: str
                               .nxs output file location including .nxs extension
    """
    main()
