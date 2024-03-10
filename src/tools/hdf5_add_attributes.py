import argparse
import logging
from HDF5Translator.utils.hdf5_utils import apply_attributes
from HDF5Translator.utils.attributes_reader import read_attributes_from_yaml

def main():
    parser = argparse.ArgumentParser(description="Apply attributes to an HDF5 file based on a YAML configuration.")
    parser.add_argument('-c', '--config', type=str, required=True, help="Path to the YAML configuration file.")
    parser.add_argument('-f', '--file', type=str, required=True, help="Path to the HDF5 file.")

    args = parser.parse_args()

    # Read attributes from YAML
    attributes_config = read_attributes_from_yaml(args.config)

    # Apply attributes to HDF5 file
    apply_attributes(args.file, attributes_config)

    logging.info(f"Attributes applied to {args.file} based on {args.config}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main()
