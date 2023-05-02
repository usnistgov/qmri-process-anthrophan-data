# qMRI Processing Anthromorphic Phantom Data

Repo for processing quantitative MRI data, specifically T1 and T2 data.

## 0. Setup, Requirements, and Command Line Calls
The `requirements.txt` file has the required packages that need to be installed to run the code in this 
repository. 

The recommended way to setup the requirements for this repository is to create a virtual environment,
and to install the required packages there. One way to create and manage virtual environments is to use 
[Conda](https://conda.io/projects/conda/en/latest/index.html#), a package management system that runs 
on Windows, macOS, and Linux. You can follow the installation guide to install Conda
 [here](https://conda.io/projects/conda/en/latest/user-guide/install/index.html).

Once Conda is installed, you can create a Python virtual environment called `qmri-anthrophan`, activate the
environment, and install the required packages into the environment 
by executing these commands in the terminal (or command line, for Windows):
```
conda create --name qmri-anthrophan python
conda activate qmri-anthrophan
pip install -r requirements.txt
```

Once the packages are installed, run the commands listed in this README once the conda environment
is activated. When finished executing code, exit the conda environment
using `conda deactivate`.

## 1. Package Functionality Overview

This package offers functionality to process quantitative MRI data. Briefly, the data processing is broken up
into the following steps:

1. [Pre-format data](#21-pre-format-data) to create consistent file structure for rest of code
2. [Save data](#22-save-data) into csv formatted data
3. Use saved csv data to [process saved data](#23-process-saved-data) to calculate quantitative parameters

Below are descriptions of each step in detail, with example command-line calls. 
Running the example code should help familiarize you with each step in the 
pipeline and the format of the output files.

 
## 2. Processing Data
### 2.1 Pre-format Data
The `preformat_data.py` script saves all input data into one consistent format, to be used for subsequent calls.
An example call is:
<details> <summary> <em> Mac OS Terminal </em> </summary>

```
python preformat_data.py \
--load-dir "example/example_data/" \
--dataset anthrobrain_3T \
--datatype t2 \
--load-subdirs \
"T2SE-TE160_0021" \
"T2SE-TE320_0022" \
"T2SE-TE80_0020" \
"T2SE-TE40_0019" \
"T2SE-TE20_0018" \
"T2SE-TE10_0017" \
--load-data-extension .IMA \
--output-dir ../data/processed/preformat_data/ \
--images
```
</details>
<details> <summary> <em> Windows Powershell </em> </summary>

```
python preformat_data.py `
--load-dir "example/example_data/" `
--dataset anthrobrain_3T `
--datatype t2 `
--load-subdirs `
"T2SE-TE160_0021" `
"T2SE-TE320_0022" `
"T2SE-TE80_0020" `
"T2SE-TE40_0019" `
"T2SE-TE20_0018" `
"T2SE-TE10_0017" `
--load-data-extension .IMA `
--output-dir ../data/processed/preformat_data/ `
--images
```
</details>
<details> <summary> <em> Windows Command Line </em> </summary>

```
python preformat_data.py ^
--load-dir "example/example_data/" ^
--dataset anthrobrain_3T ^
--datatype t2 ^
--load-subdirs ^
"T2SE-TE160_0021" ^
"T2SE-TE320_0022" ^
"T2SE-TE80_0020" ^
"T2SE-TE40_0019" ^
"T2SE-TE20_0018" ^
"T2SE-TE10_0017" ^
--load-data-extension .IMA ^
--output-dir ../data/processed/preformat_data/ ^
--images
```
</details>

where the arguments are:
```
  --load-dir LOAD_DIR   Directory to load raw data from
  --load-subdirs LOAD_SUBDIRS [LOAD_SUBDIRS ...]
                        Sub-directories to load raw data from. Data will be loaded from each directory and combined. E.g., data will be loaded from: <load-dir>/<load-subdir> for each load-
                        subdir in load-subdirs. For example, all TI data for a T1 dataset should be given in the load-subdirs list.
  --load-data-extension {.dcm,.dim,,.fdf,.IMA}
                        File extension of the raw data. A file extension of an empty string will load dicom data.
  --dataset DATASET     Dataset name - data will be saved with this name
  --datatype {t1,t2,t2_map}
                        Type of data to process
  --output-dir OUTPUT_DIR
                        Directory to output data to. The output convention is: <output-dir>/<datatype>/<dataset>/raw_{slc}.csv, where slc is the slice number
  --images              (Optional) Store images of fits when saving data. Note: for grouping by voxel, this will be overwritten to False because it takes too long to run
```


### 2.2 Save Data
The `save_data.py` script re-saves data and saves images on the same color scale. This is a 
legacy step that is remnant from a previous codebase, and could likely be consolidated into the
pre-format data step.

An example call to `save_data.py` is:

<details> <summary> <em> Mac OS Terminal </em> </summary>

```
python save_data.py \
--dataset anthrobrain_3T \
--datatype t2 \
--preformat-data-dir ../data/processed/preformat_data/ \
--output-dir ../data/processed/saved_data \
--images
```
</details>
<details> <summary> <em> Windows Powershell </em> </summary>

```
python save_data.py `
--dataset anthrobrain_3T `
--datatype t2 `
--preformat-data-dir ../data/processed/preformat_data/ `
--output-dir ../data/processed/saved_data `
--images
```
</details>
<details> <summary> <em> Windows Command Line </em> </summary>

```
python save_data.py ^
--dataset anthrobrain_3T ^
--datatype t2 ^
--preformat-data-dir ../data/processed/preformat_data/ ^
--output-dir ../data/processed/saved_data ^
--images
```
</details>


where the arguments are:
```
  --dataset DATASET [DATASET ...]
                        Dataset name(s) - data will be loaded and saved with this name
  --datatype {t1,t2,t2_map} [{t1,t2,t2_map} ...]
                        Type(s) of data to process. If multiple datatypes are given, cannot specify datatype-values
  --preformat-data-dir PREFORMAT_DATA_DIR
                        Directory to load preformatted data from
  --output-dir OUTPUT_DIR
                        Directory to output data to. The output convention is: <output-dir>/<datatype>/<dataset>/raw_{slc}.csv, where slc is the slice number
  --images              (Optional) If included, store images when saving data
```


### 2.3 Process Saved Data
The `process_saved_data.py` step fits quantitative parameters (T1 or T2) to saved data. 
This step fits quantitative values for each voxel in the image.
Note that the "fit-by-voxel-threshold"
parameter indicates the threshold for masking out noise voxels. 
A low voxel threshold will result in a generous mask, and may take a long time to run if 
fitting is done over most of the voxels in the volume.

An example `process_saved_data` script call is:

<details> <summary> <em> Mac OS Terminal </em> </summary>

```
python process_saved_data.py \
--dataset anthrobrain_3T \
--datatype t2 \
--fit-by-voxel-threshold 0.01 \
--saved-data-dir ../data/processed/saved_data \
--output-dir  ../data/processed/fit_data/ \
--images
```
</details>
<details> <summary> <em> Windows Powershell </em> </summary>

```
python process_saved_data.py `
--dataset anthrobrain_3T `
--datatype t2 `
--fit-by-voxel-threshold 0.01 `
--saved-data-dir ../data/processed/saved_data `
--output-dir  ../data/processed/fit_data/ `
--images
```
</details>
<details> <summary> <em> Windows Command Line </em> </summary>

```
python process_saved_data.py ^
--dataset anthrobrain_3T ^
--datatype t2 ^
--fit-by-voxel-threshold 0.01 ^
--saved-data-dir ../data/processed/saved_data ^
--output-dir  ../data/processed/fit_data/ ^
--images
```
</details>

where the arguments are:
```
  --dataset DATASETS [DATASETS ...]
                        Dataset(s) to process
  --datatype {t1,t2,t2_map} [{t1,t2,t2_map} ...]
                        Type(s) of data to process. If multiple datatypes are given, cannot specify datatype-values
  --datatype-values VALUES_TO_USE [VALUES_TO_USE ...]
                        (Optional) Limited values to use for quantitative fit. For example, if you are fitting the t1 datatype and have collected data for inversion times (tis) [100, 200,
                        600, 800], setting --datatype-values to: 100 800 will only use the data collected for those tis to estimate t1. Note: Only valid when only one datatype is specified!
  --fit-by-voxel-threshold FIT_BY_VOXEL_THRESHOLD
                        (Optional) Threshold to mask the data by when fitting by voxel. This is used to speed up fit by voxel by not fitting background noise voxels. The default value is 0.2
  --saved-data-dir SAVED_DATA_DIR
                        Directory to load saved data from. Saved data will be loaded from: <saved-data-dir>/<datatype>/<dataset>/raw_{slc}.csv
  --output-dir OUTPUT_DIR
                        Directory to output data to. The output convention is: <output-dir>/<datatype>/<dataset>/raw.csv
  --images              (Optional) Store images of fits when saving data. Note: for grouping by voxel, this will be overwritten to False because it takes too long to run
```

