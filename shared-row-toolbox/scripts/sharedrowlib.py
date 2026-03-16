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
    """Decorator for wrapping functions with basic try/except reporting.

    If a function fails, reports the function name and its arguments. If
    reportBool is True, also logs inputs and outputs on success.

    Parameters
    ----------
    function : callable, optional
        The function to wrap. If omitted, returns a decorator waiting for the function.
    reportBool : bool, optional
        If True, print function name, inputs, and outputs on success. Default False.

    Returns
    -------
    callable
        Wrapped function with error reporting.
    """

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
    """Decorator for wrapping ArcGIS functions with try/except reporting via arcpy messages.

    If a function fails, reports the function name and arguments via arcpy.AddMessage.
    If arcToolMessageBool is True, also logs inputs and outputs on success.
    If arcProgressorBool is True, updates the ArcGIS progressor label.

    Parameters
    ----------
    function : callable, optional
        The function to wrap. If omitted, returns a decorator waiting for the function.
    arcToolMessageBool : bool, optional
        If True, send function name, inputs, and outputs to arcpy messages on success. Default False.
    arcProgressorBool : bool, optional
        If True, update the ArcGIS progressor label with function details on success. Default False.

    Returns
    -------
    callable
        Wrapped function with ArcGIS error and progress reporting.
    """

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
    """Print a message to the ArcGIS message window and the console.

    Parameters
    ----------
    string : any
        The message to print. Will be cast to str.
    progressor_Bool : bool, optional
        If True, also update the ArcGIS progressor label. Default False.
    """
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
    """Check whether a field exists in a feature class.

    Parameters
    ----------
    featureclass : str
        Path to the feature class or table.
    fieldname : str
        Name of the field to check.

    Returns
    -------
    bool
        True if the field exists, False otherwise.
    """
    fieldList = arcpy.ListFields(featureclass, fieldname)
    fieldCount = len(fieldList)
    if (fieldCount >= 1) and fieldname.strip():  # If there is one or more of this field return true
        return True
    else:
        return False


@arc_tool_report
def add_new_field(in_table, field_name, field_type, field_precision="#", field_scale="#", field_length="#",
                  field_alias="#", field_is_nullable="#", field_is_required="#", field_domain="#"):
    """Add a new field to a table only if it does not already exist.

    Checking existence before calling AddField is faster than calling AddField unconditionally.

    Parameters
    ----------
    in_table : str
        Path to the input table or feature class.
    field_name : str
        Name of the field to add.
    field_type : str
        ArcGIS field type (e.g. "TEXT", "DOUBLE", "LONG").
    field_precision : int or str, optional
        Field precision. Default "#".
    field_scale : int or str, optional
        Field scale. Default "#".
    field_length : int or str, optional
        Field length. Default "#".
    field_alias : str, optional
        Field alias. Default "#".
    field_is_nullable : str, optional
        Whether the field allows nulls. Default "#".
    field_is_required : str, optional
        Whether the field is required. Default "#".
    field_domain : str, optional
        Domain name to assign to the field. Default "#".
    """
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
    """Rename all DataFrame columns to be valid ArcGIS field names.

    Parameters
    ----------
    dataframe : pandas.DataFrame
        The DataFrame whose column names will be validated.
    output_feature_class_workspace : str
        Workspace path used by arcpy.ValidateFieldName to check name validity.

    Returns
    -------
    pandas.DataFrame
        DataFrame with columns renamed to ArcGIS-compatible names.
    """
    new_name_list = []
    old_names = dataframe.columns.names
    for name in old_names:
        new_name = arcpy.ValidateFieldName(name, output_feature_class_workspace)
        new_name_list.append(new_name)
    rename_dict = {i: j for i, j in zip(old_names, new_name_list)}
    dataframe.rename(index=str, columns=rename_dict)
    return dataframe


def construct_index_dict(field_names, index_start=0):
    """Build a dictionary mapping field names to their cursor row index positions.

    Parameters
    ----------
    field_names : list of str
        Ordered list of field names matching the cursor field order.
    index_start : int, optional
        Starting index value. Default 0.

    Returns
    -------
    dict
        Dictionary in the form ``{field_name: index, ...}``.
    """
    dict = {str(field): index for index, field in enumerate(field_names, start=index_start)}
    return dict


def retrieve_row_values(row, field_names, index_dict):
    """Extract specific field values from a cursor row using an index dictionary.

    Parameters
    ----------
    row : tuple
        A cursor row from an arcpy SearchCursor or UpdateCursor.
    field_names : list of str
        Ordered list of field names whose values should be retrieved.
    index_dict : dict
        Dictionary mapping field names to row index positions, as produced by
        ``construct_index_dict``.

    Returns
    -------
    list
        Values from the cursor row in the order specified by field_names.
        Fields not found in index_dict return None.
    """
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
    """Convert an ArcGIS table or feature class to a pandas DataFrame using a SearchCursor.

    Parameters
    ----------
    in_fc : str
        Path to the input feature class or table.
    input_fields : list of str, optional
        Fields to retrieve. If None, all fields are included.
    query : str, optional
        SQL where clause to filter rows. Default "".

    Returns
    -------
    pandas.DataFrame
        DataFrame indexed by the OID field with the requested columns.
    """
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
    """Convert an ArcGIS table or feature class to a pandas DataFrame using TableToNumPyArray.

    Parameters
    ----------
    in_fc : str
        Path to the input feature class or table.
    input_fields : list of str
        Fields to retrieve.
    query : str, optional
        SQL where clause to filter rows. Default "".
    skip_nulls : bool, optional
        If True, skip rows with null values. Default False.
    null_values : scalar or dict, optional
        Value(s) used to replace nulls. Default None.

    Returns
    -------
    pandas.DataFrame
        DataFrame indexed by the OID field with the requested columns.
    """
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
    """Add fields to a feature class based on a CSV field specification.

    Parameters
    ----------
    in_fc : str
        Path to the input feature class to add fields to.
    csv_path : str
        Path to the CSV file defining fields to add.
    field_name_col : str, optional
        Column in the CSV containing field names. Default "Name".
    type_col : str, optional
        Column in the CSV containing field types. Default "Type".
    shp_field_name : str, optional
        Column in the CSV with shapefile-compatible field names, used when in_fc is a .shp file.
        Default "Name_Shp".
    optional_col : str, optional
        Column in the CSV marking optional fields with 1 and required fields with 0.
        Default "Optional".
    optional_bool : bool, optional
        If True, add optional fields in addition to required ones. Default True.
    validate : bool, optional
        If True, validate field names against the workspace before adding. Default False.

    Returns
    -------
    list of str
        Names of the fields that were added.
    """
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
    """Count the number of through lanes from a list of additive specification field tuples.

    Parameters
    ----------
    non_zero_width_fields : list of tuple
        List of ``(field_name, field_value)`` pairs for fields with non-zero widths.
    side_filter : str, optional
        Restrict the count to one side. Pass "left" or "right". If None, counts all
        through lanes on both sides. Default None.

    Returns
    -------
    int
        Number of through lanes matching the filter criteria.
    """
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
