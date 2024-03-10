import unittest
import h5py
import numpy as np
import tempfile
from HDF5Translator.utils.hdf5_utils import copy_dataset

class TestHDF5Utils(unittest.TestCase):

    def setUp(self):
        # Setup temporary HDF5 files for testing
        self.source_file = tempfile.NamedTemporaryFile(delete=False, suffix='.h5')
        self.dest_file = tempfile.NamedTemporaryFile(delete=False, suffix='.h5')

        # Create a dataset in the source file
        with h5py.File(self.source_file.name, 'w') as f:
            data = np.arange(10)
            f.create_dataset('data', data=data)

    def tearDown(self):
        # Clean up temporary files
        self.source_file.close()
        self.dest_file.close()

    def test_copy_dataset_with_unit_conversion(self):
        # Copy dataset with unit conversion (e.g., from meters to millimeters)
        with h5py.File(self.source_file.name, 'r') as source, h5py.File(self.dest_file.name, 'w') as dest:
            copy_dataset(source['data'], dest, 'converted_data', input_units='meters', output_units='millimeters')

            # Verify the data was converted correctly (e.g., multiplied by 1000)
            self.assertTrue(np.array_equal(dest['converted_data'][...], source['data'][...] * 1000))

    def test_copy_dataset_with_dimensionality_adjustment(self):
        # Copy dataset with dimensionality adjustment
        with h5py.File(self.source_file.name, 'r') as source, h5py.File(self.dest_file.name, 'w') as dest:
            copy_dataset(source['data'], dest, 'adjusted_data', minimum_dimensionality=3)

            # Verify that dimensions were added as expected
            self.assertEqual(dest['adjusted_data'].ndim, 3)
            self.assertTrue(np.array_equal(dest['adjusted_data'][...], np.expand_dims(np.expand_dims(source['data'][...], 0), 0)))

if __name__ == '__main__':
    unittest.main()
