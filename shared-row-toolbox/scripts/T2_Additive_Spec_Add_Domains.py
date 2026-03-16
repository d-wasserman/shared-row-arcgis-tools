# --------------------------------
# Name: 2_Additive_Spec_Add_Domains.py
# Purpose: This tool will add domains to all categorical fields associated with the additive shared-row specification.
# Current Owner: David Wasserman
# Last Modified: 10/1/2019
# Copyright:   David Wasserman
# ArcGIS Version:   ArcGIS Pro/10.4
# Python Version:   3.5/2.7
# --------------------------------
# Copyright 2019 David J. Wasserman
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# --------------------------------

# Import Modules
import arcpy
import pandas as pd
from collections import OrderedDict
import sharedrowlib as srl


def add_additive_specification_coded_domains_to_gdb(in_gdb, in_features, csv, prepended_name="srs_additive",
                                                    field_name_col="FieldName",
                                                    domain_desc_col="DomainDescription", field_type_col="FieldType",
                                                    domain_type_col="DomainType", coded_value_col="CodedValues",
                                                    value_descrip_col="ValueDescriptions"):
    """Add coded value domains for Additive Shared-Row Specification categorical fields.

    Reads domain definitions from a CSV and creates coded value domains in the target
    geodatabase. Optionally assigns the created domains to matching fields in a feature class.

    Parameters
    ----------
    in_gdb : str
        Path to the geodatabase to add domains to.
    in_features : str
        Path to the feature class to assign domains to. Pass an empty string or non-existent
        path to skip domain assignment.
    csv : str
        Path to the CSV file defining domain names, types, coded values, and descriptions.
    prepended_name : str, optional
        Prefix added to each domain name in the form ``{prepended_name}_{field_name}``.
        Default "srs_additive".
    field_name_col : str, optional
        Column in the CSV containing the field names. Default "FieldName".
    domain_desc_col : str, optional
        Column in the CSV containing domain descriptions. Default "DomainDescription".
    field_type_col : str, optional
        Column in the CSV containing field types. Default "FieldType".
    domain_type_col : str, optional
        Column in the CSV containing domain types (CODED or RANGE). Default "DomainType".
    coded_value_col : str, optional
        Column in the CSV with a semicolon-delimited list of coded values. Default "CodedValues".
    value_descrip_col : str, optional
        Column in the CSV with a semicolon-delimited list of value descriptions.
        Default "ValueDescriptions".
    """
    try:
        arcpy.env.overwriteOutput = True
        srl.arc_print("Reading input CSV...")
        df = pd.read_csv(csv)
        for index, row in df.iterrows():
            # Process: Create the coded value domain
            try:
                dom_name = str(prepended_name) + "_" + str(row[field_name_col])
                dom_description = row[domain_desc_col]
                field_type = row[field_type_col]
                domain_type = row[domain_type_col]
                if str(domain_type).upper() != "RANGE" or str(domain_type).upper() != "CODED":
                    domain_type = "CODED"
                srl.arc_print("Creating domain named {0}...".format(str(dom_name)))
                arcpy.CreateDomain_management(in_gdb, dom_name, dom_description, field_type, domain_type)
                # Store all the domain values in a dictionary with the domain code as the "key" and the
                # domain description as the "value" (domDict[code])
            except:
                arcpy.AddWarning("Could not add domain {0} - QAQC.".format(dom_name))

            coded_value_list = str(row[coded_value_col]).split(";")
            coded_value_descrip_list = str(row[value_descrip_col]).split(";")
            if len(coded_value_list) != len(coded_value_descrip_list):
                arcpy.AddWarning("The length of coded values and the length of coded descriptions for domain"
                                 "named {0} do not match. Check output coded values if no error occurs..."
                                 .format(dom_name))
            dom_dictionary = OrderedDict()
            srl.arc_print("Setting up domain dictionary...")
            for value, description in zip(coded_value_list, coded_value_descrip_list):
                dom_dictionary[str(value)] = str(description)
            # Process: Add valid material types to the domain
            # use a for loop to cycle through all the domain codes in the dictionary
            srl.arc_print("Adding coded values for domain...")
            for code in dom_dictionary:
                try:
                    arcpy.AddCodedValueToDomain_management(in_gdb, dom_name, code, str(dom_dictionary[code]).strip())
                except:
                    srl.arc_print("Could not add coded values and descriptions for value {0} "
                                  "and description {1}...".format(code, [dom_dictionary[code]]))
        if arcpy.Exists(in_features):
            srl.arc_print("Assign domains to in features fields...")
            try:
                for field in pd.unique(df[field_name_col]):
                    dom_name = str(prepended_name) + "_" + str(field)
                    arcpy.AssignDomainToField_management(in_features, field, dom_name)
            except:
                arcpy.AddError(
                    "Could not assign all domains to fields in feature class. Check inputs for correct fields...")
        srl.arc_print("Script Complete!")
    except Exception as e:
        srl.arc_print("Tool Script Error!")
        import traceback, sys
        tb = sys.exc_info()[2]
        srl.arc_print("An error occurred on line %i" % tb.tb_lineno)
        arcpy.AddError("The error occurred on line {0}...".format(tb.tb_lineno))


def add_additive_specification_range_domain_to_gdb(in_gdb, in_features, fields, domain_name, field_type="DOUBLE",
                                                   range_min=0, range_max=25):
    """Add a numeric range domain to a geodatabase and assign it to specified fields.

    Parameters
    ----------
    in_gdb : str
        Path to the geodatabase to add the domain to.
    in_features : str
        Path to the feature class to assign the domain to.
    fields : list of str
        Field names to assign the range domain to.
    domain_name : str
        Name of the new range domain.
    field_type : str, optional
        ArcGIS field type for the domain (e.g. "DOUBLE", "LONG"). Default "DOUBLE".
    range_min : int or float, optional
        Minimum value allowed by the range domain. Default 0.
    range_max : int or float, optional
        Maximum value allowed by the range domain. Default 25.
    """
    try:
        domain_description = str(domain_name) + "_Range_Domain"
        try:
            srl.arc_print("Adding range domain for numeric values...")
            arcpy.CreateDomain_management(in_gdb, domain_name, domain_description, field_type, "RANGE")
        except:
            arcpy.AddWarning("Could not create domain. Either it already exists or some other error...")
        srl.arc_print("Set min and max values of domains...")
        arcpy.SetValueForRangeDomain_management(in_gdb, domain_name, range_min, range_max)
        srl.arc_print("Attempting to assign numeric fields ...")
        for field in fields:
            try:
                if len(arcpy.ListFields(in_features, field)) > 0:
                    arcpy.AssignDomainToField_management(in_features, field, domain_name)
            except:
                arcpy.AddWarning("Could not assign domain to field {0}...".format(field))
    except Exception as e:
        srl.arc_print("Tool Script Error!")
        import traceback, sys
        tb = sys.exc_info()[2]
        srl.arc_print("An error occurred on line %i" % tb.tb_lineno)
        arcpy.AddError("The error occurred on line {0}...".format(tb.tb_lineno))


# End do_analysis function

# This test allows the script to be used from the operating
# system command prompt (stand-alone), in a Python IDE,
# as a geoprocessing script tool, or as a module imported in
# another script
if __name__ == '__main__':
    # Define input parameterss
    import os
    input_geodatabase = arcpy.GetParameterAsText(0)
    input_features = arcpy.GetParameterAsText(1)
    specification_data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "specification_data")
    additive_domain_csv = os.path.join(specification_data_dir, r"additive_shared_row_domains.csv")
    add_additive_specification_coded_domains_to_gdb(input_geodatabase, input_features, additive_domain_csv)
    left_through_lanes = ["Left_Through_Lane_{0}".format(i) for i in range(1, 26)]
    right_through_lanes = ["Right_Through_Lane_{0}".format(i) for i in range(1, 26)]
    right_through_lanes.reverse()
    additive_fields_slice_order = ["Left_Sidewalk_Frontage_Zone", "Left_Sidewalk_Through_Zone",
                                   "Left_Sidewalk_Furniture_Zone", "Left_Bike_Lane", "Left_Bike_Buffer",
                                   "Left_Parking_Lane"] + left_through_lanes + ["Left_Transit_Lane", "Center_Lane",
                                                                                "Right_Transit_Lane"] + right_through_lanes + [
                                      "Right_Parking_Lane",
                                      "Right_Bike_Buffer", "Right_Bike_Lane", "Right_Sidewalk_Furniture_Zone",
                                      "Right_Sidewalk_Through_Zone", "Right_Sidewalk_Frontage_Zone", "Off_Street_Width"]
    add_additive_specification_range_domain_to_gdb(input_geodatabase, input_features, additive_fields_slice_order,
                                                   "srs_additive_Width_Ranges")
