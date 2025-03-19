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
        Lab_Aging TEXT,
        RepNumber INTEGER,
        Wheel_Side TEXT, 
        FileName TEXT,
        FileDirectory TEXT,
        Data BLOB,
        Data_shape TEXT,
        Data_dtype TEXT,
        StrippingNumber REAL,
        Max_Rut_mm REAL,
        Max_Pass REAL, 
        RuttingAt10k_mm REAL, 
        RuttingAt20k_mm REAL, 
        ModelCoeff_a REAL, 
        ModelCoeff_b REAL, 
        ModelCoeff_alpha REAL, 
        ModelCoeff_beta REAL, 
        ModelCoeff_gamma REAL, 
        ModelCoeff_Phi REAL, 
        Stripping_Rutting_mm REAL, 
        Stripping_Rutting_Pass REAL, 
        SIP REAL, 
        SIP_Yvalue REAL, 
        CreepLine_Slope REAL,
        CreepLine_Intercept REAL, 
        StrippingLine_Slope REAL,
        StrippingLine_Intercept REAL,
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
    print(data['Max_Pass'])
    print(type(data['Max_Pass']))
    cursor.execute("""
    INSERT INTO HWTT (
        Bnumber, Lab_Aging, RepNumber, Wheel_Side, FileName, FileDirectory, Data, Data_shape, Data_dtype, 
        StrippingNumber, Max_Rut_mm, Max_Pass, RuttingAt10k_mm, RuttingAt20k_mm, 
        ModelCoeff_a, ModelCoeff_b, ModelCoeff_alpha, ModelCoeff_beta, ModelCoeff_gamma, ModelCoeff_Phi, 
        Stripping_Rutting_mm, Stripping_Rutting_Pass, SIP, SIP_Yvalue, CreepLine_Slope, CreepLine_Intercept, 
        StrippingLine_Slope, StrippingLine_Intercept, Valid_Min_Pass, Valid_Max_Pass, Test_Name, Technician_Name, 
        Test_Date, Test_Time, Test_Condition, Target_Test_Temperature, Avg_Test_Temperature, Std_Test_Temperature, 
        Other_Comments, IsOutlier
    ) VALUES (
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
        ?, ?, ?)
    """, (
        data["Bnumber"], data["Lab_Aging"], data["RepNumber"], data["Wheel_Side"], data["FileName"], 
        data["FileDirectory"], data["Data"], data["Data_shape"], data["Data_dtype"], int(data["StrippingNumber"]), 
        data["Max_Rut_mm"], int(data["Max_Pass"]), data["RuttingAt10k_mm"], data["RuttingAt20k_mm"], 
        data["ModelCoeff_a"], data["ModelCoeff_b"], data["ModelCoeff_alpha"], data["ModelCoeff_beta"], 
        data["ModelCoeff_gamma"], data["ModelCoeff_Phi"], data["Stripping_Rutting_mm"], data["Stripping_Rutting_Pass"], 
        data["SIP"], data["SIP_Yvalue"], data["CreepLine_Slope"], data["CreepLine_Intercept"], 
        data["StrippingLine_Slope"], data["StrippingLine_Intercept"], data["Valid_Min_Pass"], data["Valid_Max_Pass"], 
        data["Test_Name"], data["Technician_Name"], data["Test_Date"], data["Test_Time"], data["Test_Condition"], 
        data["Target_Test_Temperature"], data["Avg_Test_Temperature"], data["Std_Test_Temperature"], 
        data["Other_Comments"], data["IsOutlier"]
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
