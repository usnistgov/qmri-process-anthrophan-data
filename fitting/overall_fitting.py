import numpy as np
import pandas as pd
from fitting.constants import get_all_quantitative_variables, get_quantitative_variable
from fitting.t1_fitting import estimate_T1
from fitting.t2_fitting import estimate_T2


def get_limited_values(data_pd,
                       datatype,
                       values_to_use):
    if datatype == "t1":
        value_column_name = "ti"
    elif datatype == "t2":
        value_column_name = "te"
    else:
        raise Exception(f"Cannot limit data for datatype {datatype}")
        # Note, can't do this for "map", since it's already mapped

    unique_values = np.unique(data_pd[value_column_name])
    data_pd = data_pd[data_pd[value_column_name].isin(values_to_use)]

    found_values = np.unique(data_pd[value_column_name])
    found_values.sort()
    assert len(values_to_use) == len(found_values), f"Error: Values are missing for datatype {datatype}." \
                                                    f"\n\tExpected to find: " \
                                                    f"{' '.join([str(m) for m in values_to_use])}" \
                                                    f"\n\tActually found: {' '.join([str(m) for m in found_values])} " \
                                                    f"out of possible values: {unique_values}"

    return data_pd


def get_measurement_estimates_for_data_by_group(data_pd,
                                                datatype,
                                                group_cols=None):
    """ Get measurement fits for the datatype, by grouping a certain way """
    # Get information on valid rows
    data_pd = data_pd.copy()
    data_pd["valid"] = ~data_pd["data"].isna()
    if "map" in datatype:
        data_pd["valid"] = data_pd["valid"] & (data_pd["data"] != 0)

    # Get some aggregate group information and subset only to valid rows
    if group_cols is None:
        data_pd = data_pd.copy()
        data_pd["dummy"] = 1
        group_cols = ["dummy"]
    grouped_pd = data_pd.groupby(group_cols)
    agg_grouped_pd = grouped_pd.agg(
        num_voxels=pd.NamedAgg(column="data", aggfunc=len),
        num_voxels_w_data=pd.NamedAgg(column="valid", aggfunc=sum)
    )
    agg_grouped_pd["group"] = range(len(agg_grouped_pd))
    data_pd = pd.merge(data_pd,
                       agg_grouped_pd.reset_index(),
                       on=group_cols,
                       how="left")
    if "map" in datatype:
        data_pd.loc[~data_pd["valid"], "data"] = np.nan
    else:
        data_pd = data_pd[data_pd["valid"]]
    data_pd = data_pd.drop(columns="valid")

    # Process the map data right away and return
    if "map" in datatype:
        grouped_pd = data_pd.groupby(group_cols)
        map_colname = datatype.split("_map")[0].upper()
        agg_grouped_pd = grouped_pd.agg(
            map_colname=pd.NamedAgg(column="data", aggfunc=np.nanmean)
        )
        agg_grouped_pd = agg_grouped_pd.rename(columns={"map_colname": map_colname})
        fit_pd = pd.merge(data_pd,
                          agg_grouped_pd.reset_index(),
                          on=group_cols,
                          how="left")
        return fit_pd

    # Otherwise, process each group individually. First add the columns for fitting
    quant_cols = get_all_quantitative_variables(datatype)
    cols_to_add = []
    for quant_c in quant_cols:
        cols_to_add.append(quant_c)
        cols_to_add.append("init_" + quant_c)
        cols_to_add.append("stderr_" + quant_c)
    cols_to_add.append("norm_redchi")
    fit_dict = {"group": []}
    for c in cols_to_add:
        fit_dict[c] = []
        # Remove these columns if they are already there
        if c in data_pd.columns:
            data_pd = data_pd.drop(columns=c)

    # Then, process the data
    grouped_pd = data_pd.groupby(group_cols)
    print_status = True
    if len(grouped_pd) < 10:
        print_status = False
    num_groups = len(grouped_pd)
    percent_done = 0
    current_group_count = 0
    all_grouped_data = pd.DataFrame()
    for name, group in grouped_pd:
        current_group_count += 1
        group["group"] = current_group_count
        all_grouped_data = pd.concat([all_grouped_data, group])
        if print_status:
            if current_group_count / num_groups * 100 >= percent_done:
                print(percent_done, "% done")
                percent_done += 10

        # Fit the models
        if datatype == "t1":
            out1, params = estimate_T1(group, ti_col="ti", data_col="data", tr_col="tr")
        elif datatype == "t2":
            out1, params = estimate_T2(group, te_col="te", data_col="data")
        else:
            raise Exception(f"Unknown data type: {datatype}")

        # Save results
        for quant_c in quant_cols:
            fit_dict[quant_c].extend([out1.params[quant_c].value])
            fit_dict["stderr_" + quant_c].extend([out1.params[quant_c].stderr])
            fit_dict["init_" + quant_c].extend([params[quant_c].value])
        fit_dict["norm_redchi"].extend([out1.redchi / out1.params['Si'].value / out1.params['Si'].value])
        fit_dict["group"].extend([current_group_count])

    # Create the dataframe, but first make sure the dictionary has the correct form
    col_lens = []
    col_len_vals = {}
    for c, v in fit_dict.items():
        col_lens.append(len(v))
        col_len_vals[c] = len(v)
    assert len(np.unique(col_lens)) == 1, f"All columns must be same length, found: {col_len_vals}"
    fit_pd = pd.DataFrame(fit_dict)

    # Merge it back into the original data
    fit_pd = pd.merge(all_grouped_data,
                      fit_pd,
                      how="left",
                      on="group")
    assert len(all_grouped_data) == len(fit_pd), f"Expected same lengths, got: {len(all_grouped_data)}, {len(fit_pd)}"

    # Finally, label valid rows based on stderrs
    map_colname = get_quantitative_variable(datatype)
    fit_pd["valid_fit_by_stderr_"+map_colname] = fit_pd["stderr_"+map_colname] < fit_pd[map_colname]
    return fit_pd
