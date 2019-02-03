# script to run in cloud -- Canadian bandwidth sucks

import os
import requests
import numpy as np
import pandas as pd
from glob import glob
from netCDF4 import Dataset
from skimage.graph import route_through_array

# Load Sea/Land fixed data to create a mask
nc_f = 'data/sftlf_ARC-22_CCCma-CanESM2_rcp45_r1i1p1_CCCma-CanRCM4_r2_fx.nc'
nc = Dataset(nc_f, 'r')
#nc.variables.keys()
sftlf = nc['sftlf'][0, :, :]

# go through each rcp
rcps = ["rcp45", "rcp85"]

weights = []
indices_len = []
times = []
rcp_track = []

for rcp in rcps:
    
    # get filenames
    site = "http://climate-modelling.canada.ca/climatemodeldata/canrcm/CanRCM4/ARC-22_CCCma-CanESM2_{}/day/atmos/sic/index.shtml".format(rcp)
    file_df = pd.read_html(site)[0]
    
    # for through files
    for filename in file_df['File name']:
        print(filename)
        
        # check if file already downloaded
        if not os.path.isfile('data/future/{}/{}'.format(rcp, filename)):
            # download file
            print('Downloading')
            download_base = "http://climate-modelling.canada.ca/cgi-bin/data_get/get_www_nc?path="
            path = "/data3/CORDEX/output/CCCma/CanRCM4/ARC-22_CCCma-CanESM2_{}/day/atmos/sic/r1i1p1/{}".format(rcp, filename)
            link = download_base + path
            response = requests.get(link, stream=True)
            response.raise_for_status()
            with open('data/future/{}/{}'.format(rcp, filename), 'wb') as f:
                for block in response.iter_content(1024):
                    f.write(block)
            
        print('Processing')
        nc = Dataset('data/future/{}/{}'.format(rcp, filename), 'r')
        times.extend(list(nc['time'][:]))
            
        for i in range(nc.variables['time'].shape[0]):
            sic = nc['sic'][i, :, :]
            sic[np.where(sftlf!=0)] = -np.inf
            indices, weight = route_through_array(sic, [0,116], [265,231], geometric=True, fully_connected=True)
            weights.append(weight)
            rcp_track.append(rcp)
            indices_len.append(len(indices))
                    
df = pd.DataFrame([weights, indices_len, times, rcp_track]).T
df.columns = ['weights', 'num_index', 'time', 'rcp']
df.to_csv('forecast_results.csv')