import numpy as np
import lmfit
from scipy.optimize import minimize


def model_T1_init_1(T1, delta_init, TI_init):
    model = (1 - (1 + delta_init) * np.exp(-TI_init / T1))**2
    return model


def model_T1_init_2(T1, delta_init, TI_init, TR):
    model = (1 - (1 + delta_init) * np.exp(-TI_init / T1) + np.exp(-TR / T1))**2
    return model


def get_t1_guess(TI, data, TR, delta_init):
    if np.min(data) > np.max(data) * .8:  # If amount of total data variation is less then 80%
        return np.min(TI) / np.log(2)   # Guess first TI since it could be very short T1

    TI_init = TI[np.argmin(data)]
    t1_guess = TI_init / np.log(2)  # minimum signal should occur at ln(2)T1
    if TR is not None:
        res = minimize(model_T1_init_2, t1_guess, args=(delta_init, TI_init, TR))
    else:
        res = minimize(model_T1_init_1, t1_guess, args=(delta_init, TI_init))

    return res.x[0]


def init(TI=None, data=None, TR=None):
    """initialize parameters for T1IR absolute value model"""

    # Get init guesses
    delta_init = 0.90
    t1_guess = get_t1_guess(TI, data, TR, delta_init)

    # Estimate SI_init based on the last TI
    # Si_init = np.amax(data)*2
    max_ti_idx = np.argmax(TI)
    if TR is not None:
        Si_init = data[max_ti_idx] / model_T1_2(Si=1, delta=delta_init, TI=TI[max_ti_idx], T1=t1_guess, TR=TR)
    else:
        Si_init = data[max_ti_idx] / model_T1_1(Si=1, delta=delta_init, TI=TI[max_ti_idx], T1=t1_guess)

    # define parameter dictionary
    params = lmfit.Parameters()
    params.add('T1', value=t1_guess, min=0, vary=True)  # max=5000
    params.add('Si', value=Si_init, min=0, vary=True)
    params.add('delta', value=delta_init, min=0.0, max=1.0, vary=True)
    return params


def model_T1_1(Si, delta, TI, T1):
    model = np.abs(Si * (1 - (1 + delta) * np.exp(-TI / T1)))
    return model


def model_T1_2(Si, delta, TI, T1, TR):
    model = np.abs(Si * (1 - (1 + delta) * np.exp(-TI / T1) + np.exp(-TR / T1)))
    return model


def objFunction1(params, TI, data):
    """ T1-IR model abs(exponential); TI inversion time array, T1 recovery time"""
    delta = params['delta'].value
    Si = params['Si'].value
    T1 = params['T1'].value
    model = model_T1_1(Si, delta, TI, T1)
    return model - data


def objFunction2(params, TI, data, TR):
    """ T1-IR model abs(exponential); TI inversion time array, T1 recovery time"""
    delta = params['delta'].value
    Si = params['Si'].value
    T1 = params['T1'].value
    model = model_T1_2(Si, delta, TI, T1, TR)
    return model - data


def estimate_T1(filtered_pd, ti_col="inv_time", data_col="mean", tr_col=None):
    TR = None
    if tr_col is not None:
        TR = np.unique(filtered_pd[tr_col])[0]

    mean_pd = filtered_pd.groupby(ti_col).agg({data_col: np.mean, ti_col: np.mean})
    mean_data = np.array(mean_pd[data_col])
    mean_TI = np.array(mean_pd[ti_col])
    params = init(TI=mean_TI, data=mean_data, TR=TR)

    TI = np.array(filtered_pd[ti_col])
    data = np.array(filtered_pd[data_col])
    if TR is not None:
        mini_mzr = lmfit.Minimizer(userfcn=objFunction2, params=params, fcn_args=(TI, data, TR))
    else:
        mini_mzr = lmfit.Minimizer(userfcn=objFunction1, params=params, fcn_args=(TI, data))
    output = mini_mzr.minimize(method="least_squares")
    # ci = lmfit.conf_interval(mini_mzr, output)  # This is far too slow...

    return output, params
