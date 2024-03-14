import fabio
import os
import h5py
import sys


def edf_to_nxs(source_file_location, destination_file_location):
    """
    source_file_location: str
                          edf file location including the .edf extension

    destination_file_location: str
                               .nxs output file location including .nxs extension
    """

    with fabio.open(source_file_location) as source_file:
        two_d_data = source_file.data
        metadata = source_file.header

    with h5py.File(destination_file_location, "w") as dest_file:
        image_grp = dest_file.create_group("image_data")
        image_grp.create_dataset("data", data=two_d_data)

        for key, value in metadata.items():
            subgroup = dest_file.create_group(key)

            subgroup.create_dataset(key, data=value)

        dest_file.close()


if __name__ == "__main__":
    """
    source_file_location: str
                          edf file location including the .edf extension

    destination_file_location: str
                               .nxs output file location including .nxs extension
    """

    source_file_location = sys.argv[1]
    destination_file_location = sys.argv[2]

    edf_to_nxs(source_file_location, destination_file_location)
