
def get_fit_pd_to_save(fit_pd, columns_to_remove):
    fit_pd_to_save = fit_pd.drop(columns=columns_to_remove)
    extra_cols_to_remove = ["te", "tr", "ti", "b_value"]
    extra_cols_to_remove = [e for e in extra_cols_to_remove if e in fit_pd.columns]
    fit_pd_to_save = fit_pd_to_save.drop(columns=extra_cols_to_remove)
    fit_pd_to_save = fit_pd_to_save.drop_duplicates()
    return fit_pd_to_save
