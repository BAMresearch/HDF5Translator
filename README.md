# HDF5Translator

HDF5Translator is a Python framework for translating and transforming data between HDF5 files. It supports operations like unit conversion, dimensionality adjustments, and subtree copying, making it suitable for managing and manipulating a wide range of scientific datasets.

## Extending with other tools

Don't forget that there are also some useful tools in the HDF5 package itself, including the ability to repack files, adjust datasets and compressions and copy particular items. They are available here: 
[hdfgroup documentation on tools](https://docs.hdfgroup.org/hdf5/v1_14/_view_tools_edit.html)

This HDF5Translator package is meant to extend this functionality with a tool to extensively reorder and reorganize HDF5 files. A library of examples [is available here](https://dx.doi.org/10.5281/zenodo.10925972)

An extensive blog post explaining the package [can be read here](https://lookingatnothing.com/)

## Features

  - Translation of HDF5 Structures: Translate data from one HDF5 file to another with flexible mapping configurations.
  - Unit Conversion: Automatically convert data units between source and destination using pint.
  - Dimensionality Adjustment: Prepend dimensions to datasets to ensure a minimum dimensionality.
  - Subtree Copying: Efficiently copy entire (sub-)trees within HDF5 files, preserving the structure and metadata.
  - Template-Based Translation: Initiate translations using an HDF5 template file for the destination structure.

## Installation

Ensure you have Python 3.10 or later installed (ideally 3.12). Clone this repository and navigate into the project directory. Install the required dependencies, as found in the pyproject.toml file. 

Then install the package as a module from within the main HDF5Translator directory:
```bash
python3 -m pip install -e .
```

Run the HDF5Translator from the command line, specifying the source file, destination file, and translation configuration.

```bash
python -m HDF5Translator -I src_file.h5 -O dest_file.h5 -C translation_config.yaml
```
### Optional Arguments
-T, --template_file: Specify a template HDF5 file for the destination.
-v, --verbose: Enable verbose (INFO) output for debugging.
-vv, --very_verbose: Enable very verbose (DEBUG) output for debugging.
-d, --delete: Delete the output file if it already exists.
-l, --logging: output the log to a timestamped file

## Configuration

Translation configurations are defined in YAML files. Here's an example configuration:

```yaml
translations:
  - source: "/source_dataset"
    destination: "/destination_dataset"
    data_type: "float32"
    source_units: "meters"
    destination_units: "millimeters"
    minimum_dimensionality: 3
    compression: "gzip"
    transformation: 'lambda x: np.squeeze(x, axis=0)'
```

## Tools

Several tools are available to help you, check the use examples for details. These include: 
  - edf_to_hdf5.py
  - excel_translator.py
  - a post-translation operation templates

### EDF to HDF5 Convertor
This can used to convert the EDF into H5 format file.

```bash
python src/tools/edf_to_h5.py -I SOURCE_FILE -O DESTINATION_FILE
```

Multiple source files can also be fed into the script. Destination file is optional

### Excel to Yaml Translator
This can be used to convert the excel files into yaml configuration file

```bash
python src/tools/excel_translator.py -I SOURCE_FILE -O DESTINATION_FILE
```

Example excel file is available in `example_configurations/UW_Xeuss`

## Components: 

### Done: 

 - Data Models (translator_elements.py): Definitions of data classes for translation rules using attrs.
 - Configuration Reader (utils/config_reader.py): Functionality to read translation configurations from YAML files.
 - HDF5 Utilities (utils/hdf5_utils.py): Utility functions for common HDF5 operations, including dataset copying with unit conversion and dimensionality adjustment, and subtree copying.
 - data utiities (utils/data_utils.py): validation, typecasting etc. 
 - CLI Interface (__main__.py): Command-line interface setup for running translations based on user inputs.

### ToDo: 

 - Unit Tests: I started on these, but never took the time to write them out. The use examples are the tests for the moment. 
 - Setup and Packaging Files (setup.py, requirements.txt): Scripts for packaging your project, making it installable via pip, and specifying dependencies that need to be installed.
 - Performance Optimization: Depending on the size of the HDF5 files you're working with, you might need to optimize the data reading, writing, and transformation operations to handle large or multiple datasets efficiently.

### Contributing

Contributions to HDF5Translator are welcome! Please read our contributing guidelines for more information.

### License

HDF5Translator is MIT licensed. See the LICENSE file for details.
