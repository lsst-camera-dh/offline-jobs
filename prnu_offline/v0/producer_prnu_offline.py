#!/usr/bin/env python
import lsst.eotest.sensor as sensorTest
import siteUtils
import eotestUtils

sensor_id = siteUtils.getUnitId()
lambda_files = siteUtils.datacatalog_glob('*_lambda_flat_*.fits',
                                          testtype='LAMBDA',
                                          imgtype='FLAT',
                                          description='Lambda files:')
mask_files = eotestUtils.glob_mask_files()
gains = eotestUtils.getSensorGains(jobname='fe55_offline')
# @todo Set correction image when it becomes available.
correction_image = None

task = sensorTest.PrnuTask()
task.run(sensor_id, lambda_files, mask_files, gains, correction_image)
