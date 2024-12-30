#!/bin/bash

# This script will run all steps of the BAM pipeline for the MOUSE data
python3 src/tools/excel_translator.py -I example_configurations/BAM_MOUSE/BAM_MOUSE_dectris_adder_configuration.xlsx
python3 src/tools/excel_translator.py -I example_configurations/BAM_MOUSE/BAM_MOUSE_xenocs_translator_configuration.xlsx
python3 HDF5Translator/tools/excel_translator.py -I example_configurations/BAM_MOUSE/BAM_MOUSE_dectris_adder_configuration.xlsx
python3 HDF5Translator/tools/excel_translator.py -I example_configurations/BAM_MOUSE/BAM_MOUSE_xenocs_translator_configuration.xlsx
python3 -m HDF5Translator -C example_configurations/BAM_MOUSE/BAM_MOUSE_xenocs_translator_configuration.yaml -I ./example_configurations/BAM_MOUSE/20240117_11/im_craw.nxs -O ./example_configurations/BAM_MOUSE/20240117_11/testBAM.nxs -d
# This one cannot be done in the original directory as the NTFS file system does not support some file operations
python3 -m HDF5Translator -C example_configurations/BAM_MOUSE/BAM_MOUSE_dectris_adder_configuration.yaml -I ./example_configurations/BAM_MOUSE/20240117_11/eiger_0045970_master.h5 -T ./example_configurations/BAM_MOUSE/20240117_11/testBAM.nxs -O ./example_configurations/BAM_MOUSE/20240117_11/testBAM_Dadd.nxs -d
# calculate the beam center, flux and transmission from the two auxiliary direct beam and beam-through-sample images
python3 src/tools/post_translation_operation_MOUSE_beamanalysis.py -f example_configurations/BAM_MOUSE/20240117_11/testBAM_Dadd.nxs -v -k roi_size=25 image_type="sample_beam"
python3 src/tools/post_translation_operation_MOUSE_beamanalysis.py -f example_configurations/BAM_MOUSE/20240117_11/testBAM_Dadd.nxs -v -k roi_size=25 image_type="direct_beam"

python3 HDF5Translator/tools/post_translation_operation_MOUSE_beamanalysis.py -f example_configurations/BAM_MOUSE/20240117_11/testBAM_Dadd.nxs -v -k roi_size=25 image_type="sample_beam"
python3 HDF5Translator/tools/post_translation_operation_MOUSE_beamanalysis.py -f example_configurations/BAM_MOUSE/20240117_11/testBAM_Dadd.nxs -v -k roi_size=25 image_type="direct_beam"
