# Title: HWTT analysis functions. 
#
# Author: Farhad Abdollahi (farhad.abdollahi.ctr@dot.gov)
# Date: 02/26/2025
# ======================================================================================================================

# Importing the required libraries.
import os
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit


def HWTT_Analysis(X, Y):
    """
    This is the main function which analyze the HWTT data by fitting two part model and extracting the analysis 
    parameters. 

    :param X: An array of the number of passes (should not include NaN values). 
    :param Y: An array of the rut depths (should not include NaN values). 
    """
    # # Ignore the exact zeros (DONT REMEMBER WHY???!!!). 
    # Indx = np.where(Y > 0)[0]
    # X = X[Indx].copy()
    # Y = Y[Indx].copy()
    # ------------------------------------------------------------------------------------------------------------------
    # First extract the maximum number of passes and its corresponding rut depth. 
    MaxRut = Y[-1]
    MaxPass= X[-1]
    # ------------------------------------------------------------------------------------------------------------------
    # Using the intercept concept by fitting linear regression model, find the boundary of creep phase. 
    Step = min([250, len(X) / 10])  # Use a sweeping span of 250 datapoints (500 cycles) or one-tenth of all datapoints.
    CurIndex = 0
    Intercepts, Indices = [], []
    # ModelRMSE, PredictRMSE = [], []
    while CurIndex < len(X):
        CurIndex += Step
        Xi, Yi = X[CurIndex-Step:CurIndex], Y[CurIndex-Step:CurIndex]       # Extract the data in sweeping region. 
        Coeff = np.polyfit(Xi, Yi, 1)                                       # Fit a line to the datapoints. 
        Intercepts.append(Coeff[1])
        Indices.append(CurIndex)
        # # --------------------------------------------------------------------------
        # # Also calculate the RMSE for the next step predictions. (ELIMINATED)
        # Xm = X[:CurIndex]           # Define the X and Y values to fit the model. 
        # Ym = Y[:CurIndex]
        # # Provide an initial guess. 
        # idx1 = int(len(Xm) / 3)
        # idx2 = int(len(Xm) * 3 / 4)
        # x1, y1 = X[idx1], Y[idx1]
        # x2, y2 = X[idx2], Y[idx2]
        # b = np.log(y1 / y2) / np.log(x1 / x2)
        # a = np.exp(np.log(y1) - b * np.log(x1))
        # # Fit the power model. 
        # coeff, _ = curve_fit(ModelPower, Xm, Ym, p0=[a, b])
        # # Calculate the RMSE. 
        # RMSE = np.sqrt(((Ym - ModelPower(Xm, coeff[0], coeff[1])) ** 2).sum() / len(Xm))
        # ModelRMSE.append(RMSE)
        # # Find the next step data. 
        # Xii, Yii = X[CurIndex:CurIndex+Step], Y[CurIndex:CurIndex+Step]
        # # Calculate the next step RMSE. 
        # if len(Xii) != 0:
        #     RMSE2 = np.sqrt(((Yii - ModelPower(Xii, coeff[0], coeff[1])) ** 2).sum() / len(Xii))
        # else: 
        #     RMSE2 = 0
        # PredictRMSE.append(RMSE2)
        # # --------------------------------------------------------------------------
    Intercepts = np.array(Intercepts)
    idx = np.argmax(Intercepts)
    SN_Index = Indices[idx]
    if SN_Index >= len(X):
        SN_Index = len(X) - 1
    # Fine tune the SN number (search over the 500 points before and after this point).
    Intercepts, Indices = [], []
    for idx in range(SN_Index - 500, SN_Index + 500): 
        if idx > len(X) - 2:
            break
        Xi, Yi = X[idx - int(Step / 2):idx + int(Step / 2)], Y[idx - int(Step / 2):idx + int(Step / 2)]
        Coeff = np.polyfit(Xi, Yi, 1)
        Intercepts.append(Coeff[1])
        Indices.append(idx)
    Intercepts = np.array(Intercepts)
    idx = np.argmax(Intercepts)
    SN_Index = Indices[idx]
    if SN_Index >= len(X):
        SN_Index = len(X) - 1
    SN_estimated = X[SN_Index]
    # ------------------------------------------------------------------------------------------------------------------
    # For the power model to the creep phase of the results. 
    Xi, Yi = X[:SN_Index], Y[:SN_Index]
    idx1 = int(len(Xi) / 3)
    idx2 = int(len(Xi) * 3 / 4)
    x1, y1 = Xi[idx1], Yi[idx1]
    x2, y2 = Xi[idx2], Yi[idx2]
    b = np.log(y1 / y2) / np.log(x1 / x2)
    a = np.exp(np.log(y1) - b * np.log(x1))
    Coeff, _ = curve_fit(ModelPower, Xi, Yi, p0=[a, b])     # Perform the curve fitting. 
    # Using the fitted model, calculate the rutting at Pass = 10,000 and 20,000. 
    Rut10k = ModelPower(10000, Coeff[0], Coeff[1])
    Rut20k = ModelPower(20000, Coeff[0], Coeff[1])
    # ------------------------------------------------------------------------------------------------------------------
    # Rutting due to the stripping. 
    idx = np.argmax(Y[-10:])
    StripRutX = X[-10:][idx]
    StripRut = Y[-10:].max() - ModelPower(StripRutX, Coeff[0], Coeff[1])
    if StripRut < 0: 
        StripRut = 0 
    # ------------------------------------------------------------------------------------------------------------------
    # Fit another power model to the data after the stripping point.
    #   NOTE: The SN was fine tuned and calculated. For pass < SN, the power model was already fitted. For pass > SN, 
    #       the other power model is fitted but with three constraints (1: continiuity, where both models should match 
    #       at SN, 2: consistency, where the slope of both models should match at the point of SN).
    #   NOTE: For better fitting, the number of passes was scaled down [0, 20000] to [0, 1].
    Xp1,  Yp1  = X[X <= SN_estimated], Y[X <= SN_estimated]         # Data for part 1 (already fitted)
    Xp2,  Yp2  = X[X > SN_estimated], Y[X > SN_estimated]           # Data for part 2.
    Xp1t, Xp2t = Xp1 / 20000, Xp2 / 20000                           # Scale down the results. 
    Yp1t, Yp2t = Yp1, Yp2                                           # Don't change the rut depths. 
    tbar       = SN_estimated / 20000                               # Also scale down the stripping point.
    b          = Coeff[1]
    a          = Coeff[0] * (20000 ** b)
    # Define the model for part 2. 
    def ModelPower_Part2_ForFitting(x, beta, gamma):
        # First calculate "alpha" and "Phi" parameters based on consistency and continiuity equations. 
        alpha = a * b * (tbar ** (b - 1)) / (beta * (tbar - gamma) ** (beta - 1))
        Phi = a * tbar ** b - alpha * (tbar - gamma) ** beta
        # Return the results based on the power model for part 2. 
        return alpha * (x - gamma) ** beta + Phi
    # Fit the second model (NOTE: this fitted parameters are in the scaled domain). 
    Coeff2, _ = curve_fit(ModelPower_Part2_ForFitting, Xp2t, Yp2t, 
                          p0=[2.5, -0.8], bounds=([1.005, -10.5], [5.5, -0.1]))
    # Extract all parameters. 
    betat  = Coeff2[0]
    gammat = Coeff2[1]
    alphat = a * b * (tbar ** (b - 1)) / (betat * (tbar - gammat) ** (betat - 1))
    Phit   = a * tbar ** b - alphat * (tbar - gammat) ** betat
    # Convert back to actual scale. 
    beta   = betat
    Phi    = Phit
    alpha  = alphat / (20000 ** beta)
    gamma  = 20000 * gammat
    # ------------------------------------------------------------------------------------------------------------------
    # Constructing the final model. 
    XX  = np.linspace(0, X.max(), num=20001)
    Yp1 = Coeff[0] * XX ** Coeff[1]
    Yp2 = alpha * (XX - gamma) ** beta + Phi
    YY  = Yp1.copy()
    YY[XX > SN_estimated] = Yp2[XX > SN_estimated]
    # ------------------------------------------------------------------------------------------------------------------
    # Find the SIP coefficient as the conflicting point between the tangential line to model at stripping number (SN) 
    #   and the tangential line to the model at the end of the curve. 
    Line1 = [Coeff[0] * Coeff[1] * (SN_estimated ** (Coeff[1] - 1)), None]
    Line1[1] = ModelPower(SN_estimated, Coeff[0], Coeff[1]) - Line1[0] * SN_estimated
    Line2 = [alpha * beta * (X.max() - gamma) ** (beta - 1), None]
    Line2[1] = YY[-1] - Line2[0] * X.max()
    SIP = (Line2[1] - Line1[1]) / (Line1[0] - Line2[0])
    SIP_Yval = Line1[0] * SIP + Line1[1]
    # For the tangential line at the end of the model, we use both fitted model (see above lines), and testing the same 
    #   sweeping concept on data points (not in effect right now, see below commented lines). For this purpose, the 
    #   line with the lowest intercept is used. Sweeping with 50 datapoints increasing rate.
    # # Intercepts, Lines, CurIndex = [], [], len(X) - 1
    # # x1, y1 = X[-1], Y[-1]
    # # while CurIndex > SN_Index:
    # #     CurIndex -= 60
    # #     if CurIndex < SN_Index: break
    # #     # Fit the line using least square method. 
    # #     Slope = np.sum((X[CurIndex:] - x1) * (Y[CurIndex:] - y1)) / np.sum((X[CurIndex:] - x1) ** 2)
    # #     Intercept = y1 - Slope * x1
    # #     line = [Slope, Intercept]
    # #     Intercepts.append(line[1])
    # #     Lines.append(line)
    # # Intercepts = np.array(Intercepts)
    # # if len(Intercepts) == 0:
    # #     SIPPass = SN_estimated
    # #     Line2 = [-1, -1]
    # # else:
    # #     idx = np.argmin(Intercepts)
    # #     Line2 = Lines[idx]
    # #     SIPPass = (Line2[1] - Line1[1]) / (Line1[0] - Line2[0])
    # #     if SIPPass < SN_estimated: 
    # #         SIPPass = SN_estimated
    # # SIP = Line1[0] * SIPPass + Line1[1]
    # ------------------------------------------------------------------------------------------------------------------
    # Return the results. 
    return {
        'Maximum_Rutting_mm': MaxRut,
        'Maximum_Passes': MaxPass,
        'Rutting@10k_mm': Rut10k,
        'Rutting@20k_mm': Rut20k,
        'Rutting_PowerModel_Coeff': Coeff,
        'Rutting_PowerModel_Part2_Coeff': [alpha, beta, gamma, Phi],
        'Stripping_Rutting_mm': StripRut,
        'Stripping_Rutting_Pass': StripRutX,
        'SIP': SIP,
        'SIP_Yval_mm': SIP_Yval,
        'Stripping_Number': SN_estimated,
        'CreepLine': Line1,
        'TangentLine': Line2,
        'Xmodel': XX,
        'Ymodel': YY,
    }
# ======================================================================================================================
# ======================================================================================================================
# ======================================================================================================================


def ModelPower(x, a, b):
    """
    This function simply defines the power model to mathematically model the creep phase in HWTT results. 

    :param x: Float or array of the number of passes. 
    :param a: Model parameter. 
    :param b: Model parameter. 
    :return: Calculated rut depth, corresponds to the number passes (mm). 
    """
    return a * (x ** b)
# ======================================================================================================================
# ======================================================================================================================
# ======================================================================================================================


def ModelPower_Part2(x, alpha, beta, gamma, Phi):
    """
    This function defines the power model to mathematically model the stripping phase in HWTT results. 

    :param x: Float or array of the number of passes. 
    :param alpha: Model parameter. 
    :param beta: Model parameter. 
    :param gamma: Model parameter. 
    :param Phi: Model parameter. 
    :return: Calculated rut depth, corresponds to the number passes (mm). 
    """
    return alpha * (x - gamma) ** beta + Phi
# ======================================================================================================================
# ======================================================================================================================
# ======================================================================================================================