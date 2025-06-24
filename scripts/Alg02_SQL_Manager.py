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
        TPP_StrippingNumber REAL,
        TPP_Max_Rut_mm REAL,
        TPP_Max_Pass REAL, 
        TPP_RuttingAt10k_mm REAL, 
        TPP_RuttingAt20k_mm REAL, 
        TPP_ModelCoeff_a REAL, 
        TPP_ModelCoeff_b REAL, 
        TPP_ModelCoeff_alpha REAL, 
        TPP_ModelCoeff_beta REAL, 
        TPP_ModelCoeff_gamma REAL, 
        TPP_ModelCoeff_Phi REAL, 
        TPP_Stripping_Rutting_mm REAL, 
        TPP_Stripping_Rutting_Pass REAL, 
        TPP_SIP REAL, 
        TPP_SIP_Yvalue REAL, 
        TPP_SIP_Adj REAL, 
        TPP_SIP_Adj_Yvalue REAL,
        TPP_CreepLine_Slope REAL,
        TPP_CreepLine_Intercept REAL, 
        TPP_StrippingLine_Slope REAL,
        TPP_StrippingLine_Intercept REAL,
        TPP_StrippingLine_Slope_Adj REAL,
        TPP_StrippingLine_Intercept_Adj REAL,
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
        Poly6_Max_Rut_mm REAL,
        Poly6_Max_Pass REAL, 
        Poly6_RuttingAt10k_mm REAL, 
        Poly6_RuttingAt20k_mm REAL, 
        Poly6_ModelCoeff_a0 REAL,
        Poly6_ModelCoeff_a1 REAL,
        Poly6_ModelCoeff_a2 REAL,
        Poly6_ModelCoeff_a3 REAL,
        Poly6_ModelCoeff_a4 REAL,
        Poly6_ModelCoeff_a5 REAL,
        Poly6_ModelCoeff_a6 REAL,
        Poly6_Stripping_Rutting_mm REAL, 
        Poly6_Stripping_Rutting_Pass REAL, 
        Poly6_StrippingNumber REAL,
        Poly6_CreepLine_Slope REAL, 
        Poly6_CreepLine_Intercept REAL, 
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
        TPP_StrippingNumber, TPP_Max_Rut_mm, TPP_Max_Pass, TPP_RuttingAt10k_mm, TPP_RuttingAt20k_mm, 
        TPP_ModelCoeff_a, TPP_ModelCoeff_b, 
        TPP_ModelCoeff_alpha, TPP_ModelCoeff_beta, TPP_ModelCoeff_gamma, TPP_ModelCoeff_Phi, 
        TPP_Stripping_Rutting_mm, TPP_Stripping_Rutting_Pass, 
        TPP_SIP, TPP_SIP_Yvalue, TPP_SIP_Adj, TPP_SIP_Adj_Yvalue, 
        TPP_CreepLine_Slope, TPP_CreepLine_Intercept, TPP_StrippingLine_Slope, TPP_StrippingLine_Intercept, 
        TPP_StrippingLine_Slope_Adj, TPP_StrippingLine_Intercept_Adj, 
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
        Poly6_Max_Rut_mm, Poly6_Max_Pass, Poly6_RuttingAt10k_mm, Poly6_RuttingAt20k_mm, 
        Poly6_ModelCoeff_a0, Poly6_ModelCoeff_a1, Poly6_ModelCoeff_a2, Poly6_ModelCoeff_a3, 
        Poly6_ModelCoeff_a4, Poly6_ModelCoeff_a5, Poly6_ModelCoeff_a6, 
        Poly6_Stripping_Rutting_mm, Poly6_Stripping_Rutting_Pass, Poly6_StrippingNumber, 
        Poly6_CreepLine_Slope, Poly6_CreepLine_Intercept, 
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
        int(data["TPP_StrippingNumber"]), 
        float(data["TPP_Max_Rut_mm"]), int(data["TPP_Max_Pass"]), 
        float(data["TPP_RuttingAt10k_mm"]), float(data["TPP_RuttingAt20k_mm"]), 
        float(data["TPP_ModelCoeff_a"]), float(data["TPP_ModelCoeff_b"]), 
        float(data["TPP_ModelCoeff_alpha"]), float(data["TPP_ModelCoeff_beta"]), 
        float(data["TPP_ModelCoeff_gamma"]), float(data["TPP_ModelCoeff_Phi"]), 
        float(data["TPP_Stripping_Rutting_mm"]), int(data["TPP_Stripping_Rutting_Pass"]), 
        float(data["TPP_SIP"]), float(data["TPP_SIP_Yvalue"]), 
        float(data["TPP_SIP_Adj"]), float(data["TPP_SIP_Adj_Yvalue"]), 
        float(data["TPP_CreepLine_Slope"]), float(data["TPP_CreepLine_Intercept"]), 
        float(data["TPP_StrippingLine_Slope"]), float(data["TPP_StrippingLine_Intercept"]), 
        float(data["TPP_StrippingLine_Slope_Adj"]), float(data["TPP_StrippingLine_Intercept_Adj"]), 
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
        float(data["Poly6_Max_Rut_mm"]), int(data["Poly6_Max_Pass"]), 
        float(data["Poly6_RuttingAt10k_mm"]), float(data["Poly6_RuttingAt20k_mm"]), 
        float(data["Poly6_ModelCoeff_a0"]), 
        float(data["Poly6_ModelCoeff_a1"]), float(data["Poly6_ModelCoeff_a2"]), 
        float(data["Poly6_ModelCoeff_a3"]), float(data["Poly6_ModelCoeff_a4"]), 
        float(data["Poly6_ModelCoeff_a5"]), float(data["Poly6_ModelCoeff_a6"]), 
        float(data["Poly6_Stripping_Rutting_mm"]), float(data["Poly6_Stripping_Rutting_Pass"]), 
        float(data["Poly6_StrippingNumber"]), 
        float(data["Poly6_CreepLine_Slope"]), float(data["Poly6_CreepLine_Intercept"]), 
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


def Get_DB_SummaryData(cursor):
    """
    This function goes through the Database and tries to extract the summary information.

    :param cursor: cursor for executing the SQL commands. 
    :return: a dictionary of the summary information. 
    """
    # First, get the total number of data. 
    cursor.execute("SELECT COUNT(*) FROM HWTT")
    NumRows = cursor.fetchone()[0]
    # Get the total number of data, excluding outliers. 
    cursor.execute("SELECT COUNT(*) FROM HWTT WHERE IsOutlier = ?", (0,))
    NumValidRows = cursor.fetchone()[0]
    # Get the number of unique B-numbers.
    cursor.execute("SELECT COUNT(DISTINCT Bnumber) FROM HWTT WHERE IsOutlier = ?", (0,))
    NumUniqueBnumber = cursor.fetchone()[0]
    # Get the number of unique Lab aging conditions.
    cursor.execute("SELECT COUNT(DISTINCT Lab_Aging) FROM HWTT WHERE IsOutlier = ?", (0,))
    NumUniqueLabAging = cursor.fetchone()[0]
    # Get the number of unique B-number and aging combinations. 
    cursor.execute("SELECT COUNT(*) FROM (SELECT DISTINCT Bnumber, Lab_Aging FROM HWTT)")
    NumUniqueBnumLabAge = cursor.fetchone()[0]
    # Get average number of replicates per each sample. 
    try:
        AvgNumReplicates = NumValidRows / NumUniqueBnumLabAge
    except:
        AvgNumReplicates = -1
    # Return the extracted information. 
    return {
        'NumRows': NumRows,
        'NumValidRows': NumValidRows,
        'NumUniqueBnumber': NumUniqueBnumber,
        'NumUniqueLabAging': NumUniqueLabAging,
        'NumUniqueBnumLabAge': NumUniqueBnumLabAge,
        'AvgNumRep': AvgNumReplicates
    }
# ======================================================================================================================
# ======================================================================================================================
# ======================================================================================================================


def Get_Identifier_Combinations(cursor):
    """
    This function fetch all combinations of the B-number, Lab aging, and repetition numbers from the database. 

    :param cursor: cursor for executing the SQLite3 commands. 
    """
    # First, query for all combinations.
    cursor.execute("SELECT DISTINCT Bnumber, Lane_Num, Lab_Aging, RepNumber FROM HWTT")
    Combinations = cursor.fetchall()
    # Convert the available combinations to the dataframe. 
    Combinations = pd.DataFrame(Combinations, columns=["Bnumber", "Lane_Num", "Lab_Aging", "RepNumber"])
    Combinations = Combinations.sort_values(by='Bnumber', ascending=True)
    Combinations['Bnumber'] = Combinations['Bnumber'].astype(str)
    # Return the combinations DF as result. 
    return Combinations
# ======================================================================================================================
# ======================================================================================================================
# ======================================================================================================================
