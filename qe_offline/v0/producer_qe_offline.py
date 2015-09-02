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
# Check if file orginates from e2v; if so, set e2v_data flag.
#
try:
    e2v_data = pyfits.open(lambda_files[0])[0].header['ORIGIN'].find('e2v') != -1
    print "analyzing QE data from e2v"
except:
    e2v_data = False

# The photodiode ratio file for BNL data.
# @todo Set this to the correct file for production runs.
pd_ratio_file = os.path.join(os.environ['EOTEST_DIR'], 'data', 'qe',
                             'BNL', 'pd_ratio_2015-08-29.txt')
mask_files = eotestUtils.glob_mask_files()
gains = eotestUtils.getSensorGains(jobname='fe55_offline')

task = sensorTest.QeTask()
task.run(sensor_id, lambda_files, pd_ratio_file, mask_files, gains,
         e2v_data=e2v_data)
