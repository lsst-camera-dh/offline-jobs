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
# The photodiode ratio file for BNL data.
# @todo Set this to the correct file for production runs.
pd_ratio_file = os.path.join(os.environ['EOTEST_DIR'], 'data', 'qe',
                             'BNL', 'pd_Cal_mar2013_v1.txt')
mask_files = eotestUtils.glob_mask_files()
gains = eotestUtils.getSensorGains(jobname='fe55_offline')

task = sensorTest.QeTask()
task.run(sensor_id, lambda_files, pd_ratio_file, mask_files, gains)
