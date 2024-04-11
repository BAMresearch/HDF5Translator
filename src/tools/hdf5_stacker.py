import argparse
import h5py
import numpy as np
import yaml
import logging

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

def stack_datasets(hdf5_paths, output_path, output_dataset):
    """
    Stack multiple HDF5 datasets into a single dataset.

    Args:
        hdf5_paths (list): List of paths to the HDF5 files (and dataset paths within them).
        output_path (str): Path to the output HDF5 file.
        output_dataset (str): Name of the dataset in the output HDF5 file.
    """
    datasets = []

    for hdf5_path in hdf5_paths:
        file_path, dataset_path = hdf5_path.split('::')
        with h5py.File(file_path, 'r') as f:
            data = f[dataset_path][...]
            datasets.append(data)

    stacked_data = np.concatenate(datasets, axis=0)

    # Create or open the output file and write the stacked dataset
    with h5py.File(output_path, 'a') as f:
        if output_dataset in f:
            del f[output_dataset]  # Remove the existing dataset if it exists
        f.create_dataset(output_dataset, data=stacked_data)

def main():
    parser = argparse.ArgumentParser(description="Stack multiple HDF5 datasets into a single dataset.")
    parser.add_argument('hdf5_paths', nargs='+', help="List of paths to HDF5 datasets to stack. Format: /dataset/path1 /dataset/path2 ...")
    parser.add_argument('--output', required=True, help="Path to the output HDF5 file, this can be an existing file.")
    parser.add_argument('--config', required=True, help="Path to the YAML configuration file.")
    parser.add_argument('--datafiles', required=True, nargs="+", help="filenames of the datafiles to stack.")

    args = parser.parse_args()

    stack_datasets(args.hdf5_paths, args.output, args.dataset)

if __name__ == "__main__":
    main()
