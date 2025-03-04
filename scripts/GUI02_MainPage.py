# Title: This script include classes for the main page of the HWTT Analysis Tool.
#
# Author: Farhad Abdollahi (farhad.abdollahi.ctr@dot.gov)
# Date: 02/21/2025
# ======================================================================================================================

# Importing the required libraries.
import os
import sys
import shutil
import sqlite3
import fnmatch
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QAction, QDoubleSpinBox, QLabel, \
    QPushButton, QWidget, QGridLayout, QFormLayout, QLineEdit, QFileDialog, QMessageBox, QGroupBox, QProgressBar, \
    QPlainTextEdit, QStackedWidget, QCheckBox, QComboBox, QTabWidget, QScrollArea, QTableWidget, QTableWidgetItem, \
    QSpinBox, QFrame
from PyQt5.QtGui import QPixmap, QFont, QRegExpValidator, QDoubleValidator, QIntValidator
from PyQt5.QtCore import Qt, QRegExp
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from scripts.Alg01_UtilityFunctions import Read_HWTT_Text_File, Read_HWTT_Excel_File, Array_to_Binary, Binary_to_Array
from scripts.Alg02_SQL_Manager import Append_to_Database
from scripts.Alg03_HWTT_Analysis_Functions import HWTT_Analysis, ModelPower
# from Alg02_SQL_Manager import Get_MC_DB_SummaryData
# from Alg03_FreeShifting import FreeShift_GordonShaw1994
# from Alg04_MasterCurve_Construction import Fit_ShiftModel_WLF, ShiftModel_WLF, Fit_MC_ChristensenAnderson, \
#     Fit_MC_ChristensenAndersonMarasteanu


class SharedData:
    """
    This is just a class to transfer the asphalt ID number between different stacks. 
    """
    def __init__(self):
        self.data = -1
# ======================================================================================================================
# ======================================================================================================================
# ======================================================================================================================


class Main_Window(QMainWindow):
    """
    This class generates the GUI for the main window of the HWTT Analysis Tool. This window is planned to have two 
    stacks: 
        (i) for entering new data and do the analysis.
        (ii) for reviewing the data in the database and make changes. 
    """
    def __init__(self, conn, cursor, DB_Name, DB_Folder):
        super().__init__()
        # Creating the main window. 
        self.setWindowTitle(f"HWTT Analysis Tool (DEMO version) | Database name: {DB_Name}")
        self.setFixedSize(1250, 900)
        self.setStyleSheet("background-color: #f0f0f0;")
        # Create shared data object
        self.shared_data = SharedData()
        # Create QStackedWidget.
        self.stack = QStackedWidget()
        # Create pages
        self.main_page = MainPage(conn, cursor, DB_Name, DB_Folder, self.stack)
            # self.db_review_page = DB_ReviewPage(conn, cursor, DB_Name, DB_Folder, self.stack, self.shared_data)
            # self.FTIR_revise_page = Revise_FTIR_AnalysisPage(conn, cursor, DB_Name, DB_Folder, self.stack, self.shared_data)
        # Add pages to the stack
        self.stack.addWidget(self.main_page)            # This page has stack index 0
            # self.stack.addWidget(self.db_review_page)       # This page has stack index 1
            # self.stack.addWidget(self.FTIR_revise_page)     # This page has stack index 2. 
        # Set the stack as the central widget
        self.setCentralWidget(self.stack)
# ======================================================================================================================
# ======================================================================================================================
# ======================================================================================================================


class MainPage(QMainWindow):
    """
    This class generates the GUI for the main page of the HWTT Analysis Tool, where the user can load a database and 
    add more data, modify the current data, etc.
    """
    def __init__(self, conn, cursor, DB_Name, DB_Folder, stack):
        # Initiate the required parameters. 
        super().__init__()
        self.conn = conn            # connection to the SQL database.
        self.cursor = cursor        # cursor for running the SQL commands. 
        self.DB_Name = DB_Name
        self.DB_Folder = DB_Folder
        self.CurrentFileList = []   # A list of the input files that need to be analyzed!
        self.CurrentFileIndex = 0   # Index of the file to be analyzed. 
        self.stack = stack
        self.ShowFileExistedError = True
        self.ValidPasses  = [0, 20000]
        self.CurIsotherms = None    # To store the current binder isotherms (raw data)
        self.AnalysisProgress = 0   # Progress of the analysis, where 0: plotting the isothersms, 1: Shifting applied, 
                                    #   2: Master curve constructed, 3: Relaxation MC constructed!, 4: LAS analzed.
        self.Results = {}           # To store the results shifting, MC fitting, etc. 
        self.PlotProps = {
            'Colors'   : np.array(plt.cm.tab10.colors)[np.random.permutation(np.arange(10)), :],
            'Markers'  : ['o', '^', 's', '*', 'D', 'x'], 
            'LineStyle': ['-', '-.', '--', ':']}
        self.PlotProps['Markers']   = [self.PlotProps['Markers'][i] for i in 
                                       np.random.permutation(np.arange(len(self.PlotProps['Markers'])))]
        self.PlotProps['LineStyle'] = [self.PlotProps['LineStyle'][i] for i in 
                                       np.random.permutation(np.arange(len(self.PlotProps['LineStyle'])))]
        self.initUI()
    # ------------------------------------------------------------------------------------------------------------------
    def initUI(self):
        # Main widget and layout
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)                   # Make a horizontal layout.
        self.setCentralWidget(main_widget)
        # self.setStyleSheet("background-color: #f0f0f0;")
        # Generate the left and right layouts, where left one include summay info and plots, and right one include the 
        #   buttons, adjustments, and controls. 
        TopLayout = QHBoxLayout()
        # --------------------------------------------------------------------------------------------------------------
        # ---------------- Top Part of Layout (Input and graphics on top, Graph on the bottom) -------------------------
        # --------------------------------------------------------------------------------------------------------------
        # Section 01 (Top Layout, first group): Input data section.
        SectT01 = QGroupBox("Input Data Section")
        SectT01.setStyleSheet("QGroupBox { font-weight: bold; }")
        SectT01_Layout = QVBoxLayout()
        # Button for adding more data to database. 
        self.Button_AddFiles = QPushButton("Import HWTT Raw Data\n(Text Files)")
        self.Button_AddFiles.setFont(QFont("Arial", 10, QFont.Bold))
        self.Button_AddFiles.clicked.connect(self.Function_Button_Add_Text_Files)
        self.Button_AddFiles.setFixedSize(200, 50)
        self.Button_AddFiles.setStyleSheet(
        """
        QPushButton:hover {background-color: lightgray;}
        QPushButton:pressed {background-color: gray;}
        """)
        # Button for adding data copied. 
        self.Button_AddCopied = QPushButton("Import HWTT Raw Data\n(Excel Files)")
        self.Button_AddCopied.setFont(QFont("Arial", 10, QFont.Bold))
        self.Button_AddCopied.clicked.connect(self.Function_Button_Add_Excel_Files)
        self.Button_AddCopied.setFixedSize(200, 50)
        self.Button_AddCopied.setStyleSheet(
        """
        QPushButton:hover {background-color: lightgray;}
        QPushButton:pressed {background-color: gray;}
        """)
        # Button for Providing the template.
        self.Button_Template = QPushButton("Template Source")
        self.Button_Template.setFont(QFont("Arial", 10, QFont.Bold))
        self.Button_Template.clicked.connect(self.Function_Button_Template)
        self.Button_Template.setFixedSize(130, 40)
        self.Button_Template.setStyleSheet(
        """
        QPushButton:hover {background-color: lightgray;}
        QPushButton:pressed {background-color: gray;}
        """)
        # Button for Finalizing the import.
        self.Button_RunAnalysis = QPushButton("Run Analysis")
        self.Button_RunAnalysis.setFont(QFont("Arial", 12, QFont.Bold))
        self.Button_RunAnalysis.clicked.connect(self.Function_Button_RunAnalysis)
        self.Button_RunAnalysis.setFixedSize(200, 50)
        self.Button_RunAnalysis.setEnabled(False)
        self.Button_RunAnalysis.setStyleSheet(
        """
        QPushButton:hover {background-color: lightgray;}
        QPushButton:pressed {background-color: gray;}
        QPushButton:checked {background-color: lime;}
        """)
        # Create a progress bar. 
        self.ProgressBar = QProgressBar(self)
        self.ProgressBar.setMinimum(0)
        self.ProgressBar.setMaximum(100)
        self.ProgressBar.setValue(0)
        self.ProgressBar.setFixedSize(220, 20)
        self.ProgressBar.setEnabled(False)
        # Create a separator. 
        SectT01_Separator = QFrame()
        SectT01_Separator.setFrameShape(QFrame.HLine)
        SectT01_Separator.setFrameShadow(QFrame.Sunken)
        # Create a label to show the file updater. 
        self.Label_InputFileUpdate = QLabel('Waiting for input files...')
        # process the layouts. 
        SectT01_Layout.addWidget(self.Button_AddFiles,  alignment=Qt.AlignHCenter | Qt.AlignTop)
        SectT01_Layout.addWidget(self.Button_AddCopied, alignment=Qt.AlignHCenter | Qt.AlignTop)
        SectT01_Layout.addWidget(self.Button_Template,  alignment=Qt.AlignHCenter | Qt.AlignTop)
        SectT01_Layout.addWidget(self.Label_InputFileUpdate)
        SectT01_Layout.addWidget(self.ProgressBar, alignment=Qt.AlignCenter)
        SectT01_Layout.addWidget(SectT01_Separator)
        SectT01_Layout.addWidget(self.Button_RunAnalysis, alignment=Qt.AlignHCenter | Qt.AlignTop)
        SectT01.setLayout(SectT01_Layout)
        TopLayout.addWidget(SectT01, 25)
        # --------------------------------------------------------------------------------------------------------------
        # Section 02 (Top Layout, second group): Visualization & Settings
        SectT02 = QGroupBox("Visualization && Setting")
        SectT02.setStyleSheet("QGroupBox { font-weight: bold; }")
        SectT02_Layout = QVBoxLayout()
        SectT02_FormLayout = QFormLayout()
        # First, ask for the spacing of datapoints. 
        ST02_Label01 = QLabel(f'{"Raw datapoint spacing:".ljust(70)}')
        self.SpinBox_RawDataSpacing = QSpinBox()
        self.SpinBox_RawDataSpacing.setRange(2, 200)
        self.SpinBox_RawDataSpacing.setValue(40)
        SectT02_FormLayout.addRow(ST02_Label01, self.SpinBox_RawDataSpacing)
        # Add spingboxes for the valid pass values.
        ST02_Label02 = QLabel(f'{"Boundary for minimum pass number:".ljust(70)}')
        self.SpinBox_MinPassNumber = QSpinBox()
        self.SpinBox_MinPassNumber.setRange(0, 1000)
        self.SpinBox_MinPassNumber.setValue(0)
        self.SpinBox_MinPassNumber.setEnabled(False)
        SectT02_FormLayout.addRow(ST02_Label02, self.SpinBox_MinPassNumber)
        ST02_Label03 = QLabel(f'{"Boundary for maximum pass number:".ljust(70)}')
        self.SpinBox_MaxPassNumber = QSpinBox()
        self.SpinBox_MaxPassNumber.setRange(15000, 20000)
        self.SpinBox_MaxPassNumber.setValue(20000)
        self.SpinBox_MaxPassNumber.setEnabled(False)
        SectT02_FormLayout.addRow(ST02_Label03, self.SpinBox_MaxPassNumber)
        # ------------- Setting part ------------------------
        # Create a separator. 
        SectT02_Separator = QFrame()
        SectT02_Separator.setFrameShape(QFrame.HLine)
        SectT02_Separator.setFrameShadow(QFrame.Sunken)
        SectT02_FormLayout.addRow(SectT02_Separator)
        # Add a checkbox for offsetting the first data to zero. 
        self.CheckBox_OffsetFirstRawData = QCheckBox(f'Offset the rut depth of first raw datapoint to zero')
        self.CheckBox_OffsetFirstRawData.setChecked(True)
        self.CheckBox_OffsetFirstRawData.setEnabled(False)
        SectT02_FormLayout.addRow(self.CheckBox_OffsetFirstRawData)

        SectT02_Layout.addLayout(SectT02_FormLayout)
        # Button for Replotting the raw data.
        self.Button_ResetRePlot = QPushButton("Reset/re-Plot raw data")
        self.Button_ResetRePlot.setFont(QFont("Arial", 12, QFont.Bold))
        self.Button_ResetRePlot.clicked.connect(self.Function_Button_ResetRePlot)
        self.Button_ResetRePlot.setFixedSize(200, 40)
        self.Button_ResetRePlot.setEnabled(False)
        self.Button_ResetRePlot.setStyleSheet(
        """
        QPushButton:hover {background-color: lightgray;}
        QPushButton:pressed {background-color: gray;}
        QPushButton:checked {background-color: lime;}
        """)
        SectT02_Layout.addWidget(self.Button_ResetRePlot, alignment=Qt.AlignHCenter)
        # Create another separator. 
        SectT02_Separator2 = QFrame()
        SectT02_Separator2.setFrameShape(QFrame.HLine)
        SectT02_Separator2.setFrameShadow(QFrame.Sunken)
        SectT02_Layout.addWidget(SectT02_Separator2)
        # Button for specify the result as outlier.
        self.Button_FailResult = QPushButton("This result is\nOutlier")
        self.Button_FailResult.setFont(QFont("Arial", 13, QFont.Bold))
        # self.Button_FailResult.clicked.connect(self.Function_Button_FailResult)
        self.Button_FailResult.setFixedSize(180, 50)
        self.Button_FailResult.setEnabled(False)
        self.Button_FailResult.setStyleSheet(
        """
        QPushButton:hover {background-color: lightgray;}
        QPushButton:pressed {background-color: gray;}
        QPushButton:checked {background-color: lime;}
        """)
        # Button for specify the result as Accepted.
        self.Button_AcceptResult = QPushButton("This result is\nAccepted")
        self.Button_AcceptResult.setFont(QFont("Arial", 13, QFont.Bold))
        self.Button_AcceptResult.clicked.connect(self.Function_Button_PassResult)
        self.Button_AcceptResult.setFixedSize(180, 50)
        self.Button_AcceptResult.setEnabled(False)
        self.Button_AcceptResult.setStyleSheet(
        """
        QPushButton:hover {background-color: lightgray;}
        QPushButton:pressed {background-color: gray;}
        QPushButton:checked {background-color: lime;}
        """)
        SectT02_LayoutH1 = QHBoxLayout()
        SectT02_LayoutH1.addWidget(self.Button_AcceptResult)
        SectT02_LayoutH1.addWidget(self.Button_FailResult)
        SectT02_Layout.addLayout(SectT02_LayoutH1)

        SectT02.setLayout(SectT02_Layout)
        TopLayout.addWidget(SectT02, 35)
        # --------------------------------------------------------------------------------------------------------------
        # Section 03 (Top Layout, Third group): Results!
        SectT03 = QGroupBox("Results")
        SectT03.setStyleSheet("QGroupBox { font-weight: bold; }")
        SectT03_Layout = QVBoxLayout()
        # --------------------------------------------
        # Creating a tab widget. 
        self.SectT03_TabWidget = QTabWidget()
        # Tab 1: Information about the imported result. 
        Tab1 = QWidget()
        Tab1_Layout = QVBoxLayout(Tab1)
        # Create a Scroll Area
        ScrollAreaT03T1 = QScrollArea()
        ScrollAreaT03T1.setWidgetResizable(True)
        ScrollContent = QWidget()
        ScrollAreaT03T1.setWidget(ScrollContent)
        ScrollAreaT03T1_Layout = QVBoxLayout(ScrollContent)
        ScrollAreaT03T1_Layout.addWidget(QLabel('General Information:'))
        SectT03T1_FormLayout = QFormLayout()
        ST03T1_Label01 = QLabel(f'{"Test name*:".ljust(50)}')
        ST03T1_Label02 = QLabel(f'{"Test date (optional):".ljust(50)}')
        ST03T1_Label03 = QLabel(f'{"Test time (optional):".ljust(50)}')
        ST03T1_Label04 = QLabel(f'{"Testing condition*:".ljust(50)}')
        ST03T1_Label05 = QLabel(f'{"Wheel path side*:".ljust(50)}')
        ST03T1_Label06 = QLabel(f'{"Target test temperature (°C):".ljust(50)}')
        ST03T1_Label07 = QLabel(f'{"Avg. recorded test temperature (°C):".ljust(50)}')
        ST03T1_Label08 = QLabel(f'{"Std. recorded test temperature (°C):".ljust(50)}')
        ST03T1_Label09 = QLabel(f'{"B-Number (ABML specific)*:".ljust(50)}')
        ST03T1_Label10 = QLabel(f'{"Lane number (optional):".ljust(50)}')
        ST03T1_Label11 = QLabel(f'{"Lift location (optional):".ljust(50)}')
        ST03T1_Label12 = QLabel(f'{"Technician name:".ljust(50)}')
        ST03T1_Label13 = QLabel(f'{"Other comments (optional):".ljust(50)}')
        ST03T1_Label14 = QLabel(f'{"State of laboratory aging*:".ljust(50)}')
        self.ST03T1_LineEdit_TestName = QLineEdit()            # For test name. 
        self.ST03T1_LineEdit_TestName.setPlaceholderText("Enter test name here ...")
        self.ST03T1_LineEdit_TestName.setReadOnly(False)
        self.ST03T1_LineEdit_TestDate = QLineEdit()
        self.ST03T1_LineEdit_TestDate.setInputMask("99/99/9999")        # Enforce date format, but not validating it. 
        self.ST03T1_LineEdit_TestDate.setPlaceholderText("01/01/1999")
        self.ST03T1_LineEdit_TestDate.setReadOnly(False)
        self.ST03T1_LineEdit_TestTime = QLineEdit()
        self.ST03T1_LineEdit_TestTime.setInputMask("99:99")             # Enforce dtime format. 
        self.ST03T1_LineEdit_TestTime.setPlaceholderText("01/01/1999")
        self.ST03T1_LineEdit_TestTime.setReadOnly(False)
        self.ST03T1_DropDown_TestCondition = QComboBox()
        self.ST03T1_DropDown_TestCondition.addItems(["Please select ...", "Wet", "Dry"])
        self.ST03T1_DropDown_TestCondition.setCurrentIndex(0)
        self.ST03T1_DropDown_WheelSide = QComboBox()
        self.ST03T1_DropDown_WheelSide.addItems(["Please select ...", "Left", "Right", "Not Determined"])
        self.ST03T1_DropDown_WheelSide.setCurrentIndex(0)
        self.ST03T1_DropDown_LabAging = QComboBox()
        self.ST03T1_DropDown_LabAging.addItems(["Please select ...", "No Lab Aging (Field Core)", 
                                                "STOA (2hr @ 135°C)", "LTOA (8hr @ 135°C)", 
                                                "LTOA (5 days @ 85°C)", "Others (Specify in comments)"])
        self.ST03T1_DropDown_LabAging.setCurrentIndex(0)
        self.ST03T1_LineEdit_TargetTestTemp = QLineEdit()                   # For target test temperature. 
        self.ST03T1_LineEdit_TargetTestTemp.setPlaceholderText("Enter test target temperature ...")
        self.ST03T1_LineEdit_TargetTestTemp.setReadOnly(False)
        Validator4TargetTemp = QDoubleValidator(0.00, 99.99, 2)
        Validator4TargetTemp.setNotation(QDoubleValidator.StandardNotation)
        self.ST03T1_LineEdit_TargetTestTemp.setValidator(QDoubleValidator(0, 99.99, 2))
        self.ST03T1_LineEdit_AvgTestTemp = QLineEdit()                      # For Average of recorded temps. 
        self.ST03T1_LineEdit_AvgTestTemp.setPlaceholderText("Avg. test temperature will be displayed here.")
        self.ST03T1_LineEdit_AvgTestTemp.setReadOnly(True)
        self.ST03T1_LineEdit_StdTestTemp = QLineEdit()                      # For Standard deviation of recorded temps. 
        self.ST03T1_LineEdit_StdTestTemp.setPlaceholderText("Std. test temperature will be displayed here.")
        self.ST03T1_LineEdit_StdTestTemp.setReadOnly(True)
        self.ST03T1_LineEdit_BNumber = QLineEdit()                          # For B-number.
        self.ST03T1_LineEdit_BNumber.setPlaceholderText("Enter only 4 or 5-digit B-number ...")
        self.ST03T1_LineEdit_BNumber.setReadOnly(False)
        IntValidator = QIntValidator(1000, 99999)
        self.ST03T1_LineEdit_BNumber.setValidator(IntValidator)
        self.ST03T1_LineEdit_LaneNumber = QLineEdit()                       # For Lane number. 
        self.ST03T1_LineEdit_LaneNumber.setPlaceholderText("Enter only lane number (1-11) ...")
        self.ST03T1_LineEdit_LaneNumber.setReadOnly(False)
        LnNumValidator = QIntValidator(1, 11)
        self.ST03T1_LineEdit_LaneNumber.setValidator(IntValidator)
        self.ST03T1_DropDown_LiftLocation = QComboBox()                     # For lift location.
        self.ST03T1_DropDown_LiftLocation.addItems(["Please Select...", "Top", "Bottom", "Not Applicable"])
        self.ST03T1_DropDown_LiftLocation.setCurrentIndex(0)
        self.ST03T1_LineEdit_TechnicianName = QLineEdit()                   # For Technician name. 
        self.ST03T1_LineEdit_TechnicianName.setPlaceholderText("Enter Technician Name ...")
        self.ST03T1_LineEdit_TechnicianName.setReadOnly(False)
        self.ST03T1_LineEdit_OtherComments = QLineEdit()                    # For Other comments
        self.ST03T1_LineEdit_OtherComments.setPlaceholderText("Enter any other comment ...")
        self.ST03T1_LineEdit_OtherComments.setReadOnly(False)
        SectT03T1_FormLayout.addRow(ST03T1_Label01, self.ST03T1_LineEdit_TestName)
        SectT03T1_FormLayout.addRow(ST03T1_Label09, self.ST03T1_LineEdit_BNumber)
        SectT03T1_FormLayout.addRow(ST03T1_Label10, self.ST03T1_LineEdit_LaneNumber)
        SectT03T1_FormLayout.addRow(ST03T1_Label11, self.ST03T1_DropDown_LiftLocation)
        SectT03T1_FormLayout.addRow(ST03T1_Label14, self.ST03T1_DropDown_LabAging)
        SectT03T1_FormLayout.addRow(ST03T1_Label12, self.ST03T1_LineEdit_TechnicianName)
        SectT03T1_FormLayout.addRow(ST03T1_Label02, self.ST03T1_LineEdit_TestDate)
        SectT03T1_FormLayout.addRow(ST03T1_Label03, self.ST03T1_LineEdit_TestTime)
        SectT03T1_FormLayout.addRow(ST03T1_Label04, self.ST03T1_DropDown_TestCondition)
        SectT03T1_FormLayout.addRow(ST03T1_Label05, self.ST03T1_DropDown_WheelSide)
        SectT03T1_FormLayout.addRow(ST03T1_Label06, self.ST03T1_LineEdit_TargetTestTemp)
        SectT03T1_FormLayout.addRow(ST03T1_Label07, self.ST03T1_LineEdit_AvgTestTemp)
        SectT03T1_FormLayout.addRow(ST03T1_Label08, self.ST03T1_LineEdit_StdTestTemp)
        SectT03T1_FormLayout.addRow(ST03T1_Label13, self.ST03T1_LineEdit_OtherComments)
        ScrollAreaT03T1_Layout.addLayout(SectT03T1_FormLayout)
        Tab1_Layout.addWidget(ScrollAreaT03T1)
        # --------------------------------------------
        # Tab 2: Model fitting details. 
        Tab2 = QWidget()
        Tab2_Layout = QVBoxLayout(Tab2)
        # Create a Scroll Area
        ScrollAreaT03T2 = QScrollArea()
        ScrollAreaT03T2.setWidgetResizable(True)
        ScrollContent2 = QWidget()
        ScrollAreaT03T2.setWidget(ScrollContent2)
        ScrollAreaT03T2_Layout = QVBoxLayout(ScrollContent2)
        ScrollAreaT03T2_Layout.addWidget(QLabel('Fitted model parameters:'))
        self.ModelParam_Table = QTableWidget(7, 3)
        self.ModelParam_Table.setHorizontalHeaderLabels(["Parameter", "Value", "Comment"])
        self.ModelParam_Table.setMinimumHeight(200)
        for i, (parameter, comment) in enumerate(zip(['a', 'b', 'SN', 'α', 'β', 'γ', 'Φ'], 
                                                   ['1st model', '1st model', 'Boundary point', '2nd model', 
                                                    '2nd model', '2nd model', '2nd model'])):
            self.ModelParam_Table.setItem(i, 0, QTableWidgetItem(parameter))
            self.ModelParam_Table.setItem(i, 1, QTableWidgetItem('Ν/Α'))
            self.ModelParam_Table.setItem(i, 2, QTableWidgetItem(comment))
        self.ModelParam_Table.setEditTriggers(QTableWidget.NoEditTriggers)          # Make Table Read-Only
        self.ModelParam_Table.setSelectionBehavior(QTableWidget.SelectItems)        # Select individual items
        self.ModelParam_Table.setSelectionMode(QTableWidget.ContiguousSelection)    # Allow selecting multiple cells
        self.ModelParam_Table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)     # Don't allow vertical scroll
        ScrollAreaT03T2_Layout.addWidget(self.ModelParam_Table)
        Tab2_Layout.addWidget(ScrollAreaT03T2)
        # --------------------------------------------
        # Tab 3: Analysis results. 
        Tab3 = QWidget()
        Tab3_Layout = QVBoxLayout(Tab3)
        # Create a Scroll Area
        ScrollAreaT03T3 = QScrollArea()
        ScrollAreaT03T3.setWidgetResizable(True)
        ScrollContent3 = QWidget()
        ScrollAreaT03T3.setWidget(ScrollContent3)
        ScrollAreaT03T3_Layout = QVBoxLayout(ScrollContent3)
        ScrollAreaT03T3_Layout.addWidget(QLabel('Analysis parameters (results):'))
        self.AnalysisParam_Table = QTableWidget(12, 3)
        self.AnalysisParam_Table.setColumnWidth(0, 170) 
        self.AnalysisParam_Table.setColumnWidth(1, 70) 
        self.AnalysisParam_Table.setColumnWidth(2, 150) 
        self.AnalysisParam_Table.setMinimumHeight(250)
        self.AnalysisParam_Table.setHorizontalHeaderLabels(["Parameter", "Value", "Comment"])
        for i, (parameter, comment) in enumerate(zip(
            ['Max Rut Depth (mm)', 'Max Passes', 'Rutting @ 10,000 (mm)', 'Rutting @ 20,000 (mm)', 
             'Stripping rut depth (mm)', 'Stripping Inflection Point (SIP)', 'SIP Y-val (mm)', 'Stripping Number (SN)', 
             'Creep line slope', 'Creep line intercept (mm)', 'Stripping line slope', 'Stripping line intercept (mm)'], 
            ['Ruttting+Stripping', '', 'Rutting only', 'Rutting only', 'Stripping only', '-', 
             '-', 'Boudary point', 'Tang. line to creep phase', 'Tang. line to creep phase', 
             'Tang. line to strip. phase', 'Tang. line to strip. phase'])):
            self.AnalysisParam_Table.setItem(i, 0, QTableWidgetItem(parameter))
            self.AnalysisParam_Table.setItem(i, 1, QTableWidgetItem('Ν/Α'))
            self.AnalysisParam_Table.setItem(i, 2, QTableWidgetItem(comment))
        self.AnalysisParam_Table.setEditTriggers(QTableWidget.NoEditTriggers)          # Make Table Read-Only
        self.AnalysisParam_Table.setSelectionBehavior(QTableWidget.SelectItems)        # Select individual items
        self.AnalysisParam_Table.setSelectionMode(QTableWidget.ContiguousSelection)    # Allow selecting multiple cells
        self.AnalysisParam_Table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)     # Don't allow vertical scroll

        ScrollAreaT03T3_Layout.addWidget(self.AnalysisParam_Table)
        Tab3_Layout.addWidget(ScrollAreaT03T3)
        # --------------------------------------------
        # Add tabs to QTabWidget
        self.SectT03_TabWidget.addTab(Tab1, "General")
        self.SectT03_TabWidget.addTab(Tab2, "Fitted Model")
        self.SectT03_TabWidget.addTab(Tab3, "Analysis Params")
        SectT03_Layout.addWidget(self.SectT03_TabWidget)
        SectT03.setLayout(SectT03_Layout)
        # --------------------------------------    
        TopLayout.addWidget(SectT03, 40)
        layout.addLayout(TopLayout, 35)
        self.SectT03_TabWidget.setEnabled(False)
        # --------------------------------------------------------------------------------------------------------------
        # -------------- Graph Section (Bottom Layout) -----------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # Section 03 (Left Layout, Bottom portion): Plotting section.
        SectB01 = QGroupBox("Plotting Section")
        SectB01.setStyleSheet("QGroupBox { font-weight: bold; }")
        SectB01_Layout = QVBoxLayout()
        # Define the figure and axe. 
        self.fig = Figure(figsize=(10, 7))
        self.fig.set_facecolor("#f0f0f0")
        self.canvas = FigureCanvas(self.fig)
        self.axes = self.fig.add_subplot(1, 1, 1)
        self.axes.set_xlabel('Number of passes', fontsize=10, fontweight='bold', color='k')
        self.axes.set_ylabel('Rut depth (mm)', fontsize=10, fontweight='bold', color='k')
        self.axes.grid(which='both', color='gray', alpha=0.1)
        self.axes.set_xlim([0, 20000])
        self.axes.set_ylim([0, 10])
        self.fig.set_constrained_layout(True)
        self.canvas.draw()
        self.ConnectionID = None            # Store the connection ID for the event listener
        # Layout properties. 
        SectB01_Layout.addWidget(self.canvas)
        SectB01.setLayout(SectB01_Layout)
        layout.addWidget(SectB01, 65)
        # --------------------------------------------------------------------------------------------------------------
        # ---------------------------- Menu bars----------- ------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        self.setStyleSheet("""
            QMenu {
                color: black;
            }
            QMenu::item:selected { 
                background-color: #005f87;
                color: white;
            }
            QMenu::item { 
                padding: 6px 20px;
            }
            QMenu::item:disabled {
                color: gray;
            }
        """)
        MenuBar  = self.menuBar()                       # Create the menu bar. 
        FileMenu = MenuBar.addMenu("File")              # Add the main menus.
        EditMenu = MenuBar.addMenu("Edit")
        RunMenu  = MenuBar.addMenu("Run")
        HelpMenu = MenuBar.addMenu("Help")
        # Add actions. 
        self.Menu_File_ImportFiles = QAction("Import MC Raw Data (Text files)")
        self.Menu_File_ImportFiles.triggered.connect(self.Function_Button_Add_Text_Files)
        self.Menu_File_ImportCopy  = QAction("Import MC Raw Data (Excel files)")
        self.Menu_File_ImportCopy.triggered.connect(self.Function_Button_Add_Excel_Files)
        self.Menu_File_Template    = QAction("Template for Input Data")
        self.Menu_File_Template.triggered.connect(self.Function_Button_Template)
        self.Menu_File_SaveAction  = QAction("Save to DB", self)
        # self.Menu_File_SaveAction.triggered.connect(self.Function_Save_to_DB)
        self.Menu_File_ExitAction  = QAction("Exit", self)
        self.Menu_File_ExitAction.triggered.connect(QApplication.quit)
        # ------------------------
        self.Menu_Edit_ResetReplot = QAction("Reset/rePlot Raw data")
        self.Menu_Edit_ResetReplot.triggered.connect(self.Function_Button_ResetRePlot)
        self.Menu_Edit_ResetReplot.setEnabled(False)
        # self.Menu_Fit_Outlier      = QAction("Specify Outlier", checkable=True)
        # self.Menu_Fit_Outlier.triggered.connect(self.Function_Button_SpecifyOutlier)
        self.Menu_Help_Help        = QAction('Help')
        self.Menu_Help_License     = QAction('License')
        # Add actions to the "File" menu
        FileMenu.addAction(self.Menu_File_ImportFiles)
        FileMenu.addAction(self.Menu_File_ImportCopy)
        FileMenu.addAction(self.Menu_File_Template)
        FileMenu.addSeparator()
        FileMenu.addAction(self.Menu_File_SaveAction)
        FileMenu.addSeparator()
        FileMenu.addAction(self.Menu_File_ExitAction)
        EditMenu.addAction(self.Menu_Edit_ResetReplot)
        EditMenu.addSeparator()
        HelpMenu.addAction(self.Menu_Help_Help)
        HelpMenu.addAction(self.Menu_Help_License)
    # ------------------------------------------------------------------------------------------------------------------
    def Function_Button_Template(self):
        # This function will ask user which template they want and then save it to the user specified location. 
        # First, deactivate the main page. 
        self.setEnabled(False)
        MsgBox_Template = QMessageBox()
        MsgBox_Template.setWindowTitle("Select Template Type")
        MsgBox_Template.setText("Which type of template file do you want to use?")
        Button1 = MsgBox_Template.addButton("General (excel)", QMessageBox.ActionRole)
        Button2 = MsgBox_Template.addButton("TFHRC-ABML HWTT device (txt)", QMessageBox.ActionRole)
        MsgBox_Template.exec_()
        # Determine the type template selected. 
        if MsgBox_Template.clickedButton() == Button1:
            FilePath = "./example/Excel Template for HWTT.xlsx"
        elif MsgBox_Template.clickedButton() == Button2:
            FilePath = "./example/TFHRC-ABML Text File Template for HWTT.txt"
        else:           # User just closed the window.
            self.setEnabled(True)   # Activate the main page again. 
            return                  # Return Nothing. 
        # Ask the user for a directory to copy the template file. 
        DestinationDir = QFileDialog.getExistingDirectory(self, "Select Folder")
        if DestinationDir:  # If a folder is selected
            try:
                shutil.copy(FilePath, os.path.join(DestinationDir, os.path.basename(FilePath)))
                MsgBox_Success = QMessageBox()
                MsgBox_Success.setIcon(QMessageBox.Information)
                MsgBox_Success.setWindowTitle("Copying Sucess")
                MsgBox_Success.setText(f"The Template file was Successful!\nFile copied to: " + \
                                       f"{DestinationDir}\nFileName: {os.path.basename(FilePath)}")
                MsgBox_Success.setStandardButtons(QMessageBox.Ok)
                MsgBox_Success.exec_()
            except Exception as err:
                MsgBox_Fail = QMessageBox()
                MsgBox_Fail.setIcon(QMessageBox.Critical)
                MsgBox_Fail.setWindowTitle("Copying Failed")
                MsgBox_Fail.setText(f"The Template file was NOT coppied!\n{err}")
                MsgBox_Fail.setStandardButtons(QMessageBox.Ok)
                MsgBox_Fail.exec_()
        # Re-activate and return nothing. 
        self.setEnabled(True)
        return
    # ------------------------------------------------------------------------------------------------------------------
    def Function_Button_Add_Text_Files(self):
        # This function will first ask user to select the input text result files, and then it will run them one by one. 
        FileList, _ = QFileDialog.getOpenFileNames(self, caption='Please select new HWTT result files:', 
                                                   directory='', 
                                                   filter="Text Files (*.txt);;All Files (*)")
        self.CurrentFileList = FileList
        self.CurrentFileIndex= 0
        # Check if file is not selected. 
        if len(FileList) == 0:          # Do nothing in case files are NOT selected. 
            self.Label_InputFileUpdate.setText('Waiting for input files...')
            self.ProgressBar.setEnabled(False)
            return
        # --------------------------------------------------------------------------------------------------------------
        # Update the GUI. 
        self.Button_AddFiles.setEnabled(False)
        self.Button_AddCopied.setEnabled(False)
        self.Button_Template.setEnabled(False)
        self.Button_ResetRePlot.setEnabled(True)
        self.SpinBox_MinPassNumber.setEnabled(True)
        self.SpinBox_MaxPassNumber.setEnabled(True)
        self.CheckBox_OffsetFirstRawData.setEnabled(True)
        self.Button_RunAnalysis.setEnabled(True)
        self.SectT03_TabWidget.setEnabled(True)
        self.Menu_File_ImportFiles.setEnabled(False)
        self.Menu_File_ImportCopy.setEnabled(False)
        self.Menu_File_Template.setEnabled(False)
        self.Menu_Edit_ResetReplot.setEnabled(True)
        # -----------------------------------------------------
        # Call the function to plot and handle the input files. 
        self.Function_Renew_MainPlot_For_Next_File()
    # ------------------------------------------------------------------------------------------------------------------
    def Function_Button_Add_Excel_Files(self):
        # This function will first ask user to select the input text result files, and then it will run them one by one. 
        FileList, _ = QFileDialog.getOpenFileNames(self, caption='Please select new HWTT result files:', 
                                                   directory='', 
                                                   filter="Excel Files (*.xlsx);;All Files (*)")
        self.CurrentFileList = FileList
        self.CurrentFileIndex= 0
        # Check if file is not selected. 
        if len(FileList) == 0:          # Do nothing in case files are NOT selected. 
            self.Label_InputFileUpdate.setText('Waiting for input files...')
            self.ProgressBar.setEnabled(False)
            return
        # Otherwise, Update the progress label.
        self.Label_InputFileUpdate.setText(f'Processing files: {1}/{len(FileList)}')
        self.ProgressBar.setEnabled(True)
        self.ProgressBar.setValue(1 / len(FileList))
        # disable the DB manager buttons. 
        self.Button_AddFiles.setEnabled(False)
        self.Button_AddCopied.setEnabled(False)
        self.Button_Template.setEnabled(False)
        self.Menu_File_ImportFiles.setEnabled(False)
        self.Menu_File_ImportCopy.setEnabled(False)
        self.Menu_File_Template.setEnabled(False)
        # Check if the selected file is already in the database. 
        self.cursor.execute("SELECT COUNT(*) FROM HWTT WHERE FileName = ?", (os.path.basename(FileList[0]),))
        count = self.cursor.fetchone()[0]
        if count > 0:
            raise Exception("The file is already existed! Maybe printing a message!")
        # Read the file. 
        Passes, RutDepth, Temperature, Props = Read_HWTT_Excel_File(FileList[0])




        # This function adds the Master curve data which are copied into the RAM. 
        # Print the message to user (for now). 
        MsgBox_AddCopied = QMessageBox()
        MsgBox_AddCopied.setIcon(QMessageBox.Information)
        MsgBox_AddCopied.setWindowTitle("Specify Outlier")
        MsgBox_AddCopied.setText(f"This function is under preparation. Will be added later.\n" + \
                                 f"For now, please use the 'Add Data from File' option")
        MsgBox_AddCopied.setStandardButtons(QMessageBox.Ok)
        MsgBox_AddCopied.exec_()



        #         # This function will first ask user to select the input Excel result files, and then it will run them one by one. 
        # FileList, _ = QFileDialog.getOpenFileNames(self, caption='Please select new binder MC result files:', 
        #                                            directory='', 
        #                                            filter="Excel Files (*.xlsx);;CSV Files (*.csv);;All Files (*)")
        # self.CurrentFileList = FileList
        # self.CurrentFileIndex= 0
        # # Check if file is not selected. 
        # if len(FileList) == 0:          # Do nothing in case files are NOT selected. 
        #     return
        # # Otherwise, Update the progress label.
        # self.Label_InputFileUpdate.setText(f'Processing files: {1}/{len(FileList)} (0.00%)')
        # # disable the DB manager buttons. 
        # self.Button_AddFiles.setEnabled(False)
        # self.Button_AddCopied.setEnabled(False)
        # self.Button_Template.setEnabled(False)
        # self.Menu_File_ImportFiles.setEnabled(False)
        # self.Menu_File_ImportCopy.setEnabled(False)
        # self.Menu_File_Template.setEnabled(False)
        # # Evaluate the input file to extract the isotherms.
        # self.CurIsotherms = EvaluateInputFile(FileList[0])
        # if self.CurIsotherms is None:
        #     raise Exception(f'Code incomplete!!! Write it so that it skip this file and move to the next!!!')
        # # Plot the isotherms.
        # self.Plot_ComplexModulus()
        # # Enable specify outlier and finalize buttons. 
        # self.Button_SpecifyOutlier.setEnabled(True)
        # self.Button_Finalize.setEnabled(True)
        # self.Menu_Fit_Outlier.setEnabled(True)
        # self.Menu_Fit_Finalize.setEnabled(True)
    # ------------------------------------------------------------------------------------------------------------------
    def Function_Button_ResetRePlot(self):
        """
        This function reset the current analysis (visuals) and replot the raw data. 
        """
        # Turn off the Accept/Fail buttons. 
        self.Button_FailResult.setEnabled(False)
        self.Button_AcceptResult.setEnabled(False)
        # Extract the data. 
        Passes   = self.Results['Passes']
        RutDepth = self.Results['RutDepth']
        # Get the raw datapoints to plot.
        RawSpacing = self.SpinBox_RawDataSpacing.value()            # Spacing for plotting the raw data. 
        Index = np.where((Passes >= self.SpinBox_MinPassNumber.value()) & \
                         (Passes <= self.SpinBox_MaxPassNumber.value()))[0]
        X = Passes[Index[::RawSpacing]]
        Y = RutDepth[Index[::RawSpacing]]
        # Perform the rut depth offsetting. 
        if self.CheckBox_OffsetFirstRawData.isChecked(): 
            Y -= Y[0]
        # Find the outlier range. 
        OutlierXmin = self.SpinBox_MaxPassNumber.value()
        OutlierXmax = Passes.max()
        # Plotting section.
        self.axes.clear()           # Clear the plot. 
        self.axes.plot(X, Y, ls='', marker='o', ms=2, color='green', alpha=0.5, label='Raw datapoints')
        if OutlierXmin != OutlierXmax:
            OutlierIndx = np.where((Passes > OutlierXmin) & (Passes <= OutlierXmax))[0]
            OutX = Passes[OutlierIndx[::RawSpacing]]
            OutY = RutDepth[OutlierIndx[::RawSpacing]]
            if self.CheckBox_OffsetFirstRawData.isChecked():
                OutY -= RutDepth[0]
            self.axes.plot(OutX, OutY, ls='', marker='d', ms=2, markerfacecolor='none', color='k', 
                           label='Outlier datapoints')
            self.axes.axvspan(xmin=OutlierXmin, xmax=OutlierXmax, color='r', alpha=0.2, label='Outlier interval')
        self.axes.set_xlabel('Number of passes', fontsize=10, fontweight='bold', color='k')
        self.axes.set_ylabel('Rut depth (mm)', fontsize=10, fontweight='bold', color='k')
        self.axes.grid(which='both', color='gray', alpha=0.1)
        if Passes.max() <= 20000:
            self.axes.set_xlim([0, 20000])
        self.axes.set_ylim([0, RutDepth.max() * 1.05])
        self.axes.legend(fontsize=12, loc='upper left', fancybox=True)
        self.fig.set_constrained_layout(True)
        self.canvas.draw()
        # ---------------------------------------
        # Clear the results.
        self.SectT03_TabWidget.setCurrentIndex(0)
        for i, (parameter, comment) in enumerate(zip(['a', 'b', 'SN', 'α', 'β', 'γ', 'Φ'], 
                                                     ['1st model', '1st model', 'Boundary point', '2nd model', 
                                                      '2nd model', '2nd model', '2nd model'])):
            self.ModelParam_Table.setItem(i, 0, QTableWidgetItem(parameter))
            self.ModelParam_Table.setItem(i, 1, QTableWidgetItem('Ν/Α'))
            self.ModelParam_Table.setItem(i, 2, QTableWidgetItem(comment))
        for i, (parameter, comment) in enumerate(zip(['Max Rut Depth (mm)', 'Max Passes', 'Rutting @ 10,000 (mm)', 
                                                      'Rutting @ 20,000 (mm)', 'Stripping rut depth (mm)', 
                                                      'Stripping Inflection Point (SIP)', 'SIP Y-val (mm)', 
                                                      'Stripping Number (SN)', 'Creep line slope', 
                                                      'Creep line intercept (mm)', 'Stripping line slope', 
                                                      'Stripping line intercept (mm)'], 
                                                     ['Ruttting+Stripping', '', 'Rutting only', 'Rutting only', 
                                                      'Stripping only', '-', '-', 'Boudary point', 
                                                      'Tang. line to creep phase', 'Tang. line to creep phase', 
                                                      'Tang. line to strip. phase','Tang. line to strip. phase'])):
            self.AnalysisParam_Table.setItem(i, 0, QTableWidgetItem(parameter))
            self.AnalysisParam_Table.setItem(i, 1, QTableWidgetItem('Ν/Α'))
            self.AnalysisParam_Table.setItem(i, 2, QTableWidgetItem(comment))
        return
    # ------------------------------------------------------------------------------------------------------------------
    def Function_Button_RunAnalysis(self):
        """
        This function will run the HWTT analysis and calculates the required parameters, then update the graph, and the 
        results section. 
        """
        # Enable the Accept/Fail buttons. 
        self.Button_FailResult.setEnabled(True)
        self.Button_AcceptResult.setEnabled(True)
        # Extract the valid X and Y values for the analysis.  
        Passes   = self.Results['Passes']
        RutDepth = self.Results['RutDepth']
        # Get the raw datapoints to plot.
        Index = np.where((Passes >= self.SpinBox_MinPassNumber.value()) & \
                         (Passes <= self.SpinBox_MaxPassNumber.value()))[0]
        X = Passes[Index]
        Y = RutDepth[Index]
        # Perform the rut depth offsetting. 
        if self.CheckBox_OffsetFirstRawData.isChecked(): 
            Y -= Y[0]
        # Check for the NaN values. 
        Index = np.where((~ np.isnan(X)) & (~ np.isnan(Y)))[0]
        X = X[Index].copy()
        Y = Y[Index].copy()
        # ----------------------------------------------------------------------------
        # Call the analysis function to fit the model and get the analysis parameters.
        Res = HWTT_Analysis(X, Y)
        # Store the results. 
        self.Results.update(Res)
        # ----------------------------------------------------------------------------
        # Plot the results on top of the current plot. 
        [a, b] = self.Results['Rutting_PowerModel_Coeff']
        Xp1 = np.linspace(0, self.Results['Stripping_Number'], num=1000)
        Xp2 = np.linspace(self.Results['Stripping_Number'], 20000, num=1000)
        Yp1 = ModelPower(Xp1, a, b)
        Yp2 = ModelPower(Xp2, a, b)
        self.axes.plot(Xp1, Yp1, ls='-',  lw=1.5, color='k', label='Power Model on Creep Phase')
        self.axes.plot(Xp2, Yp2, ls='--', lw=1.5, color='k', label='Power Model extrapolation')
        self.axes.plot(self.Results['Xmodel'], self.Results['Ymodel'], ls='--', lw=1.5, color='b', label='Full model')
        self.axes.plot([0, 20000], np.polyval(self.Results['CreepLine'], [0, 20000]), ls='--', color='r', lw=0.5)
        self.axes.plot([0, 20000], np.polyval(self.Results['TangentLine'], [0, 20000]), ls='--', color='r', lw=0.5)
        self.axes.plot(self.Results['Stripping_Number'], ModelPower(self.Results['Stripping_Number'], a, b), 
                       ls='', marker='*', ms=12, color='b', label='Stripping Number')
        self.axes.plot(self.Results['SIP'], self.Results['SIP_Yval_mm'], ls='', marker='X', ms=12, color='m', 
                       label='SIP point')
        self.axes.legend()
        if Passes.max() <= 20000:
            self.axes.set_xlim([0, 20000])
        self.axes.set_ylim([0, RutDepth.max() * 1.05])
        self.fig.set_constrained_layout(True)
        self.canvas.draw()
        # ----------------------------------------------------------------------------
        # Update the results section. 
        self.Function_Update_Model_Fit_Analysis_Parameters()
        return
    # ------------------------------------------------------------------------------------------------------------------
    def Function_Update_General_Information(self):
        """
        This function updates the general information of the project after entering. 
        """
        self.ST03T1_LineEdit_TestName.setText(self.Results['Props']['Test_Name'])      # The test name. 
        self.ST03T1_LineEdit_TestDate.setText(self.Results['Props']['Test_Date'])
        self.ST03T1_LineEdit_TestTime.setText(self.Results['Props']['Test_Time'])
        if self.Results['Props']['Test_Condition'].lower() == 'wet':            # Evaluate the testing condition.
            self.ST03T1_DropDown_TestCondition.setCurrentIndex(1)
        elif self.Results['Props']['Test_Condition'].lower() == 'dry':
            self.ST03T1_DropDown_TestCondition.setCurrentIndex(2)
        else:
            self.ST03T1_DropDown_TestCondition.setCurrentIndex(0)
        if self.Results['Props']['Wheel_Side'].lower() == 'left':
            self.ST03T1_DropDown_WheelSide.setCurrentIndex(1)
        elif self.Results['Props']['Wheel_Side'].lower() == 'right':
            self.ST03T1_DropDown_WheelSide.setCurrentIndex(2)
        else:
            self.ST03T1_DropDown_WheelSide.setCurrentIndex(3)
        self.ST03T1_LineEdit_TargetTestTemp.setText(f'{float(self.Results["Props"]["Test_Temperature"]):.2f}')
        self.ST03T1_LineEdit_AvgTestTemp.setText(f"{self.Results['Temperatures'].mean():.2f}")
        self.ST03T1_LineEdit_StdTestTemp.setText(f"{self.Results['Temperatures'].std():.4f}")
    # ------------------------------------------------------------------------------------------------------------------
    def Function_Update_Model_Fit_Analysis_Parameters(self):
        """
        This function updates the tables in the result tabs for model fitting parameters and analysis results. 
        """
        # Fill for the first part power model. 
        self.ModelParam_Table.setItem(0, 1, QTableWidgetItem(f'{self.Results["Rutting_PowerModel_Coeff"][0]:.6f}'))
        self.ModelParam_Table.setItem(1, 1, QTableWidgetItem(f'{self.Results["Rutting_PowerModel_Coeff"][1]:.6f}'))
        # Fill the table for the Stripping number point (boundary point).
        self.ModelParam_Table.setItem(2, 1, QTableWidgetItem(f'{self.Results["Stripping_Number"]:.2f}'))
        # Fill the table for the second part power model. 
        self.ModelParam_Table.setItem(3, 1, QTableWidgetItem(f'{self.Results["Rutting_PowerModel_Part2_Coeff"][0]:.6e}'))
        self.ModelParam_Table.setItem(4, 1, QTableWidgetItem(f'{self.Results["Rutting_PowerModel_Part2_Coeff"][1]:.6f}'))
        self.ModelParam_Table.setItem(5, 1, QTableWidgetItem(f'{self.Results["Rutting_PowerModel_Part2_Coeff"][2]:.4f}'))
        self.ModelParam_Table.setItem(6, 1, QTableWidgetItem(f'{self.Results["Rutting_PowerModel_Part2_Coeff"][3]:.6f}'))
        # Fill the analysis results. 
        self.AnalysisParam_Table.setItem(0, 1, QTableWidgetItem(f'{self.Results["RutDepth"].max():.3f}'))
        self.AnalysisParam_Table.setItem(1, 1, QTableWidgetItem(f'{self.Results["Passes"].max():d}'))
        self.AnalysisParam_Table.setItem(2, 1, QTableWidgetItem(f'{self.Results["Rutting@10k_mm"]:.3f}'))
        self.AnalysisParam_Table.setItem(3, 1, QTableWidgetItem(f'{self.Results["Rutting@20k_mm"]:.3f}'))
        self.AnalysisParam_Table.setItem(4, 1, QTableWidgetItem(f'{self.Results["Stripping_Rutting_mm"]:.3f}'))
        self.AnalysisParam_Table.setItem(5, 1, QTableWidgetItem(f'{self.Results["SIP"]:.2f}'))
        self.AnalysisParam_Table.setItem(6, 1, QTableWidgetItem(f'{self.Results["SIP_Yval_mm"]:.3f}'))
        self.AnalysisParam_Table.setItem(7, 1, QTableWidgetItem(f'{self.Results["Stripping_Number"]:.2f}'))
        self.AnalysisParam_Table.setItem(8, 1, QTableWidgetItem(f'{self.Results["CreepLine"][0]:.4f}'))
        self.AnalysisParam_Table.setItem(9, 1, QTableWidgetItem(f'{self.Results["CreepLine"][1]:.2f}'))
        self.AnalysisParam_Table.setItem(10, 1, QTableWidgetItem(f'{self.Results["TangentLine"][0]:.4f}'))
        self.AnalysisParam_Table.setItem(11, 1, QTableWidgetItem(f'{self.Results["TangentLine"][0]:.2f}'))
        self.SectT03_TabWidget.setCurrentIndex(2)
    # ------------------------------------------------------------------------------------------------------------------
    def Function_Button_PassResult(self):
        """
        This function get the analysis results and submit them to the database as valid result. 
        """
        # First, check if the B-number and lift location was properly indicated. 
        Check = self.Function_Check_Before_Submit_to_DB()
        if not Check:
            return
        # --------------------------------------------------------------------------------------------------------------
        # Submit data to DB. 
        # Preparing the rep number. 
        self.cursor.execute("SELECT COUNT(*) FROM HWTT WHERE Bnumber = ? AND Lab_Aging = ?;", 
                            (int(self.ST03T1_LineEdit_BNumber.text()), self.ST03T1_DropDown_LabAging.currentText()))
        RepNumber = self.cursor.fetchone()[0] + 1
        # Preparing the data in binary form. 
        RutData, RutData_shape, RutData_dtype = Array_to_Binary(np.vstack((self.Results['Passes'], 
                                                                           self.Results['RutDepth'], 
                                                                           self.Results['Temperatures'])))
        # Append the data to the database. 
        Append_to_Database(self.conn, self.cursor, {
            "Bnumber": int(self.ST03T1_LineEdit_BNumber.text()), 
            "Lab_Aging": self.ST03T1_DropDown_LabAging.currentText(), 
            "RepNumber": RepNumber, 
            "Wheel_Side": self.ST03T1_DropDown_WheelSide.currentText(), 
            "FileName": os.path.basename(self.CurrentFileList[self.CurrentFileIndex]), 
            "FileDirectory": os.path.dirname(self.CurrentFileList[self.CurrentFileIndex]), 
            "Data": RutData, "Data_shape": RutData_shape, "Data_dtype": RutData_dtype, 
            "StrippingNumber": self.Results['Stripping_Number'], 
            "Max_Rut_mm": self.Results['Maximum_Rutting_mm'], "Max_Pass": self.Results['Maximum_Passes'], 
            "RuttingAt10k_mm": self.Results['Rutting@10k_mm'], "RuttingAt20k_mm": self.Results['Rutting@20k_mm'], 
            "ModelCoeff_a": self.Results['Rutting_PowerModel_Coeff'][0], 
            "ModelCoeff_b": self.Results['Rutting_PowerModel_Coeff'][1], 
            "ModelCoeff_alpha": self.Results['Rutting_PowerModel_Part2_Coeff'][0], 
            "ModelCoeff_beta": self.Results['Rutting_PowerModel_Part2_Coeff'][1], 
            "ModelCoeff_gamma": self.Results['Rutting_PowerModel_Part2_Coeff'][2], 
            "ModelCoeff_Phi": self.Results['Rutting_PowerModel_Part2_Coeff'][3], 
            "Stripping_Rutting_mm": self.Results['Stripping_Rutting_mm'], 
            "Stripping_Rutting_Pass": self.Results['Stripping_Rutting_Pass'], 
            "SIP": self.Results['SIP'], "SIP_Yvalue": self.Results['SIP_Yval_mm'], 
            "CreepLine_Slope": self.Results['CreepLine'][0], 
            "CreepLine_Intercept": self.Results['CreepLine'][1], 
            "StrippingLine_Slope": self.Results['TangentLine'][0], 
            "StrippingLine_Intercept": self.Results['TangentLine'][1], 
            "Valid_Min_Pass": self.SpinBox_MinPassNumber.value(), "Valid_Max_Pass": self.SpinBox_MaxPassNumber.value(), 
            "Test_Name": self.ST03T1_LineEdit_TestName.text(), 
            "Technician_Name": self.ST03T1_LineEdit_TechnicianName.text(), 
            "Test_Date": self.ST03T1_LineEdit_TestDate.text(), 
            "Test_Time": self.ST03T1_LineEdit_TestTime.text(), 
            "Test_Condition": self.ST03T1_DropDown_TestCondition.currentText(), 
            "Target_Test_Temperature": float(self.ST03T1_LineEdit_TargetTestTemp.text()), 
            "Avg_Test_Temperature": float(self.ST03T1_LineEdit_AvgTestTemp.text()), 
            "Std_Test_Temperature": float(self.ST03T1_LineEdit_StdTestTemp.text()), 
            "Other_Comments": self.ST03T1_LineEdit_OtherComments.text(), "IsOutlier": 0
            })
        # --------------------------------------------------------------------------------------------------------------
        # Update the index and check for end of the process. 
        self.CurrentFileIndex += 1
        Check = self.Function_Check_End_of_Loop()
        if Check:
            return
        # --------------------------------------------------------------------------------------------------------------
        # Update the plots and everything. 
        self.Function_Renew_MainPlot_For_Next_File()
        # Return Nothing.
        return
    # ------------------------------------------------------------------------------------------------------------------
    def Function_Button_FailResult(self):
        """
        This function get the analysis results and submit them to the database as an outlier result. 
        """
        # First, check if the B-number and lift location was properly indicated. 
        Check = self.Function_Check_Before_Submit_to_DB()
        if not Check:
            return
        # --------------------------------------------------------------------------------------------------------------
        # Submit data to DB. 
        # Preparing the rep number. 
        self.cursor.execute("SELECT COUNT(*) FROM HWTT WHERE Bnumber = ? AND Lab_Aging = ?;", 
                            (int(self.ST03T1_LineEdit_BNumber.text()), self.ST03T1_DropDown_LabAging.currentText()))
        RepNumber = self.cursor.fetchone()[0] + 1
        # Preparing the data in binary form. 
        RutData, RutData_shape, RutData_dtype = Array_to_Binary(np.vstack((self.Results['Passes'], 
                                                                           self.Results['RutDepth'], 
                                                                           self.Results['Temperatures'])))
        # Append the data to the database. 
        Append_to_Database(self.conn, self.cursor, {
            "Bnumber": int(self.ST03T1_LineEdit_BNumber.text()), 
            "Lab_Aging": self.ST03T1_DropDown_LabAging.currentText(), 
            "RepNumber": RepNumber, 
            "Wheel_Side": self.ST03T1_DropDown_WheelSide.currentText(), 
            "FileName": os.path.basename(self.CurrentFileList[self.CurrentFileIndex]), 
            "FileDirectory": os.path.dirname(self.CurrentFileList[self.CurrentFileIndex]), 
            "Data": RutData, "Data_shape": RutData_shape, "Data_dtype": RutData_dtype, 
            "StrippingNumber": self.Results['Stripping_Number'], 
            "Max_Rut_mm": self.Results['Maximum_Rutting_mm'], "Max_Pass": self.Results['Maximum_Passes'], 
            "RuttingAt10k_mm": self.Results['Rutting@10k_mm'], "RuttingAt20k_mm": self.Results['Rutting@20k_mm'], 
            "ModelCoeff_a": self.Results['Rutting_PowerModel_Coeff'][0], 
            "ModelCoeff_b": self.Results['Rutting_PowerModel_Coeff'][1], 
            "ModelCoeff_alpha": self.Results['Rutting_PowerModel_Part2_Coeff'][0], 
            "ModelCoeff_beta": self.Results['Rutting_PowerModel_Part2_Coeff'][1], 
            "ModelCoeff_gamma": self.Results['Rutting_PowerModel_Part2_Coeff'][2], 
            "ModelCoeff_Phi": self.Results['Rutting_PowerModel_Part2_Coeff'][3], 
            "Stripping_Rutting_mm": self.Results['Stripping_Rutting_mm'], 
            "Stripping_Rutting_Pass": self.Results['Stripping_Rutting_Pass'], 
            "SIP": self.Results['SIP'], "SIP_Yvalue": self.Results['SIP_Yval_mm'], 
            "CreepLine_Slope": self.Results['CreepLine'][0], 
            "CreepLine_Intercept": self.Results['CreepLine'][1], 
            "StrippingLine_Slope": self.Results['TangentLine'][0], 
            "StrippingLine_Intercept": self.Results['TangentLine'][1], 
            "Valid_Min_Pass": self.SpinBox_MinPassNumber.value(), "Valid_Max_Pass": self.SpinBox_MaxPassNumber.value(), 
            "Test_Name": self.ST03T1_LineEdit_TestName.text(), 
            "Technician_Name": self.ST03T1_LineEdit_TechnicianName.text(), 
            "Test_Date": self.ST03T1_LineEdit_TestDate.text(), 
            "Test_Time": self.ST03T1_LineEdit_TestTime.text(), 
            "Test_Condition": self.ST03T1_DropDown_TestCondition.currentText(), 
            "Target_Test_Temperature": float(self.ST03T1_LineEdit_TargetTestTemp.text()), 
            "Avg_Test_Temperature": float(self.ST03T1_LineEdit_AvgTestTemp.text()), 
            "Std_Test_Temperature": float(self.ST03T1_LineEdit_StdTestTemp.text()), 
            "Other_Comments": self.ST03T1_LineEdit_OtherComments.text(), "IsOutlier": 1
            })
        # --------------------------------------------------------------------------------------------------------------
        # Update the index and check for end of the process. 
        self.CurrentFileIndex += 1
        Check = self.Function_Check_End_of_Loop()
        if Check:
            return
        # --------------------------------------------------------------------------------------------------------------
        # Update the plots and everything. 
        self.Function_Renew_MainPlot_For_Next_File()
        # Return Nothing.
        return
    # ------------------------------------------------------------------------------------------------------------------
    def Function_Check_Before_Submit_to_DB(self):
        """
        This function performs some simple checks before accepting or rejecting the data and submit them to Database. 
        """
        # Check for B-number.
        if self.ST03T1_LineEdit_BNumber.text() == '' or int(self.ST03T1_LineEdit_BNumber.text()) < 1000:
            self.SectT03_TabWidget.setCurrentIndex(0)
            QMessageBox.critical(self, "Invalid B-Number", 
                                 f"B-number is required to submit this test results to database. Please provide a " + 
                                 f"valid B-number under 'General' tab.\n\n" + 
                                 f"B-number is an unique identification number of materials in TFHRC laboratory, " +
                                 f"which is used as primary key to filter materials. If your using this tool for " + 
                                 f"any other laboratory, you may assign a 4 or 5 digit integer number to the tested " + 
                                 f"sample and use it as B-number.")
            return False
        # -----------------------------
        # Check for the lift location. 
        if self.ST03T1_DropDown_LiftLocation.currentIndex() == 0:
            self.SectT03_TabWidget.setCurrentIndex(0)
            QMessageBox.critical(self, "Invalid Lift Location", 
                                 f"Lift location (Top/Bottom) is required to submit this test results to database. " + 
                                 f"Please select the lift location from the corresponding dropdown menu under " + 
                                 f"'General' tab.\n\n" + 
                                 f"Lift Location is required as the HWTT Analysis Tool was developed to analyze " + 
                                 f"HWTT test results for materials from Pavement Testing Facility (PTF), located at " +
                                 f"Turner-Fairbank Highway Research Center (TFHRC), where most lanes consists of 2 " +
                                 f"lifts of asphalt mixtures. If you are using this tool for another project where " +
                                 f"lift location is not applicable, please select 'Not Applicable' option.")
            return False
        # -----------------------------
        # Check for the state of laboratory aging. 
        if self.ST03T1_DropDown_LabAging.currentIndex() == 0:
            self.SectT03_TabWidget.setCurrentIndex(0)
            QMessageBox.critical(self, "Invalid Lab Aging", 
                                 f"State of laboratory aging is required to submit this test results to database. " + 
                                 f"Please select the state of laboratory aging from the corresponding dropdown menu " + 
                                 f"under 'General' tab.\n\n" + 
                                 f"All samples prepared for HWTT testing could be collected either from Field cores, " + 
                                 f"or compacted in the lab. According to TFHRC experience, almost all field cores " +
                                 f"were not undergone any laboratory aging. This is while the loose mixtures " +
                                 f"collected during the construction of Pavement Testing Facility (PTF) were " +
                                 f"undergone short- or long-term aging. If you don't have any laboratory aging " + 
                                 f"associated to your samples, please select 'no lab aging' option. If the proper " +
                                 f"laboratory aging procedure is not available in dropdown menu, please use 'others' " +
                                 f"and provide summary of laboratory aging in comments section or contact developers " +
                                 f"to add your desire laboratory aging option.")
            return False
        # -----------------------------
        # Check if comments provided in case of other laboratory methods. 
        if self.ST03T1_DropDown_LabAging.currentText() == 'Others (Specify in comments)' and \
            self.ST03T1_LineEdit_OtherComments.text() == '':
            self.SectT03_TabWidget.setCurrentIndex(0)
            QMessageBox.critical(self, "Error with Lab Aging", 
                                 f"You've selected 'Others (Specify in comments)' as your laboratory aging method, " + 
                                 f"but the comments section was empty. Please provide your desire laboratory aging " + 
                                 f"method in 'Other comments' text box under 'General' tab.")
            return False
        # Otherwise, return true.
        return True
    # ------------------------------------------------------------------------------------------------------------------
    def Function_Check_End_of_Loop(self):
        """
        This function only checks if all the required files are analyzed, and if the analysis is finished, it reactivate
        the main window. 
        """
        if self.CurrentFileIndex >= len(self.CurrentFileList):
            QMessageBox.information(self, "Success", f"Loop over {len(self.CurrentFileList)} files has been finished!")
            # Clear the plots.
            self.axes.clear()
            self.axes.set_xlabel('Number of passes', fontsize=10, fontweight='bold', color='k')
            self.axes.set_ylabel('Rut depth (mm)', fontsize=10, fontweight='bold', color='k')
            self.axes.grid(which='both', color='gray', alpha=0.1)
            self.axes.set_xlim([0, 20000])
            self.axes.set_ylim([0, 10])
            self.fig.set_constrained_layout(True)
            self.canvas.draw()
            # Empty the result tabs.
            self.SectT03_TabWidget.setCurrentIndex(0)
            self.SectT03_TabWidget.setEnabled(False)
            self.ST03T1_LineEdit_TestName.setText('')
            self.ST03T1_LineEdit_TestDate.setText('')
            self.ST03T1_LineEdit_TestTime.setText('')
            self.ST03T1_DropDown_TestCondition.setCurrentIndex(2)
            self.ST03T1_DropDown_WheelSide.setCurrentIndex(2)
            self.ST03T1_LineEdit_TargetTestTemp.setText('')
            self.ST03T1_LineEdit_AvgTestTemp.setText('')
            self.ST03T1_LineEdit_StdTestTemp.setText('')
            for i, (parameter, comment) in enumerate(zip(['a', 'b', 'SN', 'α', 'β', 'γ', 'Φ'], 
                                                         ['1st model', '1st model', 'Boundary point', '2nd model', 
                                                          '2nd model', '2nd model', '2nd model'])):
                self.ModelParam_Table.setItem(i, 0, QTableWidgetItem(parameter))
                self.ModelParam_Table.setItem(i, 1, QTableWidgetItem('Ν/Α'))
                self.ModelParam_Table.setItem(i, 2, QTableWidgetItem(comment))
            for i, (parameter, comment) in enumerate(zip(['Max Rut Depth (mm)', 'Max Passes', 'Rutting @ 10,000 (mm)', 
                                                          'Rutting @ 20,000 (mm)', 'Stripping rut depth (mm)', 
                                                          'Stripping Inflection Point (SIP)', 'SIP Y-val (mm)', 
                                                          'Stripping Number (SN)', 'Creep line slope', 
                                                          'Creep line intercept (mm)', 'Stripping line slope', 
                                                          'Stripping line intercept (mm)'], 
                                                          ['Ruttting+Stripping', '', 'Rutting only', 'Rutting only', 
                                                           'Stripping only', '-', '-', 'Boudary point', 
                                                           'Tang. line to creep phase', 'Tang. line to creep phase', 
                                                           'Tang. line to strip. phase','Tang. line to strip. phase'])):
                self.AnalysisParam_Table.setItem(i, 0, QTableWidgetItem(parameter))
                self.AnalysisParam_Table.setItem(i, 1, QTableWidgetItem('Ν/Α'))
                self.AnalysisParam_Table.setItem(i, 2, QTableWidgetItem(comment))
            # Adjust the buttons the buttons. 
            self.Button_RunAnalysis.setEnabled(False)
            self.Button_ResetRePlot.setEnabled(False)
            self.Menu_Edit_ResetReplot.setEnabled(False)
            self.Button_FailResult.setEnabled(False)
            self.Button_AcceptResult.setEnabled(False)
            self.Button_Template.setEnabled(True)
            self.Menu_File_Template.setEnabled(True)
            self.Button_AddCopied.setEnabled(True)
            self.Menu_File_ImportCopy.setEnabled(True)
            self.Button_AddFiles.setEnabled(True)
            self.Menu_File_ImportFiles.setEnabled(True)
            self.SpinBox_MaxPassNumber.setEnabled(False)
            self.SpinBox_MinPassNumber.setEnabled(False)
            self.CheckBox_OffsetFirstRawData.setEnabled(False)
            self.ProgressBar.setValue(0)
            self.Label_InputFileUpdate.setText('Waiting for input files...')
            # Return "True".
            return True
        # Otherwise, return False.
        return False
    # ------------------------------------------------------------------------------------------------------------------
    def Function_Renew_MainPlot_For_Next_File(self):
        """
        This function goes through the next input file in the queue and try to read and plot the file. 
        """
        FileCompatibleFlag = False
        # Iterate over the files. 
        for i in range(self.CurrentFileIndex, len(self.CurrentFileList)):
            self.CurrentFileIndex = i
            # Check if the file is already exist in the database. 
            self.cursor.execute("SELECT EXISTS(SELECT 1 FROM HWTT WHERE FileName = ?)", 
                                (os.path.basename(self.CurrentFileList[i]),))
            exists = self.cursor.fetchone()[0]
            if exists:
                if not self.ShowFileExistedError:
                    continue
                self.cursor.execute("SELECT Bnumber, RepNumber, Lab_Aging FROM HWTT WHERE FileName = ?", 
                                    (os.path.basename(self.CurrentFileList[i]),))
                [bnum, repnum, labage] = self.cursor.fetchone()
                self.FileExistedError(f"File Already Existed!", 
                                      f"The file <{os.path.basename(self.CurrentFileList[i])}> was already exists " + 
                                      f"in the database. Instead of reloading the file, please try to edit/modify " + 
                                      f"the analysis on that specific file. Take note of B-number, Rep number and " + 
                                      f"laboratory aging state (as provided below), and try to use 'Edit/Modify DB' " + 
                                      f"button to edit this result!\n" + 
                                      f"B-number: {bnum}\nRep number: {repnum}\nLaboratory Aging: {labage}\n" + 
                                      f"File directory: {os.path.dirname(self.CurrentFileList[i])}")
                continue
            # Check the file compatibility.
            try:
                if fnmatch.fnmatch(os.path.basename(self.CurrentFileList[i][-4:]), '*.txt'):
                    Passes, RutDepth, Temperature, Props = Read_HWTT_Text_File(self.CurrentFileList[i])
                    FileCompatibleFlag = True
                    break
                elif fnmatch.fnmatch(os.path.basename(self.CurrentFileList[i][-4:]), '*.xlsx'):
                    Passes, RutDepth, Temperature, Props = Read_HWTT_Excel_File(self.CurrentFileList[i])
                    FileCompatibleFlag = True
                    break
                else:
                    raise ValueError(f'File format should be either "*.txt" or "*.xlsx". Please check the input file ' + 
                                    f'format.')
            except Exception as err:
                progress = int((i + 0.5) / len(self.CurrentFileList) * 100)
                if progress > 100: progress = 100
                self.ProgressBar.setValue(progress)
                QMessageBox.critical(self, "Unable to Read File!", 
                                     f"There is a problem in reading the input file:\n" + 
                                     f"File: <{os.path.basename(self.CurrentFileList[i])}>\nDirectory: " + 
                                     f"{os.path.dirname(self.CurrentFileList[i])}.\n\n" +
                                     f"Input file should be either *.txt or *.xlsx. To ensure compatibility, please " + 
                                     f"use the template files in construction of your input files.\n" +
                                     f"Error: {err}")
                continue
        # --------------------------------------------------------------------------------------------------------------
        # Check if a compatible file found.
        if not FileCompatibleFlag:
            self.CurrentFileIndex += 1
            self.Function_Check_End_of_Loop()
            return
        # Otherwise, perform the analysis. 
        # --------------------------------------------------------------------------------------------------------------
        # Save the extracted results. 
        self.Results['Passes']       = Passes.copy()
        self.Results['RutDepth']     = RutDepth.copy()
        self.Results['Temperatures'] = Temperature.copy()
        self.Results['Props']        = Props.copy()
        # Update the progress bar. 
        self.Label_InputFileUpdate.setText(f'Processing files: ' + 
                                           f'{self.CurrentFileIndex}/{len(self.CurrentFileList)} done!')
        self.ProgressBar.setValue(int((self.CurrentFileIndex + 0.5) / len(self.CurrentFileList) * 100))
        # --------------------------------------------------------------------------------------------------------------
        # Update the valid passes and their corresponding spinboxes. 
        self.ValidPasses = [0, int(Passes.max())]
        self.SpinBox_MaxPassNumber.setRange(self.SpinBox_MinPassNumber.value() + 1, int(Passes.max()))
        self.SpinBox_MinPassNumber.setRange(0, self.SpinBox_MaxPassNumber.value() - 1)
        # --------------------------------------------------------------------------------------------------------------
        # Plot the results.
        self.Function_Button_ResetRePlot()
        # Update the general information in result tab. 
        self.Function_Update_General_Information()
    # ------------------------------------------------------------------------------------------------------------------
    def FileExistedError(self, Title, Body):
        # Create a QMessageBox
        message_box = QMessageBox()
        message_box.setIcon(QMessageBox.Critical)
        message_box.setText(Title)
        message_box.setInformativeText(Body)
        message_box.setWindowTitle("File Existed Error")
        message_box.setStandardButtons(QMessageBox.Ok)
        # Add a checkbox
        checkbox = QCheckBox("Do not show this again")
        # Access the layout of the QMessageBox and add the checkbox
        layout = message_box.layout()
        layout.addWidget(checkbox, layout.rowCount(), 0, 1, layout.columnCount())
        # Show the message box
        message_box.exec_()
        # Check the state of the checkbox after the message box is closed
        if checkbox.isChecked():
            self.ShowFileExistedError = False
        else:
            self.ShowFileExistedError = True
# ======================================================================================================================
# ======================================================================================================================
# ======================================================================================================================
if __name__ == '__main__':

    app = QApplication(sys.argv)
    # Connect to a SQL database. 
    conn = sqlite3.connect("C:\\Users\\SF.Abdollahi.ctr\\OneDrive - DOT OST\\GitHub_HWTT_Analysis_Tool\\HWTT_Analysis_Tool\\example\\PTF5_DB.db")
    cursor = conn.cursor()
    Main = Main_Window(conn, cursor, 'PTF5_DB.db', 'C:\\Users\\SF.Abdollahi.ctr\\OneDrive - DOT OST\\GitHub_HWTT_Analysis_Tool\\HWTT_Analysis_Tool\\example')
    Main.show()
    app.exec()



    app.quit()
    print('finish')