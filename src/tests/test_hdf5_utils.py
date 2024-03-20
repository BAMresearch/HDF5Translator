import unittest
import h5py
import numpy as np
import tempfile

from HDF5Translator.utils.hdf5_utils import (
    get_data_and_attributes_from_source,
    write_dataset,
)


class TestHDF5Utils(unittest.TestCase):

    def setUp(self):
        # Setup temporary HDF5 files for testing
        self.source_file = tempfile.NamedTemporaryFile(delete=False, suffix=".h5")
        self.dest_file = tempfile.NamedTemporaryFile(delete=False, suffix=".h5")

        # Create a dataset in the source file
        with h5py.File(self.source_file.name, "w") as f:
            data = np.arange(10)
            f.create_dataset("data", data=data)

    def tearDown(self):
        # Remove temporary files
        self.source_file.close()
        self.dest_file.close()


if __name__ == "__main__":
    unittest.main()
