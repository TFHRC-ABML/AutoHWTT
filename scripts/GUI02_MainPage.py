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
    QSpinBox, QFrame, QDialog, QRadioButton, QButtonGroup
from PyQt5.QtGui import QPixmap, QFont, QRegExpValidator, QDoubleValidator, QIntValidator, QPixmap
from PyQt5.QtCore import Qt, QRegExp
from qtwidgets import AnimatedToggle
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from scripts.Alg01_UtilityFunctions import Read_HWTT_Text_File, Read_HWTT_Excel_File, Array_to_Binary, Binary_to_Array
from scripts.Alg02_SQL_Manager import Append_to_Database
from scripts.Alg03_HWTT_Analysis_Functions import HWTT_Analysis, ModelPower, TsengLyttonModel, YinModel
from scripts.GUI03_ReviewPage import DB_ReviewPage
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
        self.setWindowTitle(f"AutoHWTT (version 1.0) | Database name: {DB_Name}")
        # self.setFixedSize(1250, 900)
        self.resize(1250, 900)
        self.setMinimumSize(900, 700)
        self.setStyleSheet("background-color: #f0f0f0;")
        # Create shared data object.
        self.shared_data = SharedData()
        # Create QStackedWidget.
        self.stack = QStackedWidget()
        # Create pages
        self.main_page = MainPage(conn, cursor, DB_Name, DB_Folder, self.stack)
        self.db_review_page = DB_ReviewPage(conn, cursor, DB_Name, DB_Folder, self.stack, self.shared_data)
            # self.FTIR_revise_page = Revise_FTIR_AnalysisPage(conn, cursor, DB_Name, DB_Folder, self.stack, self.shared_data)
        # Add pages to the stack
        self.stack.addWidget(self.main_page)            # This page has stack index 0
        self.stack.addWidget(self.db_review_page)       # This page has stack index 1
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
        self.Results = {}           # To store the results and required data. 
        self.Results['Plot_Level'] = 0      # 0 means only raw data, 1 means raw data + fitted model, 
                                            # 2 means raw data + fitted model for calculating adjusted SIP.
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
        SectT01 = QGroupBox("Input Data Section && Review")
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
        # Button for Run the analysis.
        self.Button_Review = QPushButton("Review Page")
        self.Button_Review.setFont(QFont("Arial", 12, QFont.Bold))
        self.Button_Review.clicked.connect(self.Function_Button_Review)
        self.Button_Review.setFixedSize(180, 40)
        self.Button_Review.setEnabled(True)
        self.Button_Review.setStyleSheet(
        """
        QPushButton:enabled {background-color: #FFE4B5; color: black;}
        QPushButton:hover {background-color: lightgray;}
        QPushButton:pressed {background-color: gray;}
        QPushButton:checked {background-color: lime;}
        """)
        # Create a label to show the file updater. 
        self.Label_InputFileUpdate = QLabel('Waiting for input files...')
        # process the layouts. 
        SectT01_Layout.addWidget(self.Button_AddFiles,  alignment=Qt.AlignHCenter | Qt.AlignTop)
        SectT01_Layout.addWidget(self.Button_AddCopied, alignment=Qt.AlignHCenter | Qt.AlignTop)
        SectT01_Layout.addWidget(self.Button_Template,  alignment=Qt.AlignHCenter | Qt.AlignTop)
        SectT01_Layout.addWidget(self.Label_InputFileUpdate)
        SectT01_Layout.addWidget(self.ProgressBar, alignment=Qt.AlignCenter)
        SectT01_Layout.addWidget(SectT01_Separator)
        SectT01_Layout.addWidget(self.Button_Review, alignment=Qt.AlignHCenter | Qt.AlignTop)
        SectT01.setLayout(SectT01_Layout)
        TopLayout.addWidget(SectT01, 20)
        # --------------------------------------------------------------------------------------------------------------
        # Section 02 (Top Layout, second group): Visualization & Settings
        SectT02 = QGroupBox("Visualization && Setting && Run")
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
        # Add a checkbox for offsetting the first data to zero. 
        self.CheckBox_OffsetFirstRawData = QCheckBox(f'Offset the rut depth of first raw datapoint to zero')
        self.CheckBox_OffsetFirstRawData.setChecked(True)
        self.CheckBox_OffsetFirstRawData.setEnabled(False)
        SectT02_FormLayout.addRow(self.CheckBox_OffsetFirstRawData)
        # Create a separator. 
        SectT02_Separator = QFrame()
        SectT02_Separator.setFrameShape(QFrame.HLine)
        SectT02_Separator.setFrameShadow(QFrame.Sunken)
        SectT02_FormLayout.addRow(SectT02_Separator)
        SectT02_Layout.addLayout(SectT02_FormLayout)
        # ------------- Setting part ------------------------
        SectT02_HLayout = QHBoxLayout()
        SectT02_FormLayout_Left = QFormLayout()
        SectT02_FormLayout_Right= QFormLayout()
        self.PlotModel_ButtonGroup = QButtonGroup()
        self.PlotModel_Label = QLabel('Active plotting model:')
        self.PlotModel_Label.setEnabled(False)
        self.PlotModel_2PP = QRadioButton("Two-Part Power (2PP) model")
        self.PlotModel_2PP.setEnabled(False)
        self.PlotModel_2PP.clicked.connect(lambda: self.Function_Plot_Model_RadioButton('2PP'))
        self.PlotModel_Yin = QRadioButton("Yin et al. (2014) model")
        self.PlotModel_Yin.setEnabled(False)
        self.PlotModel_Yin.clicked.connect(lambda: self.Function_Plot_Model_RadioButton('Yin'))
        self.PlotModel_6deg = QRadioButton("6th Degree Polynomial model")
        self.PlotModel_6deg.setEnabled(False)
        self.PlotModel_6deg.clicked.connect(lambda: self.Function_Plot_Model_RadioButton('6deg'))
        self.PlotModel_2PP.setChecked(True)
        self.Results['Plot_Current_Model'] = '2PP'
        self.PlotModel_ButtonGroup.addButton(self.PlotModel_2PP)
        self.PlotModel_ButtonGroup.addButton(self.PlotModel_Yin)
        self.PlotModel_ButtonGroup.addButton(self.PlotModel_6deg)
        # Add the widgets to the layout. 
        SectT02_FormLayout_Left.addRow(self.PlotModel_Label)
        SectT02_FormLayout_Left.addRow(self.PlotModel_2PP)
        SectT02_FormLayout_Left.addRow(self.PlotModel_Yin)
        SectT02_FormLayout_Left.addRow(self.PlotModel_6deg)
        SectT02_HLayout.addLayout(SectT02_FormLayout_Left)
        # Add the Adjusted SIP option.
        self.SIPAdjusted_ButtonGroup = QButtonGroup()
        self.SIPAdjusted_Label = QLabel('SIP Calculation Method:')
        self.SIPAdjusted_Label.setEnabled(False)
        self.SIPAdjusted_Threshold = QRadioButton("Using end point at 12.5 mm")
        self.SIPAdjusted_Threshold.setEnabled(False)
        self.SIPAdjusted_Threshold.clicked.connect(lambda: self.Function_PLOT_SIPAdjusted_RadioButton('Threshold'))
        self.SIPAdjusted_MaxRut    = QRadioButton("Using end point at Max Rut")
        self.SIPAdjusted_MaxRut.setEnabled(False)
        self.SIPAdjusted_MaxRut.clicked.connect(lambda: self.Function_PLOT_SIPAdjusted_RadioButton('MaxRut'))
        self.SIPAdjusted_ButtonGroup.addButton(self.SIPAdjusted_Threshold)
        self.SIPAdjusted_ButtonGroup.addButton(self.SIPAdjusted_MaxRut)
        SectT02_FormLayout_Right.addWidget(self.SIPAdjusted_Label)
        SectT02_FormLayout_Right.addWidget(self.SIPAdjusted_MaxRut)
        SectT02_FormLayout_Right.addWidget(self.SIPAdjusted_Threshold)
        self.SIPAdjusted_MaxRut.setChecked(True)
        self.Results['Plot_Current_SIPMethod'] = 'MaxRut'
        SectT02_HLayout.addLayout(SectT02_FormLayout_Left)
        SectT02_HLayout.addLayout(SectT02_FormLayout_Right)
        SectT02_Layout.addLayout(SectT02_HLayout)
        # ------------- Setting part ------------------------
        # Create a separator.
        SectT02_Separator2 = QFrame()
        SectT02_Separator2.setFrameShape(QFrame.HLine)
        SectT02_Separator2.setFrameShadow(QFrame.Sunken)
        SectT02_Layout.addWidget(SectT02_Separator2)
        SectT02_Layout.addLayout(SectT02_FormLayout)
        # Button for Run the analysis.
        self.Button_RunAnalysis = QPushButton("Run Analysis")
        self.Button_RunAnalysis.setFont(QFont("Arial", 12, QFont.Bold))
        self.Button_RunAnalysis.clicked.connect(self.Function_Button_RunAnalysis)
        self.Button_RunAnalysis.setFixedSize(200, 50)
        self.Button_RunAnalysis.setEnabled(False)
        self.Button_RunAnalysis.setStyleSheet(
        """
        QPushButton:enabled {background-color: lightblue; color: black;}
        QPushButton:hover {background-color: lightgray;}
        QPushButton:pressed {background-color: gray;}
        QPushButton:checked {background-color: lime;}
        """)
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
        SectT02_LayoutH1 = QHBoxLayout()
        SectT02_LayoutH1.addWidget(self.Button_RunAnalysis)
        SectT02_LayoutH1.addWidget(self.Button_ResetRePlot)
        # SectT02_Layout.addWidget(self.Button_ResetRePlot, alignment=Qt.AlignHCenter)
        # SectT01_Layout.addWidget(self.Button_RunAnalysis, alignment=Qt.AlignHCenter | Qt.AlignTop)
        SectT02_Layout.addLayout(SectT02_LayoutH1)
        # Create another separator. 
        SectT02_Separator2 = QFrame()
        SectT02_Separator2.setFrameShape(QFrame.HLine)
        SectT02_Separator2.setFrameShadow(QFrame.Sunken)
        SectT02_Layout.addWidget(SectT02_Separator2)
        # Button for specify the result as outlier.
        self.Button_FailResult = QPushButton("This result is\nOutlier")
        self.Button_FailResult.setFont(QFont("Arial", 13, QFont.Bold))
        self.Button_FailResult.clicked.connect(self.Function_Button_FailResult)
        self.Button_FailResult.setFixedSize(180, 50)
        self.Button_FailResult.setEnabled(False)
        self.Button_FailResult.setStyleSheet(
        """
        QPushButton:enabled {background-color: #FFB6C1; color: black;}
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
        QPushButton:enabled {background-color: lightgreen; color: black;}
        QPushButton:hover {background-color: lightgray;}
        QPushButton:pressed {background-color: gray;}
        QPushButton:checked {background-color: lime;}
        """)
        SectT02_LayoutH2 = QHBoxLayout()
        SectT02_LayoutH2.addWidget(self.Button_AcceptResult)
        SectT02_LayoutH2.addWidget(self.Button_FailResult)
        SectT02_Layout.addLayout(SectT02_LayoutH2)

        SectT02.setLayout(SectT02_Layout)
        TopLayout.addWidget(SectT02, 30)
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
        LengthText = 40
        ST03T1_Label01 = QLabel(f'{"Test name*:".ljust(LengthText)}')
        ST03T1_Label02 = QLabel(f'{"Test date (optional):".ljust(LengthText)}')
        ST03T1_Label03 = QLabel(f'{"Test time (optional):".ljust(LengthText)}')
        ST03T1_Label04 = QLabel(f'{"Testing condition*:".ljust(LengthText)}')
        ST03T1_Label05 = QLabel(f'{"Wheel path side*:".ljust(LengthText)}')
        ST03T1_Label06 = QLabel(f'{"Target test temperature (°C):".ljust(LengthText)}')
        ST03T1_Label07 = QLabel(f'{"Avg. recorded test temperature (°C):".ljust(LengthText)}')
        ST03T1_Label08 = QLabel(f'{"Std. recorded test temperature (°C):".ljust(LengthText)}')
        ST03T1_Label09 = QLabel(f'{"B-Number (ABML specific)*:".ljust(LengthText)}')
        ST03T1_Label10 = QLabel(f'{"Lane number (optional):".ljust(LengthText)}')
        ST03T1_Label11 = QLabel(f'{"Lift location (optional):".ljust(LengthText)}')
        ST03T1_Label12 = QLabel(f'{"Technician name:".ljust(LengthText)}')
        ST03T1_Label13 = QLabel(f'{"Other comments (optional):".ljust(LengthText)}')
        ST03T1_Label14 = QLabel(f'{"State of laboratory aging*:".ljust(LengthText)}')
        self.ST03T1_LineEdit_FileName = QLineEdit()
        self.ST03T1_LineEdit_FileName.setPlaceholderText("Enter input file name here ...")
        self.ST03T1_LineEdit_FileName.setReadOnly(True)
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
        SectT03T1_FormLayout.addRow(QLabel('FileName'), self.ST03T1_LineEdit_FileName)
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
        self.AnalysisParam_Label_2PP = QLabel('For the <a href="Model_2PP">Two-Part Power (2PP)</a> model, which is developed by FHWA.')
        self.AnalysisParam_Label_2PP.setOpenExternalLinks(False)
        self.AnalysisParam_Label_2PP.linkActivated.connect(self.Function_Show_Model_Properties)
        ScrollAreaT03T2_Layout.addWidget(self.AnalysisParam_Label_2PP)
        ScrollAreaT03T2_Layout.addWidget(QLabel('Fitted model coefficients:'))
        self.ModelParam_Table = QTableWidget(7, 3)
        self.ModelParam_Table.setHorizontalHeaderLabels(["Parameter", "Value", "Comment"])
        self.ModelParam_Table.setMinimumHeight(245)
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
        self.AnalysisParam_Label_2PP = QLabel()
        self.AnalysisParam_Label_2PP.setText('For the <a href="Model_2PP">Two-Part Power (2PP)</a> model, which is developed by FHWA.')
        self.AnalysisParam_Label_2PP.setOpenExternalLinks(False)
        self.AnalysisParam_Label_2PP.linkActivated.connect(self.Function_Show_Model_Properties)
        ScrollAreaT03T3_Layout.addWidget(self.AnalysisParam_Label_2PP)
        ScrollAreaT03T3_Layout.addWidget(QLabel('Analysis parameters (results):'))
        self.AnalysisParam_Table = QTableWidget(16, 3)
        self.AnalysisParam_Table.setColumnWidth(0, 170) 
        self.AnalysisParam_Table.setColumnWidth(1, 70) 
        self.AnalysisParam_Table.setColumnWidth(2, 150) 
        self.AnalysisParam_Table.setMinimumHeight(520)
        self.AnalysisParam_Table.setHorizontalHeaderLabels(["Parameter", "Value", "Comment"])
        for i, (parameter, comment) in enumerate(zip(
            ['Max Rut Depth (mm)', 'Max Passes', 'Rutting @ 10,000 (mm)', 'Rutting @ 20,000 (mm)', 
             'Stripping rut depth (mm)', 'Stripping Number (SN)', 
             'Stripping Inflection Point (SIP)', 'SIP Y-val (mm)', 
             'Adjusted SIP (12.5 mm threshold)', 'Adjusted SIP Y-value (mm)',  
             'Creep line slope', 'Creep line intercept (mm)', 
             'Stripping line slope', 'Stripping line intercept (mm)', 
             'Adjusted stripping line slope', 'Adjusted stripping line intercept (mm)',], 
            ['Ruttting+Stripping', '', 'Rutting only', 'Rutting only', 'Stripping only', 'Boudary point', 
             '-', '-', '-', '-', 
             'Tang. line to creep phase', 'Tang. line to creep phase', 
             'Tang. line to strip. phase', 'Tang. line to strip. phase', 
             'Tang. line to strip. phase (Adjusted)', 'Tang. line to strip. phase (Adjusted)'])):
            self.AnalysisParam_Table.setItem(i, 0, QTableWidgetItem(parameter))
            self.AnalysisParam_Table.setItem(i, 1, QTableWidgetItem('Ν/Α'))
            self.AnalysisParam_Table.setItem(i, 2, QTableWidgetItem(comment))
        self.AnalysisParam_Table.setEditTriggers(QTableWidget.NoEditTriggers)          # Make Table Read-Only
        self.AnalysisParam_Table.setSelectionBehavior(QTableWidget.SelectItems)        # Select individual items
        self.AnalysisParam_Table.setSelectionMode(QTableWidget.ContiguousSelection)    # Allow selecting multiple cells
        self.AnalysisParam_Table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)     # Don't allow vertical scroll
        # Add the widgets. 
        ScrollAreaT03T3_Layout.addWidget(self.AnalysisParam_Table)
        Tab3_Layout.addWidget(ScrollAreaT03T3)
        # --------------------------------------------
        # Tab 4: Analysis results (Yin et al. model of Yin et al. 2014). 
        Tab4 = QWidget()
        Tab4_Layout = QVBoxLayout(Tab4)
        # Create a Scroll Area
        ScrollAreaT03T4 = QScrollArea()
        ScrollAreaT03T4.setWidgetResizable(True)
        ScrollContent4 = QWidget()
        ScrollAreaT03T4.setWidget(ScrollContent4)
        ScrollAreaT03T4_Layout = QVBoxLayout(ScrollContent4)
        self.AnalysisParam_Label_Yin = QLabel('For the <a href="Model_Yin">Yin et al. (2014)</a> model, which is developed by Yin et al. (2014).')
        self.AnalysisParam_Label_Yin.setOpenExternalLinks(False)
        self.AnalysisParam_Label_Yin.linkActivated.connect(self.Function_Show_Model_Properties)
        ScrollAreaT03T4_Layout.addWidget(self.AnalysisParam_Label_Yin)
        ScrollAreaT03T4_Layout.addWidget(QLabel('Analysis results:'))
        self.AnalysisParam_Yin_Table = QTableWidget(19, 3)
        self.AnalysisParam_Yin_Table.setColumnWidth(0, 170) 
        self.AnalysisParam_Yin_Table.setColumnWidth(1, 70) 
        self.AnalysisParam_Yin_Table.setColumnWidth(2, 150) 
        self.AnalysisParam_Yin_Table.setMinimumHeight(600)
        self.AnalysisParam_Yin_Table.setHorizontalHeaderLabels(["Parameter", "Value", "Comment"])
        for i, (parameter, comment) in enumerate(zip(
            ['Max Rut Depth (mm)', 'Max Passes', 'Rutting @ 10,000 (mm)', 'Rutting @ 20,000 (mm)', 
             'LCSN', 'LCST', 'Δεp @ 10,000',
             'Stripping rut depth (mm)', 'Stripping Number (SN)',
             'Stripping Inflection Point (SIP)', 'SIP Y-value (mm)', 
             'Adjusted SIP (12.5 mm threshold)', 'Adjusted SIP Y-value (mm)',  
             'Creep line slope', 'Creep line intercept (mm)', 
             'Stripping line slope', 'Stripping line intercept (mm)', 
             'Adjusted stripping line slope', 'Adjusted stripping line intercept (mm)', ], 
            ['Ruttting+Stripping', '', 'Rutting only', 'Rutting only', 
             '-', '-', 'Rutting only',
             'Stripping only', 'Boudary point', '-', '-', '-', '-', 
             'Tang. line to creep phase', 'Tang. line to creep phase', 
             'Tang. line to strip. phase', 'Tang. line to strip. phase', 
             'Tang. line to strip. phase (Adjusted)', 'Tang. line to strip. phase (Adjusted)'])):
            self.AnalysisParam_Yin_Table.setItem(i, 0, QTableWidgetItem(parameter))
            self.AnalysisParam_Yin_Table.setItem(i, 1, QTableWidgetItem('Ν/Α'))
            self.AnalysisParam_Yin_Table.setItem(i, 2, QTableWidgetItem(comment))
        self.AnalysisParam_Yin_Table.setEditTriggers(QTableWidget.NoEditTriggers)          # Make Table Read-Only
        self.AnalysisParam_Yin_Table.setSelectionBehavior(QTableWidget.SelectItems)        # Select individual items
        self.AnalysisParam_Yin_Table.setSelectionMode(QTableWidget.ContiguousSelection)    # Allow selecting multiple cells
        self.AnalysisParam_Yin_Table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)     # Don't allow vertical scroll
        ScrollAreaT03T4_Layout.addWidget(self.AnalysisParam_Yin_Table)
        ScrollAreaT03T4_Layout.addWidget(QLabel('Fitted model coefficients:'))
        self.ModelParam_Yin_Table = QTableWidget(9, 3)
        self.ModelParam_Yin_Table.setColumnWidth(0, 170) 
        self.ModelParam_Yin_Table.setColumnWidth(1, 70) 
        self.ModelParam_Yin_Table.setColumnWidth(2, 150) 
        self.ModelParam_Yin_Table.setMinimumHeight(300)
        self.ModelParam_Yin_Table.setHorizontalHeaderLabels(["Parameter", "Value", "Comment"])
        for i, (parameter, comment) in enumerate(zip(
            ['ρ', 'LCult', 'β', 'Rut∞', 'α', 'λ', 'ε0', 'θ', 'SN'],
            ['Step 1 model (SN estimation)', 'Step 1 model (SN estimation)', 'Step 1 model (SN estimation)', 
             'Step 2 model (corrected rut depth)', 'Step 2 model (corrected rut depth)', 
             'Step 2 model (corrected rut depth)', 
             'Step 3 model (stripping)', 'Step 3 model (stripping)', 'Step 3 model (stripping)'])):
            self.ModelParam_Yin_Table.setItem(i, 0, QTableWidgetItem(parameter))
            self.ModelParam_Yin_Table.setItem(i, 1, QTableWidgetItem('Ν/Α'))
            self.ModelParam_Yin_Table.setItem(i, 2, QTableWidgetItem(comment))
        self.ModelParam_Yin_Table.setEditTriggers(QTableWidget.NoEditTriggers)          # Make Table Read-Only
        self.ModelParam_Yin_Table.setSelectionBehavior(QTableWidget.SelectItems)        # Select individual items
        self.ModelParam_Yin_Table.setSelectionMode(QTableWidget.ContiguousSelection)    # Allow selecting multiple cells
        self.ModelParam_Yin_Table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)     # Don't allow vertical scroll
        ScrollAreaT03T4_Layout.addWidget(self.ModelParam_Yin_Table)
        # ScrollAreaT03T4_Layout.addWidget()
        Tab4_Layout.addWidget(ScrollAreaT03T4)
        # --------------------------------------------
        # Tab 5: Analysis results (6th degree polynomial model). 
        Tab5 = QWidget()
        Tab5_Layout = QVBoxLayout(Tab5)
        # Create a Scroll Area
        ScrollAreaT03T5 = QScrollArea()
        ScrollAreaT03T5.setWidgetResizable(True)
        ScrollContent5 = QWidget()
        ScrollAreaT03T5.setWidget(ScrollContent5)
        ScrollAreaT03T5_Layout = QVBoxLayout(ScrollContent5)
        self.AnalysisParam_Label_6deg = QLabel('For the <a href="Model_6deg">6th Degree Polynomial</a> model.')
        self.AnalysisParam_Label_6deg.setOpenExternalLinks(False)
        self.AnalysisParam_Label_6deg.linkActivated.connect(self.Function_Show_Model_Properties)
        ScrollAreaT03T5_Layout.addWidget(self.AnalysisParam_Label_6deg)
        ScrollAreaT03T5_Layout.addWidget(QLabel('Analysis results:'))
        self.AnalysisParam_6deg_Table = QTableWidget(8, 3)
        self.AnalysisParam_6deg_Table.setColumnWidth(0, 170) 
        self.AnalysisParam_6deg_Table.setColumnWidth(1, 70) 
        self.AnalysisParam_6deg_Table.setColumnWidth(2, 150) 
        self.AnalysisParam_6deg_Table.setMinimumHeight(270)
        self.AnalysisParam_6deg_Table.setHorizontalHeaderLabels(["Parameter", "Value", "Comment"])
        for i, (parameter, comment) in enumerate(zip(
            ['Max Rut Depth (mm)', 'Max Passes', 'Rutting @ 10,000 (mm)', 'Rutting @ 20,000 (mm)', 
             'Stripping rut depth (mm)', 'Stripping Number (SN)',
             'Creep line slope', 'Creep line intercept (mm)'], 
            ['Ruttting+Stripping', '', 'Rutting only', 'Rutting only', 
             'Stripping only', 'Boudary point', 
             'Tang. line to creep phase', 'Tang. line to creep phase'])):
            self.AnalysisParam_6deg_Table.setItem(i, 0, QTableWidgetItem(parameter))
            self.AnalysisParam_6deg_Table.setItem(i, 1, QTableWidgetItem('Ν/Α'))
            self.AnalysisParam_6deg_Table.setItem(i, 2, QTableWidgetItem(comment))
        self.AnalysisParam_6deg_Table.setEditTriggers(QTableWidget.NoEditTriggers)          # Make Table Read-Only
        self.AnalysisParam_6deg_Table.setSelectionBehavior(QTableWidget.SelectItems)        # Select individual items
        self.AnalysisParam_6deg_Table.setSelectionMode(QTableWidget.ContiguousSelection)    # Allow selecting multiple cells
        self.AnalysisParam_6deg_Table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)     # Don't allow vertical scroll
        ScrollAreaT03T5_Layout.addWidget(self.AnalysisParam_6deg_Table)
        ScrollAreaT03T5_Layout.addWidget(QLabel('Fitted model coefficients:'))
        self.ModelParam_6deg_Table = QTableWidget(7, 3)
        self.ModelParam_6deg_Table.setColumnWidth(0, 170) 
        self.ModelParam_6deg_Table.setColumnWidth(1, 70) 
        self.ModelParam_6deg_Table.setColumnWidth(2, 150) 
        self.ModelParam_6deg_Table.setMinimumHeight(245)
        self.ModelParam_6deg_Table.setHorizontalHeaderLabels(["Parameter", "Value", "Comment"])
        for i, (parameter, comment) in enumerate(zip(
            ['a0', 'a1', 'a2', 'a3', 'a4', 'a5', 'a6'], 
            ['Polynomial coefficients', 'Polynomial coefficients', 'Polynomial coefficients', 'Polynomial coefficients', 
             'Polynomial coefficients', 'Polynomial coefficients', 'Polynomial coefficients'])):
            self.ModelParam_6deg_Table.setItem(i, 0, QTableWidgetItem(parameter))
            self.ModelParam_6deg_Table.setItem(i, 1, QTableWidgetItem('Ν/Α'))
            self.ModelParam_6deg_Table.setItem(i, 2, QTableWidgetItem(comment))
        self.ModelParam_6deg_Table.setEditTriggers(QTableWidget.NoEditTriggers)          # Make Table Read-Only
        self.ModelParam_6deg_Table.setSelectionBehavior(QTableWidget.SelectItems)        # Select individual items
        self.ModelParam_6deg_Table.setSelectionMode(QTableWidget.ContiguousSelection)    # Allow selecting multiple cells
        self.ModelParam_6deg_Table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)     # Don't allow vertical scroll
        ScrollAreaT03T5_Layout.addWidget(self.ModelParam_6deg_Table)
        # ScrollAreaT03T5_Layout.addWidget()
        Tab5_Layout.addWidget(ScrollAreaT03T5)
        # --------------------------------------------
        # Add tabs to QTabWidget
        self.SectT03_TabWidget.addTab(Tab1, "General")
        self.SectT03_TabWidget.addTab(Tab2, "Fitted Model (2PP)")
        self.SectT03_TabWidget.addTab(Tab3, "Analysis Params (2PP)")
        self.SectT03_TabWidget.addTab(Tab4, "Analysis Params (Yin et al. model)")
        self.SectT03_TabWidget.addTab(Tab5, "Analysis Params (6th deg. Polynomial)")
        SectT03_Layout.addWidget(self.SectT03_TabWidget)
        SectT03.setLayout(SectT03_Layout)
        # --------------------------------------    
        TopLayout.addWidget(SectT03, 40)
        layout.addLayout(TopLayout, 45)
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
        # ---------------------------- Menu bars------------------------------------------------------------------------
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
        self.Button_Review.setEnabled(False)
        self.Button_ResetRePlot.setEnabled(True)
        self.Button_FailResult.setEnabled(True)
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
        self.Button_Review.setEnabled(False)
        self.Menu_File_ImportFiles.setEnabled(False)
        self.Menu_File_ImportCopy.setEnabled(False)
        self.Menu_File_Template.setEnabled(False)
        self.Button_FailResult.setEnabled(True)
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
        self.Button_RunAnalysis.setEnabled(True)
        self.Button_FailResult.setEnabled(True)
        self.Button_AcceptResult.setEnabled(False)
        self.PlotModel_Label.setEnabled(False)
        self.PlotModel_2PP.setEnabled(False)
        self.PlotModel_Yin.setEnabled(False)
        self.PlotModel_6deg.setEnabled(False)
        self.SIPAdjusted_Label.setEnabled(False)
        self.SIPAdjusted_MaxRut.setEnabled(False)
        self.SIPAdjusted_Threshold.setEnabled(False)
        # Plot the raw data. 
        self.Results['Plot_Level'] = 0                  # Reset the plot level to only raw data. 
        self.Function_Plotter()
        # Clear the tables in the results section (different tabs).
        self.Function_Clear_Result_Tables()
    # ------------------------------------------------------------------------------------------------------------------
    def Function_Plotter(self):
        """
        This function plots the raw data and results on the main axes
        """
        # Extract some information for plotting the raw data. 
        Passes   = self.Results['Passes']
        RutDepth = self.Results['RutDepth']
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
        # Plotting the raw data. 
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
        # ------------------------------------------
        # Plotting only the raw data. 
        if self.Results['Plot_Level'] == 0: 
            if Passes.max() <= 20000:
                self.axes.set_xlim([0, 20000])
            self.axes.set_ylim([0, RutDepth.max() * 1.05])
            self.axes.legend(fontsize=12, loc='upper left', fancybox=True)
        # ------------------------------------------
        # Plotting the raw data and selected model. 
        elif self.Results['Plot_Level'] == 1:
            if self.Results['Plot_Current_Model'] == '2PP':
                [a, b] = self.Results['2PP']['Rutting_PowerModel_Coeff']
                Xp1 = np.linspace(0, self.Results['2PP']['Stripping_Number'], num=1000)
                Xp2 = np.linspace(self.Results['2PP']['Stripping_Number'], 20000, num=1000)
                Yp1 = ModelPower(Xp1, a, b)
                Yp2 = ModelPower(Xp2, a, b)
                self.axes.plot(Xp1, Yp1, ls='-',  lw=1.5, color='k', label='Power Model on Creep Phase')
                self.axes.plot(Xp2, Yp2, ls='--', lw=1.5, color='k', label='Power Model extrapolation')
                self.axes.plot(self.Results['2PP']['Xmodel'], self.Results['2PP']['Ymodel'], 
                               ls='--', lw=1.5, color='b', label='Full model')
                self.axes.plot([0, 20000], np.polyval(self.Results['2PP']['CreepLine'], [0, 20000]), 
                               ls='--', color='r', lw=0.5)
                self.axes.plot([0, 20000], np.polyval(self.Results['2PP']['TangentLine'], [0, 20000]), 
                               ls='--', color='r', lw=0.5)
                self.axes.plot(self.Results['2PP']['Stripping_Number'], 
                               ModelPower(self.Results['2PP']['Stripping_Number'], a, b), 
                               ls='', marker='*', ms=12, color='b', label='Stripping Number')
                self.axes.plot(self.Results['2PP']['SIP'], self.Results['2PP']['SIP_Yval_mm'], 
                               ls='', marker='X', ms=12, color='m', 
                            label='SIP point (End point at max rutting)')
                self.axes.legend()
                if Passes.max() <= 20000:
                    self.axes.set_xlim([0, 20000])
                self.axes.set_ylim([0, RutDepth.max() * 1.05])
            # ------------------------------------------------
            elif self.Results['Plot_Current_Model'] == 'Yin':
                self.axes.plot(self.Results['Yin']['Xmodel'], self.Results['Yin']['Ymodel'], 
                               ls='--', lw=1.5, color='b', label='Yin et al. model (Step 1)')
                self.axes.plot(self.Results['Yin']['Xmodel'], 
                               TsengLyttonModel(self.Results['Yin']['Xmodel'],
                                                self.Results['Yin']['Rutting_Step2_Coeff'][0],
                                                self.Results['Yin']['Rutting_Step2_Coeff'][1],
                                                self.Results['Yin']['Rutting_Step2_Coeff'][2]), 
                               ls='-.', lw=1.0, color='k', label='Yin et al. model (Step 2)')
                self.axes.plot([0, 20000], np.polyval(self.Results['Yin']['CreepLine'], [0, 20000]), 
                               ls='--', color='r', lw=0.5)
                self.axes.plot([0, 20000], np.polyval(self.Results['Yin']['TangentLine'], [0, 20000]), 
                               ls='--', color='r', lw=0.5)
                self.axes.plot(self.Results['Yin']['Stripping_Number'], 
                               TsengLyttonModel(self.Results['Yin']['Stripping_Number'],
                                                self.Results['Yin']['Rutting_Step2_Coeff'][0],
                                                self.Results['Yin']['Rutting_Step2_Coeff'][1],
                                                self.Results['Yin']['Rutting_Step2_Coeff'][2]), 
                               ls='', marker='*', ms=12, color='b', label='Stripping Number')
                self.axes.plot(self.Results['Yin']['SIP'], self.Results['Yin']['SIP_Yval_mm'], 
                               ls='', marker='X', ms=12, color='m', 
                            label='SIP point (End point at max rutting)')
                self.axes.legend()
                if Passes.max() <= 20000:
                    self.axes.set_xlim([0, 20000])
                self.axes.set_ylim([0, max([RutDepth.max(), self.Results['6deg']['Ymodel'].max()]) * 1.05])
            # ------------------------------------------------
            elif self.Results['Plot_Current_Model'] == '6deg':
                self.axes.plot(self.Results['6deg']['Xmodel'], self.Results['6deg']['Ymodel'], 
                               ls='--', lw=1.5, color='b', label='6th degree polynomial model')
                self.axes.plot([0, 20000], np.polyval(self.Results['6deg']['CreepLine'], [0, 20000]), 
                               ls='--', color='r', lw=0.5, label='Creep line')
                self.axes.plot(self.Results['6deg']['Stripping_Number'], 
                               np.polyval(self.Results['6deg']['Rutting_6degPolynomial_Coeff'], 
                                          self.Results['6deg']['Stripping_Number']), 
                               ls='', marker='*', ms=12, color='b', label='Stripping Number')
                self.axes.legend()
                if Passes.max() <= 20000:
                    self.axes.set_xlim([0, 20000])
                self.axes.set_ylim([0, max([RutDepth.max(), self.Results['6deg']['Ymodel'].max()]) * 1.05])
        # ------------------------------------------------
        # Plotting the raw data and selected model to calculate the adjusted SIP using the threshold value of 12.5 mm. 
        elif self.Results['Plot_Level'] == 2: 
            if self.Results['Plot_Current_Model'] == '2PP':
                if np.isnan(self.Results['2PP']['SIP_Adj']):
                    pass
                else:
                    # Extract the information. 
                    [a, b] = self.Results['2PP']['Rutting_PowerModel_Coeff']
                    [alpha, beta, gamma, Phi] = self.Results['2PP']['Rutting_PowerModel_Part2_Coeff']
                    SN = self.Results['2PP']['Stripping_Number']
                    X_Threshold = np.exp(np.log((12.5 - Phi) / alpha) / beta) + gamma
                    Xmax = (int(X_Threshold * 1.05 / 1000) + 1) * 1000
                    XX  = np.linspace(0, Xmax, num=20001)
                    YY1 = a * (XX ** b)
                    YY2 = alpha * (XX - gamma) ** beta + Phi
                    YY  = YY1.copy()
                    YY[XX > SN] = YY2[XX > SN]
                    Xp1 = np.linspace(0, SN, num=1000)
                    Xp2 = np.linspace(SN, 20000, num=1000)
                    Yp1 = ModelPower(Xp1, a, b)
                    Yp2 = ModelPower(Xp2, a, b)
                    self.axes.plot(Xp1, Yp1, ls='-',  lw=1.5, color='k', label='Power Model on Creep Phase')
                    self.axes.plot(Xp2, Yp2, ls='--', lw=1.5, color='k', label='Power Model extrapolation')
                    self.axes.plot(XX, YY, ls='--', lw=1.5, color='b', label='Full model')
                    self.axes.plot([0, Xmax], np.polyval(self.Results['2PP']['CreepLine'], [0, Xmax]), 
                                   ls='--', color='r', lw=0.5)
                    self.axes.plot([0, Xmax], np.polyval(self.Results['2PP']['TangentLine_Adj'], [0, Xmax]), 
                                   ls='--', color='r', lw=0.5)
                    self.axes.plot(SN, ModelPower(SN, a, b), 
                                   ls='', marker='*', ms=12, color='b', label='Stripping Number')
                    self.axes.plot(self.Results['2PP']['SIP_Adj'], self.Results['2PP']['SIP_Adj_Yval_mm'], 
                                   ls='', marker='X', ms=12, color='m', 
                                label='SIP point (End point at 12.5 mm)')
                    self.axes.plot([0, X_Threshold], [12.5, 12.5], ls=':', lw=0.5, color='k', label='12.5 mm threshold')
                    self.axes.legend(loc='upper left')
                    if Passes.max() <= 20000:
                        self.axes.set_xlim([0, 20000])
                    if Xmax > 20000:
                        self.axes.set_xlim([0, Xmax])
                    self.axes.set_ylim([0, max([RutDepth.max(), YY.max(), 12.5]) * 1.05])
            # ------------------------------------------------
            elif self.Results['Plot_Current_Model'] == 'Yin':
                Step1Coeff = self.Results['Yin']['Rutting_Step1_Coeff']
                X_Threshold = Step1Coeff[1] / np.exp((12.5 / Step1Coeff[0]) ** (-Step1Coeff[2]))
                Xmax = (int(X_Threshold * 1.05 / 1000) + 1) * 1000
                XX = np.linspace(0, Xmax, num=20001)
                YY = YinModel(XX, Step1Coeff[0], Step1Coeff[1], Step1Coeff[2])
                self.axes.plot(XX, YY, ls='--', lw=1.5, color='b', label='Yin et al. model (Step 1)')
                self.axes.plot(XX, 
                               TsengLyttonModel(XX,
                                                self.Results['Yin']['Rutting_Step2_Coeff'][0],
                                                self.Results['Yin']['Rutting_Step2_Coeff'][1],
                                                self.Results['Yin']['Rutting_Step2_Coeff'][2]), 
                               ls='-.', lw=1.0, color='k', label='Yin et al. model (Step 2)')
                self.axes.plot([0, Xmax], np.polyval(self.Results['Yin']['CreepLine'], [0, Xmax]), 
                               ls='--', color='r', lw=0.5)
                self.axes.plot([0, Xmax], np.polyval(self.Results['Yin']['TangentLine_Adj'], [0, Xmax]), 
                               ls='--', color='r', lw=0.5)
                self.axes.plot(self.Results['Yin']['Stripping_Number'], 
                               TsengLyttonModel(self.Results['Yin']['Stripping_Number'],
                                                self.Results['Yin']['Rutting_Step2_Coeff'][0],
                                                self.Results['Yin']['Rutting_Step2_Coeff'][1],
                                                self.Results['Yin']['Rutting_Step2_Coeff'][2]), 
                               ls='', marker='*', ms=12, color='b', label='Stripping Number')
                self.axes.plot(self.Results['Yin']['SIP_Adj'], self.Results['Yin']['SIP_Adj_Yval_mm'], 
                               ls='', marker='X', ms=12, color='m', 
                            label='SIP point (End point at 12.5 mm)')
                self.axes.plot([0, X_Threshold], [12.5, 12.5], ls=':', lw=0.5, color='k', label='12.5 mm threshold')
                self.axes.legend(loc='upper left')
                if Passes.max() <= 20000:
                    self.axes.set_xlim([0, 20000])
                if Xmax > 20000:
                    self.axes.set_xlim([0, Xmax])
                self.axes.set_ylim([0, max([RutDepth.max(), YY.max(), 12.5]) * 1.05])
            # ------------------------------------------------
            elif self.Results['Plot_Current_Model'] == '6deg':
                self.axes.plot(self.Results['6deg']['Xmodel'], self.Results['6deg']['Ymodel'], 
                               ls='--', lw=1.5, color='b', label='6th degree polynomial model')
                self.axes.plot([0, 20000], np.polyval(self.Results['6deg']['CreepLine'], [0, 20000]), 
                               ls='--', color='r', lw=0.5, label='Creep line')
                self.axes.plot(self.Results['6deg']['Stripping_Number'], 
                               np.polyval(self.Results['6deg']['Rutting_6degPolynomial_Coeff'], 
                                          self.Results['6deg']['Stripping_Number']), 
                               ls='', marker='*', ms=12, color='b', label='Stripping Number')
                self.axes.legend()
                if Passes.max() <= 20000:
                    self.axes.set_xlim([0, 20000])
                self.axes.set_ylim([0, max([RutDepth.max(), self.Results['6deg']['Ymodel'].max()]) * 1.05])
        self.fig.set_constrained_layout(True)
        self.canvas.draw()
    # ------------------------------------------------------------------------------------------------------------------
    def Function_Clear_Result_Tables(self):
        """
        This function simply clears the tables in the results sections (different tabs). 
        """
        # Clear the results (2PP model).
        self.SectT03_TabWidget.setCurrentIndex(0)
        for i, (parameter, comment) in enumerate(zip(['a', 'b', 'SN', 'α', 'β', 'γ', 'Φ'], 
                                                     ['1st model', '1st model', 'Boundary point', '2nd model', 
                                                      '2nd model', '2nd model', '2nd model'])):
            self.ModelParam_Table.setItem(i, 0, QTableWidgetItem(parameter))
            self.ModelParam_Table.setItem(i, 1, QTableWidgetItem('Ν/Α'))
            self.ModelParam_Table.setItem(i, 2, QTableWidgetItem(comment))
        for i, (parameter, comment) in enumerate(zip(
            ['Max Rut Depth (mm)', 'Max Passes', 'Rutting @ 10,000 (mm)', 'Rutting @ 20,000 (mm)', 
             'Stripping rut depth (mm)', 'Stripping Number (SN)', 
             'Stripping Inflection Point (SIP)', 'SIP Y-val (mm)', 
             'Adjusted SIP (12.5 mm threshold)', 'Adjusted SIP Y-value (mm)',  
             'Creep line slope', 'Creep line intercept (mm)', 
             'Stripping line slope', 'Stripping line intercept (mm)', 
             'Adjusted stripping line slope', 'Adjusted stripping line intercept (mm)',], 
            ['Ruttting+Stripping', '', 'Rutting only', 'Rutting only', 'Stripping only', 'Boudary point', 
             '-', '-', '-', '-', 
             'Tang. line to creep phase', 'Tang. line to creep phase', 
             'Tang. line to strip. phase', 'Tang. line to strip. phase', 
             'Tang. line to strip. phase (Adjusted)', 'Tang. line to strip. phase (Adjusted)'])):
            self.AnalysisParam_Table.setItem(i, 0, QTableWidgetItem(parameter))
            self.AnalysisParam_Table.setItem(i, 1, QTableWidgetItem('Ν/Α'))
            self.AnalysisParam_Table.setItem(i, 2, QTableWidgetItem(comment))
        # ---------------------------------------
        # Clear the results (Yin et al. model).
        for i, (parameter, comment) in enumerate(zip(
            ['Max Rut Depth (mm)', 'Max Passes', 'Rutting @ 10,000 (mm)', 'Rutting @ 20,000 (mm)', 
             'LCSN', 'LCST', 'Δεp @ 10,000',
             'Stripping rut depth (mm)', 'Stripping Number (SN)',
             'Stripping Inflection Point (SIP)', 'SIP Y-value (mm)', 
             'Adjusted SIP (12.5 mm threshold)', 'Adjusted SIP Y-value (mm)',  
             'Creep line slope', 'Creep line intercept (mm)', 
             'Stripping line slope', 'Stripping line intercept (mm)', 
             'Adjusted stripping line slope', 'Adjusted stripping line intercept (mm)', ], 
            ['Ruttting+Stripping', '', 'Rutting only', 'Rutting only', 
             '-', '-', 'Rutting only',
             'Stripping only', 'Boudary point', '-', '-', '-', '-', 
             'Tang. line to creep phase', 'Tang. line to creep phase', 
             'Tang. line to strip. phase', 'Tang. line to strip. phase', 
             'Tang. line to strip. phase (Adjusted)', 'Tang. line to strip. phase (Adjusted)'])):
            self.AnalysisParam_Yin_Table.setItem(i, 0, QTableWidgetItem(parameter))
            self.AnalysisParam_Yin_Table.setItem(i, 1, QTableWidgetItem('Ν/Α'))
            self.AnalysisParam_Yin_Table.setItem(i, 2, QTableWidgetItem(comment))
        for i, (parameter, comment) in enumerate(zip(
            ['ρ', 'LCult', 'β', 'Rut∞', 'α', 'λ', 'ε0', 'θ', 'SN'],
            ['Step 1 model (SN estimation)', 'Step 1 model (SN estimation)', 'Step 1 model (SN estimation)', 
             'Step 2 model (corrected rut depth)', 'Step 2 model (corrected rut depth)', 
             'Step 2 model (corrected rut depth)', 
             'Step 3 model (stripping)', 'Step 3 model (stripping)', 'Step 3 model (stripping)'])):
            self.ModelParam_Yin_Table.setItem(i, 0, QTableWidgetItem(parameter))
            self.ModelParam_Yin_Table.setItem(i, 1, QTableWidgetItem('Ν/Α'))
            self.ModelParam_Yin_Table.setItem(i, 2, QTableWidgetItem(comment))
        # ---------------------------------------
        # Clear the results (6th degree polynomial model).
        for i, (parameter, comment) in enumerate(zip(
            ['Max Rut Depth (mm)', 'Max Passes', 'Rutting @ 10,000 (mm)', 'Rutting @ 20,000 (mm)', 
             'Stripping rut depth (mm)', 'Stripping Number (SN)',
             'Creep line slope', 'Creep line intercept (mm)'], 
            ['Ruttting+Stripping', '', 'Rutting only', 'Rutting only', 
             'Stripping only', 'Boudary point', 
             'Tang. line to creep phase', 'Tang. line to creep phase'])):
            self.AnalysisParam_6deg_Table.setItem(i, 0, QTableWidgetItem(parameter))
            self.AnalysisParam_6deg_Table.setItem(i, 1, QTableWidgetItem('Ν/Α'))
            self.AnalysisParam_6deg_Table.setItem(i, 2, QTableWidgetItem(comment))
        for i, (parameter, comment) in enumerate(zip(
            ['a0', 'a1', 'a2', 'a3', 'a4', 'a5', 'a6'], 
            ['Polynomial coefficients', 'Polynomial coefficients', 'Polynomial coefficients', 'Polynomial coefficients', 
             'Polynomial coefficients', 'Polynomial coefficients', 'Polynomial coefficients'])):
            self.ModelParam_6deg_Table.setItem(i, 0, QTableWidgetItem(parameter))
            self.ModelParam_6deg_Table.setItem(i, 1, QTableWidgetItem('Ν/Α'))
            self.ModelParam_6deg_Table.setItem(i, 2, QTableWidgetItem(comment))
        # Return Nothing. 
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
        self.PlotModel_Label.setEnabled(True)
        self.PlotModel_2PP.setEnabled(True)
        self.PlotModel_Yin.setEnabled(True)
        self.PlotModel_6deg.setEnabled(True)
        self.SIPAdjusted_Label.setEnabled(True)
        self.SIPAdjusted_MaxRut.setEnabled(True)
        self.SIPAdjusted_Threshold.setEnabled(True)
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
        self.Results['Plot_Level'] = 1          # Plot the raw data and fitted model. 
        self.Function_Plotter()
        # ----------------------------------------------------------------------------
        # Update the results section. 
        self.Function_Update_Model_Fit_Analysis_Parameters()
        # Deactivate the Run analysis button. 
        self.Button_RunAnalysis.setEnabled(False)
        return
    # ------------------------------------------------------------------------------------------------------------------
    def Function_Update_General_Information(self):
        """
        This function updates the general information of the project after entering. 
        """
        self.ST03T1_LineEdit_FileName.setText(os.path.splitext(os.path.basename(self.CurrentFileList[self.CurrentFileIndex]))[0])
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
        self.ST03T1_LineEdit_BNumber.setText("")
        self.ST03T1_DropDown_LabAging.setCurrentIndex(0)
        self.ST03T1_LineEdit_OtherComments.setText("")
        self.ST03T1_DropDown_LiftLocation.setCurrentIndex(0)
        self.ST03T1_LineEdit_LaneNumber.setText("")
    # ------------------------------------------------------------------------------------------------------------------
    def Function_Update_Model_Fit_Analysis_Parameters(self):
        """
        This function updates the tables in the result tabs for model fitting parameters and analysis results. 
        """
        # For the 2PP model. 
        # Fill for the first part power model. 
        self.ModelParam_Table.setItem(
            0, 1, QTableWidgetItem(f'{self.Results["2PP"]["Rutting_PowerModel_Coeff"][0]:.6f}'))
        self.ModelParam_Table.setItem(
            1, 1, QTableWidgetItem(f'{self.Results["2PP"]["Rutting_PowerModel_Coeff"][1]:.6f}'))
        # Fill the table for the Stripping number point (boundary point).
        self.ModelParam_Table.setItem(
            2, 1, QTableWidgetItem(f'{self.Results["2PP"]["Stripping_Number"]:.2f}'))
        # Fill the table for the second part power model. 
        self.ModelParam_Table.setItem(
            3, 1, QTableWidgetItem(f'{self.Results["2PP"]["Rutting_PowerModel_Part2_Coeff"][0]:.6e}'))
        self.ModelParam_Table.setItem(
            4, 1, QTableWidgetItem(f'{self.Results["2PP"]["Rutting_PowerModel_Part2_Coeff"][1]:.6f}'))
        self.ModelParam_Table.setItem(
            5, 1, QTableWidgetItem(f'{self.Results["2PP"]["Rutting_PowerModel_Part2_Coeff"][2]:.4f}'))
        self.ModelParam_Table.setItem(
            6, 1, QTableWidgetItem(f'{self.Results["2PP"]["Rutting_PowerModel_Part2_Coeff"][3]:.6f}'))
        # Fill the analysis results. 
        self.AnalysisParam_Table.setItem(
            0, 1, QTableWidgetItem(f'{self.Results["RutDepth"].max():.3f}'))
        self.AnalysisParam_Table.setItem(
            1, 1, QTableWidgetItem(f'{self.Results["Passes"].max():d}'))
        self.AnalysisParam_Table.setItem(
            2, 1, QTableWidgetItem(f'{self.Results["2PP"]["Rutting@10k_mm"]:.3f}'))
        self.AnalysisParam_Table.setItem(
            3, 1, QTableWidgetItem(f'{self.Results["2PP"]["Rutting@20k_mm"]:.3f}'))
        self.AnalysisParam_Table.setItem(
            4, 1, QTableWidgetItem(f'{self.Results["2PP"]["Stripping_Rutting_mm"]:.3f}'))
        self.AnalysisParam_Table.setItem(
            5, 1, QTableWidgetItem(f'{self.Results["2PP"]["Stripping_Number"]:.2f}'))        
        self.AnalysisParam_Table.setItem(
            6, 1, QTableWidgetItem(f'{self.Results["2PP"]["SIP"]:.2f}'))
        self.AnalysisParam_Table.setItem(
            7, 1, QTableWidgetItem(f'{self.Results["2PP"]["SIP_Yval_mm"]:.3f}'))
        self.AnalysisParam_Table.setItem(
            8, 1, QTableWidgetItem(f'{self.Results["2PP"]["SIP_Adj"]:.2f}'))
        self.AnalysisParam_Table.setItem(
            9, 1, QTableWidgetItem(f'{self.Results["2PP"]["SIP_Adj_Yval_mm"]:.3f}'))
        self.AnalysisParam_Table.setItem(
            10, 1, QTableWidgetItem(f'{self.Results["2PP"]["CreepLine"][0]:.3e}'))
        self.AnalysisParam_Table.setItem(
            11, 1, QTableWidgetItem(f'{self.Results["2PP"]["CreepLine"][1]:.2f}'))
        self.AnalysisParam_Table.setItem(
            12, 1, QTableWidgetItem(f'{self.Results["2PP"]["TangentLine"][0]:.3e}'))
        self.AnalysisParam_Table.setItem(
            13, 1, QTableWidgetItem(f'{self.Results["2PP"]["TangentLine"][0]:.2f}'))
        self.AnalysisParam_Table.setItem(
            14, 1, QTableWidgetItem(f'{self.Results["2PP"]["TangentLine_Adj"][0]:.3e}'))
        self.AnalysisParam_Table.setItem(
            15, 1, QTableWidgetItem(f'{self.Results["2PP"]["TangentLine_Adj"][0]:.2f}'))
        # ------------------------------------------------------------
        # For the Yin model. 
        # Model parameters. 
        self.ModelParam_Yin_Table.setItem(
            0, 1, QTableWidgetItem(f'{self.Results["Yin"]["Rutting_Step1_Coeff"][0]:.6f}'))
        self.ModelParam_Yin_Table.setItem(
            1, 1, QTableWidgetItem(f'{self.Results["Yin"]["Rutting_Step1_Coeff"][1]:.6f}'))
        self.ModelParam_Yin_Table.setItem(
            2, 1, QTableWidgetItem(f'{self.Results["Yin"]["Rutting_Step1_Coeff"][2]:.6f}'))
        self.ModelParam_Yin_Table.setItem(
            3, 1, QTableWidgetItem(f'{self.Results["Yin"]["Rutting_Step2_Coeff"][0]:.6f}'))
        self.ModelParam_Yin_Table.setItem(
            4, 1, QTableWidgetItem(f'{self.Results["Yin"]["Rutting_Step2_Coeff"][1]:.6f}'))
        self.ModelParam_Yin_Table.setItem(
            5, 1, QTableWidgetItem(f'{self.Results["Yin"]["Rutting_Step2_Coeff"][2]:.6f}'))
        self.ModelParam_Yin_Table.setItem(
            6, 1, QTableWidgetItem(f'{self.Results["Yin"]["Rutting_Step3_Coeff"][0]:.6f}'))
        self.ModelParam_Yin_Table.setItem(
            7, 1, QTableWidgetItem(f'{self.Results["Yin"]["Rutting_Step3_Coeff"][1]:.6f}'))
        self.ModelParam_Yin_Table.setItem(
            8, 1, QTableWidgetItem(f'{self.Results["Yin"]["Stripping_Number"]:.2f}'))
        # Analysis parameters. 
        self.AnalysisParam_Yin_Table.setItem(
            0, 1, QTableWidgetItem(f'{self.Results["Yin"]["Maximum_Rutting_mm"]:.3f}'))
        self.AnalysisParam_Yin_Table.setItem(
            1, 1, QTableWidgetItem(f'{self.Results["Yin"]["Maximum_Passes"]:d}'))
        self.AnalysisParam_Yin_Table.setItem(
            2, 1, QTableWidgetItem(f'{self.Results["Yin"]["Rutting@10k_mm"]:.3f}'))
        self.AnalysisParam_Yin_Table.setItem(
            3, 1, QTableWidgetItem(f'{self.Results["Yin"]["Rutting@20k_mm"]:.3f}'))
        self.AnalysisParam_Yin_Table.setItem(
            4, 1, QTableWidgetItem(f'{self.Results["Yin"]["LCSN"]:.2f}'))
        self.AnalysisParam_Yin_Table.setItem(
            5, 1, QTableWidgetItem(f'{self.Results["Yin"]["LCST"]:.2f}'))
        self.AnalysisParam_Yin_Table.setItem(
            6, 1, QTableWidgetItem(f'{self.Results["Yin"]["DeltaEps@10k"]:.6f}'))
        self.AnalysisParam_Yin_Table.setItem(
            7, 1, QTableWidgetItem(f'{self.Results["Yin"]["Stripping_Rutting_mm"]:.3f}'))
        self.AnalysisParam_Yin_Table.setItem(
            8, 1, QTableWidgetItem(f'{self.Results["Yin"]["Stripping_Number"]:.2f}'))
        self.AnalysisParam_Yin_Table.setItem(
            9, 1, QTableWidgetItem(f'{self.Results["Yin"]["SIP"]:.2f}'))
        self.AnalysisParam_Yin_Table.setItem(
            10, 1, QTableWidgetItem(f'{self.Results["Yin"]["SIP_Yval_mm"]:.3f}'))
        self.AnalysisParam_Yin_Table.setItem(
            11, 1, QTableWidgetItem(f'{self.Results["Yin"]["SIP_Adj"]:.2f}'))
        self.AnalysisParam_Yin_Table.setItem(
            12, 1, QTableWidgetItem(f'{self.Results["Yin"]["SIP_Adj_Yval_mm"]:.3f}'))
        self.AnalysisParam_Yin_Table.setItem(
            13, 1, QTableWidgetItem(f'{self.Results["Yin"]["CreepLine"][0]:.3e}'))
        self.AnalysisParam_Yin_Table.setItem(
            14, 1, QTableWidgetItem(f'{self.Results["Yin"]["CreepLine"][1]:.2f}'))
        self.AnalysisParam_Yin_Table.setItem(
            15, 1, QTableWidgetItem(f'{self.Results["Yin"]["TangentLine"][0]:.3e}'))
        self.AnalysisParam_Yin_Table.setItem(
            16, 1, QTableWidgetItem(f'{self.Results["Yin"]["TangentLine"][1]:.2f}'))
        self.AnalysisParam_Yin_Table.setItem(
            17, 1, QTableWidgetItem(f'{self.Results["Yin"]["TangentLine_Adj"][0]:.3e}'))
        self.AnalysisParam_Yin_Table.setItem(
            18, 1, QTableWidgetItem(f'{self.Results["Yin"]["TangentLine_Adj"][1]:.2f}'))
        # ------------------------------------------------------------
        # For the 6th degree polynomial model. 
        # Model parameters. 
        self.ModelParam_6deg_Table.setItem(
            0, 1, QTableWidgetItem(f'{self.Results["6deg"]["Rutting_6degPolynomial_Coeff"][0]:.3e}'))
        self.ModelParam_6deg_Table.setItem(
            1, 1, QTableWidgetItem(f'{self.Results["6deg"]["Rutting_6degPolynomial_Coeff"][1]:.3e}'))
        self.ModelParam_6deg_Table.setItem(
            2, 1, QTableWidgetItem(f'{self.Results["6deg"]["Rutting_6degPolynomial_Coeff"][2]:.3e}'))
        self.ModelParam_6deg_Table.setItem(
            3, 1, QTableWidgetItem(f'{self.Results["6deg"]["Rutting_6degPolynomial_Coeff"][3]:.3e}'))
        self.ModelParam_6deg_Table.setItem(
            4, 1, QTableWidgetItem(f'{self.Results["6deg"]["Rutting_6degPolynomial_Coeff"][4]:.3e}'))
        self.ModelParam_6deg_Table.setItem(
            5, 1, QTableWidgetItem(f'{self.Results["6deg"]["Rutting_6degPolynomial_Coeff"][5]:.3e}'))
        self.ModelParam_6deg_Table.setItem(
            6, 1, QTableWidgetItem(f'{self.Results["6deg"]["Rutting_6degPolynomial_Coeff"][6]:.3e}'))
        # Analysis parameters. 
        self.AnalysisParam_6deg_Table.setItem(
            0, 1, QTableWidgetItem(f'{self.Results["6deg"]["Maximum_Rutting_mm"]:.3f}'))
        self.AnalysisParam_6deg_Table.setItem(
            1, 1, QTableWidgetItem(f'{self.Results["6deg"]["Maximum_Passes"]:d}'))
        self.AnalysisParam_6deg_Table.setItem(
            2, 1, QTableWidgetItem(f'{self.Results["6deg"]["Rutting@10k_mm"]:.3f}'))
        self.AnalysisParam_6deg_Table.setItem(
            3, 1, QTableWidgetItem(f'{self.Results["6deg"]["Rutting@20k_mm"]:.3f}'))
        self.AnalysisParam_6deg_Table.setItem(
            4, 1, QTableWidgetItem(f'{self.Results["6deg"]["Stripping_Rutting_mm"]:.3f}'))
        self.AnalysisParam_6deg_Table.setItem(
            5, 1, QTableWidgetItem(f'{self.Results["6deg"]["Stripping_Number"]:.2f}'))
        self.AnalysisParam_6deg_Table.setItem(
            6, 1, QTableWidgetItem(f'{self.Results["6deg"]["CreepLine"][0]:.4f}'))
        self.AnalysisParam_6deg_Table.setItem(
            7, 1, QTableWidgetItem(f'{self.Results["6deg"]["CreepLine"][1]:.2f}'))
        # Update the tab widget with the 2PP analysis results tab. 
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
            "Lane_Num": int(self.ST03T1_LineEdit_LaneNumber.text()),
            "Lab_Aging": self.ST03T1_DropDown_LabAging.currentText(), 
            "RepNumber": RepNumber, 
            "Wheel_Side": self.ST03T1_DropDown_WheelSide.currentText(), 
            "Lift_Location": self.ST03T1_DropDown_LiftLocation.currentText(),
            "FileName": os.path.basename(self.CurrentFileList[self.CurrentFileIndex]), 
            "FileDirectory": os.path.dirname(self.CurrentFileList[self.CurrentFileIndex]), 
            "Data": RutData, "Data_shape": RutData_shape, "Data_dtype": RutData_dtype, 
            "TPP_StrippingNumber": self.Results["2PP"]["Stripping_Number"], 
            "TPP_Max_Rut_mm": self.Results["2PP"]["Maximum_Rutting_mm"], 
            "TPP_Max_Pass": self.Results["2PP"]["Maximum_Passes"], 
            "TPP_RuttingAt10k_mm": self.Results["2PP"]["Rutting@10k_mm"], 
            "TPP_RuttingAt20k_mm": self.Results["2PP"]["Rutting@20k_mm"], 
            "TPP_ModelCoeff_a": self.Results["2PP"]["Rutting_PowerModel_Coeff"][0], 
            "TPP_ModelCoeff_b": self.Results["2PP"]["Rutting_PowerModel_Coeff"][0], 
            "TPP_ModelCoeff_alpha": self.Results["2PP"]["Rutting_PowerModel_Part2_Coeff"][0], 
            "TPP_ModelCoeff_beta": self.Results["2PP"]["Rutting_PowerModel_Part2_Coeff"][1], 
            "TPP_ModelCoeff_gamma": self.Results["2PP"]["Rutting_PowerModel_Part2_Coeff"][2], 
            "TPP_ModelCoeff_Phi": self.Results["2PP"]["Rutting_PowerModel_Part2_Coeff"][3], 
            "TPP_Stripping_Rutting_mm": self.Results["2PP"]["Stripping_Rutting_mm"], 
            "TPP_Stripping_Rutting_Pass": self.Results["2PP"]["Stripping_Rutting_Pass"], 
            "TPP_SIP": self.Results["2PP"]["SIP"], 
            "TPP_SIP_Yvalue": self.Results["2PP"]["SIP_Yval_mm"], 
            "TPP_SIP_Adj": self.Results["2PP"]["SIP_Adj"], 
            "TPP_SIP_Adj_Yvalue": self.Results["2PP"]["SIP_Adj_Yval_mm"], 
            "TPP_CreepLine_Slope": self.Results["2PP"]["CreepLine"][0], 
            "TPP_CreepLine_Intercept": self.Results["2PP"]["CreepLine"][1], 
            "TPP_StrippingLine_Slope": self.Results["2PP"]["TangentLine"][0], 
            "TPP_StrippingLine_Intercept": self.Results["2PP"]["TangentLine"][1], 
            "TPP_StrippingLine_Slope_Adj": self.Results["2PP"]["TangentLine_Adj"][0], 
            "TPP_StrippingLine_Intercept_Adj": self.Results["2PP"]["TangentLine_Adj"][1], 
            "Yin_Max_Rut_mm": self.Results["Yin"]["Maximum_Rutting_mm"], 
            "Yin_Max_Pass": self.Results["Yin"]["Maximum_Passes"], 
            "Yin_RuttingAt10k_mm": self.Results["Yin"]["Rutting@10k_mm"], 
            "Yin_RuttingAt20k_mm": self.Results["Yin"]["Rutting@20k_mm"], 
            "Yin_ModelCoeff_Step1_ro": self.Results["Yin"]["Rutting_Step1_Coeff"][0], 
            "Yin_ModelCoeff_Step1_LCult": self.Results["Yin"]["Rutting_Step1_Coeff"][1], 
            "Yin_ModelCoeff_Step1_beta": self.Results["Yin"]["Rutting_Step1_Coeff"][2], 
            "Yin_ModelCoeff_Step2_RutMax": self.Results["Yin"]["Rutting_Step2_Coeff"][0], 
            "Yin_ModelCoeff_Step2_alpha": self.Results["Yin"]["Rutting_Step2_Coeff"][1], 
            "Yin_ModelCoeff_Step2_lambda": self.Results["Yin"]["Rutting_Step2_Coeff"][2], 
            "Yin_ModelCoeff_Step3_Eps0": self.Results["Yin"]["Rutting_Step3_Coeff"][0], 
            "Yin_ModelCoeff_Step3_theta": self.Results["Yin"]["Rutting_Step3_Coeff"][1], 
            "Yin_Stripping_Rutting_mm": self.Results["Yin"]["Stripping_Rutting_mm"], 
            "Yin_Stripping_Rutting_Pass": self.Results["Yin"]["Stripping_Rutting_Pass"], 
            "Yin_SIP": self.Results["Yin"]["SIP"], 
            "Yin_SIP_Yvalue": self.Results["Yin"]["SIP_Yval_mm"], 
            "Yin_SIP_Adj": self.Results["Yin"]["SIP_Adj"], 
            "Yin_SIP_Adj_Yvalue": self.Results["Yin"]["SIP_Adj_Yval_mm"], 
            "Yin_StrippingNumber": self.Results["Yin"]["Stripping_Number"], 
            "Yin_CreepLine_Slope": self.Results["Yin"]["CreepLine"][0], 
            "Yin_CreepLine_Intercept": self.Results["Yin"]["CreepLine"][1], 
            "Yin_StrippingLine_Slope": self.Results["Yin"]["TangentLine"][0], 
            "Yin_StrippingLine_Intercept": self.Results["Yin"]["TangentLine"][1], 
            "Yin_StrippingLine_Slope_Adj": self.Results["Yin"]["TangentLine_Adj"][0], 
            "Yin_StrippingLine_Intercept_Adj": self.Results["Yin"]["TangentLine_Adj"][1], 
            "Yin_Parameter_LCSN": self.Results["Yin"]["LCSN"], 
            "Yin_Parameter_LCST": self.Results["Yin"]["LCST"], 
            "Yin_Parameter_DeltaEpsAt10k": self.Results["Yin"]["DeltaEps@10k"], 
            "Poly6_Max_Rut_mm": self.Results["6deg"]["Maximum_Rutting_mm"], 
            "Poly6_Max_Pass": self.Results["6deg"]["Maximum_Passes"], 
            "Poly6_RuttingAt10k_mm": self.Results["6deg"]["Rutting@10k_mm"], 
            "Poly6_RuttingAt20k_mm": self.Results["6deg"]["Rutting@20k_mm"], 
            "Poly6_ModelCoeff_a0": self.Results["6deg"]["Rutting_6degPolynomial_Coeff"][6], 
            "Poly6_ModelCoeff_a1": self.Results["6deg"]["Rutting_6degPolynomial_Coeff"][5], 
            "Poly6_ModelCoeff_a2": self.Results["6deg"]["Rutting_6degPolynomial_Coeff"][4], 
            "Poly6_ModelCoeff_a3": self.Results["6deg"]["Rutting_6degPolynomial_Coeff"][3], 
            "Poly6_ModelCoeff_a4": self.Results["6deg"]["Rutting_6degPolynomial_Coeff"][2], 
            "Poly6_ModelCoeff_a5": self.Results["6deg"]["Rutting_6degPolynomial_Coeff"][1], 
            "Poly6_ModelCoeff_a6": self.Results["6deg"]["Rutting_6degPolynomial_Coeff"][0], 
            "Poly6_Stripping_Rutting_mm": self.Results["6deg"]["Stripping_Rutting_mm"], 
            "Poly6_Stripping_Rutting_Pass": self.Results["6deg"]["Stripping_Rutting_Pass"], 
            "Poly6_StrippingNumber": self.Results["6deg"]["Stripping_Number"], 
            "Poly6_CreepLine_Slope": self.Results["6deg"]["CreepLine"][0], 
            "Poly6_CreepLine_Intercept": self.Results["6deg"]["CreepLine"][1], 
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
        self.SpinBox_MaxPassNumber.setRange(10, 20001)
        self.SpinBox_MinPassNumber.setRange(0, 19980)
        self.SpinBox_MaxPassNumber.setValue(20000)
        self.SpinBox_MinPassNumber.setValue(0)
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
            "Lane_Num": int(self.ST03T1_LineEdit_LaneNumber.text()),
            "Lab_Aging": self.ST03T1_DropDown_LabAging.currentText(), 
            "RepNumber": RepNumber, 
            "Wheel_Side": self.ST03T1_DropDown_WheelSide.currentText(), 
            "Lift_Location": self.ST03T1_DropDown_LiftLocation.currentText(),
            "FileName": os.path.basename(self.CurrentFileList[self.CurrentFileIndex]), 
            "FileDirectory": os.path.dirname(self.CurrentFileList[self.CurrentFileIndex]), 
            "Data": RutData, "Data_shape": RutData_shape, "Data_dtype": RutData_dtype, 
            "TPP_StrippingNumber": -1, "TPP_Max_Rut_mm": -1, "TPP_Max_Pass": -1, 
            "TPP_RuttingAt10k_mm": -1, "TPP_RuttingAt20k_mm": -1, 
            "TPP_ModelCoeff_a": -1, "TPP_ModelCoeff_b": -1, 
            "TPP_ModelCoeff_alpha": -1, "TPP_ModelCoeff_beta": -1, "TPP_ModelCoeff_gamma": -1, "TPP_ModelCoeff_Phi": -1, 
            "TPP_Stripping_Rutting_mm": -1, "TPP_Stripping_Rutting_Pass": -1, 
            "TPP_SIP": -1, "TPP_SIP_Yvalue": -1, "TPP_SIP_Adj": -1, "TPP_SIP_Adj_Yvalue": -1, 
            "TPP_CreepLine_Slope": -1, "TPP_CreepLine_Intercept": -1, 
            "TPP_StrippingLine_Slope": -1, "TPP_StrippingLine_Intercept": -1, 
            "TPP_StrippingLine_Slope_Adj": -1, "TPP_StrippingLine_Intercept_Adj": -1, 
            "Yin_Max_Rut_mm": -1, "Yin_Max_Pass": -1, "Yin_RuttingAt10k_mm": -1, "Yin_RuttingAt20k_mm": -1, 
            "Yin_ModelCoeff_Step1_ro": -1, "Yin_ModelCoeff_Step1_LCult": -1, "Yin_ModelCoeff_Step1_beta": -1, 
            "Yin_ModelCoeff_Step2_RutMax": -1, "Yin_ModelCoeff_Step2_alpha": -1, "Yin_ModelCoeff_Step2_lambda": -1, 
            "Yin_ModelCoeff_Step3_Eps0": -1, "Yin_ModelCoeff_Step3_theta": -1, 
            "Yin_Stripping_Rutting_mm": -1, "Yin_Stripping_Rutting_Pass": -1, 
            "Yin_SIP": -1, "Yin_SIP_Yvalue": -1, "Yin_SIP_Adj": -1, "Yin_SIP_Adj_Yvalue": -1, 
            "Yin_StrippingNumber": -1, "Yin_CreepLine_Slope": -1, "Yin_CreepLine_Intercept": -1, 
            "Yin_StrippingLine_Slope": -1, "Yin_StrippingLine_Intercept": -1, 
            "Yin_StrippingLine_Slope_Adj": -1, "Yin_StrippingLine_Intercept_Adj": -1, 
            "Yin_Parameter_LCSN": -1, "Yin_Parameter_LCST": -1, "Yin_Parameter_DeltaEpsAt10k": -1, 
            "Poly6_Max_Rut_mm": -1, "Poly6_Max_Pass": -1, "Poly6_RuttingAt10k_mm": -1, "Poly6_RuttingAt20k_mm": -1, 
            "Poly6_ModelCoeff_a0": -1, "Poly6_ModelCoeff_a1": -1, "Poly6_ModelCoeff_a2": -1, "Poly6_ModelCoeff_a3": -1, 
            "Poly6_ModelCoeff_a4": -1, "Poly6_ModelCoeff_a5": -1, "Poly6_ModelCoeff_a6": -1, 
            "Poly6_Stripping_Rutting_mm": -1, "Poly6_Stripping_Rutting_Pass": -1, "Poly6_StrippingNumber": -1, 
            "Poly6_CreepLine_Slope": -1, "Poly6_CreepLine_Intercept": -1, 
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
        self.SpinBox_MaxPassNumber.setRange(10, 20001)
        self.SpinBox_MinPassNumber.setRange(0, 19980)
        self.SpinBox_MaxPassNumber.setValue(20000)
        self.SpinBox_MinPassNumber.setValue(0)
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
            self.Button_Review.setEnabled(True)
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
    def Function_Show_Model_Properties(self, link):
        """
        This function will create a new pop-up window to show the model properties.
        """
        if link == "Model_2PP":
            jpg_path = "./assets/Model_2PP.jpg"
            popup = ScrollableImagePopup(jpg_path)
            popup.exec_()
        elif link == "Model_Yin":
            jpg_path = "./assets/Model_Yin.jpg"
            popup = ScrollableImagePopup(jpg_path)
            popup.exec_()
        elif link == 'Model_6deg':
            jpg_path = "./assets/Model_6deg.jpg"
            popup = ScrollableImagePopup(jpg_path)
            popup.exec_()
        else:
            print(f"Unknown link clicked: {link}")
        # Return Nothing. 
        return 
    # ------------------------------------------------------------------------------------------------------------------
    def Function_Plot_Model_RadioButton(self, Model_Name):
        """
        This function called when the plotting model radio buttons are selected. This function calls another function 
        to plot fitted model on top of the raw data. 
        """
        if 'Plot_Current_Model' in self.Results and Model_Name != self.Results['Plot_Current_Model']:
            # Update the current model used in plotting. 
            self.Results['Plot_Current_Model'] = Model_Name
            if Model_Name == '6deg':
                # We don't have extrapolation to use end point at 12.5 threshold. 
                self.SIPAdjusted_MaxRut.setChecked(True)
                self.SIPAdjusted_Threshold.setChecked(False)
                self.Results['Plot_Current_SIPMethod'] == 'MaxRut'
            # Call the plotter function. 
            self.Function_Plotter()
    # ------------------------------------------------------------------------------------------------------------------
    def Function_PLOT_SIPAdjusted_RadioButton(self, SIPMethod):
        """
        This function called when the SIP calculation method is changed. This function calls another function to plot 
        the fitted model considering the selected SIP calculation method, where method 1 is the end point at the 
        threshold of 12.5 mm, and method 2 uses the end point at the maximum rut depth. 
        """
        if SIPMethod == 'Threshold' and self.Results['Plot_Current_Model'] == '6deg':
            # Set back the SIP method to end point. 
            self.Results['Plot_Current_SIPMethod'] = 'MaxRut'
            self.SIPAdjusted_Threshold.setChecked(False)
            self.SIPAdjusted_MaxRut.setChecked(True)
        elif 'Plot_Current_SIPMethod' in self.Results and SIPMethod != self.Results['Plot_Current_SIPMethod']:
            # Update the current model used in plotting. 
            self.Results['Plot_Current_SIPMethod'] = SIPMethod
            # Update the plotter level. 
            if SIPMethod == 'MaxRut':
                self.Results['Plot_Level'] = 1
            elif SIPMethod == 'Threshold':
                self.Results['Plot_Level'] = 2
            # Call the plotter function. 
            self.Function_Plotter()
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
    # ------------------------------------------------------------------------------------------------------------------
    def Function_Button_Review(self):
        self.stack.setCurrentIndex(1)  # Switch to the second page
# ======================================================================================================================
# ======================================================================================================================
# ======================================================================================================================


class ScrollableImagePopup(QDialog):
    """
    This class is defined to create popup windows that shows the model properties. 
    """
    def __init__(self, jpg_path):
        super().__init__()
        self.setWindowTitle("AutoHWTT Image Viewer")
        self.initUI(jpg_path)

    def initUI(self, jpg_path):
        # Set initial size for the pop-up
        self.resize(730, 600)
        # Create a scrollable area
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        # Create a QLabel to hold the image
        image_label = QLabel(self)
        pixmap = QPixmap(jpg_path)
        if pixmap.isNull():
            image_label.setText("Failed to load image.")
            image_label.setAlignment(Qt.AlignCenter)
        else:
            image_label.setPixmap(pixmap)
            image_label.setAlignment(Qt.AlignCenter)
        # Set QLabel as the scrollable widget
        scroll_area.setWidget(image_label)
        # Layout for pop-up dialog
        layout = QVBoxLayout(self)
        layout.addWidget(scroll_area)
        self.setLayout(layout)
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