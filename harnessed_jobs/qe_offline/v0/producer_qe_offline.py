#!/usr/bin/env python
import os
import pyfits
import lsst.eotest.sensor as sensorTest
import siteUtils
import eotestUtils

sensor_id = siteUtils.getUnitId()
lambda_files = siteUtils.datacatalog_glob('*_lambda_flat_*.fits',
                                          testtype='LAMBDA',
                                          imgtype='FLAT',
                                          description='Lambda files:')

#
# Check if frames orginate from one of the vendors.  If so, assume
# MONDIODE keyword contains incident power and use that in the QeTask.
#
try:
    header = pyfits.open(lambda_files[0])[0].header
    vendor_data = ((header['ORIGIN'].find('e2v') != -1) or
                   (header['ORIGIN'].find('UAITL') != -1))
    
except:
    vendor_data = False

# The photodiode ratio file for BNL data.
# @todo Set this to the correct file for production runs.
pd_ratio_file = os.path.join(os.environ['EOTEST_DIR'], 'data', 'qe',
                             'BNL', 'pd_ratio_2015-08-29.txt')
mask_files = eotestUtils.glob_mask_files()
gains = eotestUtils.getSensorGains(jobname='fe55_offline')

task = sensorTest.QeTask()
task.run(sensor_id, lambda_files, pd_ratio_file, mask_files, gains,
         vendor_data=vendor_data)
