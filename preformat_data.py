import os
import glob
from utils_io.MRIData import MRIData, turn_mri_data_into_dfs_by_slice
import argparse
import numpy as np
import matplotlib.pyplot as plt

# #######################################################################################################
# Input arguments
parser = argparse.ArgumentParser(description='Pre-processing step to format and save MRI data into CSV format.')
parser.add_argument('--load-dir', dest='load_dir',
                    type=str, action='store', required=True,
                    help='Directory to load raw data from')
parser.add_argument('--load-subdirs', dest='load_subdirs',
                    type=str, action='store', nargs="+", required=True,
                    help='Sub-directories to load raw data from. Data will be loaded from each directory and \n'
                         'combined. E.g., data will be loaded from: <load-dir>/<load-subdir> for each load-subdir in \n'
                         'load-subdirs. For example, all TI data for a T1 dataset should be given in the load-subdirs\n'
                         ' list.')
parser.add_argument('--load-data-extension', dest='load_data_extension',
                    type=str, action='store', required=True, choices=[".dcm", ".dim", "", ".fdf", ".IMA"],
                    help='File extension of the raw data. A file extension of an empty string will load dicom data.')
parser.add_argument('--dataset', dest='dataset',
                    type=str, action='store', required=True,
                    help='Dataset name - data will be saved with this name')
parser.add_argument('--datatype', dest='datatype',
                    type=str, action='store', required=True,
                    choices=["t1", "t2", "t2_map"],
                    help='Type of data to process')
parser.add_argument('--output-dir', dest='output_dir',
                    action='store', required=True,
                    help='Directory to output data to. The output convention is: \n'
                         '<output-dir>/<datatype>/<dataset>/raw_{slc}.csv, where slc is the slice number')
parser.add_argument("--images",
                    dest="save_images",
                    default=False,
                    action="store_true",
                    help="(Optional) Store images of fits when saving data. Note: for grouping by voxel, "
                         "this will be overwritten to False because it takes too long to run")

args = parser.parse_args()
dataset = args.dataset
datatype = args.datatype
output_dir = args.output_dir
parent_load_dir = args.load_dir
load_subdirs = args.load_subdirs
load_data_extension = args.load_data_extension
save_images = args.save_images

# #######################################################################################################
# Code
print(f"\n----------------start {dataset}-----------------")

# First, load all files for all specified directories
mri_data_objs = []
for raw_data_dir in load_subdirs:
    load_dir = os.path.join(parent_load_dir, raw_data_dir)

    print("Checking for files in", load_dir)
    filenames = glob.glob(os.path.join(load_dir, "**", "*" + load_data_extension), recursive=True)
    filenames.sort()
    n_files = len(filenames)
    print(n_files)
    if n_files > 0:
        print("Loading", n_files, "files from", load_dir, ", e.g.:", filenames[0])
        for filename in filenames:
            if (load_data_extension == ".dcm") or (load_data_extension == ".dim") or (load_data_extension == "") or\
                    (load_data_extension == ".IMA"):
                mri_data = MRIData().readDicom(filename, datatype=datatype, file_extension=load_data_extension)
            elif load_data_extension == ".fdf":
                mri_data = MRIData().readFDF(filename)
            else:
                # TODO: Make nii processing again
                raise Exception(f"Unknown data extension: {load_data_extension}")
            mri_data_objs.append(mri_data)
    else:
        raise Exception(f"No files found in {load_dir} for extension {load_data_extension}")

# #######################################################################################################
# Combnie the data all into one dataframe structure
mri_dfs_by_slice = turn_mri_data_into_dfs_by_slice(mri_data_objs)

# #######################################################################################################
# Save data
save_directory = os.path.join(output_dir,
                              datatype,
                              dataset)
os.makedirs(save_directory, exist_ok=True)
print("Saving data to:", save_directory)
if save_images:
    save_image_directory = os.path.join(save_directory, "images")
    os.makedirs(save_image_directory, exist_ok=True)
    print("Saving images to:", save_image_directory)
for slc_location, mri_df in mri_dfs_by_slice.items():
    assert len(np.unique(mri_df["slc"])) == 1, f"Multiple slices found for slice {slc_location}"
    slc = mri_df["slc"].values[0]
    print("Saving data for slc", slc, "at", slc_location)
    save_filename = os.path.join(save_directory, f"raw_{slc}.csv")
    with open(save_filename, "w") as f:
        mri_df.to_csv(f, index=False)

    # Save images
    if save_images:
        for group_name, group_df in mri_df.groupby(["te", "ti", "tr", "b_value", "b_vec_0", "b_vec_1", "b_vec_2"]):
            te = group_name[0]
            ti = group_name[1]
            tr = group_name[2]
            b_value = group_name[3]
            b_vec_0 = group_name[4]
            b_vec_1 = group_name[5]
            b_vec_2 = group_name[6]
            im = np.zeros((group_df["nx"].values[0], group_df["ny"].values[0]))
            im[list(group_df["x"]), list(group_df["y"])] = list(group_df["data"])
            f = plt.figure(num=1, clear=True)
            ax = f.add_subplot()
            im_ax = ax.imshow(im)
            plt.colorbar(im_ax, ax=ax)
            f.savefig(os.path.join(save_image_directory,
                                   f"slc_{slc}_te{te}_ti{ti}_tr{tr}_b{b_value}_at{b_vec_0}_{b_vec_1}_{b_vec_2}.png"))

# #######################################################################################################
print("Finished")
print(f"----------------end {dataset}-----------------")

print("\nFinished Saving Data!")
