# Title: This script include utility functions used within HWTT Analysis Tool.
#
# Author: Farhad Abdollahi (farhad.abdollahi.ctr@dot.gov)
# Date: 02/21/2025
# ======================================================================================================================

# Importing the required libraries.
import os
import re
import sys
import ast
import datetime
import numpy as np
import pandas as pd
from openpyxl.drawing.image import Image
from PyQt5.QtWidgets import QApplication, QPushButton, QVBoxLayout, QHBoxLayout, QDialog, QTextEdit




class ScrollableMessageBox(QDialog):
    """
    This class generates a scrollable message box for showing the disclaimer to the user. 

    :param QDialog: _description_
    """
    def __init__(self, text, Title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(Title)
        self.resize(700, 500)
        layout = QVBoxLayout(self)
        # Create a scrollable text area
        text_edit = QTextEdit(self)
        text_edit.setPlainText(text)
        text_edit.setReadOnly(True)
        text_edit.setMinimumSize(380, 200)
        Font = text_edit.font()
        Font.setPointSize(12)
        Font.setFamily("Times New Roman")
        text_edit.setFont(Font)
        layout.addWidget(text_edit)
        # Create buttons
        btn_accept = QPushButton("Accept", self)
        btn_exit = QPushButton("Exit", self)
        btn_accept.clicked.connect(self.accept)
        btn_exit.clicked.connect(self.reject)
        btn_accept.setFixedSize(100, 40)
        btn_exit.setFixedSize(100, 40)
        BottonLayout = QHBoxLayout()
        BottonLayout.addWidget(btn_accept)
        BottonLayout.addWidget(btn_exit)
        layout.addLayout(BottonLayout)
# ======================================================================================================================
# ======================================================================================================================
# ======================================================================================================================


def Read_HWTT_Text_File(FilePath):
    """
    This function reads the input text file and extract the array of number passes and corresponding rut depths (mm). 

    :param FilePath: The full path to the given text file. 
    """
    # Read the input text file (NOTE: the HWTT device at TFHRC uses encoding of 'utf-16'). 
    with open(FilePath, 'r', encoding='utf-16') as file:
        cont = file.readlines()
    # Find the starting index for the result. 
    for i, line in enumerate(cont):
        if '[GRAPH]' in line:
            idx = i
            break
    # Extract the results. 
    pattern = r"^(-?\d+)\t(-?\d+\.\d+)\t(-?\d+\.\d+)\n$"
    Passes, RutDepth, Temperature = [], [], []
    for i in range(idx+2, len(cont)):
        match = re.match(pattern, cont[i])
        if match:
            Passes.append(int(match.group(1)))
            RutDepth.append(float(match.group(2)))
            Temperature.append(float(match.group(3)))
        else:
            break
    # Convert the results into numpy array. 
    Passes      = np.array(Passes)
    RutDepth    = np.array(RutDepth)
    Temperature = np.array(Temperature)
    # ------------------------------------------------------------------------------------------------------------------
    # Extract some properties from the text file. 
    Props = {'Test_Condition': '', 'Test_Temperature': -1, 'Test_Date': '', 'Test_Time': '', 'Wheel_Side': '', 
             'Test_Name': ''}
    # Check the wheel side from the file name. 
    for i in range(idx):        # Search only over the lines before the results. 
        if 'Mode:' in cont[i]:
            TestCondition = cont[i].split('Mode:')[1].replace('\n', '')
            if 'water' in TestCondition.lower():
                Props['Test_Condition'] = 'Wet'
            elif 'dry' in TestCondition.lower():
                Props['Test_Condition'] = 'Dry'
            else:
                Props['Test_Condition'] = TestCondition
        elif 'Temperature:' in cont[i]:
            Props['Test_Temperature'] = cont[i].split('Temperature:')[1].replace('\n', '').replace('°C', '')
        elif 'Test date:' in cont[i]:
            Date  = cont[i].split('Test date:')[1].replace('\n', '')
            Month = int(Date.split('/')[0].replace(' ', ''))
            Day   = int(Date.split('/')[1])
            Year  = int(Date.split('/')[-1].replace(' ', ''))
            Props['Test_Date'] = f'{Month:02d}/{Day:02d}/{Year:04d}'
        elif 'Test time:' in cont[i]:
            Time = cont[i].split('Test time:')[1].replace('\n', '')
            Hr   = int(Time.split(':')[0].replace(' ', ''))
            Min  = int(Time.split(':')[1])
            if 'PM' in Time:
                Hr += 12
            Props['Test_Time'] = f'{Hr:02d}:{Min:02d}'
        elif 'Test type:' in cont[i]:
            if 'right' in cont[i].lower():
                Props['Wheel_Side'] = 'Right'
            elif 'left' in cont[i].lower():
                Props['Wheel_Side'] = 'Left'
            else:
                if 'RIGHT' in os.path.basename(FilePath):
                    Props['Wheel_Side'] = 'Right'
                elif 'LEFT' in os.path.basename(FilePath):
                    Props['Wheel_Side'] = 'Left'
                else:
                    Props['Wheel_Side'] = 'N/A'
        elif 'Test:' in cont[i]:
            Props['Test_Name'] = cont[i].split('Test:')[1].replace('\n', '')

    # Return the results. 
    return Passes, RutDepth, Temperature, Props
# ======================================================================================================================
# ======================================================================================================================
# ======================================================================================================================


def Read_HWTT_Excel_File(FilePath):
    """
    This function reads the input Excel file and extract the array of number passes and corresponding rut depths (mm). 

    :param FilePath: The full path to the given text file. 
    """
    try:
        # Reading the data (First two columns). 
        data = pd.read_excel(FilePath, sheet_name='Sheet1', usecols='A:C', names=['Pass', 'Rut', 'Temp'], skiprows=0)
        Pass = data['Pass'].to_numpy()
        Rut  = data['Rut'].to_numpy()
        Temp = data['Temp'].to_numpy()
        Index= np.where((~ np.isnan(Pass)) & (~ np.isnan(Rut)))[0]
        if len(Index) == 0:
            raise Exception(f'Input Excel file is empty!!!!')
        Pass = Pass[Index].astype(int)
        Rut  = Rut[Index].astype(float)
        Temp = Temp[Index]
        # Reading the properties. 
        data = pd.read_excel(FilePath, sheet_name='Sheet1', usecols='E:F', skiprows=1)
        Props = {
            'Test_Condition'    : data.loc[0, 'Value'], 
            'Test_Temperature'  : float(data.loc[1, 'Value']), 
            'Wheel_Side'        : data.loc[2, 'Value'], 
            'Test_Date'         : '01/01/1990', 
            'Test_Time'         : '00:00', 
            'Test_Name'         : data.loc[3, 'Value'], 
            'ID Number'         : 0}
        Time = data.loc[6, 'Value']
        if type(Time) == datetime.time:
            Props['Test_Time'] = Time.strftime("%H:%M")
        elif type(Time) == str and Time != '':
            try:
                Props['Test_Time'] = f"{int(Time.split(':')[0]):02d}:{int(Time.split(':')[1]):02d}"
            except:
                pass
        Date = data.loc[7, 'Value']
        if type(Date) == datetime.date:
            Props['Test_Date'] = Date.strftime("%m/%d/%Y")
        elif type(Date) == datetime.date:
            Props['Test_Date'] = Date.strftime("%m/%d/%Y")
        elif type(Date) == str and re.search(r'(\d+/\d+/\d+)', Date):
            match = re.search(r'(\d+/\d+/\d+)', Date)
            Props['Test_Date'] = Date
        elif type(Date) == str and Date != '':
            Month = int(Date.split('-')[0])
            Day   = int(Date.split('-')[1])
            Year  = int(Date.split(' ')[0].split('-')[-1])
            Props['Test_Date'] = f'{Month:02d}/{Day:02d}/{Year:04d}'
        IDNum = data.loc[4, 'Value']
        if type(IDNum) == str:
            try: 
                IDNum = int(IDNum)
            except:
                IDNum = 0
        Props['ID Number'] = IDNum
        # Modify the temperatures. 
        if np.all(np.isnan(Temp)):
            Temp = np.ones(Temp.shape) * Props['Test_Temperature']
        else:
            Temp = Temp.astype(float)
        # Return the results. 
        return Pass, Rut, Temp, Props
    except Exception as err:
        return err, None, None, None
# ======================================================================================================================
# ======================================================================================================================
# ======================================================================================================================


def Array_to_Binary(Arr):
    """
    This function converts a np.ndarray to binary bytes, so that it could be stored in SQL table. 

    :param Arr: Input numpy array.
    :return: three variable, including (i) serialized array in binary bytes, (ii) array shape as string, and (iii) 
    array type as string.
    """
    return Arr.tobytes(), str(Arr.shape), str(Arr.dtype)
# ======================================================================================================================
# ======================================================================================================================
# ======================================================================================================================


def Binary_to_Array(BinaryArr, StrShape, StrDtype):
    """
    This function converts the binary bytes into a np.ndarray. This is the reverse function for the "Array_to_Binary".

    :param BinaryArr: Serialized binary bytes of the array.
    :param StrShape: Shape of the array as string. 
    :param StrDtype: type of the data in array as string.
    """
    Shape = ast.literal_eval(StrShape)
    # Shape = int(StrShape[1:-1].split(',')[0])
    return np.frombuffer(BinaryArr, dtype=StrDtype).reshape(Shape)
# ======================================================================================================================
# ======================================================================================================================
# ======================================================================================================================


def Read_Resize_Image(path, targetPixel):
    """
    This function reads the image (*.png, *.jpg) and resize it to properly fit in the Excel file. 

    :param path: The complete/relative path to the image. 
    :param targetPixel: The height of the image after resize in pixels, given the fixed aspect ratio. 
    :param return: the resized image object. 
    """
    Image_Obj = Image(path)
    Ratio = targetPixel / Image_Obj.height
    Image_Obj.height = targetPixel
    Image_Obj.width  = Image_Obj.width * Ratio
    return Image_Obj
# ======================================================================================================================
# ======================================================================================================================
# ======================================================================================================================


def ResourcePath(relative_path):
    """
    Get the absolute path to the resource, works for dev and PyInstaller build.

    :param RelativePath: The relative path, which is going to be converted to the Resource Path. 
    """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller stores resources in a temporary folder (_MEIPASS)
        return os.path.join(sys._MEIPASS, relative_path)
    else:
        # Use the relative path during development
        return os.path.join(os.path.abspath(relative_path))