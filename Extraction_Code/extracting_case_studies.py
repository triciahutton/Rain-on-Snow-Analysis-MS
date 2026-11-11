import os
import glob
import time
from datetime import datetime
import numpy as np
import xarray as xr

def load_dec_2021_dataset():
    print("Loading December 2021 dataset...")
    load_start = time.time()

    year = 2003
    month = "02"
    path = f'/import/beegfs/CMIP6/wrf_era5/04km/{year}'
    pattern = f"era5_wrf_dscale_4km_{year}-{month}-*.nc"

    file_list = sorted(glob.glob(os.path.join(path, pattern)))

    if not file_list:
        raise ValueError("No December 2021 files found!")

    def select_vars(ds):
        return ds[['T2', 'SNOW', 'acsnow', 'rainnc', 'XLAT', 'XLONG', 'Time']]

    data = xr.open_mfdataset(file_list, combine='by_coords', preprocess=select_vars)

    load_end = time.time()
    print("Dataset loaded. Time (min):", round((load_end - load_start) / 60, 2))

    return data


def land_mask(data):
    os.chdir("/import/beegfs/CMIP6/wrf_era5")
    geo = xr.open_dataset("geo_em.d02.nc")

    landmask = geo['LANDMASK'].squeeze(dim="Time")
    landmask_expanded = landmask.expand_dims(Time=data.Time)

    data_fixed = data.where(landmask_expanded == 1)

    oceanmask = geo['LU_INDEX'].squeeze(dim='Time')
    oceanmask_expanded = oceanmask.expand_dims(Time=data.Time)

    data_masked = data_fixed.where(oceanmask_expanded != 17)

    print("Land and Ocean Mask applied.")
    return data_masked


def calculate_hourly_ros(data):
    print("Calculating hourly Rain-on-Snow events...")

    SNOW = data['SNOW']
    RAIN = data['rainnc'] - data['acsnow']

    # Hourly ROS condition
    ros_events = (RAIN > 0.254) & (SNOW > 2.54)

    print("ROS filtering complete.")

    return xr.Dataset({
        "ROS_hourly": ros_events,
        "RAIN": RAIN,
        "SNOW": SNOW
    })


def main():
    print("Starting December 2021 ROS extraction")
    print("Started at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    ds = load_dec_2021_dataset()
    ds_masked = land_mask(ds)
    ros_ds = calculate_hourly_ros(ds_masked)

    output_path = "/center1/DYNDOWN/phutton5/ROS/All_of_AK/All_of_AK_netcdf_files/ROS_Feb2003_hourly.nc"

    encoding = {var: {'zlib': True, 'complevel': 5} for var in ros_ds.data_vars}

    ros_ds.to_netcdf(output_path, engine='netcdf4', encoding=encoding)

    print("Saved:", output_path)
    print("Finished successfully.")


if __name__ == "__main__":
    main()
