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
        Field_Aging TEXT,
        RepNumber INTEGER,
        Wheel_Side TEXT, 
        FileName TEXT,
        Data BLOB,
        Data_shape TEXT,
        Data_dtype TEXT,
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
        SIP_Pass REAL, 
        CreepLine_Slope REAL,
        CreepLine_Intercept REAL, 
        StrippingLine_Slope REAL,
        StrippingLine_Intercept REAL,
        IsOutlier INTEGER 
    )
    """)
    cursor.execute("CREATE INDEX idx_filename ON HWTT (FileName);")       # Creating an index for "FileName"

    # Return the connection. 
    return conn, cursor
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
