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
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QAction, QDoubleSpinBox, QLabel, \
    QPushButton, QWidget, QGridLayout, QFormLayout, QLineEdit, QFileDialog, QMessageBox, QGroupBox, QProgressBar, \
    QPlainTextEdit, QStackedWidget, QCheckBox, QComboBox, QTabWidget, QScrollArea, QTableWidget, QTableWidgetItem, \
    QSpinBox, QFrame
from PyQt5.QtGui import QPixmap, QFont, QRegExpValidator, QDoubleValidator
from PyQt5.QtCore import Qt, QRegExp
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from Alg01_UtilityFunctions import Read_HWTT_Text_File, Read_HWTT_Excel_File
from Alg03_HWTT_Analysis_Functions import HWTT_Analysis, ModelPower
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
        # self.Button_AcceptResult.clicked.connect(self.Function_Button_PassResult)
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
        ST03T1_Label01 = QLabel(f'{"Test Name*:".ljust(50)}')
        ST03T1_Label02 = QLabel(f'{"Test Date:".ljust(50)}')
        ST03T1_Label03 = QLabel(f'{"Test Time:".ljust(50)}')
        ST03T1_Label04 = QLabel(f'{"Testing condition*:".ljust(50)}')
        ST03T1_Label05 = QLabel(f'{"Wheel path side*:".ljust(50)}')
        ST03T1_Label06 = QLabel(f'{"Target test temperature (°C):".ljust(50)}')
        ST03T1_Label07 = QLabel(f'{"Avg. recorded test temperature (°C):".ljust(50)}')
        ST03T1_Label08 = QLabel(f'{"Std. recorded test temperature (°C):".ljust(50)}')
        self.ST03T1_LineEdit_TestName = QLineEdit()            # For test name. 
        self.ST03T1_LineEdit_TestName.setPlaceholderText("Enter test name here ...")
        self.ST03T1_LineEdit_TestName.setReadOnly(False)
        self.ST03T1_LineEdit_TestDate = QLineEdit()
        self.ST03T1_LineEdit_TestDate.setInputMask("99/99/9999")       # Enforce date format, but not validating it. 
        self.ST03T1_LineEdit_TestDate.setPlaceholderText("01/01/1999")
        self.ST03T1_LineEdit_TestDate.setReadOnly(False)
        self.ST03T1_LineEdit_TestTime = QLineEdit()
        self.ST03T1_LineEdit_TestTime.setInputMask("99:99")        # Enforce dtime format. 
        self.ST03T1_LineEdit_TestTime.setPlaceholderText("01/01/1999")
        self.ST03T1_LineEdit_TestTime.setReadOnly(False)
        self.ST03T1_DropDown_TestCondition = QComboBox()
        self.ST03T1_DropDown_TestCondition.addItems(["Wet", "Dry"])
        self.ST03T1_DropDown_TestCondition.setCurrentIndex(0)
        self.ST03T1_DropDown_WheelSide = QComboBox()
        self.ST03T1_DropDown_WheelSide.addItems(["Left", "Right", "Not Determined"])
        self.ST03T1_DropDown_WheelSide.setCurrentIndex(0)
        self.ST03T1_LineEdit_TargetTestTemp = QLineEdit()            # For test name. 
        self.ST03T1_LineEdit_TargetTestTemp.setPlaceholderText("Enter test target temperature ...")
        self.ST03T1_LineEdit_TargetTestTemp.setReadOnly(False)
        Validator4TargetTemp = QDoubleValidator(0.00, 99.99, 2)
        Validator4TargetTemp.setNotation(QDoubleValidator.StandardNotation)
        self.ST03T1_LineEdit_TargetTestTemp.setValidator(QDoubleValidator(0, 99.99, 2))
        self.ST03T1_LineEdit_AvgTestTemp = QLineEdit()            # For test name. 
        self.ST03T1_LineEdit_AvgTestTemp.setPlaceholderText("Avg. test temperature will be displayed here.")
        self.ST03T1_LineEdit_AvgTestTemp.setReadOnly(True)
        self.ST03T1_LineEdit_StdTestTemp = QLineEdit()            # For test name. 
        self.ST03T1_LineEdit_StdTestTemp.setPlaceholderText("Std. test temperature will be displayed here.")
        self.ST03T1_LineEdit_StdTestTemp.setReadOnly(True)


        SectT03T1_FormLayout.addRow(ST03T1_Label01, self.ST03T1_LineEdit_TestName)
        SectT03T1_FormLayout.addRow(ST03T1_Label02, self.ST03T1_LineEdit_TestDate)
        SectT03T1_FormLayout.addRow(ST03T1_Label03, self.ST03T1_LineEdit_TestTime)
        SectT03T1_FormLayout.addRow(ST03T1_Label04, self.ST03T1_DropDown_TestCondition)
        SectT03T1_FormLayout.addRow(ST03T1_Label05, self.ST03T1_DropDown_WheelSide)
        SectT03T1_FormLayout.addRow(ST03T1_Label06, self.ST03T1_LineEdit_TargetTestTemp)
        SectT03T1_FormLayout.addRow(ST03T1_Label07, self.ST03T1_LineEdit_AvgTestTemp)
        SectT03T1_FormLayout.addRow(ST03T1_Label08, self.ST03T1_LineEdit_StdTestTemp)
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
        self.AnalysisParam_Table.setColumnWidth(0, 160) 
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
        # Otherwise, Update the progress label.
        self.Label_InputFileUpdate.setText(f'Processing files: {0}/{len(FileList)} done!')
        self.ProgressBar.setEnabled(True)
        self.ProgressBar.setValue(int(0.5 / len(FileList) * 100))
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
        # Check if the selected file is already in the database. 
        self.cursor.execute("SELECT COUNT(*) FROM HWTT WHERE FileName = ?", (os.path.basename(FileList[0]),))
        count = self.cursor.fetchone()[0]
        if count > 0:
            raise Exception("The file is already existed! Maybe printing a message!")
        # --------------------------------------------------------------------------------------------------------------
        # Read the file and save the data. 
        Passes, RutDepth, Temperature, Props = Read_HWTT_Text_File(FileList[0])
        self.Results['Passes']       = Passes.copy()
        self.Results['RutDepth']     = RutDepth.copy()
        self.Results['Temperatures'] = Temperature.copy()
        self.Results['Props']        = Props.copy()
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
            self.ST03T1_DropDown_TestCondition.setCurrentIndex(0)
        elif self.Results['Props']['Test_Condition'].lower() == 'dry':
            self.ST03T1_DropDown_TestCondition.setCurrentIndex(1)
        else:
            self.ST03T1_DropDown_TestCondition.setCurrentIndex(2)
        if self.Results['Props']['Wheel_Side'].lower() == 'left':
            self.ST03T1_DropDown_WheelSide.setCurrentIndex(0)
        elif self.Results['Props']['Wheel_Side'].lower() == 'right':
            self.ST03T1_DropDown_WheelSide.setCurrentIndex(1)
        else:
            self.ST03T1_DropDown_WheelSide.setCurrentIndex(2)
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
        self.ModelParam_Table.setItem(3, 1, QTableWidgetItem(f'{self.Results["Rutting_PowerModel_Part2_Coeff"][0]:.6f}'))
        self.ModelParam_Table.setItem(4, 1, QTableWidgetItem(f'{self.Results["Rutting_PowerModel_Part2_Coeff"][1]:.6f}'))
        self.ModelParam_Table.setItem(5, 1, QTableWidgetItem(f'{self.Results["Rutting_PowerModel_Part2_Coeff"][2]:.6f}'))
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


    def Plot_ComplexModulus(self):
        # First, clear the axes. 
        self.axes.clear()
        # --------------------------------
        # Take care of the visualization part. 
        for Obj in [self.Check_Visual_Gstar, self.Check_Visual_Phase, self.Check_Visual_GP, self.Check_Visual_GPP]:
            Obj.blockSignals(True)
            Obj.setChecked(False)
            Obj.blockSignals(False)
        self.Check_Visual_Gstar.blockSignals(True)    
        self.Check_Visual_Gstar.setChecked(True)
        self.Check_Visual_Gstar.blockSignals(False)
        # --------------------------------
        # This function will plot the |G*| data at different phases. 
        if self.AnalysisProgress == 0:          # In the first step, only plot the isotherms. 
            Temperatures = self.CurIsotherms['Temperature'].unique()
            for i, temp in enumerate(Temperatures):
                Tempdf = self.CurIsotherms[(self.CurIsotherms['Temperature'] == temp) & \
                                           (self.CurIsotherms['IsOutlier'] == 0)]
                Tempdf = Tempdf.sort_values(by='Frequency')
                self.axes.loglog(Tempdf['Frequency'], Tempdf['|G*|'], label=f'{temp:.1f}°C', 
                                 color=self.PlotProps['Colors'][i % 10], 
                                 marker=self.PlotProps['Markers'][i % 6], 
                                 ls=self.PlotProps['LineStyle'][i % 4])
            self.axes.set_xlabel('Frequency (rad/s)', fontsize=10, fontweight='bold', color='k')
        elif self.AnalysisProgress == 1:        # After performing the shift, plot the shifting results. 
            Temperatures = self.CurIsotherms['Temperature'].unique()
            for i, temp in enumerate(Temperatures):
                Tempdf = self.CurIsotherms[(self.CurIsotherms['Temperature'] == temp) & \
                                           (self.CurIsotherms['IsOutlier'] == 0)]
                Tempdf = Tempdf.sort_values(by='Frequency')
                self.axes.loglog(Tempdf['Red_Frequency'], Tempdf['|G*|'], label=f'{temp:.1f}°C', 
                                 color=self.PlotProps['Colors'][i % 10], 
                                 marker=self.PlotProps['Markers'][i % 6], 
                                 ls='')
            self.axes.set_xlabel('Reduced Frequency (rad/s)', fontsize=10, fontweight='bold', color='k')
        elif self.AnalysisProgress == 2:        # After performing the master curve construction, plot the MC and data.
            Temperatures = self.CurIsotherms['Temperature'].unique()
            for i, temp in enumerate(Temperatures):
                Tempdf = self.CurIsotherms[(self.CurIsotherms['Temperature'] == temp) & \
                                           (self.CurIsotherms['IsOutlier'] == 0)]
                Tempdf = Tempdf.sort_values(by='Frequency')
                self.axes.loglog(Tempdf['Red_Frequency'], Tempdf['|G*|'], label=f'{temp:.1f}°C', 
                                 color=self.PlotProps['Colors'][i % 10], 
                                 marker=self.PlotProps['Markers'][i % 6], ls='', alpha=0.5)
            self.axes.loglog(self.Results['MC_Plot']['Freq'], self.Results['MC_Plot']['Gstar'], 
                                ls='--', lw=1.5, color='k', label=f'{self.Results["MC_Model"]} model')
            self.axes.set_xlabel('Reduced Frequency (rad/s)', fontsize=10, fontweight='bold', color='k')
        else:
            raise Exception(f'For other analysis progress states, the code is under development!')
        # --------------------------------
        self.axes.set_ylabel('Complex Modulus, |G*| (Pa)', fontsize=10, fontweight='bold', color='k')
        self.axes.legend(fontsize=10, fancybox=True)
        self.axes.grid(which='both', color='gray', alpha=0.1)
        # Redraw the canvas
        self.fig.set_constrained_layout(True)
        self.canvas.draw()
    # ------------------------------------------------------------------------------------------------------------------
    def Plot_PhaseAngle(self):
        # First, clear the axes. 
        self.axes.clear()
        # --------------------------------
        # Take care of the visualization part. 
        for Obj in [self.Check_Visual_Gstar, self.Check_Visual_Phase, self.Check_Visual_GP, self.Check_Visual_GPP]:
            Obj.blockSignals(True)
            Obj.setChecked(False)
            Obj.blockSignals(False)
        self.Check_Visual_Phase.blockSignals(True)
        self.Check_Visual_Phase.setChecked(True)
        self.Check_Visual_Phase.blockSignals(False)
        # --------------------------------
        # This function will plot the |G*| data at different phases. 
        if self.AnalysisProgress == 0:          # In the first step, only plot the isotherms. 
            Temperatures = self.CurIsotherms['Temperature'].unique()
            for i, temp in enumerate(Temperatures):
                Tempdf = self.CurIsotherms[(self.CurIsotherms['Temperature'] == temp) & \
                                           (self.CurIsotherms['IsOutlier'] == 0)]
                Tempdf = Tempdf.sort_values(by='Frequency')
                self.axes.semilogx(Tempdf['Frequency'], Tempdf['PhaseAngle'], label=f'{temp:.1f}°C', 
                                   color=self.PlotProps['Colors'][i % 10],
                                   marker=self.PlotProps['Markers'][i % 6], 
                                   ls=self.PlotProps['LineStyle'][i % 4])
            self.axes.set_xlabel('Frequency (rad/s)', fontsize=10, fontweight='bold', color='k')
        elif self.AnalysisProgress == 1:        # After performing the shift, plot the shifting results. 
            Temperatures = self.CurIsotherms['Temperature'].unique()
            for i, temp in enumerate(Temperatures):
                Tempdf = self.CurIsotherms[(self.CurIsotherms['Temperature'] == temp) & \
                                           (self.CurIsotherms['IsOutlier'] == 0)]
                Tempdf = Tempdf.sort_values(by='Frequency')
                self.axes.semilogx(Tempdf['Red_Frequency'], Tempdf['PhaseAngle'], label=f'{temp:.1f}°C', 
                                   color=self.PlotProps['Colors'][i % 10],
                                   marker=self.PlotProps['Markers'][i % 6], 
                                   ls='')
            self.axes.set_xlabel('Reduced Frequency (rad/s)', fontsize=10, fontweight='bold', color='k')
        elif self.AnalysisProgress == 2:        # After performing the master curve construction, plot the MC and data.
            Temperatures = self.CurIsotherms['Temperature'].unique()
            for i, temp in enumerate(Temperatures):
                Tempdf = self.CurIsotherms[(self.CurIsotherms['Temperature'] == temp) & \
                                           (self.CurIsotherms['IsOutlier'] == 0)]
                Tempdf = Tempdf.sort_values(by='Frequency')
                self.axes.semilogx(Tempdf['Red_Frequency'], Tempdf['PhaseAngle'], label=f'{temp:.1f}°C', 
                                   color=self.PlotProps['Colors'][i % 10], 
                                   marker=self.PlotProps['Markers'][i % 6], ls='', alpha=0.5)
            self.axes.semilogx(self.Results['MC_Plot']['Freq'], self.Results['MC_Plot']['Phase'], 
                                ls='--', lw=1.5, color='k', label=f'{self.Results["MC_Model"]} model')
            self.axes.set_xlabel('Reduced Frequency (rad/s)', fontsize=10, fontweight='bold', color='k')
        else:
            raise Exception(f'For other analysis progress states, the code is under development!')
        # --------------------------------
        self.axes.set_ylabel('Phase Angle, δ (°)', fontsize=10, fontweight='bold', color='k')
        self.axes.legend(fontsize=10, fancybox=True)
        self.axes.grid(which='both', color='gray', alpha=0.1)
        # Redraw the canvas
        self.fig.set_constrained_layout(True)
        self.canvas.draw()
    # ------------------------------------------------------------------------------------------------------------------
    def Plot_StorageModulus(self):
        # First, clear the axes. 
        self.axes.clear()
        # --------------------------------
        # Take care of the visualization part. 
        for Obj in [self.Check_Visual_Gstar, self.Check_Visual_Phase, self.Check_Visual_GP, self.Check_Visual_GPP]:
            Obj.blockSignals(True)
            Obj.setChecked(False)
            Obj.blockSignals(False)
        self.Check_Visual_GP.blockSignals(True)    
        self.Check_Visual_GP.setChecked(True)
        self.Check_Visual_GP.blockSignals(False)
        # --------------------------------
        # This function will plot the StorageModulus data at different phases. 
        if self.AnalysisProgress == 0:          # In the first step, only plot the isotherms. 
            Temperatures = self.CurIsotherms['Temperature'].unique()
            for i, temp in enumerate(Temperatures):
                Tempdf = self.CurIsotherms[(self.CurIsotherms['Temperature'] == temp) & \
                                           (self.CurIsotherms['IsOutlier'] == 0)]
                Tempdf = Tempdf.sort_values(by='Frequency')
                self.axes.loglog(Tempdf['Frequency'], Tempdf['StorageModulus'], label=f'{temp:.1f}°C', 
                                 color=self.PlotProps['Colors'][i % 10], 
                                 marker=self.PlotProps['Markers'][i % 6], 
                                 ls=self.PlotProps['LineStyle'][i % 4])
            self.axes.set_xlabel('Frequency (rad/s)', fontsize=10, fontweight='bold', color='k')
        elif self.AnalysisProgress == 1:        # After performing the shift, plot the shifting results. 
            Temperatures = self.CurIsotherms['Temperature'].unique()
            for i, temp in enumerate(Temperatures):
                Tempdf = self.CurIsotherms[(self.CurIsotherms['Temperature'] == temp) & \
                                           (self.CurIsotherms['IsOutlier'] == 0)]
                Tempdf = Tempdf.sort_values(by='Frequency')
                self.axes.loglog(Tempdf['Red_Frequency'], Tempdf['StorageModulus'], label=f'{temp:.1f}°C', 
                                 color=self.PlotProps['Colors'][i % 10], 
                                 marker=self.PlotProps['Markers'][i % 6], 
                                 ls='')
            self.axes.set_xlabel('Reduced Frequency (rad/s)', fontsize=10, fontweight='bold', color='k')
        elif self.AnalysisProgress == 2:        # After performing the master curve construction, plot the MC and data.
            Temperatures = self.CurIsotherms['Temperature'].unique()
            for i, temp in enumerate(Temperatures):
                Tempdf = self.CurIsotherms[(self.CurIsotherms['Temperature'] == temp) & \
                                           (self.CurIsotherms['IsOutlier'] == 0)]
                Tempdf = Tempdf.sort_values(by='Frequency')
                self.axes.loglog(Tempdf['Red_Frequency'], Tempdf['StorageModulus'], label=f'{temp:.1f}°C', 
                                 color=self.PlotProps['Colors'][i % 10], 
                                 marker=self.PlotProps['Markers'][i % 6], ls='', alpha=0.5)
            self.axes.loglog(self.Results['MC_Plot']['Freq'], self.Results['MC_Plot']['GP'], 
                                ls='--', lw=1.5, color='k', label=f'{self.Results["MC_Model"]} model')
            self.axes.set_xlabel('Reduced Frequency (rad/s)', fontsize=10, fontweight='bold', color='k')
        else:
            raise Exception(f'For other analysis progress states, the code is under development!')
        # --------------------------------
        self.axes.set_ylabel("Storage modulus, G' (Pa)", fontsize=10, fontweight='bold', color='k')
        self.axes.legend(fontsize=10, fancybox=True)
        self.axes.grid(which='both', color='gray', alpha=0.1)
        # Redraw the canvas
        self.fig.set_constrained_layout(True)
        self.canvas.draw()
    # ------------------------------------------------------------------------------------------------------------------
    def Plot_LossModulus(self):
        # First, clear the axes. 
        self.axes.clear()
        # --------------------------------
        # Take care of the visualization part. 
        for Obj in [self.Check_Visual_Gstar, self.Check_Visual_Phase, self.Check_Visual_GP, self.Check_Visual_GPP]:
            Obj.blockSignals(True)
            Obj.setChecked(False)
            Obj.blockSignals(False)
        self.Check_Visual_GPP.blockSignals(True)    
        self.Check_Visual_GPP.setChecked(True)
        self.Check_Visual_GPP.blockSignals(False)
        # --------------------------------
        # This function will plot the Loss Modulus data at different phases. 
        if self.AnalysisProgress == 0:          # In the first step, only plot the isotherms. 
            Temperatures = self.CurIsotherms['Temperature'].unique()
            for i, temp in enumerate(Temperatures):
                Tempdf = self.CurIsotherms[(self.CurIsotherms['Temperature'] == temp) & \
                                           (self.CurIsotherms['IsOutlier'] == 0)]
                Tempdf = Tempdf.sort_values(by='Frequency')
                self.axes.loglog(Tempdf['Frequency'], Tempdf['LossModulus'], label=f'{temp:.1f}°C', 
                                 color=self.PlotProps['Colors'][i % 10], 
                                 marker=self.PlotProps['Markers'][i % 6], 
                                 ls=self.PlotProps['LineStyle'][i % 4])
            self.axes.set_xlabel('Frequency (rad/s)', fontsize=10, fontweight='bold', color='k')
        elif self.AnalysisProgress == 1:        # After performing the shift, plot the shifting results. 
            Temperatures = self.CurIsotherms['Temperature'].unique()
            for i, temp in enumerate(Temperatures):
                Tempdf = self.CurIsotherms[(self.CurIsotherms['Temperature'] == temp) & \
                                           (self.CurIsotherms['IsOutlier'] == 0)]
                Tempdf = Tempdf.sort_values(by='Frequency')
                self.axes.loglog(Tempdf['Red_Frequency'], Tempdf['LossModulus'], label=f'{temp:.1f}°C', 
                                 color=self.PlotProps['Colors'][i % 10], 
                                 marker=self.PlotProps['Markers'][i % 6], 
                                 ls='')
            self.axes.set_xlabel('Reduced Frequency (rad/s)', fontsize=10, fontweight='bold', color='k')
        elif self.AnalysisProgress == 2:        # After performing the master curve construction, plot the MC and data.
            Temperatures = self.CurIsotherms['Temperature'].unique()
            for i, temp in enumerate(Temperatures):
                Tempdf = self.CurIsotherms[(self.CurIsotherms['Temperature'] == temp) & \
                                           (self.CurIsotherms['IsOutlier'] == 0)]
                Tempdf = Tempdf.sort_values(by='Frequency')
                self.axes.loglog(Tempdf['Red_Frequency'], Tempdf['LossModulus'], label=f'{temp:.1f}°C', 
                                 color=self.PlotProps['Colors'][i % 10], 
                                 marker=self.PlotProps['Markers'][i % 6], ls='', alpha=0.5)
            self.axes.loglog(self.Results['MC_Plot']['Freq'], self.Results['MC_Plot']['GPP'], 
                                ls='--', lw=1.5, color='k', label=f'{self.Results["MC_Model"]} model')
            self.axes.set_xlabel('Reduced Frequency (rad/s)', fontsize=10, fontweight='bold', color='k')
        else:
            raise Exception(f'For other analysis progress states, the code is under development!')
        # --------------------------------
        self.axes.set_ylabel('Loss modulus, G" (Pa)', fontsize=10, fontweight='bold', color='k')
        self.axes.legend(fontsize=10, fancybox=True)
        self.axes.grid(which='both', color='gray', alpha=0.1)
        # Redraw the canvas
        self.fig.set_constrained_layout(True)
        self.canvas.draw()
    # ------------------------------------------------------------------------------------------------------------------
    def Function_Button_SpecifyOutlier(self, checked):
        # This function should connect or disconnect the "Connection ID" for the click event trigger listener, by which 
        #   user can specify the outlier datapoints. 
        if checked:             # The button is pressed and wait to specify the outliers. 
            # Adjust the status of GUI. 
            self.Button_Finalize.setEnabled(False)          # Disable finalize buttons. 
            self.Menu_Fit_Finalize.setEnabled(False)
            if not self.Button_SpecifyOutlier.isChecked():
                self.Button_SpecifyOutlier.blockSignals(True)
                self.Button_SpecifyOutlier.setChecked(True)
                self.Button_SpecifyOutlier.blockSignals(False)
            if not self.Menu_Fit_Outlier.isChecked():
                self.Menu_Fit_Outlier.blockSignals(True)
                self.Menu_Fit_Outlier.setChecked(True)
                self.Menu_Fit_Outlier.blockSignals(False)
            self.Check_Visual_Gstar.setEnabled(False)       # Disable the plot type controllers.
            self.Check_Visual_Phase.setEnabled(False)
            self.Check_Visual_GP.setEnabled(False)
            self.Check_Visual_GPP.setEnabled(False)
            # Print the message to user. 
            MsgBox_Outlier_Instruct = QMessageBox()
            MsgBox_Outlier_Instruct.setIcon(QMessageBox.Information)
            MsgBox_Outlier_Instruct.setWindowTitle("Specify Outlier")
            MsgBox_Outlier_Instruct.setText(f"Please click near datapoints on graph to specify them as outlier.\n" +
                                            f"When finished, please click on 'Operation Done!' button.")
            MsgBox_Outlier_Instruct.setStandardButtons(QMessageBox.Ok)
            MsgBox_Outlier_Instruct.exec_()
            # Enable mouse click handling
            self.ConnectionID = self.canvas.mpl_connect("button_press_event", self.Function_On_Mouse_Click_Outlier)
            self.Button_SpecifyOutlier.setText("Operation Done!")       # Change the name.
            self.Menu_Fit_Outlier.setText("Operation Done!")
            # Plot the outlier datapoints. 
            Tempdf = self.CurIsotherms[self.CurIsotherms['IsOutlier'] == 1]
            self.OutlierIndex = self.CurIsotherms.index[self.CurIsotherms['IsOutlier'] == 1].tolist()
            X = Tempdf['Frequency'].to_numpy()
            if self.Check_Visual_Gstar.isChecked():
                Y = Tempdf['|G*|'].to_numpy()
                self.Outlier_Line = self.axes.loglog(X, Y, ls='', marker='*', ms=12, color='r')
            elif self.Check_Visual_Phase.isChecked():
                Y = Tempdf['PhaseAngle'].to_numpy()
                self.Outlier_Line = self.axes.semilogx(X, Y, ls='', marker='*', ms=12, color='r')
            elif self.Check_Visual_GP.isChecked():
                Y = Tempdf['StorageModulus'].to_numpy()
                self.Outlier_Line = self.axes.loglog(X, Y, ls='', marker='*', ms=12, color='r')
            elif self.Check_Visual_GPP.isChecked():
                Y = Tempdf['LossModulus'].to_numpy()
                self.Outlier_Line = self.axes.loglog(X, Y, ls='', marker='*', ms=12, color='r')
            else:
                raise Exception(f'Only one of the checkboxes in the Visualization section should be checked!')
            self.fig.set_constrained_layout(True)
            self.canvas.draw()      # Redraw the canvas
        else:
            if self.Button_SpecifyOutlier.isChecked():
                self.Button_SpecifyOutlier.blockSignals(True)
                self.Button_SpecifyOutlier.setChecked(False)
                self.Button_SpecifyOutlier.blockSignals(False)
            if self.Menu_Fit_Outlier.isChecked():
                self.Menu_Fit_Outlier.blockSignals(True)
                self.Menu_Fit_Outlier.setChecked(False)
                self.Menu_Fit_Outlier.blockSignals(False)
            # Modify the outlier status of the datapoints.
            self.CurIsotherms['IsOutlier'] = 0
            self.CurIsotherms.loc[self.OutlierIndex, 'IsOutlier'] = 1
            # Re-plot the data. 
            self.Plot_ComplexModulus()
            # Adjust back the GUI.
            self.Button_Finalize.setEnabled(True)           # Enable back the finalize buttons. 
            self.Menu_Fit_Finalize.setEnabled(True)
            self.Check_Visual_Gstar.setEnabled(True)        # Disable the plot type controllers.
            self.Check_Visual_Phase.setEnabled(True)
            self.Check_Visual_GP.setEnabled(True)
            self.Check_Visual_GPP.setEnabled(True)
            # Disable mouse click handling.
            if self.ConnectionID is not None:
                self.canvas.mpl_disconnect(self.ConnectionID)
                self.ConnectionID = None
            self.Button_SpecifyOutlier.setText("Specify Outliers")      # Change back the name. 
            self.Menu_Fit_Outlier.setText("Specify Outlier")
    # ------------------------------------------------------------------------------------------------------------------
    def Function_On_Mouse_Click_Outlier(self, event):
        # The main function to specify the outliers based on the mouse click. 
        if event.xdata is None or event.ydata is None:                  # Ignore clicks outside the axes
            return
        # Get the coordinate of the clicked points and all datapoints. 
        X_clicked = event.xdata
        Y_clicked = event.ydata
        self.CurIsotherms['Distance'] = 10000
        # Find the closest datapoint to the clicked point. 
        if self.Check_Visual_Gstar.isChecked():
            self.CurIsotherms['Distance'] = \
                np.sqrt((np.log10(self.CurIsotherms['Frequency']) - np.log10(X_clicked)) ** 2 + \
                        (np.log10(self.CurIsotherms['|G*|'])      - np.log10(Y_clicked)) ** 2)
            Index = self.CurIsotherms['Distance'].idxmin()
            X_picked = self.CurIsotherms.loc[Index, 'Frequency']
            Y_picked = self.CurIsotherms.loc[Index, '|G*|']
        elif self.Check_Visual_Phase.isChecked():
            self.CurIsotherms['Distance'] = \
                np.sqrt((np.log10(self.CurIsotherms['Frequency']) - np.log10(X_clicked)) ** 2 + \
                        (self.CurIsotherms['PhaseAngle'] - Y_clicked) ** 2)
            Index = self.CurIsotherms['Distance'].idxmin()
            X_picked = self.CurIsotherms.loc[Index, 'Frequency']
            Y_picked = self.CurIsotherms.loc[Index, 'PhaseAngle']
        elif self.Check_Visual_GP.isChecked():
            self.CurIsotherms['Distance'] = \
                np.sqrt((np.log10(self.CurIsotherms['Frequency'])      - np.log10(X_clicked)) ** 2 + \
                        (np.log10(self.CurIsotherms['StorageModulus']) - np.log10(Y_clicked)) ** 2)
            Index = self.CurIsotherms['Distance'].idxmin()
            X_picked = self.CurIsotherms.loc[Index, 'Frequency']
            Y_picked = self.CurIsotherms.loc[Index, 'StorageModulus']
        elif self.Check_Visual_GPP.isChecked():
            self.CurIsotherms['Distance'] = \
                np.sqrt((np.log10(self.CurIsotherms['Frequency'])   - np.log10(X_clicked)) ** 2 + \
                        (np.log10(self.CurIsotherms['LossModulus']) - np.log10(Y_clicked)) ** 2)
            Index = self.CurIsotherms['Distance'].idxmin()
            X_picked = self.CurIsotherms.loc[Index, 'Frequency']
            Y_picked = self.CurIsotherms.loc[Index, 'LossModulus']
        # Add the selected point to the line. 
        Xdata = list(self.Outlier_Line[0].get_xdata())
        Ydata = list(self.Outlier_Line[0].get_ydata())
        if Index in self.OutlierIndex:          # Point is already available in the line. So, remove it. 
            Xdata.remove(X_picked)
            Ydata.remove(Y_picked)
            self.OutlierIndex.remove(Index)
        else:
            Xdata.append(X_picked)
            Ydata.append(Y_picked)
            self.OutlierIndex.append(Index)
        self.Outlier_Line[0].set_data(Xdata, Ydata)         # Update the line. 
        self.fig.set_constrained_layout(True)
        self.canvas.draw()                                  # Redraw the canvas
    # ------------------------------------------------------------------------------------------------------------------
    def Function_Button_Finalize(self, checked):
        # This function will take care of finalizing the Raw Data. After clicking this button, the raw data 
        #   pre-processing options will be disabled and the shifting options will be enabled to user. The button itself,
        #   will also changed and will be used to redo the shifting and back to pre-processing. 
        if checked:
            # The pre-processing is done. Adjust the GUI. 
            self.Button_SpecifyOutlier.setEnabled(False)
            self.Menu_Fit_Outlier.setEnabled(False)
            self.Button_Finalize.setText('Redo Pre-Processing')
            self.Menu_Fit_Finalize.setText('Redo Pre-Processing')
            self.DropDown_ShiftMethod.setCurrentIndex(0)
            self.DropDown_ShiftModel.setCurrentIndex(0)
            self.DropDown_ShiftSeparate.setCurrentIndex(1)
            self.DropDown_ShiftMethod.setEnabled(True)
            self.DropDown_ShiftModel.setEnabled(True)
            self.DropDown_ShiftSeparate.setEnabled(False)
            self.ReferenceTemp.setEnabled(True)
            self.Button_ApplyShift.setEnabled(True)
            self.Menu_Fit_ApplyShift.setEnabled(True)
        else:
            # The "Redo" button was pressed, therefore, go back to the pre-processing. Adjust the GUI:
            self.Button_SpecifyOutlier.setEnabled(True)
            self.Menu_Fit_Outlier.setEnabled(True)
            self.Button_Finalize.setText('Finalize Inputs')
            self.Menu_Fit_Finalize.setText('Finalize Raw Data')
            self.DropDown_ShiftMethod.setEnabled(False)
            self.DropDown_ShiftModel.setEnabled(False)
            self.DropDown_ShiftSeparate.setEnabled(False)
            self.ReferenceTemp.setEnabled(False)
            self.Button_ApplyShift.setEnabled(False)
            self.Menu_Fit_ApplyShift.setEnabled(False)
            self.DropDown_FitType.setEnabled(False)
            self.DropDown_MCModel.setEnabled(False)
            self.Button_Construct_MC.setEnabled(False)
            self.Menu_Fit_ConstructMC.setEnabled(False)
            # Modify the analysis progress. 
            self.AnalysisProgress = 0
            # Redo the plotting. 
            self.Plot_ComplexModulus()
            self.Button_Finalize.setEnabled(True)           # Enable back the finalize buttons. 
            self.Check_Visual_Gstar.setEnabled(True)        # Disable the plot type controllers.
            self.Check_Visual_Phase.setEnabled(True)
            self.Check_Visual_GP.setEnabled(True)
            self.Check_Visual_GPP.setEnabled(True)
            # Clear the shift plot and shift table. 
            self.Shift_axes.clear()
            self.Shift_axes.set_xlabel('Temperature (°C)', fontsize=8, fontweight='bold', color='k')
            self.Shift_axes.set_ylabel('log(aT)', fontsize=8, fontweight='bold', color='k')
            self.Shift_axes.set_title('Shift Factors', fontsize=8, fontweight='bold', color='k')
            self.Shift_axes.grid(which='both', color='gray', alpha=0.1)
            self.Shift_canvas.draw()
            # Clear the shift factor table and fitted model. 
            self.LabelL03_ShiftFactorModel = QLabel('Shift Factor Model: N/A')
            self.LabelL03_ShiftFactorCoeff = QLabel('C1 = N/A\nC2 = N/A\nC3 = N/A')
            self.ShiftFactor_Table.setRowCount(5)
            for i, temp in enumerate([10, 20, 30, 40, 50]):
                self.ShiftFactor_Table.setItem(i, 0, QTableWidgetItem(temp))
                self.ShiftFactor_Table.setItem(i, 1, QTableWidgetItem('0.00'))
            self.MCCoeff_Table.setRowCount(4)
            for i in range(4):
                self.MCCoeff_Table.setItem(i, 0, QTableWidgetItem(f'Parameter {i+1}'))
                self.MCCoeff_Table.setItem(i, 1, QTableWidgetItem('N/A'))
            self.MCIndex_Table.setRowCount(3)
            for i, parameter in enumerate(['Rheology index', 'Crossover frequency (rad/s)', 'Crossover modulus']):
                self.MCIndex_Table.setItem(i, 0, QTableWidgetItem(parameter))
                self.MCIndex_Table.setItem(i, 1, QTableWidgetItem('N/A'))
            self.MCError_Table.setRowCount(4)
            for i, parameter in enumerate(['MLAE (|G*|)', 'MLAE (δ)', "MLAE (G')", 'MLAE (G")']):
                self.MCError_Table.setItem(i, 0, QTableWidgetItem(parameter))
                self.MCError_Table.setItem(i, 1, QTableWidgetItem('N/A'))
        self.TabWidget.setCurrentIndex(0)
    # ------------------------------------------------------------------------------------------------------------------
    def Function_DropDown_ShiftMethod(self):
        # This function is only adjust the GUI.
        if self.DropDown_ShiftMethod.currentIndex() == 0:       # Free shifting. 
            self.DropDown_ShiftSeparate.setEnabled(False)
            self.DropDown_ShiftSeparate.setCurrentIndex(1)
            self.DropDown_MCModel.setEnabled(False)
            self.DropDown_FitType.setEnabled(False)
            self.Button_Construct_MC.setEnabled(False)
            self.DropDown_ShiftModel.clear()
            self.DropDown_ShiftModel.addItems(['Gordon & Shaw (1994)', 'Log-linear Extrapolation', 
                                               'Log-Parabula Extrapolation'])
            self.DropDown_ShiftModel.setCurrentIndex(0)
        elif self.DropDown_ShiftMethod.currentIndex() == 1:     # Shifting along side fitting the master curve. 
            self.DropDown_ShiftSeparate.setEnabled(False)
            self.DropDown_ShiftSeparate.setCurrentIndex(1)
            self.DropDown_MCModel.setEnabled(True)
            self.DropDown_FitType.setEnabled(True)
            self.Button_Construct_MC.setEnabled(True)
            self.DropDown_ShiftModel.clear()
            self.DropDown_ShiftModel.addItems(['WLF', 'Kaelble', 'Modified Kaelble', 'Witczak', 
                                               'Arrhenius', 'Modified Arrhenius'])
            self.DropDown_ShiftModel.setCurrentIndex(0)
    # ------------------------------------------------------------------------------------------------------------------
    def Function_Button_ApplyShift(self):
        # This button will apply the free shifting, provide the results, and plot the shifted values.
        if self.DropDown_ShiftMethod.currentIndex() != 0:
            raise Exception(f'The "Apply Shift" button should be available only when "Free Shift" is selected. " + \
                            f"Please check manually!')
        if self.DropDown_ShiftModel.currentIndex() == 0:
            # Using the Gordon & Shaw (1994) method. 
            DensityShift = {'Active': False}        # Disable density-temperature shift for now!
            Tglassy      = -30                      # Use -30C as glassy temperature for now!
            ShiftFactors, self.CurIsotherms = FreeShift_GordonShaw1994(self.CurIsotherms, 
                                                                       float(self.ReferenceTemp.text()), 
                                                                       Tglassy, 
                                                                       DensityShift)
        elif self.DropDown_ShiftModel.currentIndex() == 1:
            # Using the log-linear extrapolation method. (NIY=Not Implemented Yet :)
            MsgBox_FreeShift2_NIY = QMessageBox()
            MsgBox_FreeShift2_NIY.setIcon(QMessageBox.Critical)
            MsgBox_FreeShift2_NIY.setWindowTitle("Under Development")
            MsgBox_FreeShift2_NIY.setText(f"The free shifting method using 'log-linear extrapolation' is under " + \
                                          f"development. Will be added in future versions.\n" + \
                                          f"Please use the Gordon & Shaw (1994) method.")
            MsgBox_FreeShift2_NIY.setStandardButtons(QMessageBox.Ok)
            MsgBox_FreeShift2_NIY.exec_()
            return
        elif self.DropDown_ShiftModel.currentIndex() == 2:
            # Using the log-parabola extrapolation method. 
            MsgBox_FreeShift3_NIY = QMessageBox()
            MsgBox_FreeShift3_NIY.setIcon(QMessageBox.Critical)
            MsgBox_FreeShift3_NIY.setWindowTitle("Under Development")
            MsgBox_FreeShift3_NIY.setText(f"The free shifting method using 'log-Parabola extrapolation' is under " + \
                                          f"development. Will be added in future versions.\n" + \
                                          f"Please use the Gordon & Shaw (1994) method.")
            MsgBox_FreeShift3_NIY.setStandardButtons(QMessageBox.Ok)
            MsgBox_FreeShift3_NIY.exec_()
            return
        # Saving the shift factors. 
        self.Results['ShiftFactor_Data'] = ShiftFactors
        # -----------------------------------------------
        # Modify the analysis progress. 
        self.AnalysisProgress = 1
        # -----------------------------------------------
        # Plot the results. 
        self.Plot_ComplexModulus()
        # -----------------------------------------------
        # Adjust the GUI and show the results in the result section. 
        self.Button_ApplyShift.setEnabled(False)
        self.ReferenceTemp.setEnabled(False)
        self.DropDown_ShiftSeparate.setEnabled(False)
        self.DropDown_ShiftModel.setEnabled(False)
        self.DropDown_ShiftMethod.setEnabled(False)
        self.DropDown_MCModel.setEnabled(True)
        self.DropDown_FitType.setEnabled(True)
        self.Button_Construct_MC.setEnabled(True)
        # -----------------------------------------------
        # Plot the shift factors. 
        self.Shift_axes.clear()
        self.Shift_axes.plot(list(ShiftFactors.keys()), list(ShiftFactors.values()), ls='--', lw=0.5,
                             marker='o', ms=3, color='k', label='datapoints')
        self.Shift_axes.set_xlabel('Temperature (°C)', fontsize=8, fontweight='bold', color='k')
        self.Shift_axes.set_ylabel('log(aT)', fontsize=8, fontweight='bold', color='k')
        self.Shift_axes.set_title('Shift Factors', fontsize=8, fontweight='bold', color='k')
        self.Shift_axes.grid(which='both', color='gray', alpha=0.1)
        self.Shift_axes.legend(fontsize=8)
        self.Shift_canvas.draw()
        # -----------------------------------------------
        # Fill the shift factor text section. 
        Temp = list(ShiftFactors.keys())
        aT   = list(ShiftFactors.values())
        self.ShiftFactor_Table.setRowCount(len(Temp))
        for i, temp in enumerate(Temp):
            self.ShiftFactor_Table.setItem(i, 0, QTableWidgetItem(f'{temp:.2f}'))
            self.ShiftFactor_Table.setItem(i, 1, QTableWidgetItem(f'{aT[i]:.4f}'))
        # Fill the labels.
        C1, C2 = Fit_ShiftModel_WLF(Temp, aT, float(self.ReferenceTemp.text()))
        self.LabelL03_ShiftFactorModel.setText('Shift Factor Model: WLF\n\t(Only FYI)')
        self.LabelL03_ShiftFactorCoeff.setText(f'    C1 = {C1:.3f}\n    C2 = {C2:.3f}')
    # ------------------------------------------------------------------------------------------------------------------
    def Function_DropDown_MCModel_Change(self):
        if self.DropDown_MCModel.currentIndex() == 0:       # CA model is selected.
            self.DropDown_FitType.clear()
            self.DropDown_FitType.addItems(['Fit to Complex modulus (|G*|)', 'Fit to Phase angle (δ)', 
                                            "Fit to Storage modulus (G')", 'Fit to Loss modulus(G")'])
            self.DropDown_FitType.setCurrentIndex(0)
        elif self.DropDown_MCModel.currentIndex() == 1:
            self.DropDown_FitType.clear()
            self.DropDown_FitType.addItems(['Fit to Complex modulus (|G*|) [4 params]', 
                                            "Fit to Storage modulus (G') [4 params]", 
                                            'Fit to Loss modulus(G") [4 params]', 
                                            'Fit to Complex modulus (|G*|) and Phase angle (δ) simultaneously ' + 
                                            '[7 param]'])
            self.DropDown_FitType.setCurrentIndex(0)
        else:           # Will be completed later. 
            pass
    # ------------------------------------------------------------------------------------------------------------------
    def Function_Button_Construct_MC(self):
        # This is the main function that performs the construction of the master curve. 
        # Check if the free shift was applied. 
        if self.DropDown_ShiftMethod.currentIndex() == 0:       # For the already shifted isotherms. 
            # Check the model. 
            if self.DropDown_MCModel.currentIndex() == 0:       # For the Christensen-Anderson Model.
                MC_Res = Fit_MC_ChristensenAnderson(self.CurIsotherms, self.DropDown_FitType.currentIndex())
                self.Results['MC_Model'] = 'CA'
            elif self.DropDown_MCModel.currentIndex() == 1:     # For the Christensen-Anderson-Marasteanu Model. 
                MC_Res = Fit_MC_ChristensenAndersonMarasteanu(self.CurIsotherms, self.DropDown_FitType.currentIndex())
                self.Results['MC_Model'] = 'CAM'

        # Save the results. 
        self.Results['MC_FitType']      = self.DropDown_FitType.currentIndex()
        self.Results['MC_Coeff']        = MC_Res['MC_Coeff']
        self.Results['MC_Coeff_Labels'] = MC_Res['MC_Coeff_Labels']
        self.Results['MC_Index']        = MC_Res['MC_Index']
        self.Results['MC_Index_Labels'] = MC_Res['MC_Index_Labels']
        self.Results['MC_Error']        = MC_Res['MC_Error']
        self.Results['MC_Error_Labels'] = MC_Res['MC_Error_Labels']
        self.Results['MC_Plot']         = {'Freq': MC_Res['Plot_Freq'] , 'Gstar': MC_Res['Plot_Gstar'], 
                                           'GP': MC_Res['Plot_Storage'], 'GPP': MC_Res['Plot_Loss'],
                                           'Phase': MC_Res['Plot_Phase']}
        # Modify the analysis progress. 
        self.AnalysisProgress = 2
        # Call the plotting function. 
        self.Plot_ComplexModulus()
        # -----------------------------------------------
        # Adjust the GUI and show the results in the result section. 
        self.DropDown_MCModel.setEnabled(False)
        self.DropDown_FitType.setEnabled(False)
        self.Button_Construct_MC.setEnabled(False)
        self.Menu_Fit_ConstructMC.setEnabled(False)
        # -----------------------------------------------
        # Fill the Master curve text section.
        self.LabelL03_MCModel.setText(f'Master curve model: {self.Results["MC_Model"]}')
        self.LabelL03_MCFit.setText(f'Master curve fitting type: {self.DropDown_FitType.currentText()}')
        self.MCCoeff_Table.setRowCount(len(self.Results["MC_Coeff_Labels"]))
        for i in range(len(self.Results["MC_Coeff_Labels"])):
            self.MCCoeff_Table.setItem(i, 0, QTableWidgetItem(self.Results["MC_Coeff_Labels"][i]))
            if i == 0:
                self.MCCoeff_Table.setItem(i, 1, QTableWidgetItem(f'{self.Results["MC_Coeff"][i]:.4e}'))
            else:
                self.MCCoeff_Table.setItem(i, 1, QTableWidgetItem(f'{self.Results["MC_Coeff"][i]:.4f}'))
        self.MCIndex_Table.setRowCount(len(self.Results["MC_Index_Labels"]))
        for i in range(len(self.Results['MC_Index_Labels'])):
            self.MCIndex_Table.setItem(i, 0, QTableWidgetItem(self.Results['MC_Index_Labels'][i]))
            if i == 0:
                self.MCIndex_Table.setItem(i, 1, QTableWidgetItem(f'{self.Results["MC_Index"][i]:.4e}'))
            else:
                self.MCIndex_Table.setItem(i, 1, QTableWidgetItem(f'{self.Results["MC_Index"][i]:.4f}'))
        self.MCError_Table.setRowCount(len(self.Results["MC_Error_Labels"]))
        for i in range(len(self.Results['MC_Error_Labels'])):
            self.MCError_Table.setItem(i, 0, QTableWidgetItem(self.Results['MC_Error_Labels'][i]))
            self.MCError_Table.setItem(i, 1, QTableWidgetItem(f'{self.Results["MC_Error"][i]:.6f}'))
        self.TabWidget.setCurrentIndex(2)
    # ------------------------------------------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------------------------------------------

# ======================================================================================================================
# ======================================================================================================================
# ======================================================================================================================
if __name__ == '__main__':

    app = QApplication(sys.argv)
    # Connect to a SQL database. 
    conn = sqlite3.connect("C:\\Users\\SF.Abdollahi.ctr\\OneDrive - DOT OST\\GitHub_HWTT_Analysis_Tool\\HWTT_Analysis_Tool\\example\\PTF5_HWTT.db")
    cursor = conn.cursor()
    Main = Main_Window(conn, cursor, 'PTF5_HWTT.db', 'C:\\Users\\SF.Abdollahi.ctr\\OneDrive - DOT OST\\GitHub_HWTT_Analysis_Tool\\HWTT_Analysis_Tool\\example')
    Main.show()
    app.exec()



    app.quit()
    print('finish')