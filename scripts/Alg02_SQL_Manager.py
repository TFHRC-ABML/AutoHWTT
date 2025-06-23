# Title: Managing SQL table for storing the HWTT data. 
#
# Author: Farhad Abdollahi (farhad.abdollahi.ctr@dot.gov)
# Date: 02/21/2025
# ======================================================================================================================

# Importing the required libraries.
import os
import sqlite3
import pandas as pd


def Create_SQLite3_HWTT_DB_Connect(path):
    """
    This function generates a new database and set up the main table in that database. 

    :param path: full path to the database file. 
    :return: connection to the generated database using the sqlite3 library. 
    """
    # Creating the new database file (it is not existed, already checked), and make a connection to the file. 
    conn = sqlite3.connect(path)
    
    # Creating a curser object to execute the sql commands. 
    cursor = conn.cursor()

    # Creating the new table. 
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS HWTT (
        id INTEGER PRIMARY KEY,
        Bnumber INTEGER,
        Lane_Num INTEGER,
        Lab_Aging TEXT,
        RepNumber INTEGER,
        Wheel_Side TEXT, 
        FileName TEXT,
        FileDirectory TEXT,
        Data BLOB,
        Data_shape TEXT,
        Data_dtype TEXT,
        2PP_StrippingNumber REAL,
        2PP_Max_Rut_mm REAL,
        2PP_Max_Pass REAL, 
        2PP_RuttingAt10k_mm REAL, 
        2PP_RuttingAt20k_mm REAL, 
        2PP_ModelCoeff_a REAL, 
        2PP_ModelCoeff_b REAL, 
        2PP_ModelCoeff_alpha REAL, 
        2PP_ModelCoeff_beta REAL, 
        2PP_ModelCoeff_gamma REAL, 
        2PP_ModelCoeff_Phi REAL, 
        2PP_Stripping_Rutting_mm REAL, 
        2PP_Stripping_Rutting_Pass REAL, 
        2PP_SIP REAL, 
        2PP_SIP_Yvalue REAL, 
        2PP_SIP_Adj REAL, 
        2PP_SIP_Adj_Yvalue REAL,
        2PP_CreepLine_Slope REAL,
        2PP_CreepLine_Intercept REAL, 
        2PP_StrippingLine_Slope REAL,
        2PP_StrippingLine_Intercept REAL,
        2PP_StrippingLine_Slope_Adj REAL,
        2PP_StrippingLine_Intercept_Adj REAL,
        Yin_Max_Rut_mm REAL,
        Yin_Max_Pass REAL, 
        Yin_RuttingAt10k_mm REAL, 
        Yin_RuttingAt20k_mm REAL, 
        Yin_ModelCoeff_Step1_ro REAL,
        Yin_ModelCoeff_Step1_LCult REAL,
        Yin_ModelCoeff_Step1_beta REAL,
        Yin_ModelCoeff_Step2_RutMax REAL,
        Yin_ModelCoeff_Step2_alpha REAL,
        Yin_ModelCoeff_Step2_lambda REAL,
        Yin_ModelCoeff_Step3_Eps0 REAL,
        Yin_ModelCoeff_Step3_theta REAL,
        Yin_Stripping_Rutting_mm REAL, 
        Yin_Stripping_Rutting_Pass REAL, 
        Yin_SIP REAL, 
        Yin_SIP_Yvalue REAL, 
        Yin_SIP_Adj REAL, 
        Yin_SIP_Adj_Yvalue REAL,
        Yin_StrippingNumber REAL,
        Yin_CreepLine_Slope REAL,
        Yin_CreepLine_Intercept REAL, 
        Yin_StrippingLine_Slope REAL,
        Yin_StrippingLine_Intercept REAL,
        Yin_StrippingLine_Slope_Adj REAL,
        Yin_StrippingLine_Intercept_Adj REAL,
        Yin_Parameter_LCSN REAL, 
        Yin_Parameter_LCST REAL, 
        Yin_Parameter_DeltaEpsAt10k REAL,
        6deg_Max_Rut_mm REAL,
        6deg_Max_Pass REAL, 
        6deg_RuttingAt10k_mm REAL, 
        6deg_RuttingAt20k_mm REAL, 
        6deg_ModelCoeff_a0 REAL,
        6deg_ModelCoeff_a1 REAL,
        6deg_ModelCoeff_a2 REAL,
        6deg_ModelCoeff_a3 REAL,
        6deg_ModelCoeff_a4 REAL,
        6deg_ModelCoeff_a5 REAL,
        6deg_ModelCoeff_a6 REAL,
        6deg_Stripping_Rutting_mm REAL, 
        6deg_Stripping_Rutting_Pass REAL, 
        6deg_StrippingNumber REAL,
        6deg_CreepLine_Slope REAL, 
        6deg_CreepLine_Intercept REAL, 
        Valid_Min_Pass REAL,
        Valid_Max_Pass REAL,
        Test_Name TEXT, 
        Technician_Name TEXT, 
        Test_Date TEXT, 
        Test_Time TEXT, 
        Test_Condition TEXT, 
        Target_Test_Temperature REAL,
        Avg_Test_Temperature REAL, 
        Std_Test_Temperature REAL,
        Other_Comments TEXT,
        IsOutlier INTEGER 
    )
    """)
    cursor.execute("CREATE INDEX idx_filename ON HWTT (FileName);")       # Creating an index for "FileName"

    # Return the connection. 
    return conn, cursor
# ======================================================================================================================
# ======================================================================================================================
# ======================================================================================================================


def Append_to_Database(conn, cursor, data):
    """
    This function adds data as new row to the database. 
    """
    # Add the data using execute command. 
    # Insert data into the table
    cursor.execute("""
    INSERT INTO HWTT (
	    Bnumber, Lane_Num, Lab_Aging, RepNumber, Wheel_Side, FileName, FileDirectory, Data, Data_shape, Data_dtype, 
        2PP_StrippingNumber, 2PP_Max_Rut_mm, 2PP_Max_Pass, 2PP_RuttingAt10k_mm, 2PP_RuttingAt20k_mm, 
        2PP_ModelCoeff_a, 2PP_ModelCoeff_b, 
        2PP_ModelCoeff_alpha, 2PP_ModelCoeff_beta, 2PP_ModelCoeff_gamma, 2PP_ModelCoeff_Phi, 
        2PP_Stripping_Rutting_mm, 2PP_Stripping_Rutting_Pass, 
        2PP_SIP, 2PP_SIP_Yvalue, 2PP_SIP_Adj, 2PP_SIP_Adj_Yvalue, 
        2PP_CreepLine_Slope, 2PP_CreepLine_Intercept, 2PP_StrippingLine_Slope, 2PP_StrippingLine_Intercept, 
        2PP_StrippingLine_Slope_Adj, 2PP_StrippingLine_Intercept_Adj, 
        Yin_Max_Rut_mm, Yin_Max_Pass, Yin_RuttingAt10k_mm, Yin_RuttingAt20k_mm, 
        Yin_ModelCoeff_Step1_ro, Yin_ModelCoeff_Step1_LCult, Yin_ModelCoeff_Step1_beta, 
        Yin_ModelCoeff_Step2_RutMax, Yin_ModelCoeff_Step2_alpha, Yin_ModelCoeff_Step2_lambda, 
        Yin_ModelCoeff_Step3_Eps0, Yin_ModelCoeff_Step3_theta, 
        Yin_Stripping_Rutting_mm, Yin_Stripping_Rutting_Pass, 
        Yin_SIP, Yin_SIP_Yvalue, Yin_SIP_Adj, Yin_SIP_Adj_Yvalue, 
        Yin_StrippingNumber, 
        Yin_CreepLine_Slope, Yin_CreepLine_Intercept, Yin_StrippingLine_Slope, Yin_StrippingLine_Intercept, 
        Yin_StrippingLine_Slope_Adj, Yin_StrippingLine_Intercept_Adj, 
        Yin_Parameter_LCSN, Yin_Parameter_LCST, Yin_Parameter_DeltaEpsAt10k, 
        6deg_Max_Rut_mm, 6deg_Max_Pass, 6deg_RuttingAt10k_mm, 6deg_RuttingAt20k_mm, 
        6deg_ModelCoeff_a0, 6deg_ModelCoeff_a1, 6deg_ModelCoeff_a2, 6deg_ModelCoeff_a3, 
        6deg_ModelCoeff_a4, 6deg_ModelCoeff_a5, 6deg_ModelCoeff_a6, 
        6deg_Stripping_Rutting_mm, 6deg_Stripping_Rutting_Pass, 6deg_StrippingNumber, 
        6deg_CreepLine_Slope, 6deg_CreepLine_Intercept, 
        Valid_Min_Pass, Valid_Max_Pass, Test_Name, Technician_Name, Test_Date, Test_Time, Test_Condition, 
        Target_Test_Temperature, Avg_Test_Temperature, Std_Test_Temperature, Other_Comments, IsOutlier
    ) VALUES (
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        int(data["Bnumber"]), int(data["Lane_Num"]), data["Lab_Aging"], int(data["RepNumber"]), data["Wheel_Side"], 
        data["FileName"], data["FileDirectory"], 
        data["Data"], data["Data_shape"], data["Data_dtype"], 
        int(data["2PP_StrippingNumber"]), 
        float(data["2PP_Max_Rut_mm"]), int(data["2PP_Max_Pass"]), 
        float(data["2PP_RuttingAt10k_mm"]), float(data["2PP_RuttingAt20k_mm"]), 
        float(data["2PP_ModelCoeff_a"]), float(data["2PP_ModelCoeff_b"]), 
        float(data["2PP_ModelCoeff_alpha"]), float(data["2PP_ModelCoeff_beta"]), 
        float(data["2PP_ModelCoeff_gamma"]), float(data["2PP_ModelCoeff_Phi"]), 
        float(data["2PP_Stripping_Rutting_mm"]), int(data["2PP_Stripping_Rutting_Pass"]), 
        float(data["2PP_SIP"]), float(data["2PP_SIP_Yvalue"]), 
        float(data["2PP_SIP_Adj"]), float(data["2PP_SIP_Adj_Yvalue"]), 
        float(data["2PP_CreepLine_Slope"]), float(data["2PP_CreepLine_Intercept"]), 
        float(data["2PP_StrippingLine_Slope"]), float(data["2PP_StrippingLine_Intercept"]), 
        float(data["2PP_StrippingLine_Slope_Adj"]), float(data["2PP_StrippingLine_Intercept_Adj"]), 
        float(data["Yin_Max_Rut_mm"]), int(data["Yin_Max_Pass"]), 
        float(data["Yin_RuttingAt10k_mm"]), float(data["Yin_RuttingAt20k_mm"]), 
        float(data["Yin_ModelCoeff_Step1_ro"]), float(data["Yin_ModelCoeff_Step1_LCult"]), 
        float(data["Yin_ModelCoeff_Step1_beta"]), 
        float(data["Yin_ModelCoeff_Step2_RutMax"]), float(data["Yin_ModelCoeff_Step2_alpha"]), 
        float(data["Yin_ModelCoeff_Step2_lambda"]), 
        float(data["Yin_ModelCoeff_Step3_Eps0"]), float(data["Yin_ModelCoeff_Step3_theta"]), 
        float(data["Yin_Stripping_Rutting_mm"]), float(data["Yin_Stripping_Rutting_Pass"]), 
        float(data["Yin_SIP"]), float(data["Yin_SIP_Yvalue"]), 
        float(data["Yin_SIP_Adj"]), float(data["Yin_SIP_Adj_Yvalue"]), 
        float(data["Yin_StrippingNumber"]), 
        float(data["Yin_CreepLine_Slope"]), float(data["Yin_CreepLine_Intercept"]), 
        float(data["Yin_StrippingLine_Slope"]), float(data["Yin_StrippingLine_Intercept"]), 
        float(data["Yin_StrippingLine_Slope_Adj"]), float(data["Yin_StrippingLine_Intercept_Adj"]), 
        float(data["Yin_Parameter_LCSN"]), float(data["Yin_Parameter_LCST"]), 
        float(data["Yin_Parameter_DeltaEpsAt10k"]), 
        float(data["6deg_Max_Rut_mm"]), int(data["6deg_Max_Pass"]), 
        float(data["6deg_RuttingAt10k_mm"]), float(data["6deg_RuttingAt20k_mm"]), 
        float(data["6deg_ModelCoeff_a0"]), 
        float(data["6deg_ModelCoeff_a1"]), float(data["6deg_ModelCoeff_a2"]), 
        float(data["6deg_ModelCoeff_a3"]), float(data["6deg_ModelCoeff_a4"]), 
        float(data["6deg_ModelCoeff_a5"]), float(data["6deg_ModelCoeff_a6"]), 
        float(data["6deg_Stripping_Rutting_mm"]), float(data["6deg_Stripping_Rutting_Pass"]), 
        float(data["6deg_StrippingNumber"]), 
        float(data["6deg_CreepLine_Slope"]), float(data["6deg_CreepLine_Intercept"]), 
        float(data["Valid_Min_Pass"]), float(data["Valid_Max_Pass"]), 
        data["Test_Name"], data["Technician_Name"], data["Test_Date"], data["Test_Time"], data["Test_Condition"], 
        float(data["Target_Test_Temperature"]), float(data["Avg_Test_Temperature"]),float(data["Std_Test_Temperature"]), 
        data["Other_Comments"], int(data["IsOutlier"])
    ))

    # Commit the changes. 
    conn.commit()

    # Return Nothing. 
    return 
# ======================================================================================================================
# ======================================================================================================================
# ======================================================================================================================


# def Get_MC_DB_SummaryData(cursor):
#     """
#     This function goes through the Database and tries to extract the summary information.

#     :param cursor: cursor for executing the SQL commands. 
#     :return: a dictionary of the summary information. 
#     """
#     # First, get the total number of data. 
#     cursor.execute("SELECT COUNT(*) FROM MasterCurve")
#     NumRows = cursor.fetchone()[0]
#     # Get the total number of data, excluding outliers. 
#     cursor.execute("SELECT COUNT(*) FROM MasterCurve WHERE IsOutlier = ?", (0,))
#     NumValidRows = cursor.fetchone()[0]
#     # Get the number of unique B-numbers.
#     cursor.execute("SELECT COUNT(DISTINCT Bnumber) FROM MasterCurve WHERE IsOutlier = ?", (0,))
#     NumUniqueBnumber = cursor.fetchone()[0]
#     # Get the number of unique Lab aging conditions.
#     cursor.execute("SELECT COUNT(DISTINCT Lab_Aging) FROM MasterCurve WHERE IsOutlier = ?", (0,))
#     NumUniqueLabAging = cursor.fetchone()[0]
#     # Get the number of unique B-number and aging combinations. 
#     cursor.execute("SELECT COUNT(*) FROM (SELECT DISTINCT Bnumber, Lab_Aging FROM MasterCurve)")
#     NumUniqueBnumLabAge = cursor.fetchone()[0]
#     # Get average number of replicates per each sample. 
#     try:
#         AvgNumReplicates = NumValidRows / NumUniqueBnumLabAge
#     except:
#         AvgNumReplicates = -1
    
#     # Return the extracted information. 
#     return {
#         'NumRows': NumRows,
#         'NumValidRows': NumValidRows,
#         'NumUniqueBnumber': NumUniqueBnumber,
#         'NumUniqueLabAging': NumUniqueLabAging,
#         'NumUniqueBnumLabAge': NumUniqueBnumLabAge,
#         'AvgNumRep': AvgNumReplicates
#     }
# ======================================================================================================================
# ======================================================================================================================
# ======================================================================================================================
