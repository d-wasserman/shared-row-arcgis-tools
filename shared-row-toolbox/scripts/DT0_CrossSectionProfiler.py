# Name: DT0_CrossSectionalProfiler.py
# Purpose: This tool creates a cross-sectional profile along a "whisker" line feature, and linearly references references
# found along the whisker to each other. The output is a table with each whisker's ID and the location, identity,
# and distance of the linearly referenced reference along the whisker.
# Author: David J. Wasserman
# Last Modified: 3/27/23
# Python Version:  3.8+
# --------------------------------
# Copyright 2023 David J. Wasserman
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
import os
import arcpy
import sharedrowlib as srl

def cross_sectional_profiler(whisker_fc, reference_fc, snap_distance, out_table):
    """Creates a cross-sectional profile of references intersecting with a line whisker feature class. The function uses a
    Feature To Point operation to convert intersection points to point features and snaps the points to the nearest
    profiling line. The function then calculates the location and distance of each point along the profiling line and
    saves the results to a table.

    :param whisker_fc: Input line feature class representing the profiling line.
    :param reference_fc: Input point, polyline, or polygon feature class representing the references to be profiled.
    :param snap_distance: The distance in linear units to snap centroids of profiling features.
    :param out_table: Output table for storing the cross-sectional profile results.
    :return: out_table
    """
    try:
        # Set overwrite output to True to overwrite existing output files
        arcpy.env.overwriteOutput = True
        
        # Create an output point feature class in the "in_memory" workspace
        out_feature = os.path.join("memory", "output_points")
        arcpy.CreateFeatureclass_management("memory", "output_points", "POINT", spatial_reference=whisker_fc)
        
        
        # Intersect the input feature classes to get the intersection points
        arcpy.AddMessage("Intersecting whiskers with other features...")
        intersect_fc = os.path.join("memory", "intersect_fc")
        arcpy.Intersect_analysis([whisker_fc, reference_fc], intersect_fc, output_type="POINT")
        arcpy.AddMessage("Preparing features for processing...")
        # Convert any multi-point features to centroids
        centroid_fc = os.path.join("memory", "centroid_fc")
        arcpy.FeatureToPoint_management(intersect_fc, centroid_fc, "CENTROID")
        # Snap the centroids to the nearest profiling line
        arcpy.Snap_edit(centroid_fc, [[whisker_fc, "EDGE", snap_distance]])

        arcpy.AddMessage("Adding fields to store distance along the whisker and sort rank...")
        arcpy.AddField_management(centroid_fc, "Whisker_ID", "LONG")
        arcpy.AddField_management(centroid_fc, "Distance", "DOUBLE")
        arcpy.AddField_management(centroid_fc, "SortRank", "LONG")
        arcpy.AddMessage("Creating Near Table for the points along the whiskers...")
        # Create Near Table for the points along the whiskers with location=True parameter
        near_table = os.path.join("memory", "near_table")
        arcpy.GenerateNearTable_analysis(centroid_fc, whisker_fc, near_table, location="LOCATION")

        # Convert Near Table to pandas DataFrame
        arcpy.AddMessage("Converting Near Table to pandas DataFrame...")
        near_table_df = srl.arcgis_table_to_df(near_table)

        # Create a SearchCursor to read whisker features
        arcpy.AddMessage("Calculating distance and sort rank along the whiskers...")
        with arcpy.da.SearchCursor(whisker_fc, ["OID@", "SHAPE@"]) as whisker_cursor:
            for whisker_id, whisker_shape in whisker_cursor:
                # Filter Near Table DataFrame to the current whisker
                filtered_df = near_table_df[near_table_df["NEAR_FID"] == whisker_id].copy()
                # Calculate the distance and sort rank along the whisker for each point
                distances = []
                for index, row in filtered_df.iterrows():
                    in_fid = row["IN_FID"]
                    point_geom = arcpy.PointGeometry(arcpy.Point(row["NEAR_X"], row["NEAR_Y"]), whisker_fc)
                    distance = whisker_shape.measureOnLine(point_geom)
                    distances.append(distance)
                filtered_df["Distance"] = distances
                filtered_df.sort_values(by=["Distance"],inplace=True)
                filtered_df["SortRank"] = range(len(filtered_df))
                for index, row in filtered_df.iterrows():
                    in_fid = row["IN_FID"]
                    distance = row["Distance"]
                    index = row["SortRank"]
                    # Update Distance and SortRank fields in output_points for the current point
                    pt_oid = arcpy.Describe(centroid_fc).OIDFieldName
                    # TODO - replace update cursor with complete write to dataframe including the points. Export to FC using NP functions or ArcGIS API.
                    with arcpy.da.UpdateCursor(centroid_fc, ["OID@", "Whisker_ID","Distance", "SortRank"],where_clause= "{0}={1}".format(pt_oid,in_fid)) as point_cursor:
                        for point_row in point_cursor: # Should be one
                            point_row[1] = whisker_id
                            point_row[2] = distance
                            point_row[3] = index + 1
                            point_cursor.updateRow(point_row)
        
        # Save the output feature class to a table
        arcpy.AddMessage("Sorting output points by whisker ID and sort rank...")
        arcpy.CopyFeatures_management(centroid_fc, out_table)
        arcpy.AddMessage("Processing complete.")
        return out_table
    
    except arcpy.ExecuteError:
        # Return any error messages
        arcpy.AddError(arcpy.GetMessages(2))
    
    except Exception as e:
        # Return any other error messages
        arcpy.AddError(e.args[0])


# This test allows the script to be used from the operating
# system command prompt (stand-alone), in a Python IDE,
# as a geoprocessing script tool, or as a module imported in
# another script
if __name__ == '__main__':
    whisker_fc = arcpy.GetParameterAsText(0)
    reference_fc = arcpy.GetParameterAsText(1)
    snap_distance = arcpy.GetParameterAsText(2)
    out_table = arcpy.GetParameterAsText(3)
    cross_sectional_profiler(whisker_fc, reference_fc, snap_distance, out_table)

