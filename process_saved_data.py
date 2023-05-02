import pandas as pd
import numpy as np
import os
from fitting.overall_fitting import get_measurement_estimates_for_data_by_group, get_limited_values
from fitting.fitting_utils import get_fit_by_str, get_fit_group_cols, remove_groups_with_zeros, limit_data_to_threshold
from plotter.fits import imshow_fits_by_slice
from utils_io.dataframe import get_fit_pd_to_save
import glob
import argparse
import sys


def parse_args(args):
    # Input arguments
    parser = argparse.ArgumentParser(description='Process raw MRI data to create quantitative value estimates.')
    parser.add_argument('--dataset',
                        dest='datasets', type=str, nargs="+", action='store', required=True,
                        help='Dataset(s) to process')
    parser.add_argument('--datatype',
                        dest='datatype', type=str, action='store', nargs="+", required=True,
                        choices=["t1", "t2", "t2_map"],
                        help='Type(s) of data to process. If multiple datatypes are given, cannot specify '
                             'datatype-values')
    parser.add_argument('--datatype-values',
                        dest='values_to_use', nargs="+", action="store", type=float,
                        help='(Optional) Limited values to use for quantitative fit. For example, if you are fitting \n'
                             'the t1 datatype and have collected data for inversion times (tis) [100, 200, 600, 800],\n'
                             'setting --datatype-values to: 100 800 will only use the data collected for those tis\n'
                             ' to estimate t1. '
                             'Note: Only valid when only one datatype is specified!')
    parser.add_argument('--fit-by-voxel-threshold',
                        dest='fit_by_voxel_threshold', type=float, default=0.2, action='store',
                        help='(Optional) Threshold to mask the data by when fitting by voxel. This is used to speed '
                             'up fit by voxel '
                             'by not fitting background noise voxels. The default value is 0.2')
    parser.add_argument('--saved-data-dir',
                        dest='saved_data_dir', action='store', required=True,
                        help='Directory to load saved data from. Saved data will be loaded from:'
                             ' <saved-data-dir>/<datatype>/<dataset>/raw_{slc}.csv')
    parser.add_argument('--output-dir',
                        dest='output_dir', action='store', required=True,
                        help='Directory to output data to. The output convention is: '
                             '<output-dir>/<datatype>/<dataset>/raw.csv')
    parser.add_argument("--images",
                        dest="save_fits", default=False, action="store_true",
                        help="(Optional) Store images of fits when saving data. Note: for grouping by voxel, "
                             "this will be overwritten to False because it takes too long to run")
    return parser.parse_args(args)


def main(args):
    ##########################################################################################
    # Get args
    fit_by = "voxel"  # Always fit by voxel for saved data
    datatypes_to_process = args.datatype
    datasets_to_process = args.datasets
    values_to_use = args.values_to_use
    output_dir = args.output_dir
    saved_data_dir = args.saved_data_dir
    save_fits = args.save_fits
    voxel_threshold = args.fit_by_voxel_threshold
    if len(datatypes_to_process) > 1 and (values_to_use is not None):
        raise Exception("Only one datatype can be given if datatype-values is specified!")

    ##########################################################################################
    # Code
    # Set up formatting for saving data
    overall_extra_str = get_fit_by_str(fit_by, voxel_threshold)
    extra_str = overall_extra_str
    values_extra_str = ""
    if values_to_use is not None:
        values_extra_str = f"_{'_'.join([str(m) for m in values_to_use])}"

    # Get group by columns for fit
    group_cols = get_fit_group_cols(fit_by)

    # Never save fits if it's by voxel, and set up the other things
    columns_to_remove = ["data"]

    exceptions = ""
    for datatype in datatypes_to_process:
        for dataset in datasets_to_process:
            if not os.path.exists(os.path.join(saved_data_dir, datatype, dataset)):
                exceptions += f"\n{os.path.join(saved_data_dir, datatype, dataset)} does not exist"
                continue

            # Make save dir ---------------------------------------------------------------------
            save_dir = os.path.join(output_dir, datatype, f"{dataset}{values_extra_str}")
            os.makedirs(save_dir, exist_ok=True)
            save_image_dir = os.path.join(save_dir, "images")
            os.makedirs(save_image_dir, exist_ok=True)

            # Load raw data ---------------------------------------------------------------------
            data_pd_dict = {}
            if os.path.exists(os.path.join(saved_data_dir, datatype, dataset, "raw.csv")):
                print("WARNING: Using deprecated load method - loading raw.csv")
                full_data_pd = pd.read_csv(os.path.join(saved_data_dir, datatype, dataset, "raw.csv"))
                data_pd_dict = {}
                for slc, data_pd in full_data_pd.groupby("slc"):
                    data_pd_dict[slc] = data_pd
            else:
                filenames = glob.glob(os.path.join(saved_data_dir, datatype, dataset, "raw*.csv"))
                filenames.sort()
                for filename in filenames:
                    print("Opening file", filename)
                    data_pd = pd.read_csv(filename)
                    slc = data_pd["slc"].values[0]
                    data_pd_dict[slc] = data_pd

            # Preprocess before fitting ----------------------------------------------------------
            max_val = -1
            for slc, data_pd in data_pd_dict.items():
                # If limits are specified, limit the data_pd 
                if values_to_use is not None:
                    print("Fitting", datatype, "using limited values:", values_to_use)
                    data_pd = get_limited_values(data_pd, datatype, values_to_use)
                # Store the data and max value 
                data_pd_dict[slc] = data_pd
                max_val = np.max([max_val, np.max(data_pd["data"])])

            # Fit by slice ---------------------------------------------------------------------
            fit_pds = []
            fit_pds_to_save = []
            for slc, data_pd in data_pd_dict.items():
                print("Processing fit by voxel for slice", slc)

                # Only look at slices that have max val of at least 10% of total max val
                slc_max_val = np.max(data_pd["data"])
                if slc_max_val > (np.min([0.1, voxel_threshold]) * max_val):
                    # Remove all groups that have any data that is exactly zero:
                    data_pd = remove_groups_with_zeros(data_pd, group_cols=["slc", "x", "y"], data_col="data")
                    # Only keep data that is above the voxel threshold:
                    data_pd = limit_data_to_threshold(data_pd, slc_max_val, voxel_threshold)
                    if len(data_pd) == 0:
                        # Nothing to fit, continue
                        continue

                # Fit data for this slice
                fit_pd = get_measurement_estimates_for_data_by_group(data_pd, datatype, group_cols=group_cols)
                fit_pds.append(fit_pd)  # For plotting the images later
                fit_pd_to_save = get_fit_pd_to_save(fit_pd, columns_to_remove=columns_to_remove)
                fit_pds_to_save.append(fit_pd_to_save)

                # Save the fits for this slice
                fit_pd_slc_filename = os.path.join(save_dir, f"fit_pd_{str(slc)}{extra_str}.csv")
                with open(fit_pd_slc_filename, "w") as f:
                    fit_pd_to_save.to_csv(f, index=False)

                # Plot the results for each slice
                if save_fits:
                    imshow_fits_by_slice(fit_pd, datatype, save_parent_dir=save_image_dir,
                                        filename_extension=extra_str)

            # Save the fits for all slices
            fit_pds_to_save = pd.concat(fit_pds_to_save)
            fit_pd_slc_filename = os.path.join(save_dir, f"fit_pd{extra_str}.csv")
            with open(fit_pd_slc_filename, "w") as f:
                fit_pds_to_save.to_csv(f, index=False)

            # Re-plot the results for each slice, to be on same colorbar scale
            if save_fits:
                fit_pds = pd.concat(fit_pds)
                print("Resaving plots on the same colorbar scale")
                imshow_fits_by_slice(fit_pds, datatype, save_parent_dir=save_image_dir,
                                    filename_extension=extra_str)

    print("\nFinished Processing Data!")
    if len(exceptions) > 0:
        print("\nNote, unable to process data for the following file and datatype combinations:")
        print(exceptions)


if __name__ == '__main__':
    args = parse_args(sys.argv[1:])
    main(args)
