import os
import glob
import pandas as pd
from plotter.data import plot_data_by_scan_params
import argparse

##########################################################################################
# Input arguments

parser = argparse.ArgumentParser(description='Save raw MRI data into CSV format.')
parser.add_argument('--dataset', dest='dataset',
                    type=str, action='store', required=True, nargs="+",
                    help='Dataset name(s) - data will be loaded and saved with this name')
parser.add_argument('--datatype', dest='datatype',
                    type=str, action='store', nargs="+", required=True,
                    choices=["t1", "t2", "t2_map"],
                    help='Type(s) of data to process. If multiple datatypes are given, cannot specify datatype-values')
parser.add_argument('--preformat-data-dir', dest='preformat_data_dir',
                    type=str, action='store', required=True,
                    help='Directory to load preformatted data from')
parser.add_argument('--output-dir', dest='output_dir',
                    action='store', required=True,
                    help='Directory to output data to. The output convention is: \n'
                         '<output-dir>/<datatype>/<dataset>/raw_{slc}.csv, where slc is the slice number')
parser.add_argument("--images", dest="plot_images",
                    default=False, action="store_true",
                    help="(Optional) If included, store images when saving data")


args = parser.parse_args()
datasets = args.dataset
datatypes = args.datatype
preformat_data_dir = args.preformat_data_dir
parent_save_dir = args.output_dir
plot_images = args.plot_images


##########################################################################################
# Code

# Get and save Raw data
print("Starting to save data...")
exceptions = ""

for dataset in datasets:
    for datatype in datatypes:
        print(f"\n----------------start {dataset} - {datatype}-----------------")
        # If we haven't found any data, abort the loop and move on to next version
        input_directory = os.path.join(preformat_data_dir, datatype, dataset)
        if not os.path.exists(input_directory):
            e = f"\t{dataset}: Path does not exist {input_directory} - not saving data for {datatype}\n"
            exceptions += e
            print(e + f"----------------end {dataset} - {datatype}-----------------")
            continue

        # Load one dataframe to get the data shape for ROI loading
        filenames = glob.glob(os.path.join(input_directory, f"raw_*"))
        slices_to_save = [f.split(os.sep)[-1].split("raw_")[-1].split(".")[0] for f in filenames]

        # Set up the save directories
        save_dir = os.path.join(parent_save_dir, datatype, dataset)
        save_image_dir = os.path.join(save_dir, "images")
        os.makedirs(save_dir, exist_ok=True)
        os.makedirs(save_image_dir, exist_ok=True)

        # Only get the ROI values out of the raw data (in some cases, the ROI is everything)
        for slc in slices_to_save:
            print("Saving raw data for slice:", slc)
            load_filename = os.path.join(preformat_data_dir, datatype, dataset, f"raw_{slc}.csv")
            data_pd = pd.read_csv(load_filename)
            pd_filename = os.path.join(save_dir, f"raw_{slc}.csv")
            with open(pd_filename, "w") as f:
                data_pd.to_csv(f, index=False)

            if plot_images:
                print("Saving images to same colorscale")
                plot_data_by_scan_params(data_pd, save_image_dir)
        print(f"----------------end {dataset} - {datatype}-----------------")

print("\nFinished Saving Data!")
if len(exceptions) > 0:
    print("\nNote, unable to save data for the following file and datatype combinations:")
    print(exceptions)
