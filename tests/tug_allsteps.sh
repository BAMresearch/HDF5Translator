#!/bin/bash

# This script will run all steps of the BAM pipeline for the MOUSE data
python3 src/tools/excel_translator.py -I example_configurations/TUG_SaxsPoint2/TUG_SP2_translator_configuration.xlsx

python3 -m HDF5Translator -C example_configurations/TUG_SaxsPoint2/TUG_SP2_translator_configuration.yaml -I ./example_configurations/TUG_SaxsPoint2/TUG_SP2_Test.h5 -O ./example_configurations/TUG_SaxsPoint2/TUG_SP2_test.nxs -vv -d
