import pandas as pd


def get_fit_by_str(fit_by, voxel_threshold):
    if fit_by == "voxel":
        overall_extra_str = "_byvoxel"
        if voxel_threshold > 0:
            overall_extra_str = f"{overall_extra_str}_{str(voxel_threshold)}"
    else:
        raise Exception(f"Unknown group by type: {fit_by}")
    return overall_extra_str


def get_fit_group_cols(fit_by):
    if fit_by == "voxel":
        group_cols = ["slc", "x", "y"]
    else:
        raise Exception(f"Unknown group by type: {fit_by}")
    return group_cols


def remove_groups_with_zeros(data_pd, group_cols, data_col="data"):
    # Remove all groups that have any data that is exactly zero:
    data_pd["zero_row"] = False
    zero_rows = data_pd[data_col] == 0
    data_pd.loc[zero_rows, "zero_row"] = True
    df_zero_row_count = data_pd.groupby(group_cols).agg(num_zeros=('zero_row', 'sum')).reset_index()
    groups_to_remove = df_zero_row_count[df_zero_row_count["num_zeros"] > 0].drop_duplicates()
    if len(groups_to_remove) > 0:
        print("Number of zero row groups removed:", len(groups_to_remove))
    groups_to_keep = df_zero_row_count[df_zero_row_count["num_zeros"] == 0].drop_duplicates().drop(
        columns=["num_zeros"])
    data_pd = pd.merge(data_pd,
                       groups_to_keep,
                       on=group_cols,
                       how="right").reset_index(drop=True)
    data_pd = data_pd.drop(columns="zero_row")
    return data_pd


def limit_data_to_threshold(data_pd, slc_max_val, voxel_threshold):
    # TODO: See if I can add this in (and simultaneously remove the comment later on):
    # Only keep data that has at least one value (e.g. if there is a ti or b_value) that is within the
    #  threshold range for the max value on each slice
    # group_cols_for_max = ["slc"]
    # group_cols_for_max.extend(dependent_variables[datatype])
    # data_pd_groups_max = data_pd[group_cols_for_max + ["data"]].groupby(group_cols_for_max).agg(max)
    # data_pd_groups_max = data_pd_groups_max.rename(columns={"data": "data_max"})
    # data_pd_with_max = pd.merge(data_pd,
    #                             data_pd_groups_max,
    #                             on=group_cols_for_max,
    #                             how="left")
    # data_pd_meets_threshold = data_pd_with_max[data_pd_with_max["data"] >= (
    #         voxel_threshold * data_pd_with_max["data_max"])]
    # data_to_keep_based_on_max = data_pd_meets_threshold[["slc", "x", "y"]].drop_duplicates()
    # data_pd = pd.merge(data_pd,
    #                    data_to_keep_based_on_max,
    #                    on=["slc", "x", "y"],
    #                    how="right").reset_index(drop=True)
    # Only keep data that is above the voxel threshold
    # TODO: See if I can remove this (and simultaneously add the comment earlier on)
    valid_xy = data_pd[data_pd["data"] > slc_max_val * voxel_threshold][["x", "y"]]
    valid_xy = valid_xy.drop_duplicates()
    data_pd = pd.merge(data_pd,
                       valid_xy,
                       on=["x", "y"],
                       how="inner")
    # END TODOS
    return data_pd