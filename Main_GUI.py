# Title: Main code for the HWTT Analysis Graphical User Interface (GUI)
#
# Author: Farhad Abdollahi (farhad.abdollahi.ctr@dot.gov)
# Date: 02/21/2025
# ======================================================================================================================

# Importing the required libraries.
import os
import sys
import sqlite3
import numpy as np
from PyQt5.QtWidgets import QApplication, QPushButton, QVBoxLayout, QHBoxLayout, QDialog, QTextEdit
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt
from scripts.Alg01_UtilityFunctions import ScrollableMessageBox
from scripts.Alg02_SQL_Manager import Create_SQLite3_HWTT_DB_Connect
from scripts.GUI01_HWTT_Welcome import HWTT_WelcomePage
from scripts.GUI02_MainPage import Main_Window
# from scripts.Sub03_MainPage import Main_Window


def main():
    # Creating an instance of the PyQt Application. 
    app = QApplication(sys.argv)
    # ------------------------------------------------------------------------------------------------------------------
    # Show a disclaimer popup. 
    Disclaimer()
    # ------------------------------------------------------------------------------------------------------------------
    # Step 01: Initiating the welcome page for the user. 
    Welcome = HWTT_WelcomePage()    # Creating an object from the welcome page. 
    Welcome.show()                  # show the welcome page. 
    app.exec_()                     # execute the program.
    # Check the results: if the path and filename to create or load the database is not provided, close the app. 
    DB_FileName = Welcome.DB_FileName               # Database file name.
    DB_Folder   = Welcome.DB_Folder                 # Database directory.
    if (not Welcome.DB_FileName) or (not Welcome.DB_Folder):
        app.quit()
        return
    # ------------------------------------------------------------------------------------------------------------------
    # Step 02: Check if the database is already existed (load the database) or create a new database.
    if os.path.isfile(os.path.join(DB_Folder, DB_FileName + '.db')):
        # Load the database. 
        conn = sqlite3.connect(os.path.join(DB_Folder, DB_FileName + '.db'))
        cursor = conn.cursor()
    else:
        # Create the database and connect the SQL courser. 
        conn, cursor = Create_SQLite3_HWTT_DB_Connect(os.path.join(DB_Folder, DB_FileName + '.db'))
    # ------------------------------------------------------------------------------------------------------------------
    # Step 03: Create a new window for the loaded/created database with more options (Actual program).
    Main = Main_Window(conn, cursor, DB_FileName, DB_Folder)
    Main.show()
    app.exec()
    # ------------------------------------------------------------------------------------------------------------------
    # Quit the application (and connection to SQL) and return Nothing. 
    conn.close()
    app.quit()
    return 
# ======================================================================================================================
# ======================================================================================================================
# ======================================================================================================================


def Disclaimer():
    """
    This function only provide the disclaimer before running the software. 
    """
    TEXT = """
HWTT Analaysis Tool DISCLAIMER
    The "HWTT Analaysis Tool" analysis product is disseminated by the Federal Highway Administration (FHWA), U.S. \
Department of Transportation (USDOT) in the interest of information exchange. The United States Government and \
analysis product developers assume no liability for its content or use. 

    This analysis product does not constitute a standard, specification, or regulation. The contents of the analysis \
product do not have the force and effect of law and are not meant to bind the public in any way, and the analysis \
product is intended only to provide information to the public regarding existing requirements under the law or \
agency policies.
    
    The United States Government does not endorse products or manufacturers. Trade and manufacturers' names may appear \
in this analysis product only because they are considered essential to the objective of the analysis product.

NO WARRANTY AND LIMITATIONS OF REMEDIES
    This analysis product is provided "as-is," without warranty of any kind, either expressed or implied (but not \
limited to the implied warranties of merchantability and fitness for a particular purpose). The entire risk arising \
out of the installation, use, evaluation, or performance of this analysis product remains with the user. The FHWA \
and analysis product developers do not warrant that the functions contained in the analysis product will meet the \
end-user's requirements or that the operation of the analysis product will be uninterrupted and free of errors. \
Under no circumstances will FHWA or analysis product developers be liable to the user or any third party for any \
direct, indirect, incidental, consequential, special, or exemplary damages or lost profit resulting from any use \
or misuse of this analysis product. 

NOTICE
    This analysis product may be used freely by the public so long as you do not 1) claim it is your own (e.g. by \
claiming copyright for the analysis product), 2) use it in a manner that implies an endorsement or affiliation \
with FHWA or USDOT, or 3) modify it in content and then present it as official government material.

Contact:
Dave Mensching, Ph.D., P.E.
Team Leader, Infrastructure Materials
Federal Highway Administration
Office of Infrastructure Research and Development
6300 Georgetown Pike, HRDI-20
McLean, VA 22101
david.mensching@dot.gov
        """
    msg_box = ScrollableMessageBox(TEXT)
    if not msg_box.exec_() == QDialog.Accepted:
        # Closing the whole program. 
        sys.exit()
# ======================================================================================================================
# ======================================================================================================================
# ======================================================================================================================


if __name__ == '__main__':
    main()
