# HDF5Translator

HDF5Translator is a Python tool designed to translate and transform data between HDF5 files. It supports complex operations like unit conversion, dimensionality adjustments, and subtree copying, making it suitable for managing and manipulating scientific datasets.

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

### Contributing

Contributions to HDF5Translator are welcome! Please read our contributing guidelines for more information.

### License

HDF5Translator is MIT licensed. See the LICENSE file for details.