from plotter.utils import colorbar
import matplotlib.pyplot as plt
import numpy as np
import os


def plot_data_by_scan_params(data_df, save_dir):
    vmax = np.max(data_df["data"])
    for group_name, plot_df in data_df.groupby(["te", "ti", "tr", "b_value", "slc"]):
        te = group_name[0]
        ti = group_name[1]
        tr = group_name[2]
        b_value = group_name[3]
        slc = group_name[4]

        plot_im = np.zeros((plot_df["nx"].values[0], plot_df["ny"].values[0]))
        plot_im[list(plot_df["x"]), list(plot_df["y"])] = list(plot_df["data"])

        f, ax = plt.subplots(1, 1)
        im = ax.imshow(plot_im, vmin=0, vmax=vmax, interpolation="none")
        colorbar(im)
        ax.set_title("Dicom data")

        f.suptitle(f"Slice: {slc}")
        plt.tight_layout()
        plt.savefig(os.path.join(save_dir, f"slc_{slc}_te{te}_ti{ti}_tr{tr}_b{b_value}.png"), bbox_inches="tight")
        plt.close()
