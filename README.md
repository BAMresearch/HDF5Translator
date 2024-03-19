# HDF5Translator

HDF5Translator is a Python tool designed to translate and transform data between HDF5 files. It supports complex operations like unit conversion, dimensionality adjustments, and subtree copying, making it suitable for managing and manipulating scientific datasets.

## Extending with other tools

Don't forget that there are also some useful tools in the HDF5 package itself, including the ability to repack files, adjust datasets and compressions and copy particular items. They are available here: 
[hdfgroup documentation on tools](https://docs.hdfgroup.org/hdf5/v1_14/_view_tools_edit.html)

This HDF5Translator package is meant to extend this functionality with a tool to extensively reorder and reorganize HDF5 files. 

## Features

  - Translation of HDF5 Structures: Translate data from one HDF5 file to another with flexible mapping configurations.
  - Unit Conversion: Automatically convert data units using pint.
  - Dimensionality Adjustment: Prepend dimensions to datasets to achieve a minimum dimensionality.
  - Subtree Copying: Efficiently copy entire (sub-)trees within HDF5 files, preserving the structure and metadata.
  - Template-Based Translation: Initiate translations using an HDF5 template file for the destination structure.

## Installation

Ensure you have Python 3.12 or later installed. Clone this repository and navigate into the project directory. Install the required dependencies:

```bash
pip install -r requirements.txt
```

Run the HDF5Translator from the command line, specifying the source file, destination file, and translation configuration.

```bash
python -m HDF5Translator src_file.h5 dest_file.h5 translation_config.yaml
```
### Optional Arguments
-t, --template_file: Specify a template HDF5 file for the destination.
-v, --verbose: Enable verbose output for debugging.
-d, --delete: Delete the output file if it already exists.

## Configuration

Translation configurations are defined in YAML files. Here's an example configuration:

```yaml
translations:
  - source: "/source_dataset"
    destination: "/destination_dataset"
    datatype: "float32"
    input_units: "meters"
    output_units: "millimeters"
    minimum_dimensionality: 3
    compression: "gzip"
```

## Tools

### Template Creator
Use the template creator tool to generate a template HDF5 file.

```bash
python -m HDF5Translator.tools.template_creator template_file.h5
```

### EDF to HDF5 Convertor
This can used to convert the EDF into H5 format file.

```bash
python -m HDF5Translator.tools.edf_to_h5.py -I SOURCE_FILE -O DESTINATION_FILE
```

Multiple source files can also be fed into the script. Destination file is optional

### Excel to Yaml Translator
This can be used to convert the excel files into yaml configuration file

```bash
python -m HDF5Translator.tools.excel_translator.py -I SOURCE_FILE -O DESTINATION_FILE
```

Example excel file is available in `src/test/testdata/UW_Xeuss`

## Components: 

### Done: 

 - Data Models (translator_elements.py): Definitions of data classes for translation rules using attrs.
 - Configuration Reader (utils/config_reader.py): Functionality to read translation configurations from YAML files.
 - HDF5 Utilities (utils/hdf5_utils.py): Utility functions for common HDF5 operations, including dataset copying with unit conversion and dimensionality adjustment, and subtree copying.
 - Main Translator Logic (translator.py): The core logic for applying translation rules to copy data from a source HDF5 file to a destination HDF5 file, potentially using a template.
 - CLI Interface (__main__.py): Command-line interface setup for running translations based on user inputs.

### ToDo: 

 - Template Creation Logic (tools/template_creator.py): If your template creation logic involves more than just copying an existing file, you might need detailed functionality for generating template HDF5 files based on specific criteria or configurations.
 - Logging Configuration (__main__.py or a separate module): Detailed logging setup to capture and record runtime information, warnings, and errors to both stdout and a log file, enhancing debugging and monitoring capabilities.
 - Comprehensive Error Handling and Validation: Across all components, especially in file operations and data transformations, robust error handling and input validation ensure the tool behaves predictably and provides useful feedback on issues.
 - Integration and Workflow Management: Ensuring all components work together seamlessly, managing file paths, handling intermediate states, and coordinating the translation process from start to finish.
 - Unit Tests for Additional Components: Further testing code for the template creation logic, CLI interface, logging setup, and any other functionalities not covered by the initial unit tests. It’s crucial to have a comprehensive test suite covering various scenarios, edge cases, and error conditions.
 - Documentation (README.md): While we discussed the structure of a README file, the actual content detailing installation instructions, usage examples, configuration file formats, and descriptions of the functionalities and components is essential to guide users and developers.
 - Setup and Packaging Files (setup.py, requirements.txt): Scripts for packaging your project, making it installable via pip, and specifying dependencies that need to be installed.
 - Performance Optimization: Depending on the size of the HDF5 files you're working with, you might need to optimize the data reading, writing, and transformation operations to handle large datasets efficiently.

### Contributing

Contributions to HDF5Translator are welcome! Please read our contributing guidelines for more information.

### License

HDF5Translator is MIT licensed. See the LICENSE file for details.