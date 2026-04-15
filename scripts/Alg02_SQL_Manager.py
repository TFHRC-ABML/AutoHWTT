# Title: Managing SQL table for storing the HWTT data. 
#
# Author: Farhad Abdollahi (farhad.abdollahi.ctr@dot.gov)
# Date: 02/21/2025
# ======================================================================================================================

# Importing the required libraries.
import os
import sqlite3
import pandas as pd
from scripts.Alg01_UtilityFunctions import CleanVal


def SQL_Columns():
    """
    This function simply returns the column names and types for main SQL table used as Database. 
    """
    ColumnNames = [
        'Bnumber', 'Lane_Num', 'Lab_Aging', 'RepNumber', 'Wheel_Side', 'Lift_Location', 'FileName', 'FileDirectory', 
        'Data', 'Data_shape', 'Data_dtype',
        'TPP_StrippingNumber', 'TPP_Max_Rut_mm', 'TPP_Max_Pass', 'TPP_RuttingAt10k_mm', 'TPP_RuttingAt20k_mm',
        'TPP_ModelCoeff_a', 'TPP_ModelCoeff_b', 'TPP_ModelCoeff_alpha', 'TPP_ModelCoeff_beta', 'TPP_ModelCoeff_gamma',
        'TPP_ModelCoeff_Phi', 'TPP_Stripping_Rutting_mm', 'TPP_Stripping_Rutting_Pass', 
        'TPP_SIP', 'TPP_SIP_Yvalue', 'TPP_SIP_Adj', 'TPP_SIP_Adj_Yvalue',
        'TPP_CreepLine_Slope', 'TPP_CreepLine_Intercept', 'TPP_StrippingLine_Slope', 'TPP_StrippingLine_Intercept',
        'TPP_StrippingLine_Slope_Adj', 'TPP_StrippingLine_Intercept_Adj',
        'Yin_Max_Rut_mm', 'Yin_Max_Pass', 'Yin_RuttingAt10k_mm', 'Yin_RuttingAt20k_mm',
        'Yin_ModelCoeff_Step1_ro', 'Yin_ModelCoeff_Step1_LCult', 'Yin_ModelCoeff_Step1_beta', 
        'Yin_ModelCoeff_Step2_RutMax', 'Yin_ModelCoeff_Step2_alpha', 'Yin_ModelCoeff_Step2_lambda', 
        'Yin_ModelCoeff_Step3_Eps0', 'Yin_ModelCoeff_Step3_theta', 
        'Yin_Stripping_Rutting_mm', 'Yin_Stripping_Rutting_Pass', 
        'Yin_SIP', 'Yin_SIP_Yvalue', 'Yin_SIP_Adj', 'Yin_SIP_Adj_Yvalue', 'Yin_StrippingNumber', 
        'Yin_CreepLine_Slope', 'Yin_CreepLine_Intercept', 'Yin_StrippingLine_Slope', 'Yin_StrippingLine_Intercept',
        'Yin_StrippingLine_Slope_Adj', 'Yin_StrippingLine_Intercept_Adj',
        'Yin_Parameter_LCSN', 'Yin_Parameter_LCST', 'Yin_Parameter_DeltaEpsAt10k',
        'Poly6_Max_Rut_mm', 'Poly6_Max_Pass', 'Poly6_RuttingAt10k_mm', 'Poly6_RuttingAt20k_mm', 
        'Poly6_ModelCoeff_a0', 'Poly6_ModelCoeff_a1', 'Poly6_ModelCoeff_a2', 'Poly6_ModelCoeff_a3',
        'Poly6_ModelCoeff_a4', 'Poly6_ModelCoeff_a5', 'Poly6_ModelCoeff_a6', 
        'Poly6_Stripping_Rutting_mm', 'Poly6_Stripping_Rutting_Pass', 'Poly6_StrippingNumber', 
        'Poly6_CreepLine_Slope', 'Poly6_CreepLine_Intercept', 
        'Valid_Min_Pass', 'Valid_Max_Pass',
        'Test_Name', 'Technician_Name', 'Test_Date', 'Test_Time', 'Test_Condition', 
        'Target_Test_Temperature', 'Avg_Test_Temperature', 'Std_Test_Temperature', 
        'Other_Comments', 'IsOutlier',
        'Fnk_Max_Rut_mm', 'Fnk_Max_Pass', 'Fnk_RuttingAt10k_mm', 'Fnk_RuttingAt20k_mm', 
        'Fnk_ModelCoeff_A', 'Fnk_ModelCoeff_B', 'Fnk_ModelCoeff_C', 'Fnk_ModelCoeff_D', 
        'Fnk_Stripping_Rutting_mm', 'Fnk_Stripping_Rutting_Pass', 'Fnk_StrippingNumber', 
        'Fnk_SIP', 'Fnk_SIP_Yvalue', 'Fnk_SIP_Adj', 'Fnk_SIP_Adj_Yvalue',
        'Fnk_CreepLine_Slope', 'Fnk_CreepLine_Intercept', 'Fnk_StrippingLine_Slope', 'Fnk_StrippingLine_Intercept',
        'Fnk_StrippingLine_Slope_Adj', 'Fnk_StrippingLine_Intercept_Adj', 
        'Is2PPGuided', 'IsOffset',
    ]
    ColumnTypes = [
        'INTEGER', 'INTEGER', 'TEXT', 'INTEGER', 'TEXT', 'TEXT', 'TEXT', 'TEXT', 'BLOB', 'TEXT', 'TEXT', 'REAL', 
        'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL',
        'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 
        'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 
        'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL',
        'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL',
        'REAL', 'REAL', 'REAL', 'TEXT', 'TEXT', 'TEXT', 'TEXT', 'TEXT', 'REAL', 'REAL', 'REAL', 'TEXT', 'INTEGER', 
        'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 
        'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL', 'REAL',
    ]
    # Return the column names and types.
    return ColumnNames, ColumnTypes
# ======================================================================================================================
# ======================================================================================================================
# ======================================================================================================================


def Check_Columns_within_DB(path):
    """
    This function reads a database and checks the already exsiting columns against the SQL columns and then add the 
    nesseccary columns if needed. 

    Args:
        path (str or pathlib.Path): path to the database file. 

    Returns:
        boolean: A boolean value indicating the success of failure in checking and updating the columns.
    """
    # Get a list of the columns and their types. 
    ReqColNames, ReqColTypes = SQL_Columns()
    # Connect to the database and get the existing columns.
    try:
        # Connect to the database.
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        # Get a list of already existing columns. 
        cursor.execute("PRAGMA table_info(HWTT)")
        TableInfo = cursor.fetchall()
        ExistingColNames = [info[1] for info in TableInfo]
        # Check the existing and update the table with new columns if needed. 
        Counter = 0
        for name, dtype in zip(ReqColNames, ReqColTypes):
            if name not in ExistingColNames:
                Counter += 1
                query = f"ALTER TABLE HWTT ADD COLUMN {name} {dtype}"
                cursor.execute(query)
        # Commit the changes and close the connection.
        conn.commit()
        conn.close()
    except:
        return False
    # print the message to the developer (user won't see this message as they run the GUI in noconsole mode.)
    if Counter > 0:
        print(f" >>> {Counter} new columns have been added to the database.")
    # Rerurn True if the process is successful.
    return True
# ======================================================================================================================
# ======================================================================================================================
# ======================================================================================================================


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

    # Creating the querry for creating the main table.
    ColNames, ColTypes = SQL_Columns()          # Retrieving the column names and types.
    Querry = f'CREATE TABLE IF NOT EXISTS HWTT (\n' + f'      id INTEGER PRIMARY KEY,\n'
    for i in range(len(ColNames)):
        Querry += f'      {ColNames[i]} {ColTypes[i]},\n'
    Querry = Querry[:-2] + '\n)'
    # Creating the new table. 
    cursor.execute(Querry)
    cursor.execute("CREATE INDEX idx_filename ON HWTT (FileName);")       # Creating an index for "FileName"

    # Return the connection. 
    return conn, cursor
# ======================================================================================================================
# ======================================================================================================================
# ======================================================================================================================


def Update_Database(conn, cursor, ID, data):
    """
    This function will update the database with the modified results from the user. 

    Args:
        conn (_type_): _description_
        cursor (_type_): _description_
        ID (_type_): The "id" of the data row in the database. 
        data (_type_): _description_

    Returns:
        _type_: _description_
    """
    # Get the column names. 
    ColumnNames, _ = SQL_Columns()
    # Update the row in the Database. 
    cursor.execute(f'UPDATE HWTT SET {", ".join([f"{col} = ?" for col in ColumnNames])} WHERE id = ?', (
        CleanVal(data["Bnumber"], int), CleanVal(data["Lane_Num"], int), data["Lab_Aging"], 
        CleanVal(data["RepNumber"], int), data["Wheel_Side"], data["Lift_Location"], 
        data["FileName"], data["FileDirectory"], data["Data"], data["Data_shape"], data["Data_dtype"],
        CleanVal(data["TPP_StrippingNumber"], int), 
        CleanVal(data["TPP_Max_Rut_mm"], float), CleanVal(data["TPP_Max_Pass"], int),
        CleanVal(data["TPP_RuttingAt10k_mm"], float), CleanVal(data["TPP_RuttingAt20k_mm"], float),
        CleanVal(data["TPP_ModelCoeff_a"], float), CleanVal(data["TPP_ModelCoeff_b"], float),
        CleanVal(data["TPP_ModelCoeff_alpha"], float), CleanVal(data["TPP_ModelCoeff_beta"], float),
        CleanVal(data["TPP_ModelCoeff_gamma"], float), CleanVal(data["TPP_ModelCoeff_Phi"], float),
        CleanVal(data["TPP_Stripping_Rutting_mm"], float), CleanVal(data["TPP_Stripping_Rutting_Pass"], int),
        CleanVal(data["TPP_SIP"], int), CleanVal(data["TPP_SIP_Yvalue"], float),
        CleanVal(data["TPP_SIP_Adj"], int), CleanVal(data["TPP_SIP_Adj_Yvalue"], float),
        CleanVal(data["TPP_CreepLine_Slope"], float), CleanVal(data["TPP_CreepLine_Intercept"], float),
        CleanVal(data["TPP_StrippingLine_Slope"], float), CleanVal(data["TPP_StrippingLine_Intercept"], float),
        CleanVal(data["TPP_StrippingLine_Slope_Adj"], float), CleanVal(data["TPP_StrippingLine_Intercept_Adj"], float),
        CleanVal(data["Yin_Max_Rut_mm"], float), CleanVal(data["Yin_Max_Pass"], int),
        CleanVal(data["Yin_RuttingAt10k_mm"], float), CleanVal(data["Yin_RuttingAt20k_mm"], float),
        CleanVal(data["Yin_ModelCoeff_Step1_ro"], float), CleanVal(data["Yin_ModelCoeff_Step1_LCult"], float),
        CleanVal(data["Yin_ModelCoeff_Step1_beta"], float), CleanVal(data["Yin_ModelCoeff_Step2_RutMax"], float),
        CleanVal(data["Yin_ModelCoeff_Step2_alpha"], float), CleanVal(data["Yin_ModelCoeff_Step2_lambda"], float),
        CleanVal(data["Yin_ModelCoeff_Step3_Eps0"], float), CleanVal(data["Yin_ModelCoeff_Step3_theta"], float),
        CleanVal(data["Yin_Stripping_Rutting_mm"], float), CleanVal(data["Yin_Stripping_Rutting_Pass"], int),
        CleanVal(data["Yin_SIP"], int), CleanVal(data["Yin_SIP_Yvalue"], float),
        CleanVal(data["Yin_SIP_Adj"], int), CleanVal(data["Yin_SIP_Adj_Yvalue"], float),
        CleanVal(data["Yin_StrippingNumber"], int),
        CleanVal(data["Yin_CreepLine_Slope"], float), CleanVal(data["Yin_CreepLine_Intercept"], float), 
        CleanVal(data["Yin_StrippingLine_Slope"], float), CleanVal(data["Yin_StrippingLine_Intercept"], float), 
        CleanVal(data["Yin_StrippingLine_Slope_Adj"], float), CleanVal(data["Yin_StrippingLine_Intercept_Adj"], float), 
        CleanVal(data["Yin_Parameter_LCSN"], float), CleanVal(data["Yin_Parameter_LCST"], float), 
        CleanVal(data["Yin_Parameter_DeltaEpsAt10k"], float),
        CleanVal(data["Poly6_Max_Rut_mm"], float), CleanVal(data["Poly6_Max_Pass"], int),
        CleanVal(data["Poly6_RuttingAt10k_mm"], float), CleanVal(data["Poly6_RuttingAt20k_mm"], float),
        CleanVal(data["Poly6_ModelCoeff_a0"], float), CleanVal(data["Poly6_ModelCoeff_a1"], float),
        CleanVal(data["Poly6_ModelCoeff_a2"], float), CleanVal(data["Poly6_ModelCoeff_a3"], float),
        CleanVal(data["Poly6_ModelCoeff_a4"], float), CleanVal(data["Poly6_ModelCoeff_a5"], float),
        CleanVal(data["Poly6_ModelCoeff_a6"], float),
        CleanVal(data["Poly6_Stripping_Rutting_mm"], float), CleanVal(data["Poly6_Stripping_Rutting_Pass"], int),
        CleanVal(data["Poly6_StrippingNumber"], int), 
        CleanVal(data["Poly6_CreepLine_Slope"], float), CleanVal(data["Poly6_CreepLine_Intercept"], float),
        CleanVal(data["Valid_Min_Pass"], float), CleanVal(data["Valid_Max_Pass"], float),
        data["Test_Name"], data["Technician_Name"], data["Test_Date"], data["Test_Time"], data["Test_Condition"],
        CleanVal(data["Target_Test_Temperature"], float), CleanVal(data["Avg_Test_Temperature"], float),
        CleanVal(data["Std_Test_Temperature"], float),
        data["Other_Comments"], CleanVal(data["IsOutlier"], int),
        CleanVal(data["Fnk_Max_Rut_mm"], float), CleanVal(data["Fnk_Max_Pass"], int),
        CleanVal(data["Fnk_RuttingAt10k_mm"], float), CleanVal(data["Fnk_RuttingAt20k_mm"], float),
        CleanVal(data["Fnk_ModelCoeff_A"], float), CleanVal(data["Fnk_ModelCoeff_B"], float),
        CleanVal(data["Fnk_ModelCoeff_C"], float), CleanVal(data["Fnk_ModelCoeff_D"], float),
        CleanVal(data["Fnk_Stripping_Rutting_mm"], float), CleanVal(data["Fnk_Stripping_Rutting_Pass"], int),
        CleanVal(data["Fnk_StrippingNumber"], int), 
        CleanVal(data["Fnk_SIP"], int), CleanVal(data["Fnk_SIP_Yvalue"], float), 
        CleanVal(data["Fnk_SIP_Adj"], int), CleanVal(data["Fnk_SIP_Adj_Yvalue"], float),
        CleanVal(data["Fnk_CreepLine_Slope"], float), CleanVal(data["Fnk_CreepLine_Intercept"], float),
        CleanVal(data["Fnk_StrippingLine_Slope"], float), CleanVal(data["Fnk_StrippingLine_Intercept"], float),
        CleanVal(data["Fnk_StrippingLine_Slope_Adj"], float), CleanVal(data["Fnk_StrippingLine_Intercept_Adj"], float),
        CleanVal(data['Is2PPGuided'], int), CleanVal(data['IsOffset'], int),
        ID,
    ))
    # Commit the changes. 
    conn.commit()
    # Return Nothing. 
    return 
# ======================================================================================================================
# ======================================================================================================================
# ======================================================================================================================


def Append_to_Database(conn, cursor, ID, data):
    """
    This function adds data as new row to the database. 

    Args:
        conn (_type_): _description_
        cursor (_type_): _description_
        ID (_type_): This variable is only added for consistency with update database function. 
        data (_type_): _description_
    """
    # Define the column names. 
    Column_Names, _ = SQL_Columns() 
    # Add the data using execute command. 
    Query = f'INSERT INTO HWTT ({", ".join(Column_Names)}) VALUES ({", ".join(["?" for ii in range(len(Column_Names))])})'
    cursor.execute(Query, (
        CleanVal(data["Bnumber"], int), CleanVal(data["Lane_Num"], int), data["Lab_Aging"], 
        CleanVal(data["RepNumber"], int), data["Wheel_Side"], data["Lift_Location"], 
        data["FileName"], data["FileDirectory"], data["Data"], data["Data_shape"], data["Data_dtype"],
        CleanVal(data["TPP_StrippingNumber"], int), 
        CleanVal(data["TPP_Max_Rut_mm"], float), CleanVal(data["TPP_Max_Pass"], int),
        CleanVal(data["TPP_RuttingAt10k_mm"], float), CleanVal(data["TPP_RuttingAt20k_mm"], float),
        CleanVal(data["TPP_ModelCoeff_a"], float), CleanVal(data["TPP_ModelCoeff_b"], float),
        CleanVal(data["TPP_ModelCoeff_alpha"], float), CleanVal(data["TPP_ModelCoeff_beta"], float),
        CleanVal(data["TPP_ModelCoeff_gamma"], float), CleanVal(data["TPP_ModelCoeff_Phi"], float),
        CleanVal(data["TPP_Stripping_Rutting_mm"], float), CleanVal(data["TPP_Stripping_Rutting_Pass"], int),
        CleanVal(data["TPP_SIP"], int), CleanVal(data["TPP_SIP_Yvalue"], float),
        CleanVal(data["TPP_SIP_Adj"], int), CleanVal(data["TPP_SIP_Adj_Yvalue"], float),
        CleanVal(data["TPP_CreepLine_Slope"], float), CleanVal(data["TPP_CreepLine_Intercept"], float),
        CleanVal(data["TPP_StrippingLine_Slope"], float), CleanVal(data["TPP_StrippingLine_Intercept"], float),
        CleanVal(data["TPP_StrippingLine_Slope_Adj"], float), CleanVal(data["TPP_StrippingLine_Intercept_Adj"], float),
        CleanVal(data["Yin_Max_Rut_mm"], float), CleanVal(data["Yin_Max_Pass"], int),
        CleanVal(data["Yin_RuttingAt10k_mm"], float), CleanVal(data["Yin_RuttingAt20k_mm"], float),
        CleanVal(data["Yin_ModelCoeff_Step1_ro"], float), CleanVal(data["Yin_ModelCoeff_Step1_LCult"], float),
        CleanVal(data["Yin_ModelCoeff_Step1_beta"], float), CleanVal(data["Yin_ModelCoeff_Step2_RutMax"], float),
        CleanVal(data["Yin_ModelCoeff_Step2_alpha"], float), CleanVal(data["Yin_ModelCoeff_Step2_lambda"], float),
        CleanVal(data["Yin_ModelCoeff_Step3_Eps0"], float), CleanVal(data["Yin_ModelCoeff_Step3_theta"], float),
        CleanVal(data["Yin_Stripping_Rutting_mm"], float), CleanVal(data["Yin_Stripping_Rutting_Pass"], int),
        CleanVal(data["Yin_SIP"], int), CleanVal(data["Yin_SIP_Yvalue"], float),
        CleanVal(data["Yin_SIP_Adj"], int), CleanVal(data["Yin_SIP_Adj_Yvalue"], float),
        CleanVal(data["Yin_StrippingNumber"], int), 
        CleanVal(data["Yin_CreepLine_Slope"], float), CleanVal(data["Yin_CreepLine_Intercept"], float),
        CleanVal(data["Yin_StrippingLine_Slope"], float), CleanVal(data["Yin_StrippingLine_Intercept"], float),
        CleanVal(data["Yin_StrippingLine_Slope_Adj"], float), CleanVal(data["Yin_StrippingLine_Intercept_Adj"], float),
        CleanVal(data["Yin_Parameter_LCSN"], float), CleanVal(data["Yin_Parameter_LCST"], float),
        CleanVal(data["Yin_Parameter_DeltaEpsAt10k"], float),
        CleanVal(data["Poly6_Max_Rut_mm"], float), CleanVal(data["Poly6_Max_Pass"], int),
        CleanVal(data["Poly6_RuttingAt10k_mm"], float), CleanVal(data["Poly6_RuttingAt20k_mm"], float),
        CleanVal(data["Poly6_ModelCoeff_a0"], float), CleanVal(data["Poly6_ModelCoeff_a1"], float),
        CleanVal(data["Poly6_ModelCoeff_a2"], float), CleanVal(data["Poly6_ModelCoeff_a3"], float),
        CleanVal(data["Poly6_ModelCoeff_a4"], float), CleanVal(data["Poly6_ModelCoeff_a5"], float),
        CleanVal(data["Poly6_ModelCoeff_a6"], float), 
        CleanVal(data["Poly6_Stripping_Rutting_mm"], float), CleanVal(data["Poly6_Stripping_Rutting_Pass"], int),
        CleanVal(data["Poly6_StrippingNumber"], int), 
        CleanVal(data["Poly6_CreepLine_Slope"], float), CleanVal(data["Poly6_CreepLine_Intercept"], float),
        CleanVal(data["Valid_Min_Pass"], float), CleanVal(data["Valid_Max_Pass"], float),
        data["Test_Name"], data["Technician_Name"], data["Test_Date"], data["Test_Time"], data["Test_Condition"], 
        CleanVal(data["Target_Test_Temperature"], float), CleanVal(data["Avg_Test_Temperature"], float),
        CleanVal(data["Std_Test_Temperature"], float),
        data["Other_Comments"], CleanVal(data["IsOutlier"], int), 
        CleanVal(data["Fnk_Max_Rut_mm"], float), CleanVal(data["Fnk_Max_Pass"], int),
        CleanVal(data["Fnk_RuttingAt10k_mm"], float), CleanVal(data["Fnk_RuttingAt20k_mm"], float),
        CleanVal(data["Fnk_ModelCoeff_A"], float), CleanVal(data["Fnk_ModelCoeff_B"], float),
        CleanVal(data["Fnk_ModelCoeff_C"], float), CleanVal(data["Fnk_ModelCoeff_D"], float),
        CleanVal(data["Fnk_Stripping_Rutting_mm"], float), CleanVal(data["Fnk_Stripping_Rutting_Pass"], int),
        CleanVal(data["Fnk_StrippingNumber"], int), 
        CleanVal(data["Fnk_SIP"], int), CleanVal(data["Fnk_SIP_Yvalue"], float),
        CleanVal(data["Fnk_SIP_Adj"], int), CleanVal(data["Fnk_SIP_Adj_Yvalue"], float),
        CleanVal(data["Fnk_CreepLine_Slope"], float), CleanVal(data["Fnk_CreepLine_Intercept"], float),
        CleanVal(data["Fnk_StrippingLine_Slope"], float), CleanVal(data["Fnk_StrippingLine_Intercept"], float),
        CleanVal(data["Fnk_StrippingLine_Slope_Adj"], float), CleanVal(data["Fnk_StrippingLine_Intercept_Adj"], float),
        CleanVal(data['Is2PPGuided'], int), CleanVal(data['IsOffset'], int),
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
