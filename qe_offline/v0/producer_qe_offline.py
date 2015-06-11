#!/usr/bin/env python
import os
import lsst.eotest.sensor as sensorTest
import siteUtils
import eotestUtils

sensor_id = siteUtils.getUnitId()
lambda_files = siteUtils.datacatalog_glob('*_lambda_*.fits',
                                          testtype='LAMBDA',
                                          imgtype='FLAT',
                                          description='Lambda files:')
mask_files = eotestUtils.glob_mask_files()
gains = eotestUtils.getSensorGains(jobname='fe55_offline')

# The photodiode ratio file for BNL data.
# @todo Set this to the correct file for production runs.
pd_cal_file = os.path.join(os.environ['EOTEST_DIR'], 'data', 'qe',
                           'BNL', 'pd_Cal_mar2013.txt')

task = sensorTest.QeTask()
task.run(sensor_id, lambda_files, None, None, None, mask_files, gains,
         pd_cal_file=pd_cal_file)
