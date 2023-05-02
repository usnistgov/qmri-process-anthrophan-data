import numpy as np
import lmfit


def init_T2(TE=None, data=None):
    """initialize parameters for T2"""
    # Get param inits
    si_init = np.amax(data)
    te_init = TE[np.argmax(data)]
    te_target_idx = np.argmin(np.abs(data - (si_init / 2)))  # Want to get the closest index to half the init signal
    te_target = TE[te_target_idx]
    si_target = data[te_target_idx]
    t2_init = (te_target - te_init) / (np.log(si_init / si_target))

    # Initialize parameters
    params = lmfit.Parameters()  # define parameter dictionary
    params.add('T2', value=t2_init, min=0, vary=True)
    params.add('Si', value=si_init, min=0, vary=True)

    return params


def model_T2(Si, TE, T2):
    """T2 model"""
    model = Si * np.exp(-TE / T2)
    return model


def objFunction_T2(params, TE, data):
    Si = params['Si'].value
    T2 = params['T2'].value
    model = model_T2(Si, TE, T2)
    return (model - data)


def estimate_T2(filtered_pd, te_col="ech_time", data_col="mean"):
    mean_pd = filtered_pd.groupby(te_col).agg({data_col: np.mean, te_col: np.mean})
    mean_data = np.array(mean_pd[data_col])
    mean_TE = np.array(mean_pd[te_col])
    params = init_T2(mean_TE, mean_data)

    TE = np.array(filtered_pd[te_col])
    data = np.array(filtered_pd[data_col])
    output1 = lmfit.minimize(objFunction_T2, params, args=(TE, data))

    return output1, params
