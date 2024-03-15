import argparse
import logging
import numpy as np
import pandas as pd
import sys
import yaml

from pathlib import Path


def excel_translator(excel_file_location, yaml_file_location):

    sheet_names = ["tree_copy", "data_copy", "attributes", "prune_list", "link_list"]
    skip_rows = 2
    read_excel = pd.read_excel(
        excel_file_location, sheet_name=sheet_names, skiprows=skip_rows
    )

    with open(yaml_file_location, "w") as file:
        for key in read_excel.keys():
            if key == "tree_copy":
                tree_copy_df = read_excel["tree_copy"]
                tree_copy_df = tree_copy_df.fillna("NA")
                tree_copy_dict = {}
                tree_copy_array = []

                for index, row in tree_copy_df.iterrows():
                    tree_dict_2 = {}
                    if row.to_dict()["source"] and row.to_dict()["destination"] == "NA":

                        continue

                    for key in row.to_dict().keys():
                        if row.to_dict()[key] == "NA":
                            continue
                        tree_dict_2[key] = row.to_dict()[key]
                    tree_copy_array.append(tree_dict_2)

                tree_copy_dict["tree_copy"] = tree_copy_array
                yaml.dump(tree_copy_dict, file)

            if key == "data_copy":

                data_copy_df = read_excel["data_copy"]
                data_copy_df = data_copy_df.fillna("NA")
                data_copy_dict = {}
                data_copy_array = []

                for index, row in data_copy_df.iterrows():
                    data_dict_2 = {}
                    if row.to_dict()["source"] and row.to_dict()["destination"] == "NA":
                        continue
                    for key in row.to_dict().keys():
                        if row.to_dict()[key] == "NA":
                            continue
                        data_dict_2[key] = row.to_dict()[key]

                    ### attributes in data_copy

                    try:
                        attrib_index = 1
                        attribute_dict = {}
                        while (
                            data_copy_df.iloc[index + attrib_index]["attribute_name"]
                            != "NA"
                        ):

                            attribute_dict[
                                data_copy_df.iloc[index + attrib_index][
                                    "attribute_name"
                                ]
                            ] = data_copy_df.iloc[index + attrib_index][
                                "attribute_value"
                            ]

                            attrib_index += 1

                        if len(attribute_dict.keys()) > 0:
                            data_dict_2["attributes"] = attribute_dict

                    except Exception as e:
                        pass

                    if len(data_dict_2) != 0:
                        data_copy_array.append(data_dict_2)

                data_copy_dict["data_copy"] = data_copy_array
                yaml.dump(data_copy_dict, file)

            if key == "attributes":

                attributes_df = read_excel["attributes"].fillna("NA")
                attribute_dict = {}
                attribute_dict_2 = {}

                for index, row in attributes_df.iterrows():

                    if row["destination"] == "NA":
                        continue

                    try:
                        attrib_index = 1
                        attribute_dict_3 = {}

                        while (
                            attributes_df.iloc[index + attrib_index]["attribute_name"]
                            != "NA"
                        ):

                            attribute_dict_3[
                                attributes_df.iloc[index + attrib_index][
                                    "attribute_name"
                                ]
                            ] = attributes_df.iloc[index + attrib_index][
                                "attribute_value"
                            ]

                            attrib_index += 1

                        if len(attribute_dict_3.keys()) > 0:

                            attribute_dict_2[row["destination"]] = attribute_dict_3

                            # attribute_dict['attributes'] = attribute_dict_2
                            # print(attribute_dict)

                    except Exception as e:
                        pass

                attribute_dict["attributes"] = attribute_dict_2
                yaml.dump(attribute_dict, file)

            if key == "prune_list":

                prune_list_dict = {}
                prune_list_df = read_excel["prune_list"].fillna("NA")
                prune_list_array = [
                    row.to_dict()["paths"]
                    for index, row in prune_list_df.iterrows()
                    if row.to_dict()["paths"] != "NA"
                ]

                prune_list_dict["prune_list"] = prune_list_array
                yaml.dump(prune_list_dict, file)

            if key == "link_list":

                link_list_dict = {}
                link_list_df = read_excel["link_list"].fillna("NA")
                link_list_array = []

                for index, row in link_list_df.iterrows():

                    link_list_dict_2 = {}
                    for key in row.to_dict().keys():
                        if row.to_dict()[key] == "NA":
                            continue

                        link_list_dict_2[key] = row.to_dict()[key]

                    if len(link_list_dict_2.keys()) != 0:
                        link_list_array.append(link_list_dict_2)

                link_list_dict["link_list"] = link_list_array
                yaml.dump(link_list_dict, file)

    file.close()


def main(args=None):

    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description="Translates the excel file \
                                     into the yaml configuration file for \
                                    HDF5Translator"
    )
    parser.add_argument(
        "-O",
        "--destination_file",
        required=False,
        type=Path,
        help="Path to the destination yaml file",
    )
    parser.add_argument(
        "-I",
        "--source_file",
        required=True,
        type=Path,
        help="Path to the source excel file outlining what to \
                            copy from where",
    )

    args = parser.parse_args(args)

    logging.info("excel to yaml configuration translation started")

    excel_translator(args.source_file, args.destination_file)


if __name__ == "__main__":
    """
    excel_file_location: str
                        excel file location including the file name
    yaml_file_location: str
                        yaml output file location including the file name

    """

    main()
