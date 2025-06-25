# Title: This script include classes for the review page of the HWTT Analysis Tool.
#
# Author: Farhad Abdollahi (farhad.abdollahi.ctr@dot.gov)
# Date: 06/24/2025
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
from scripts.Alg02_SQL_Manager import Get_DB_SummaryData, Get_Identifier_Combinations
from scripts.Alg03_HWTT_Analysis_Functions import HWTT_Analysis, ModelPower, TsengLyttonModel, YinModel


class DB_ReviewPage(QMainWindow):
    """
    This class design a review database page in which the database is shown as table where user can select any specific 
    sample and revise its analysis procedure. 
    """
    def __init__(self, conn, cursor, DB_Name, DB_Folder, stack, shared_data):
        # Initiate the required parameters.
        super().__init__()
        self.conn = conn            # connection to the SQL database.
        self.cursor = cursor        # cursor for running the SQL commands. 
        self.DB_Name = DB_Name      # Name of the database.
        self.DB_Folder = DB_Folder  # Directory at which the database is saved. 
        self.stack = stack
        self.shared_data = shared_data
        self.stack.currentChanged.connect(self.Function_Button_Sync_Summary_Info)
        self.ColumnNames = ['ID', 'B-number', 'Lane #', 'Lift Location', 'Lab Aging', 'Rep #', 'Wheel Side',
                            'Max Rutting (mm)', 'Max Passes', 
                            'Rutting @ 10k (mm) [2PP]', 'Rutting @ 20k (mm) [2PP]', 
                            'Stripping Number [2PP]', 'SIP [2PP]', 'SIP @ 12.5 mm [2PP]', 
                            'Creep Slope [2PP]', 'Stripping Slope [2PP]', 
                            'Rutting @ 10k (mm) [Yin]', 'Rutting @ 20k (mm) [Yin]', 
                            'Stripping Number [Yin]', 'SIP [Yin]', 'SIP @ 12.5 mm [Yin]', 
                            'Creep Slope [Yin]', 'Stripping Slope [Yin]', 
                            'Rutting @ 10k (mm) [6deg]', 'Rutting @ 20k (mm) [6deg]', 
                            'Stripping Number [6deg]', 'Creep Slope [6deg]', 'Is Outlier?']
        self.SQL_ColumnNames = [
            'id', 'Bnumber', 'Lane_Num', 'Lift_Location', 'Lab_Aging', 'RepNumber', 'Wheel_Side',
            'TPP_Max_Rut_mm', 'TPP_Max_Pass', 
            'TPP_RuttingAt10k_mm', 'TPP_RuttingAt20k_mm', 
            'TPP_StrippingNumber', 'TPP_SIP', 'TPP_SIP_Adj', 
            'TPP_CreepLine_Slope', 'TPP_StrippingLine_Slope', 
            'Yin_RuttingAt10k_mm', 'Yin_RuttingAt20k_mm', 
            'Yin_StrippingNumber', 'Yin_SIP', 'Yin_SIP_Adj', 
            'Yin_CreepLine_Slope', 'Yin_StrippingLine_Slope', 
            'Poly6_RuttingAt10k_mm', 'Poly6_RuttingAt20k_mm', 
            'Poly6_StrippingNumber', 'Poly6_CreepLine_Slope', 'IsOutlier']
        # self.ColumnNamesAnalysis = [
        #     'B_Number', 'Lab_Aging_Condition', 'Num_Data', 
        #     'ICO_Baseline_mean', 'ICO_Baseline_std', 'ICO_Baseline_COV', 
        #     'ICO_Deconv_mean', 'ICO_Deconv_std', 'ICO_Deconv_COV', 
        #     'ICO_Tangential_mean', 'ICO_Tangential_std', 'ICO_Tangential_COV', 
        #     'ISO_Baseline_mean', 'ISO_Baseline_std', 'ISO_Baseline_COV', 
        #     'ISO_Deconv_mean', 'ISO_Deconv_std', 'ISO_Deconv_COV', 
        #     'ISO_Tangential_mean', 'ISO_Tangential_std', 'ISO_Tangential_COV', 
        #     'Aliphatic_Area_Baseline_mean', 'Aliphatic_Area_Baseline_std', 'Aliphatic_Area_Baseline_COV', 
        #     'Aliphatic_Area_Tangential_mean', 'Aliphatic_Area_Tangential_std', 'Aliphatic_Area_Tangential_COV', 
        #     'Carbonyl_Peak_Wavenumber_mean', 'Carbonyl_Peak_Wavenumber_std', 'Carbonyl_Peak_Wavenumber_COV', 
        #     'Sulfoxide_Peak_Wavenumber_mean', 'Sulfoxide_Peak_Wavenumber_std', 'Sulfoxide_Peak_Wavenumber_COV', 
        #     'Carbonyl_Peak_Absorption_mean', 'Carbonyl_Peak_Absorption_std', 'Carbonyl_Peak_Absorption_COV', 
        #     'Sulfoxide_Peak_Absorption_mean', 'Sulfoxide_Peak_Absorption_std', 'Sulfoxide_Peak_Absorption_COV']
        self.IdentifierCombs = Get_Identifier_Combinations(self.cursor)
        self.initUI()
    # ------------------------------------------------------------------------------------------------------------------
    def initUI(self):
        # Initiate the user interface. 
        # Main widget and layout
        main_widget = QWidget()
        layout = QHBoxLayout(main_widget)                   # Make a horizontal layout.
        self.setCentralWidget(main_widget)
        # self.setStyleSheet("background-color: #f0f0f0;")
        # Generate the left and right layouts, where left one include the main table of results, and right one include 
        #   the sections for: Summary of DB, Filter and find, and action buttons. 
        # --------------------------------------------------------------------------------------------------------------
        # ---------------- Left Layout (Main table) --------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # Section 01 (Left Layout): Main Table.
        SectT01 = QGroupBox("Review Table")
        SectT01.setStyleSheet("QGroupBox { font-weight: bold; }")
        SectT01_Layout = QVBoxLayout()
        self.SectT01_Label_NumRecords = QLabel('Number of records shown in table: 0')
        self.SectT01_Label_NumRecords.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        # Define the table. 
        self.Table = QTableWidget()
        self.Table.setRowCount(10)
        self.Table.setColumnCount(len(self.ColumnNames))
        self.Table.setHorizontalHeaderLabels(self.ColumnNames)
        self.Table.setSelectionBehavior(self.Table.SelectRows)
        self.Table.setSelectionMode(self.Table.SingleSelection)
        # Place them inside the section. 
        SectT01_Layout.addWidget(self.SectT01_Label_NumRecords)
        SectT01_Layout.addWidget(self.Table)
        SectT01.setLayout(SectT01_Layout)
        layout.addWidget(SectT01, 75)
        # --------------------------------------------------------------------------------------------------------------
        # ------------- Right Layout (Sections for Summary of DB, Filter and Search, and Action Buttons) ---------------
        # --------------------------------------------------------------------------------------------------------------
        SummaryData = Get_DB_SummaryData(self.cursor)
        Right_Layout = QVBoxLayout()
        # Section 02 (Right Layout, Top section): Summary of DB.
        SectT02 = QGroupBox("Summary of DB")
        SectT02.setStyleSheet("QGroupBox { font-weight: bold; }")
        SectT02_Layout = QVBoxLayout()
        SummayText_Label = QLabel("This section shows a summary of the analyzed data available in the Database.")
        SummayText_Label.setWordWrap(True)
        SectT02_Layout.addWidget(SummayText_Label)
        SectT02_FormLayout = QFormLayout()          # Define a form layout.
        # Create the labels in Section 02.
        Label01 = QLabel("Number of data:")
        self.Label_NumData = QLabel(f'{SummaryData["NumRows"]}')
        Label02 = QLabel("Number of valid data:")
        self.Label_NumValidData = QLabel(f'{SummaryData["NumValidRows"]}')
        Label03 = QLabel("Avg Number Replicates:")
        self.Label_AvgNumReplicates = QLabel(f'{SummaryData["AvgNumRep"]:.1f}')
        Label04 = QLabel("Number of unique B-numbers:")
        self.Label_NumUniqueBnum = QLabel(f'{SummaryData["NumUniqueBnumber"]}')
        Label05 = QLabel("Number of unique Lab agings:")
        self.Label_NumUniqueLabAge = QLabel(f'{SummaryData["NumUniqueLabAging"]}')
        Label06 = QLabel("Number of Unique Bnum/LabAge:")
        self.Label_NumUniqueBnumLabAge = QLabel(f'{SummaryData["NumUniqueBnumLabAge"]}')
        # Syncing button.
        self.Button_Sync = QPushButton("Refresh summay")
        self.Button_Sync.setFont(QFont("Arial", 8))
        self.Button_Sync.clicked.connect(self.Function_Button_Sync_Summary_Info)
        self.Button_Sync.setFixedSize(100, 30)
        self.Button_Sync.setStyleSheet(
        """
        QPushButton:hover {background-color: lightgray;}
        QPushButton:pressed {background-color: gray;}
        """)
        # Place the labels in the GUI.
        SectT02_FormLayout.addRow(Label01,  self.Label_NumData)
        SectT02_FormLayout.addRow(Label02,  self.Label_NumValidData)
        SectT02_FormLayout.addRow(Label03,  self.Label_AvgNumReplicates)
        SectT02_FormLayout.addRow(Label04, self.Label_NumUniqueBnum)
        SectT02_FormLayout.addRow(Label05, self.Label_NumUniqueLabAge)
        SectT02_FormLayout.addRow(Label06, self.Label_NumUniqueBnumLabAge)
        SectT02_Layout.addLayout(SectT02_FormLayout)
        SectT02_Layout.addWidget(self.Button_Sync, alignment=Qt.AlignHCenter | Qt.AlignTop)
        SectT02.setLayout(SectT02_Layout)
        Right_Layout.addWidget(SectT02, 25)
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # Section 03 (Right Layout, Middle section): Search and Filter the DB. 
        SectT03 = QGroupBox("Search and Filter")
        SectT03.setStyleSheet("QGroupBox { font-weight: bold; }")
        SectT03_Layout = QVBoxLayout()
        # First, dropdown for the B-numbers. 
        Label_DropDown01 = QLabel("Select the asphalt binder B-number:")
        self.DropDown_Bnumber = QComboBox()
        self.DropDown_Bnumber.addItems(['Please select...', 'All mixtures'] + 
                                       list(self.IdentifierCombs['Bnumber'].unique()))
        self.DropDown_Bnumber.activated.connect(self.Function_DropDown_Bnumber)
        # Second dropdown for the Lane number.
        Label_DropDown02 = QLabel("Select the lane number:")
        self.DropDown_LaneNumber = QComboBox()
        self.DropDown_LaneNumber.addItems(
            ['All lanes'] + [f'Lane {ii}' for ii in sorted(list(self.IdentifierCombs['Lane_Num'].unique()))])
        self.DropDown_LaneNumber.setEnabled(True)
        self.DropDown_LaneNumber.activated.connect(self.Function_DropDown_LaneNumber) 
        # Next, dropdown for the Laboratory aging state. 
        Label_DropDown03 = QLabel("Select the laboratory aging level:")
        self.DropDown_LabAging = QComboBox()
        self.DropDown_LabAging.addItems(['All aging levels'])
        self.DropDown_LabAging.setEnabled(False)
        self.DropDown_LabAging.activated.connect(self.Function_DropDown_LabAging)
        # Finally, add the apply button. 
        self.Button_Fetch = QPushButton("Fetch data")
        self.Button_Fetch.setStyleSheet(
        """
        QPushButton:hover {background-color: lightgray;}
        QPushButton:pressed {background-color: gray;}
        """)
        self.Button_Fetch.clicked.connect(self.Function_Button_Fetch)
        self.Button_Fetch.setFixedWidth(150)
        # Place the items in the window. 
        SectT03_Layout.addWidget(Label_DropDown01)
        SectT03_Layout.addWidget(self.DropDown_Bnumber)
        SectT03_Layout.addWidget(Label_DropDown02)
        SectT03_Layout.addWidget(self.DropDown_LaneNumber)
        SectT03_Layout.addWidget(Label_DropDown03)
        SectT03_Layout.addWidget(self.DropDown_LabAging)
        SectT03_Layout.addWidget(self.Button_Fetch, alignment=Qt.AlignHCenter)
        SectT03.setLayout(SectT03_Layout)
        Right_Layout.addWidget(SectT03, 25)
        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # Section 03 (Right Layout, Middle section): Search and Filter the DB. 
        SectT04 = QGroupBox("Action Buttons")
        SectT04.setStyleSheet("QGroupBox { font-weight: bold; }")
        SectT04_Layout = QVBoxLayout()
        # Button for Return to the main page.
        self.Button_Main = QPushButton("Main Page")
        self.Button_Main.setFont(QFont("Arial", 11, QFont.Bold))
        self.Button_Main.clicked.connect(self.Function_Button_MainPage)
        self.Button_Main.setFixedSize(160, 35)
        self.Button_Main.setEnabled(True)
        self.Button_Main.setStyleSheet(
        """
        QPushButton:enabled {background-color: #FFE4B5; color: black;}
        QPushButton:hover {background-color: lightgray;}
        QPushButton:pressed {background-color: gray;}
        QPushButton:checked {background-color: lime;}
        """)
        # Button for move to the analysis page.
        self.Button_Analysis = QPushButton("Analysis Page")
        self.Button_Analysis.setFont(QFont("Arial", 11, QFont.Bold))
        self.Button_Analysis.clicked.connect(self.Function_Button_MainPage)
        self.Button_Analysis.setFixedSize(160, 35)
        self.Button_Analysis.setEnabled(True)
        self.Button_Analysis.setStyleSheet(
        """
        QPushButton:enabled {background-color: #FFE4B5; color: black;}
        QPushButton:hover {background-color: lightgray;}
        QPushButton:pressed {background-color: gray;}
        QPushButton:checked {background-color: lime;}
        """)
        SectT04_Layout.addWidget(self.Button_Main)
        SectT04_Layout.addWidget(self.Button_Analysis)
        SectT04.setLayout(SectT04_Layout)
        Right_Layout.addWidget(SectT04, 50)
        layout.addLayout(Right_Layout, 25)
    # ==================================================================================================================
    # =========================== Define the Functions =================================================================
    # ==================================================================================================================
    def Function_Button_Sync_Summary_Info(self):
        # Get the latest summary information. 
        SummaryData = Get_DB_SummaryData(self.cursor)
        # Update the values. 
        self.Label_NumData.setText(f'{SummaryData["NumRows"]}')
        self.Label_NumValidData.setText(f'{SummaryData["NumValidRows"]}')
        self.Label_AvgNumReplicates.setText(f'{SummaryData["AvgNumRep"]:.1f}')
        self.Label_NumUniqueBnum.setText(f'{SummaryData["NumUniqueBnumber"]}')
        self.Label_NumUniqueLabAge.setText(f'{SummaryData["NumUniqueLabAging"]}')
        self.Label_NumUniqueBnumLabAge.setText(f'{SummaryData["NumUniqueBnumLabAge"]}')
        # ----------------------------
        # Also update the identifiers. 
        self.IdentifierCombs = Get_Identifier_Combinations(self.cursor)         # Update the Identifiers.
        # Update the dropdown menu as well. 
        self.DropDown_Bnumber.clear()           # Clear and reset the B-number dropdown menu. 
        self.DropDown_Bnumber.addItems(['Please Select...', 'All mixtures'] + 
                                       list(self.IdentifierCombs['Bnumber'].unique()))
        self.DropDown_Bnumber.setCurrentIndex(0)
        self.DropDown_Bnumber.setEnabled(True)
        self.DropDown_LaneNumber.clear()        # Clear and reset the lane number dropdown menu. 
        self.DropDown_LaneNumber.addItems(
            ['All Lanes'] + [f'Lane {ii}' for ii in sorted(list(self.IdentifierCombs['Lane_Num'].unique()))])
        self.DropDown_LaneNumber.setCurrentIndex(0)
        self.DropDown_LaneNumber.setEnabled(True)
        self.DropDown_LabAging.clear()
        self.DropDown_LabAging.addItems(['All Aging Levels'])
        self.DropDown_LabAging.setCurrentIndex(0)
        self.DropDown_LabAging.setEnabled(False)
        # Return Nothing.
        return
    # ------------------------------------------------------------------------------------------------------------------
    def Function_Button_Fetch(self):
        """
        This function reads the filters and then update the table with the information from the DB. 
        """
        # First clear the table and row selector. 
        self.Function_Clear_Tables()
        self.Table.clearSelection()
        # Read the filters. 
        Bnumber    = self.DropDown_Bnumber.currentText()
        LaneNumber = self.DropDown_LaneNumber.currentText()
        LabAging   = self.DropDown_LabAging.currentText()
        if self.DropDown_Bnumber.currentIndex() == 0:
            # When B-number dropdown is "Please select...", the table should remain empty. 
            return
        elif self.DropDown_Bnumber.currentIndex() == 1:
            # When B-number dropdown is "All mixtures", the table should be filled accordingly, considering other 
            #   dropdown values.
            if self.DropDown_LaneNumber.currentIndex() == 0:
                # It means all lane numbers. 
                if self.DropDown_LabAging.currentIndex() == 0:          # Considering all lab aging levels. 
                    self.cursor.execute(f"SELECT {', '.join(self.SQL_ColumnNames)} FROM HWTT")
                elif self.DropDown_LabAging.currentIndex() > 0:         # Considering a specific lab aging level. 
                    self.cursor.execute(f"SELECT {', '.join(self.SQL_ColumnNames)} FROM HWTT WHERE Lab_Aging = ?", 
                               (LabAging,))
                else:
                    raise ValueError(f'Unexpected error occured! ' + 
                                     f'Lab_Aging index={self.DropDown_LabAging.currentIndex()}')
            elif self.DropDown_LaneNumber.currentIndex() > 0:
                # It means a specific lane is selected. 
                LaneNo = int(LaneNumber[5:])
                if self.DropDown_LabAging.currentIndex() == 0:          # Considering all lab aging levels. 
                    self.cursor.execute(f"SELECT {', '.join(self.SQL_ColumnNames)} FROM HWTT WHERE Lane_Num = ?", 
                               (LaneNo,))
                elif self.DropDown_LabAging.currentIndex() > 0:         # Considering a specific lab aging level. 
                    self.cursor.execute(
                        f"SELECT {', '.join(self.SQL_ColumnNames)} FROM HWTT WHERE Lab_Aging = ?, Lane_Num = ?", 
                        (LabAging, LaneNo))
                else:
                    raise ValueError(f'Unexpected error occured! ' + 
                                     f'Lab_Aging index={self.DropDown_LabAging.currentIndex()}')
            else:
                raise ValueError(f'Unexpected error occured! ' + 
                                 f'Lane_Num index={self.DropDown_LaneNumber.currentIndex()}')
        elif self.DropDown_Bnumber.currentIndex() > 1:
            # When a specific B-number is selected, the table should be filled accordingly, considering other dropdowns, 
            #   it is noted in this case, we don't have to worry about the lane numbers, as the B-number is specific to 
            #   a certain lane number.
            if self.DropDown_LabAging.currentIndex() == 0:      # For all aging levels. 
                self.cursor.execute(f"SELECT {', '.join(self.SQL_ColumnNames)} FROM HWTT WHERE Bnumber = ?", (Bnumber,))
            elif self.DropDown_LabAging.currentIndex() > 0:     # For a specific lab aging level. 
                self.cursor.execute(
                    f"SELECT {', '.join(self.SQL_ColumnNames)} FROM HWTT WHERE Bnumber = ?, Lab_Aging = ?", 
                    (Bnumber, LabAging))
            else:
                raise ValueError(f'Unexpected error occured! ' + 
                                 f'Lab_Aging index={self.DropDown_LabAging.currentIndex()}')
        else:
            raise ValueError(f'Unexpected error occured! ' + 
                             f'Bnumber index={self.DropDown_Bnumber.currentIndex()}')
        # Get the rows. 
        Rows = self.cursor.fetchall()
        # Modify the table with the row value
        self.SectT01_Label_NumRecords.setText(f'Number of records shown in table: {len(Rows)}')
        self.Table.setRowCount(len(Rows))
        for row_idx, row_data in enumerate(Rows):
            for col_idx, cell_data in enumerate(row_data):
                if type(cell_data) == float:
                    item = QTableWidgetItem(f'{cell_data:.4f}')
                else:
                    item = QTableWidgetItem(str(cell_data))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.Table.setItem(row_idx, col_idx, item)
    # ------------------------------------------------------------------------------------------------------------------
    def Function_Clear_Tables(self):
        """
        This function clears the main table. 
        """
        self.Table.clearSelection()         # Clear the row selection in table. 
        self.SectT01_Label_NumRecords.setText('Number of fetched data (rows): 0')
        self.Table.setRowCount(10)          # Set the number of rows to 10 empty rows. 
        for row_idx in range(10):
            for col_idx in range(len(self.ColumnNames)):
                self.Table.setItem(row_idx, col_idx, QTableWidgetItem(''))
    # ------------------------------------------------------------------------------------------------------------------
    def Function_DropDown_Bnumber(self):
        """
        This function called when the user change another B-number. 
        """
        # First, clear the main table.
        self.Function_Clear_Tables()         
        # Depending on the selection, update the other dropdowns. 
        if self.DropDown_Bnumber.currentIndex() == 0:
            # "Please select..." is selected. 
            self.DropDown_LaneNumber.setEnabled(True)
            self.DropDown_LaneNumber.setCurrentIndex(0)
            self.DropDown_LabAging.clear()
            self.DropDown_LabAging.addItems(['All aging levels'])
            self.DropDown_LabAging.setEnabled(False)
            self.DropDown_LabAging.setCurrentIndex(0)
        elif self.DropDown_Bnumber.currentIndex() == 1:
            # "All mixtures" is selected. 
            self.DropDown_Bnumber.clear()
            self.DropDown_Bnumber.addItems(['Please select...', 'All mixtures'] + 
                                           sorted(list(self.IdentifierCombs['Bnumber'].unique())))
            self.DropDown_Bnumber.setCurrentIndex(1)
            self.DropDown_Bnumber.setEnabled(True)
            self.DropDown_LaneNumber.clear()
            self.DropDown_LaneNumber.addItems(
                ['All lanes'] + [f'Lane {ii}' for ii in sorted(list(self.IdentifierCombs['Lane_Num'].unique()))])
            self.DropDown_LaneNumber.setCurrentIndex(0)
            self.DropDown_LaneNumber.setEnabled(True)
            self.DropDown_LabAging.clear()
            self.DropDown_LabAging.addItems(['All aging levels'] + 
                                            sorted(list(self.IdentifierCombs['Lab_Aging'].unique())))
            self.DropDown_LabAging.setEnabled(True)
            self.DropDown_LabAging.setCurrentIndex(0)
        elif self.DropDown_Bnumber.currentIndex() > 1:
            # A specific B-number is selected. 
            Bnumber = self.DropDown_Bnumber.currentText()
            TempDF = self.IdentifierCombs[self.IdentifierCombs['Bnumber'] == Bnumber]
            LaneNo = TempDF.iloc[0, 1]
            self.DropDown_LaneNumber.clear()
            self.DropDown_LaneNumber.addItems(['All lanes', f'Lane {LaneNo}'])
            self.DropDown_LaneNumber.setCurrentIndex(1)
            self.DropDown_LaneNumber.setEnabled(True)
            self.DropDown_LabAging.clear()
            self.DropDown_LabAging.addItems(['All aging levels'] + sorted(list(TempDF['Lab_Aging'].unique())))
            self.DropDown_LabAging.setCurrentIndex(0)
            self.DropDown_LabAging.setEnabled(True)
        else:
            pass
    # ------------------------------------------------------------------------------------------------------------------
    def Function_DropDown_LaneNumber(self):
        """
        This function called when the user select another lane number, change selection. 
        """
        # First, clear the main table.
        self.Function_Clear_Tables()
        # Depending on the selection, update the other dropdowns. 
        if self.DropDown_LaneNumber.currentIndex() == 0:
            # "All lanes" is selected. 
            self.DropDown_Bnumber.clear()
            self.DropDown_Bnumber.addItems(['Please select...', 'All mixtures'] + 
                                           list(self.IdentifierCombs['Bnumber'].unique()))
            self.DropDown_Bnumber.setCurrentIndex(0)
            self.DropDown_Bnumber.setEnabled(True)
            self.DropDown_LaneNumber.clear()
            self.DropDown_LaneNumber.addItems(
                ['All lanes'] + [f'Lane {ii}' for ii in sorted(list(self.IdentifierCombs['Lane_Num'].unique()))])
            self.DropDown_LaneNumber.setCurrentIndex(0)
            self.DropDown_LaneNumber.setEnabled(True)
            self.DropDown_LabAging.clear()
            self.DropDown_LabAging.addItems(['All aging levels'])
            self.DropDown_LabAging.setCurrentIndex(0)
            self.DropDown_LabAging.setEnabled(False)
        elif self.DropDown_LaneNumber.currentIndex() > 0:
            # A specific lane number is selected. 
            LaneNo = int(self.DropDown_LaneNumber.currentText()[5:])
            TempDF = self.IdentifierCombs[self.IdentifierCombs['Lane_Num'] == LaneNo]
            self.DropDown_Bnumber.clear()
            self.DropDown_Bnumber.addItems(['Please select...', 'All mixtures'] + list(TempDF['Bnumber'].unique()))
            self.DropDown_Bnumber.setCurrentIndex(1)
            self.DropDown_Bnumber.setEnabled(True)
            self.DropDown_LaneNumber.clear()
            self.DropDown_LaneNumber.addItems(['All lanes', f'Lane {LaneNo}'])
            self.DropDown_LaneNumber.setCurrentIndex(1)
            self.DropDown_LaneNumber.setEnabled(True)
            self.DropDown_LabAging.clear()
            self.DropDown_LabAging.addItems(['All aging levels'] + sorted(list(TempDF['Lab_Aging'].unique())))
            self.DropDown_LabAging.setCurrentIndex(0)
            self.DropDown_LabAging.setEnabled(True)
        else:
            pass
    # ------------------------------------------------------------------------------------------------------------------
    def Function_DropDown_LabAging(self):
        """
        This function called when the user select another lab aging level, where it needs to clear the table. 
        """
        # Only clear the table. 
        self.Function_Clear_Tables()
    # ------------------------------------------------------------------------------------------------------------------
    def Function_Button_MainPage(self):
        """
        This function changes the stack view from the Review page to the Main page. 
        """
        self.stack.setCurrentIndex(0)  # Switch to the first page, Main page.
    # ------------------------------------------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------------------------------------------