#!/bin/bash


example_configurations/UW_Xeuss/

python3 src/tools/excel_translator.py -I example_configurations/UW_Xeuss/UW_Xeuss_translator_configuration.xlsx
python3 src/tools/edf_to_h5.py -I ./example_configurations/UW_Xeuss/experiment_0_00003.edf
python3 -m HDF5Translator -C example_configurations/UW_Xeuss/UW_Xeuss_translator_configuration.yaml -I ./example_configurations/UW_Xeuss/experiment_0_00003.h5 -O ./example_configurations/UW_Xeuss/UW_Xeuss_test.nxs -vv -d
