from pathlib import Path
import h5py
import argparse
import logging 
from ..HDF5Translator.utils.hdf5_utils import copy_hdf5_tree

def setup_argparser():
    parser = argparse.ArgumentParser(description="""
        Copies an existing tree from one HDF5 file to another. Source and destination points can be specified.  
        Useful for adding original entries to a processed HDF5 file.
        
        Example usage:
        python AddHDF5TreeToHDF5.py -i input_file.h5 -o output_file.h5 -I /source/path -O /destination/path
    """)
    parser.add_argument("-i", "--input_file", type=Path, required=True, help="Input HDF5 filename")
    parser.add_argument("-o", "--output_file", type=Path, required=True, help="Output HDF5 filename")
    parser.add_argument("-I", "--input_path", type=str, required=True, help="Internal HDF5 path in the input file to copy from")
    parser.add_argument("-O", "--output_path", type=str, required=True, help="Internal HDF5 path in the output file to copy to")
    return parser.parse_args()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    args = setup_argparser()
    
    copy_hdf5_tree(args.input_file, args.output_file, args.input_path, args.output_path)
