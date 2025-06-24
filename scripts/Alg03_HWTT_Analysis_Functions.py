# Title: HWTT analysis functions. 
#
# Author: Farhad Abdollahi (farhad.abdollahi.ctr@dot.gov)
# Date: 02/26/2025
# ======================================================================================================================

# Importing the required libraries.
import os
import warnings
import numpy as np
import pandas as pd
from time import perf_counter
from scipy.optimize import curve_fit, differential_evolution
from sklearn.metrics import r2_score


def HWTT_Analysis(X, Y):
    """
    This is the main function which analyze the HWTT data by fitting Two-Part Model (2PP), Yin et al. (2014) model, and 
    6th degree polynomial model and extracting the analysis parameters. 

    :param X: An array of the number of passes (should not include NaN values). 
    :param Y: An array of the rut depths (should not include NaN values). 
    """
    # First run the 2PP model. 
    TimeTrack = perf_counter()
    Res2PP = HWTT_Analysis_2PP(X, Y)
    Res2PP['RunTime'] = perf_counter() - TimeTrack
    # -------------------------------------------------
    # Run the Yin et al. model. 
    TimeTrack = perf_counter()
    ResYin = HWTT_Analysis_Yin(X, Y)
    ResYin['RunTime'] = perf_counter() - TimeTrack
    # -------------------------------------------------
    # Run the 6th degree polynomial model. 
    TimeTrack = perf_counter()
    Res6deg = HWTT_Analysis_6deg(X, Y)
    Res6deg['RunTime'] = perf_counter() - TimeTrack
    # -------------------------------------------------
    # Aggregate and return the results.
    return {
        '2PP' : Res2PP, 
        'Yin' : ResYin,
        '6deg': Res6deg,
    } 
# ======================================================================================================================
# ======================================================================================================================
# ======================================================================================================================


def HWTT_Analysis_2PP(X, Y):
    """
    This is the main function to fit the proposed Two-Part Power (2PP) model to the HWTT raw data. This model has been 
    developed at the Asphalt Binder and Mixture Laboratory (ABML) of the FHWA's Turner-Fairbank Highway Research Center 
    (TFHRC). 

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
    CreepLine = [Coeff[0] * Coeff[1] * (SN_estimated ** (Coeff[1] - 1)), None]
    CreepLine[1] = ModelPower(SN_estimated, Coeff[0], Coeff[1]) - CreepLine[0] * SN_estimated
    TangLine = [alpha * beta * (X.max() - gamma) ** (beta - 1), None]
    TangLine[1] = YY[-1] - TangLine[0] * X.max()
    SIP = (TangLine[1] - CreepLine[1]) / (CreepLine[0] - TangLine[0])
    SIP_Yval = CreepLine[0] * SIP + CreepLine[1]
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
    # Calculating the SIP based on the constant threshold value of 12.5 mm. 
    if ModelPower(SN_estimated, Coeff[0], Coeff[1]) > 12.5:
        SIPAdj      = np.nan
        SIPAdj_Yval = np.nan
        TangLineAdj = TangLine
    else:
        X_Threshold = np.exp(np.log((12.5 - Phi) / alpha) / beta) + gamma
        TangLineAdj  = [alpha * beta * ((X_Threshold - gamma) ** (beta - 1)), 0]
        TangLineAdj[1] = ModelPower_Part2(X_Threshold, alpha, beta, gamma, Phi) - TangLineAdj[0] * X_Threshold
        SIPAdj = (TangLineAdj[1] - CreepLine[1]) / (CreepLine[0] - TangLineAdj[0])
        SIPAdj_Yval = CreepLine[0] * SIPAdj + CreepLine[1]
    # ------------------------------------------------------------------------------------------------------------------
    # Return the results. 
    return {
        'Maximum_Rutting_mm'            : MaxRut,
        'Maximum_Passes'                : MaxPass,
        'Rutting@10k_mm'                : Rut10k,
        'Rutting@20k_mm'                : Rut20k,
        'Rutting_PowerModel_Coeff'      : Coeff,
        'Rutting_PowerModel_Part2_Coeff': [alpha, beta, gamma, Phi],
        'Stripping_Rutting_mm'          : StripRut,
        'Stripping_Rutting_Pass'        : StripRutX,
        'SIP'                           : SIP,
        'SIP_Yval_mm'                   : SIP_Yval,
        'SIP_Adj'                       : SIPAdj,
        'SIP_Adj_Yval_mm'               : SIPAdj_Yval,
        'Stripping_Number'              : SN_estimated,
        'CreepLine'                     : CreepLine,
        'TangentLine'                   : TangLine,
        'TangentLine_Adj'               : TangLineAdj,
        'Xmodel'                        : XX,
        'Ymodel'                        : YY,
    }
# ======================================================================================================================
# ======================================================================================================================
# ======================================================================================================================


def HWTT_Analysis_Yin(X, Y):
    """
    This is the main function to fit the proposed model by Yin et al. (2014) to the HWTT raw data. Please refer to the 
    following reference for more details: 
    "Yin, F., Arambula, E., Lytton, R., Martin, A. E., & Cucalon, L. G. (2014). Novel method for moisture susceptibility 
    and rutting evaluation using Hamburg wheel tracking test. Transportation Research Record, 2446(1), 1-7."

    :param X: An array of the number of passes (should not include NaN values). 
    :param Y: An array of the rut depths (should not include NaN values). 
    """
    # First extract the maximum number of passes and its corresponding rut depth. 
    MaxRut = Y[-1]
    MaxPass= X[-1]
    # Step 1: Fit the first model to estimate the Stripping Number (SN). 
    LNcoeff, _ = curve_fit(YinModel, X, Y, p0=[2.0, 50000, 2.5], maxfev=5000, 
                           bounds=([0.5, X.max() + 500, 0.05], [10000.0, 100000, 10.0]))
    # Calculate the SN. 
    SN = LNcoeff[1] * np.exp((LNcoeff[2] + 1) / -LNcoeff[2])
    LCSN = SN
    # ------------------------------------------------------------------------------------------------------------------
    # Step 2: Fit Tseng-Lytton model to the first portion of the data. 
    Indx = np.where(X < SN)[0]
    X1   = X[Indx]
    Y1   = Y[Indx]
    ObjectiveFunction = lambda params: np.sum((Y1 - TsengLyttonModel(X1, params[0], 10 ** params[1], params[2])) ** 2)
    result = differential_evolution(ObjectiveFunction, [(2.0, 50.0), (3.0, 10.0), (0.01, 0.5)])    
    TLcoeff = result.x
    TLcoeff[1] = 10 ** TLcoeff[1]
    R2 = r2_score(Y1, TsengLyttonModel(X1, TLcoeff[0], TLcoeff[1], TLcoeff[2])) * 100
    if R2 < 90: 
        raise Exception(f'Problem in fitting Tseng-Lytton model, which result in R2={R2:.2f}%')
    # Calculate Δε
    T      = 62                     # Thickness of the samples (assumed 62 mm). 
    EpsVPmax = TLcoeff[0] / T
    Alpha    = TLcoeff[1]
    Lambda   = TLcoeff[2]
    DeltaEps10 = (Alpha ** Lambda) * Lambda * EpsVPmax * \
        np.exp(-1 * ((Alpha / 10000) ** Lambda)) * (10000 ** (-1 - Lambda)) 
    # ------------------------------------------------------------------------------------------------------------------
    # Calculate the ε.
    X2 = X[X > SN]
    if len(X2) == 0:
        LCST = -1
        STcoeff = np.array([-1, -1])
    elif X2.max() > SN:
        StripStrn = (Y - TsengLyttonModel(X, TLcoeff[0], TLcoeff[1], TLcoeff[2])) / T
        IndxST = np.where(X > SN)[0]
        X2 = X[IndxST]
        Y2 = StripStrn[IndxST]
        # Fit the third model for the stripping strain. 
        ObjectiveFunctionST = lambda params: np.sum((Y2 - StripModel(X2, 10 ** params[0], 10 ** params[1], SN)) ** 2)
        resultST = differential_evolution(ObjectiveFunctionST, bounds=[(-5.0, -1.0), (-7.0, -2.0)])    
        STcoeff = 10 ** resultST.x
        # Calculting the LCST. 
        EpsST0 = STcoeff[0]
        Theta  = STcoeff[1]
        LCST = (1 / Theta) * np.log((12.5 / (T * EpsST0)) + 1)
        # Evaluate the goodness of fit. 
        R2 = r2_score(Y2, StripModel(X2, STcoeff[0], STcoeff[1], SN)) * 100
        if R2 < 90:
            warnings.warn(f'Warning: Problem in fitting Stripping Model, which result in R2={R2:.2f}%, LCST={LCST:.0f}')
    else:
        LCST = -1
        STcoeff = np.array([-1, -1])
    # ------------------------------------------------------------------------------------------------------------------
    # Calculate the CRD10, and CRD20. 
    Rut10k = TsengLyttonModel(10000, TLcoeff[0], TLcoeff[1], TLcoeff[2])
    Rut20k = TsengLyttonModel(20000, TLcoeff[0], TLcoeff[1], TLcoeff[2])
    # Calculating the stripping rutting. 
    idx = np.argmax(Y[-10:])
    StripRutX = X[-10:][idx]
    StripRut = Y[-10:].max() - TsengLyttonModel(StripRutX, TLcoeff[0], TLcoeff[1], TLcoeff[2])
    if StripRut < 0: 
        StripRut = 0 
    # ------------------------------------------------------------------------------------------------------------------
    # Calculating the stripping, using two method: (i) at the maximum passes, (ii) at the threshold of 12.5 mm. 
    #   First method: calculating the SIP using the tangential line at the maximum passes. 
    CreepLine = [diffYinModel(SN, LNcoeff[0], LNcoeff[1], LNcoeff[2]), 0]
    CreepLine[1] = YinModel(SN, LNcoeff[0], LNcoeff[1], LNcoeff[2]) - CreepLine[0] * SN
    TangLine  = [diffYinModel(X.max(), LNcoeff[0], LNcoeff[1], LNcoeff[2]), 0]
    TangLine[1] = YinModel(X.max(), LNcoeff[0], LNcoeff[1], LNcoeff[2]) - TangLine[0] * X.max()
    SIP = (TangLine[1] - CreepLine[1]) / (CreepLine[0] - TangLine[0])
    SIP_Yval = CreepLine[0] * SIP + CreepLine[1]
    #   Second method: calculating the SIP using the tangential line at the threshold of 12.5 mm. 
    X_Threshold = LNcoeff[1] / np.exp((12.5 / LNcoeff[0]) ** (-LNcoeff[2]))
    TangLineAdj  = [diffYinModel(X_Threshold, LNcoeff[0], LNcoeff[1], LNcoeff[2]), 0]
    TangLineAdj[1] = YinModel(X_Threshold, LNcoeff[0], LNcoeff[1], LNcoeff[2]) - TangLineAdj[0] * X_Threshold
    SIPAdj = (TangLineAdj[1] - CreepLine[1]) / (CreepLine[0] - TangLineAdj[0])
    SIPAdj_Yval = CreepLine[0] * SIPAdj + CreepLine[1]
    # ------------------------------------------------------------------------------------------------------------------
    # Constructing the final model using the Step 1 model. 
    XX = np.linspace(0, X.max(), num=20001)
    YY = YinModel(XX, LNcoeff[0], LNcoeff[1], LNcoeff[2])
    # ------------------------------------------------------------------------------------------------------------------
    # Prepare the results for return and return the results. 
    return {
        'Maximum_Rutting_mm'    : MaxRut,
        'Maximum_Passes'        : MaxPass,
        'Rutting@10k_mm'        : Rut10k,
        'Rutting@20k_mm'        : Rut20k,
        'Rutting_Step1_Coeff'   : LNcoeff,
        'Rutting_Step2_Coeff'   : TLcoeff,
        'Rutting_Step3_Coeff'   : STcoeff,
        'Stripping_Rutting_mm'  : StripRut,
        'Stripping_Rutting_Pass': StripRutX,
        'SIP'                   : SIP,
        'SIP_Yval_mm'           : SIP_Yval,
        'SIP_Adj'               : SIPAdj,
        'SIP_Adj_Yval_mm'       : SIPAdj_Yval,
        'Stripping_Number'      : SN,
        'CreepLine'             : CreepLine,
        'TangentLine'           : TangLine,
        'TangentLine_Adj'       : TangLineAdj,
        'Xmodel'                : XX,
        'Ymodel'                : YY,
        'LCSN'                  : LCSN,
        'LCST'                  : LCST, 
        'DeltaEps@10k'          : DeltaEps10,
    }
# ======================================================================================================================
# ======================================================================================================================
# ======================================================================================================================


def HWTT_Analysis_6deg(X, Y):
    """
    This is the main function to fit the 6th degree polynomial model which has been used in many studies in the 
    literature. This is a simple and typical model for quick analysis of the HWTT results. 

    :param X: An array of the number of passes (should not include NaN values). 
    :param Y: An array of the rut depths (should not include NaN values). 
    """
    # First extract the maximum number of passes and its corresponding rut depth. 
    MaxRut = Y[-1]
    MaxPass= X[-1]
    # Fit a 6th degree polynomial model. 
    Coeff = np.polyfit(X, Y, 6)
    # Find the inflection points, if any. 
    First_Derivative  = np.polyder(Coeff, m=1)
    Second_Derivative = np.polyder(Coeff, m=2)
    Roots = np.roots(Second_Derivative)
    Roots = np.unique([Roots[i] for i in range(len(Roots)) if Roots[i].imag == 0])
    # Calculate the CRD at 10,000 and 20,000 passes. 
    SN = abs(Roots[0])
    SN_Yval = np.interp(SN, X, Y)
    if SN < 10000:
        Rut10k = SN_Yval + np.polyval(First_Derivative, SN) * (10000 - SN)
        Rut20k = SN_Yval + np.polyval(First_Derivative, SN) * (20000 - SN)
    elif SN < 20000:
        Rut10k = np.interp(10000, X, Y)
        Rut20k = SN_Yval + np.polyval(First_Derivative, SN) * (20000 - SN)
    else: 
        Rut10k = np.interp(10000, X, Y)
        Rut20k = np.interp(20000, X, Y)
    # ------------------------------------------------------------------------------------------------------------------
    # Calculating the stripping rutting. 
    idx = np.argmax(Y[-10:])
    StripRutX = X[-10:][idx]
    if StripRutX < SN:
        StripRut = Y[-10:].max() - np.interp(StripRutX, X, Y)
    else:
        StripRut = Y[-10:].max() - (SN_Yval + np.polyval(First_Derivative, SN) * (StripRutX - SN))
    if StripRut < 0: 
        StripRut = 0 
    # ------------------------------------------------------------------------------------------------------------------
    # Constructing the final model. 
    XX = np.linspace(0, X.max(), num=20001)
    YY = np.polyval(Coeff, XX)
    # ------------------------------------------------------------------------------------------------------------------
    # Prepare the results for return and return the results. 
    return {
        'Maximum_Rutting_mm': MaxRut,
        'Maximum_Passes': MaxPass,
        'Rutting@10k_mm': Rut10k,
        'Rutting@20k_mm': Rut20k,
        'Rutting_6degPolynomial_Coeff': Coeff,
        'Stripping_Rutting_mm': StripRut,
        'Stripping_Rutting_Pass': StripRutX,
        'Stripping_Number': SN,
        'CreepLine': [np.polyval(First_Derivative, SN), 
                      SN_Yval - np.polyval(First_Derivative, SN) * SN],
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


def YinModel(x, ro, LCult, beta): 
    """
    This function defines the model used in step 1 of the Yin et al. (2014) approach to estimate the Stripping 
    Number (SN). 

    :param x: Float or array of the number of passes. 
    :param ro: Model parameter. 
    :param LCult: Model parameter. 
    :param beta: Model parameter. 
    :return: Calculated rut depth, corresponds to the number passes (mm). 
    """
    return ro * (np.log(LCult / x) ** (-1 / beta))
# ======================================================================================================================
# ======================================================================================================================
# ======================================================================================================================


def diffYinModel(x, ro, LCult, beta): 
    """
    This function calculates the slope of the model used in step 1 of the Yin et al. (2014) approach. 

    :param x: Float or array of the number of passes. 
    :param ro: Model parameter. 
    :param LCult: Model parameter. 
    :param beta: Model parameter. 
    :return: Calculated rut depth, corresponds to the number passes (mm). 
    """
    return (ro / beta / x) * (np.log(LCult / x) ** ((-1 - beta) / beta))
# ======================================================================================================================
# ======================================================================================================================
# ======================================================================================================================


def TsengLyttonModel(x, RutMax, Alpha, Lambda): 
    """
    This function is the model used in the Step 2 of the Yin et al. (2014) approach to calculate the corrected rut 
    depth (CRD). 

    :param x: Float or array of the number of passes. 
    :param RutMax: Model parameter, maximum rut depth (mm). 
    :param Alpha: Model parameter. 
    :param Lambda: Model parameter. 
    :return: Calculated corrected rut depth, corresponds to the number passes (mm). 
    """
    return RutMax * np.exp(-((Alpha / x) ** Lambda))
# ======================================================================================================================
# ======================================================================================================================
# ======================================================================================================================


def StripModel(x, EpsST0, Theta, SN): 
    """
    This function is the stripping model used in Step 3 of the Yin et al. (2014) approach. 

    :param x: Float or array of the number of passes. 
    :param EpsST0: Model parameter. 
    :param Theta: Model parameter. 
    :param SN: Stripping Number. 
    :return: Calculated stripping strain, corresponds to the number passes (mm). 
    """
    return EpsST0 * (np.exp(Theta * (x - SN)) - 1)
# ======================================================================================================================
# ======================================================================================================================
# ======================================================================================================================
