import numpy as np
import matplotlib.pyplot as plt
import os
from fitting.t1_fitting import model_T1_2
from fitting.t2_fitting import model_T2
from fitting.overall_fitting import get_measurement_estimates_for_data_by_group
import seaborn as sns
from fitting.constants import get_all_quantitative_variables
from plotter.utils import colorbar

sns.set_palette("flare")


def imshow_fits_by_slice(data_pd, datatype, save_parent_dir, plot_column="slc", filename_extension="",
                         use_median=True):
    if use_median:
        plot_median = [True]
    else:
        plot_median = [False]

    # Create the full image for the scan results
    quant_cols = get_all_quantitative_variables(datatype)

    for quant_col in quant_cols:
        for quant_col in [quant_col, "stderr_"+quant_col, "init_"+quant_col]:
            if quant_col not in data_pd.columns:
                continue
            for plt_median in plot_median:
                vmin = np.min([0, np.min(data_pd[quant_col])])
                if plt_median:
                    vmax = np.nanmedian(data_pd[quant_col]) * 6
                else:
                    vmax = np.nanmax(data_pd[quant_col])
                data_shape = (data_pd["nx"].values[0], data_pd["ny"].values[0], data_pd["nslc"].values[0])
                full_im = np.zeros(data_shape)
                full_im[list(data_pd["x"]),
                        list(data_pd["y"]),
                        list(data_pd["slc"])] = list(data_pd[quant_col])

                # Plot and save each slice of the full scan image
                for slc in np.unique(data_pd[plot_column]):
                    im = full_im[:, :, slc]
                    f, ax = plt.subplots(1,1)
                    ax_im = ax.imshow(im, vmin=vmin, vmax=vmax)
                    colorbar(ax_im)
                    ax.set_title(f"{datatype} data: {quant_col} results for slice {slc}")
                    filename = f"{quant_col}_slc{slc}{filename_extension}.png"
                    if plt_median:
                        filename = "median_"+filename
                    plt.savefig(os.path.join(save_parent_dir, filename),
                                bbox_inches="tight")
                    plt.close()
