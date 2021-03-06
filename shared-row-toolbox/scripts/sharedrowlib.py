# --------------------------------
# Name: sharedrowlib.py
# Purpose: This file serves as a function library for the shared-row toolset for ArcGIS. Import as srl.
# Current Owner: David Wasserman
# Last Modified: 8/25/2019
# Copyright:   David Wasserman
# ArcGIS Version:   ArcGIS Pro/10.6
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
import numpy as np
import os, re
import datetime

try:
    import pandas as pd
except:
    arcpy.AddError("This library requires Pandas installed in the ArcGIS Python Install."
                   " Might require installing pre-requisite libraries and software.")


# Function Definitions
def func_report(function=None, reportBool=False):
    """This decorator function is designed to be used as a wrapper with other functions to enable basic try and except
     reporting (if function fails it will report the name of the function that failed and its arguments. If a report
      boolean is true the function will report inputs and outputs of a function.-David Wasserman"""

    def func_report_decorator(function):
        def func_wrapper(*args, **kwargs):
            try:
                func_result = function(*args, **kwargs)
                if reportBool:
                    print("Function:{0}".format(str(function.__name__)))
                    print("     Input(s):{0}".format(str(args)))
                    print("     Ouput(s):{0}".format(str(func_result)))
                return func_result
            except Exception as e:
                print(
                    "{0} - function failed -|- Function arguments were:{1}.".format(str(function.__name__), str(args)))
                print(e.args[0])

        return func_wrapper

    if not function:  # User passed in a bool argument
        def waiting_for_function(function):
            return func_report_decorator(function)

        return waiting_for_function
    else:
        return func_report_decorator(function)


def arc_tool_report(function=None, arcToolMessageBool=False, arcProgressorBool=False):
    """This decorator function is designed to be used as a wrapper with other GIS functions to enable basic try and except
     reporting (if function fails it will report the name of the function that failed and its arguments. If a report
      boolean is true the function will report inputs and outputs of a function.-David Wasserman"""

    def arc_tool_report_decorator(function):
        def func_wrapper(*args, **kwargs):
            try:
                func_result = function(*args, **kwargs)
                if arcToolMessageBool:
                    arcpy.AddMessage("Function:{0}".format(str(function.__name__)))
                    arcpy.AddMessage("     Input(s):{0}".format(str(args)))
                    arcpy.AddMessage("     Ouput(s):{0}".format(str(func_result)))
                if arcProgressorBool:
                    arcpy.SetProgressorLabel("Function:{0}".format(str(function.__name__)))
                    arcpy.SetProgressorLabel("     Input(s):{0}".format(str(args)))
                    arcpy.SetProgressorLabel("     Ouput(s):{0}".format(str(func_result)))
                return func_result
            except Exception as e:
                arcpy.AddMessage(
                    "{0} - function failed -|- Function arguments were:{1}.".format(str(function.__name__),
                                                                                    str(args)))
                print(
                    "{0} - function failed -|- Function arguments were:{1}.".format(str(function.__name__), str(args)))
                print(e.args[0])

        return func_wrapper

    if not function:  # User passed in a bool argument
        def waiting_for_function(function):
            return arc_tool_report_decorator(function)

        return waiting_for_function
    else:
        return arc_tool_report_decorator(function)


@arc_tool_report
def arc_print(string, progressor_Bool=False):
    """ This function is used to simplify using arcpy reporting for tool creation,if progressor bool is true it will
    create a tool label."""
    casted_string = str(string)
    if progressor_Bool:
        arcpy.SetProgressorLabel(casted_string)
        arcpy.AddMessage(casted_string)
        print(casted_string)
    else:
        arcpy.AddMessage(casted_string)
        print(casted_string)


@arc_tool_report
def field_exist(featureclass, fieldname):
    """ArcFunction
     Check if a field in a feature class field exists and return true it does, false if not.- David Wasserman"""
    fieldList = arcpy.ListFields(featureclass, fieldname)
    fieldCount = len(fieldList)
    if (fieldCount >= 1) and fieldname.strip():  # If there is one or more of this field return true
        return True
    else:
        return False


@arc_tool_report
def add_new_field(in_table, field_name, field_type, field_precision="#", field_scale="#", field_length="#",
                  field_alias="#", field_is_nullable="#", field_is_required="#", field_domain="#"):
    """ArcFunction
    Add a new field if it currently does not exist. Add field alone is slower than checking first.- David Wasserman"""
    if field_exist(in_table, field_name):
        print(field_name + " Exists")
        arcpy.AddMessage(field_name + " Exists")
    else:
        print("Adding " + field_name)
        arcpy.AddMessage("Adding " + field_name)
        arcpy.AddField_management(in_table, field_name, field_type, field_precision, field_scale,
                                  field_length,
                                  field_alias,
                                  field_is_nullable, field_is_required, field_domain)


@arc_tool_report
def validate_df_names(dataframe, output_feature_class_workspace):
    """Returns pandas dataframe with all col names renamed to be valid arcgis table names."""
    new_name_list = []
    old_names = dataframe.columns.names
    for name in old_names:
        new_name = arcpy.ValidateFieldName(name, output_feature_class_workspace)
        new_name_list.append(new_name)
    rename_dict = {i: j for i, j in zip(old_names, new_name_list)}
    dataframe.rename(index=str, columns=rename_dict)
    return dataframe


def construct_index_dict(field_names, index_start=0):
    """This function will construct a dictionary used to retrieve indexes for cursors.
    :param - field_names - list of strings (field names) to load as keys into a dictionary
    :param - index_start - an int indicating the beginning index to start from (default 0).
    :return - dictionary in the form of {field:index,...}"""
    dict = {str(field): index for index, field in enumerate(field_names, start=index_start)}
    return dict


def retrieve_row_values(row, field_names, index_dict):
    """This function will take a given list of field names, cursor row, and an index dictionary provide
    a tuple of passed row values.
    :param - row - cursor row
    :param - field_names -list of fields and their order to retrieve
    :param - index_dict - cursors dictionary in the form of {field_name : row_index}
    :return - list of values from cursor"""
    row_values = []
    for field in field_names:
        index = index_dict.get(field, None)
        if index is None:
            print("Field could not be retrieved. Passing None.")
            value = None
        else:
            value = row[index]
        row_values.append(value)
    return row_values


@arc_tool_report
def arcgis_table_to_df(in_fc, input_fields=None, query=""):
    """Function will convert an arcgis table into a pandas dataframe with an object ID index, and the selected
    input fields using an arcpy.da.SearchCursor.
    :param - in_fc - input feature class or table to convert
    :param - input_fields - fields to input to a da search cursor for retrieval
    :param - query - sql query to grab appropriate values
    :returns - pandas.DataFrame"""
    OIDFieldName = arcpy.Describe(in_fc).OIDFieldName
    if input_fields:
        final_fields = [OIDFieldName] + input_fields
    else:
        final_fields = [field.name for field in arcpy.ListFields(in_fc)]
    data = [row for row in arcpy.da.SearchCursor(in_fc,final_fields,where_clause=query)]
    fc_dataframe = pd.DataFrame(data,columns=final_fields)
    fc_dataframe = fc_dataframe.set_index(OIDFieldName,drop=True)
    return fc_dataframe

@arc_tool_report
def arcgis_table_to_dataframe(in_fc, input_fields, query="", skip_nulls=False, null_values=None):
    """Function will convert an arcgis table into a pandas dataframe with an object ID index, and the selected
    input fields. Uses TableToNumPyArray to get initial data."""
    OIDFieldName = arcpy.Describe(in_fc).OIDFieldName
    if input_fields:
        final_fields = [OIDFieldName] + input_fields
    else:
        final_fields = [field.name for field in arcpy.ListFields(in_fc)]
    np_array = arcpy.da.TableToNumPyArray(in_fc, final_fields, query, skip_nulls, null_values)
    object_id_index = np_array[OIDFieldName]
    fc_dataframe = pd.DataFrame(np_array, index=object_id_index, columns=input_fields)
    return fc_dataframe

@arc_tool_report
def add_fields_from_csv(in_fc, csv_path, field_name_col="Name", type_col="Type", shp_field_name="Name_Shp",
                        optional_col="Optional", optional_bool=True, validate=False):
    """Add fields to a feature class using arcpy based on the field names, types, shapefile name, and optional
    column in the CSV.
    :param - in_fc - input feature class to add fields to
    :param - csv_path - path to the csv with fields to add
    :param - field_name_col - name of column with field names
    :param - type_col - name of column with field types
    :param - shp_field_name - name of the field to use if the file is a shapefile
    :param - optional_col - the column identify if a field is optional with a 1 and a 0 for not.
    :param - optional_bool - if true add optional fields
    :param - validate- optional boolean controls whether field names are validated
     :return - list of fields added"""
    workspace = os.path.dirname(in_fc)
    df = pd.read_csv(csv_path)
    new_fields = []
    for index, row in df.iterrows():
        raw_field = str(row[field_name_col])
        if validate:
            fieldname = arcpy.ValidateFieldName(raw_field, workspace)
        else:
            fieldname = raw_field
        if shp_field_name and ".shp" in in_fc:
            fieldname = str(row[shp_field_name])
        if not optional_bool:
            if row[optional_col] == 1:
                print("Not adding optional field.")
                continue
        field_type = row[type_col]
        add_new_field(in_fc, fieldname, field_type)
        new_fields.append(fieldname)
    return new_fields

# Additive Shared Row Specific Functions
def get_additive_lane_count(non_zero_width_fields, side_filter=None):
    """This function will determine the number of lanes on a street given a list of tuples with additive field names
    and values. If a side is specified ("left" or "right"), it will only return the lane count for that side.
    :param - non_zero_width_fields - a list of tuples in the form [(field_name,field_value),...]
    :param - side_filter = either "right" or "left". Filters count based ont hat. """
    lane_count = 0
    through_lane_check = "Through_Lane"
    if side_filter is None:
        pass
    elif side_filter == "right":
        through_lane_check = "Right_" + through_lane_check
    else:
        through_lane_check = "Left_" + through_lane_check
    through_lanes = [slice_tuple for slice_tuple in non_zero_width_fields if
                     through_lane_check in slice_tuple[0] and slice_tuple[1] > 0]
    lane_count = len(through_lanes)
    return lane_count

# End do_analysis function

# This test allows the script to be used from the operating
# system command prompt (stand-alone), in a Python IDE,
# as a geoprocessing script tool, or as a module imported in
# another script
if __name__ == '__main__':
    # Define input parameters
    print("Function library: sharedrowlib.py")
