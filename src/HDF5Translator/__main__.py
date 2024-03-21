import argparse
import sys
from pathlib import Path

# from .utils.config_reader import read_translation_config
# Import or define your translation function here
from .translator import translate
import logging
from datetime import datetime


def configure_logging(verbose: bool = False, very_verbose: bool = False):
    """Configure logging to output to stdout and a log file."""
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    log_datefmt = "%Y-%m-%d %H:%M:%S"
    log_filename = f"HDF5Translator_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    if very_verbose: 
        level = logging.DEBUG
    elif verbose:
        level = logging.INFO
    else:
        level = logging.WARNING

    # Configure root logger
    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt=log_datefmt,
        handlers=[logging.FileHandler(log_filename), logging.StreamHandler(sys.stdout)],
    )


def file_exists_and_is_file(file_path: Path):
    """Check if the file exists and is a file."""
    assert file_path.exists() and file_path.is_file(), logging.error(
        f"{file_path} does not exist or is not a file."
    )


def main(args=None):
    """Entry point for the HDF5Translator CLI."""

    if args is None:
        args = sys.argv[1:]

    # Set up the argument parser
    parser = argparse.ArgumentParser(
        description="Translate HDF5 file structures based on specified configurations."
    )
    parser.add_argument(
        "-O",
        "--destination_file",
        required=True,
        type=Path,
        help="Path to the destination HDF5 file.",
    )
    parser.add_argument(
        "-C",
        "--config_file",
        required=True,
        type=Path,
        help="Path to the YAML configuration file specifying the translation.",
    )
    parser.add_argument(
        "-I",
        "--source_file",
        required=False,
        type=Path,
        help="Path to the source HDF5 file, can be left out if you want to make just a template structure .",
    )
    parser.add_argument(
        "-T",
        "--template_file",
        type=Path,
        default=None,
        help="Path to an optional template HDF5 file to use as a base for the destination.",
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
        "-d",
        "--delete",
        action="store_true",
        help="Delete the output file if it already exists, before starting the translation.",
    )

    # Parse arguments
    args = parser.parse_args(args)
    configure_logging(args.verbose, args.very_verbose)
    logging.info("HDF5Translator started.")

    # Validate file existence
    file_exists_and_is_file(args.config_file)
    if args.source_file:
        file_exists_and_is_file(args.source_file)
    if args.template_file:
        file_exists_and_is_file(args.template_file)

    # Handle the output file
    if args.delete and args.destination_file.exists():
        if args.verbose:
            logging.info(f"Deleting existing destination file: {args.destination_file}")
        args.destination_file.unlink()  # Delete the file

    # Read translation configuration
    # translation_config = read_translation_config(args.config_file)
    # logging.debug({f"{translation_config=}"})

    # Perform the translation
    translate(
        args.source_file,
        args.destination_file,
        args.config_file,
        args.template_file,
        args.delete,
    )

    if args.verbose:
        print("Translation completed successfully.")


if __name__ == "__main__":
    main()
