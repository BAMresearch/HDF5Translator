#!/bin/bash

# This script will run all steps of the BAM pipeline for the MOUSE data
python3 HDF5Translator/tools/excel_translator.py -I example_configurations/UW_Xeuss/UW_Xeuss_translator_configuration.xlsx

python3 -m HDF5Translator -C example_configurations/TUG_SaxsPoint2/TUG_SP2_translator_configuration.yaml -I ./example_configurations/TUG_SaxsPoint2/TUG_SP2_Test.h5 -O ./example_configurations/TUG_SaxsPoint2/TUG_SP2_test.nxs -vv -d

python3 HDF5Translator/tools/edf_to_h5.py -I ./example_configurations/UW_Xeuss/experiment_0_00003.edf
