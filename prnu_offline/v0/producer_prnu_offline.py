#!/usr/bin/env python
import sys
import lsst.eotest.sensor as sensorTest
from lcatr.harness.helpers import dependency_glob
import siteUtils
import eotestUtils

sensor_id = siteUtils.getUnitId()

lambda_files = siteUtils.datacatalog_glob(sensor_id, 'FLAT', 'QE', 
                                          pattern='*_lambda_*.fits')
correction_image = None
mask_files = dependency_glob('*_mask.fits')

print lambda_files
print correction_image
print mask_files
sys.stdout.flush()

gains = eotestUtils.getSensorGains(sensor_id, jobname='fe55_offline')

task = sensorTest.PrnuTask()
task.run(sensor_id, lambda_files, mask_files, gains, correction_image)
