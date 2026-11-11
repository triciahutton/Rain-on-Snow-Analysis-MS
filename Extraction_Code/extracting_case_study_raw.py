import os
import xarray as xr
import numpy as np

# -----------------------------
# SETTINGS
# -----------------------------
year = 2010
month = "11"
varlist = ['t2m','tp','sf','sd']

geo_path = "/import/beegfs/CMIP6/wrf_era5/geo_em.d02.nc"
era5_base = "/import/AKCASC/data/cds/reanalysis-era5-single-levels/"
output_dir = "/center1/DYNDOWN/phutton5/ROS/"
os.makedirs(output_dir, exist_ok=True)

# -----------------------------
# LOAD GEO FILE
# -----------------------------
geo = xr.open_dataset(geo_path)

def crop_data(datatocrop, geodata):
    lat_geo = geodata['XLAT_M'].values
    lon_geo = geodata['XLONG_M'].values
    
    geo_lat_min = lat_geo.min()
    geo_lat_max = lat_geo.max()
    geo_lon_min = lon_geo.min()
    geo_lon_max = lon_geo.max()

    if datatocrop.longitude.max() > 180:
        datatocrop = datatocrop.assign_coords(
            longitude=(((datatocrop.longitude + 180) % 360) - 180)
        )
        datatocrop = datatocrop.sortby('longitude')

    return datatocrop.where(
        (datatocrop.latitude >= geo_lat_min) &
        (datatocrop.latitude <= geo_lat_max) &
        (datatocrop.longitude >= geo_lon_min) &
        (datatocrop.longitude <= geo_lon_max),
        drop=True
    )

# -----------------------------
# LOAD DECEMBER 2021 DATA
# -----------------------------
data = xr.Dataset()

for var in varlist:
    file_path = f"{era5_base}/{var}/reanalysis-era5-single-levels_{var}_{year}_{month}.nc"

    with xr.open_dataset(file_path) as ds:
        try:
            ds = ds.rename({'valid_time': 'time'})
        except ValueError:
            pass

        ds = ds.drop_vars(['expver', 'number'], errors='ignore')
        da = crop_data(ds[var], geo)
        data[var] = da

# -----------------------------
# UNIT CONVERSIONS
# -----------------------------
data['sf'] = data['sf'] * 1000      # m -> mm
data['tp'] = data['tp'] * 1000      # m -> mm
data['sd'] = data['sd'] * 1000      # m water equiv -> mm

data['RAIN'] = data['tp'] - data['sf']

# -----------------------------
# CALCULATE ROS EVENTS
# -----------------------------
RAIN = data['RAIN']
SNOW = data['sd']

ros_events = (RAIN > 0.254) & (SNOW > 2.54)

# Extract only ROS rain and snow
rain_ros = RAIN.where(ros_events)
snow_ros = SNOW.where(ros_events)

# Optional: totals for the month
rain_ros_sum = rain_ros.sum(dim='time')
snow_ros_mean = snow_ros.mean(dim='time')

# -----------------------------
# SAVE OUTPUT
# -----------------------------
output_ds = xr.Dataset({
    "ros_mask": ros_events,
    "rain_during_ros": rain_ros,
    "snow_during_ros": snow_ros,
    "rain_ros_sum": rain_ros_sum,
    "snow_ros_mean": snow_ros_mean
})

output_file = os.path.join(output_dir, "ROS_November_2010.nc")

comp = dict(zlib=True, complevel=4)
encoding = {var: comp for var in output_ds.data_vars}

output_ds.to_netcdf(output_file, format="NETCDF4", encoding=encoding)

print("Finished. File saved:", output_file)
