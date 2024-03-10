import argparse
import h5py
import numpy as np


import argparse
import h5py
import numpy as np
import yaml

def stack_datasets_from_config(config_path):
    """
    Stack datasets specified in a YAML configuration file.
    
    Args:
        config_path (str): Path to the YAML configuration file.
    """
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    
    datasets = config['datasets']
    output_path = config['output']['file']
    output_dataset = config['output']['dataset']
    
    # Following the stacking logic from before
    stacked_data = []
    
    for hdf5_path in datasets:
        file_path, dataset_path = hdf5_path.split('::')
        with h5py.File(file_path, 'r') as f:
            data = f[dataset_path][...]
            stacked_data.append(data)
    
    stacked_data = np.concatenate(stacked_data, axis=0)
    
    with h5py.File(output_path, 'a') as f:
        if output_dataset in f:
            del f[output_dataset]  # Remove the existing dataset if it exists
        f.create_dataset(output_dataset, data=stacked_data)

def main():
    parser = argparse.ArgumentParser(description="Stack datasets specified in a YAML configuration file.")
    
    args = parser.parse_args()
    
    stack_datasets_from_config(args.config)

if __name__ == "__main__":
    main()

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
    parser.add_argument('hdf5_paths', nargs='+', help="List of paths to HDF5 datasets to stack. Format: /path/to/file.h5::/dataset/path")
    parser.add_argument('--output', required=True, help="Path to the output HDF5 file.")
    parser.add_argument('--config', required=True, help="Path to the YAML configuration file.")

    args = parser.parse_args()

    stack_datasets(args.hdf5_paths, args.output, args.dataset)

if __name__ == "__main__":
    main()
