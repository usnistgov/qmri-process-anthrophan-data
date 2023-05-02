import re
import numpy as np
import struct
import pydicom
import pandas as pd
from typing import List


class MRIData:
    ''' Unpacks Varian fdf files'''

    def __init__(self):
        self.bValue = 0.0
        self.targetBValue = 0.0
        self.bVector = [0, 0, 0]
        self.Columns = 0
        self.ColumnDirection = [0, 0, 0]
        self.DataType = ""
        self.EchoTime = 1.0
        self.FileType = "fdf"
        self.FlipAngle = 0.0
        self.FoVX = 50.
        self.FoVY = 50.
        self.ImageOrientationPatient = []
        self.InversionTime = 0.0
        self.fmt = ""
        self.header = ""
        self.Manufacturer = "Agilent"
        self.matrix = []
        self.pixel_array = np.zeros([128, 128])  # pixel array
        self.PixelSpacing = [1.0, 1.0]
        self.ProtocolName = ""
        self.RepetitionTime = 1.0
        self.Rows = 0
        self.RowDirection = [1, 0, 0]
        self.StudyDate = ""
        self.SeriesDescription = ""
        self.SliceLocation = ""  # given bugs in fdf output slicelocation is set to slice number
        self.SliceThickness = 0
        self.ro = 0  # number of readout points
        self.pe = 0  # number of phase encode points

    def readFDF(self, filename):
        fdfImage = MRIData()
        xsize = -1
        ysize = -1
        zsize = 1
        bigendian = -1

        fp = open(filename, "rb")
        for line_bytes in fp:
            line = str(line_bytes)
            fdfImage.header += line

            if (len(line) >= 1 and line[0] != chr(12)):  # unpack header
                line = line.split(";")[0]
                if (line.find("bigendian") > 0):
                    endian = line.split("=")[-1].rstrip("\n; ").strip(" ")
                if (line.find("bvalue") > 0):
                    fdfImage.bValue = float(line.split("=")[-1].rstrip("\n; ").strip(" "))
                    fdfImage.targetBValue = fdfImage.bValue
                if (line.find("*type") > 0):
                    fdfImage.DataType = line.split("=")[-1].rstrip("\n; ").strip(" ").replace('"', '')
                if (line.find("echos") > 0):
                    nechoes = line.split("=")[-1].rstrip("\n; ").strip(" ")
                if (line.find("orientation") > 0):
                    orient = line.split("=")[-1].rstrip("\n; ").strip(" ")
                    fdfImage.ImageOrientationPatient = orient.replace("{", " ").replace("}", " ").split(",")
                    # print fdfImage.ImageOrientationPatient
                if (line.find("studyid") > 0):
                    fdfImage.SeriesDescription = line.split("=")[-1].rstrip("\n; ").strip(" ").replace('"', '')
                if (line.find("sequence") > 0):
                    fdfImage.ProtocolName = line.split("=")[-1].rstrip("\n; ").strip(" ").replace('"', '')
                if (line.find("span") > 0):
                    span = re.findall("{(.*)}", line.rstrip())[0]
                    fdfImage.FoVX = float(span.split(",")[0]) * 10.  # asuming cm and converts to mm, needs work
                    fdfImage.FoVY = float(span.split(",")[1]) * 10.
                if (line.find("TR =") > 0):
                    fdfImage.RepetitionTime = float(line.split("=")[-1].rstrip("\n; ").strip(" "))
                if (line.find("TE =") > 0):
                    fdfImage.EchoTime = float(line.split("=")[-1].rstrip("\n; ").strip(" "))
                if (line.find("TI =") > 0):
                    fdfImage.InversionTime = float(line.split("=")[-1].rstrip("\n; ").strip(" "))
                if (line.find("ro_size") > 0):
                    fdfImage.ro = line.split("=")[-1].rstrip("\n; ").strip(" ")
                    # print "ro found=" + str(fdfImage.ro)
                if (line.find("pe_size") > 0):
                    fdfImage.pe = line.split("=")[-1].rstrip("\n; ").strip(" ")
                    # print "pe found=" + str(fdfImage.pe)
                if (line.find("echo_no") > 0):
                    echo_no = line.split("=")[-1].rstrip("\n; ").strip(" ")
                if (line.find("nslices") > 0):
                    nslices = line.split("=")[-1].rstrip("\n; ").strip(" ")
                if (line.find("slice_no") > 0):
                    sl = line.split("=")[-1].rstrip("\n; ").strip(" ")
                if (line.find("location") > 0):
                    location = re.findall("{(.*)}", line.rstrip())[0]
                    fdfImage.SliceLocation = float(
                        location[1:-2].split(',')[2]) * 10  # last element in location string is slice location in cm
                if (line.find("matrix") > 0):
                    fdfImage.matrix = re.findall("(\d+)", line.rstrip())
                    if len(fdfImage.matrix) == 2:
                        xsize, ysize = int(fdfImage.matrix[0]), int(fdfImage.matrix[1])
                        # print("xsize,ysize=" + str(xsize) + str(ysize))
                    elif len(fdfImage.matrix) == 3:
                        xsize, ysize, zsize = int(fdfImage.matrix[0]), int(fdfImage.matrix[1]), int(fdfImage.matrix[2])
                        # print("xsize,ysize,zsize=" + str(xsize) + str(ysize) + str(zsize))
        fp.seek(-xsize * ysize * zsize * 4, 2)  # set files current position xsize*ysize*zsize*4bytes from end of file

        if bigendian == 1:
            fdfImage.fmt = ">%df" % (xsize * ysize * zsize)
        else:
            fdfImage.fmt = "<%df" % (xsize * ysize * zsize)  # our images ar bigendian=0

        # print "fmt=" + str(fdfImage.fmt)
        fdfImage.Rows = float(fdfImage.pe)  # phase encode is normally along row
        fdfImage.Columns = float(fdfImage.ro)  # read out is normally along column
        fdfImage.PixelSpacing = [fdfImage.FoVY / fdfImage.Columns,
                                 fdfImage.FoVX / fdfImage.Rows]  # conform to DICOM standard
        data = struct.unpack(fdfImage.fmt, fp.read(xsize * ysize * zsize * 4))
        if len(fdfImage.matrix) == 2:
            fdfImage.pixel_array = np.transpose(np.resize(data, [ysize, xsize]))
        if len(fdfImage.matrix) == 3:
            fdfImage.pixel_array = np.transpose(np.resize(data, [ysize, xsize, zsize]))
        fp.close()
        return fdfImage

    def readDicom(self, filename, datatype, file_extension=".dcm"):
        dicomImage = MRIData()
        dicomImage.FileType = file_extension

        p = pydicom.dcmread(filename)
        dicomImage.header = p

        if "Manufacturer" in p:
            dicomImage.Manufacturer = p.Manufacturer
        print("Manufacturer:", dicomImage.Manufacturer)
        if "StudyDate" in p:
            dicomImage.StudyDate = p.StudyDate
        # Loading b_value is complicated depending on manufacturer
        bvalue_tag = "bValue"
        if "hyperfine" in p.Manufacturer.lower():
            bvalue_tag = "0x00189087"
        elif "siemens" in p.Manufacturer.lower():
            if "0x0019100c" in p:
                bvalue_tag = "0x0019100c"
            else:
                bvalue_tag = "0x0019a00c"
        elif ("ge" in dicomImage.Manufacturer.lower()) or "general electric" in dicomImage.Manufacturer.lower():
            bvalue_tag = "0x0043a039"
        elif "philips" in dicomImage.Manufacturer.lower():
            bvalue_tag = "0x00189087"
        if bvalue_tag in p:
            dicomImage.bValue = extract_b_value(p, bvalue_tag)
            dicomImage.targetBValue = dicomImage.bValue

        if "ImageOrientationPatient" in p:
            dicomImage.ImageOrientationPatient = p.ImageOrientationPatient
        if "SeriesDescription" in p:
            dicomImage.SeriesDescription = p.SeriesDescription
        if "ProtocolName" in p:
            dicomImage.ProtocolName = p.ProtocolName
        if "RepetitionTime" in p:
            dicomImage.RepetitionTime = p.RepetitionTime
        if "EchoTime" in p:
            dicomImage.EchoTime = p.EchoTime
        if "InversionTime" in p:
            dicomImage.InversionTime = p.InversionTime
        if "EchoNumbers" in p:
            echo_no = p.EchoNumbers
        if "FlipAngle" in p:
            dicomImage.FlipAngle = p.FlipAngle

        rows_are_ro_dir = True
        if "InPlanePhaseEncodingDirection" in p:
            if "row" in p.InPlanePhaseEncodingDirection.lower():
                rows_are_ro_dir = False
        if "Rows" in p:
            dicomImage.Rows = p.Rows
            if rows_are_ro_dir:
                dicomImage.ro = p.Rows
            else:
                dicomImage.pe = p.Rows
        if "Columns" in p:
            dicomImage.Columns = p.Columns
            if rows_are_ro_dir:
                dicomImage.pe = p.Columns
            else:
                dicomImage.ro = p.Columns
        if "PixelSpacing" in p:
            dicomImage.PixelSpacing = p.PixelSpacing
            dicomImage.FoVX = dicomImage.PixelSpacing[0] * dicomImage.Rows
            dicomImage.FoVY = dicomImage.PixelSpacing[1] * dicomImage.Columns

        if "SliceThickness" in p:
            dicomImage.SliceThickness = p.SliceThickness
        if "SliceLocation" in p:
            dicomImage.SliceLocation = p.SliceLocation

        # Get the data, rescale it if necessary
        dicomImage.pixel_array = p.pixel_array
        if "hyperfine" in dicomImage.Manufacturer.lower():
            if (datatype == "t1") or (datatype == "t2"):
                dicomImage.pixel_array = rescale_images_hyperfine(p)
        if "philips" in dicomImage.Manufacturer.lower():
            rescale_slope = 1
            rescale_intercept = 0
            if "RescaleSlope" in p:
                rescale_slope = p.RescaleSlope
            if "RescaleIntercept" in p:
                rescale_intercept = p.RescaleIntercept
            print(f"Rescaling philips image with slope {rescale_slope} and intercept {rescale_intercept}")
            dicomImage.pixel_array = (p.pixel_array * rescale_slope) + rescale_intercept

        return dicomImage


def extract_b_value(ds, tag):
    if tag in ["0x0019100c", "0x0019a00c", "0x00189087"]:
        b_value = get_b_direct_from_tag(ds, tag)
    elif tag in ["0x00431039", "0x0043a039"]:
        b_value = get_and_process_b_from_tag(ds, tag)
    else:
        raise Exception(f"No method to handle tag: {tag}")
    return b_value


def get_b_direct_from_tag(ds, tag):
    return int(ds[tag].value)


def get_and_process_b_from_tag(ds, tag):
    return int(str(ds[tag].value[0]).split("1000000")[-1])


def turn_mri_data_into_dfs_by_slice(mri_data_objs: List[MRIData]):
    all_dfs_by_slice = {}
    n_mridata = len(mri_data_objs)

    print("Processing", n_mridata, "loaded files")
    percent_done = 10
    idx = 0
    for mri_data in mri_data_objs:
        idx += 1
        if (idx / n_mridata * 100) > percent_done:
            print(percent_done, "% done")
            percent_done += 10

        # Process the data based on the data shape
        data_shape = np.shape(mri_data.pixel_array)
        if len(data_shape) == 3:
            data_3d = mri_data.pixel_array
            nz, nx, ny = np.shape(data_3d)
            assert nx == mri_data.Rows, f"Expected nx of {mri_data.Rows}, got {nx}"
            assert ny == mri_data.Columns, f"Expected nx of {mri_data.Columns}, got {ny}"
            # 3D data - need to loop through z and slice location will be z location
            for slc_location in range(nz):
                data_2d = data_3d[slc_location, :, :]
                df = get_df_for_2d_data(mri_data, data_2d)
                df["slc_location"] = slc_location  # Need to do this again here, since it was probably null before
                # df["slc"] = slc_location
                # df["nslc"] = nz
                if slc_location not in all_dfs_by_slice:
                    all_dfs_by_slice[slc_location] = [df]
                else:
                    all_dfs_by_slice[slc_location].append(df)
        elif len(data_shape) == 2:
            data_2d = mri_data.pixel_array
            df = get_df_for_2d_data(mri_data, data_2d)

            slc_location = mri_data.SliceLocation
            if slc_location not in all_dfs_by_slice:
                all_dfs_by_slice[slc_location] = [df]
            else:
                all_dfs_by_slice[slc_location].append(df)

    # Add in the slice location if it's not there
    nslc = len(all_dfs_by_slice)
    dfs_by_slice = {}
    all_slc_locations = list(all_dfs_by_slice.keys())
    all_slc_locations.sort()
    slc_idx = 0
    for slc_location in all_slc_locations:
        dfs = all_dfs_by_slice[slc_location]
        print("Getting all data for slc", slc_location)
        for df in dfs:
            if "slc" not in df:
                df["slc"] = slc_idx
            if "nslc" not in df:
                df["nslc"] = nslc
        # compress them all
        dfs_by_slice[slc_location] = pd.concat(dfs)
        slc_idx += 1
    print("Finished processing", n_mridata, "loaded files")
    return dfs_by_slice


def get_df_for_2d_data(mri_data, data_2d):
    nx, ny = np.shape(data_2d)
    # First create a dataframe with the data
    df = pd.DataFrame(data_2d)
    df = df.unstack().reset_index()  # This unstacks y first, then x
    df.columns = ["y", "x", "data"]
    df["nx"] = nx
    df["ny"] = ny

    # Then add all the other things
    df["ti"] = mri_data.InversionTime
    df["tr"] = mri_data.RepetitionTime
    df["te"] = mri_data.EchoTime
    df["b_value"] = mri_data.bValue
    df["target_b_value"] = mri_data.targetBValue
    df["b_vec_0"] = mri_data.bVector[0]
    df["b_vec_1"] = mri_data.bVector[1]
    df["b_vec_2"] = mri_data.bVector[2]
    df["slc_location"] = mri_data.SliceLocation

    # Sort the columns
    df = df[["x", "y", "slc_location", "data", "tr", "te", "ti",
             "b_value", "target_b_value",
             "b_vec_0", "b_vec_1", "b_vec_2",
             "nx", "ny"]]
    return df


def rescale_images_hyperfine(ds):
    print("RESCALING IMAGES ....")
    images = ds.pixel_array

    # Calculate scale factors
    tmp_min = float(ds[0x03511000].value)
    tmp_max = float(ds[0x03511001].value)
    uint_x_max = float(ds[0x03511002].value)
    mult_factor = (tmp_max - tmp_min) / uint_x_max
    if np.isnan(mult_factor) or np.isnan(tmp_min):
        print("Scale factor data is NaN! Returning non-scaled image")
        return images
    print("Scan scale factors:", tmp_min, tmp_max, uint_x_max)
    print("\tMultiplication factor:", mult_factor)
    print("\tMin to add:", tmp_min)

    scaled_images = []
    n_slices, n_y, n_x = np.shape(images)
    for s in range(n_slices):
        scaled_images.append((images[s, :, :] * mult_factor) + tmp_min)
    #         scaled_images.append(images[s, :, :] )
    scaled_images = np.asarray(scaled_images)
    return scaled_images
