#!/usr/bin/env python
import sys
import lsst.eotest.sensor as sensorTest
from lcatr.harness.helpers import dependency_glob
import siteUtils
import eotestUtils

sensor_id = siteUtils.getUnitId()

dark_files = siteUtils.datacatalog_glob(sensor_id, 'DARK', 'DARK', 
                                        pattern='*dark_dark_*.fits')
mask_files = dependency_glob('*_mask.fits')

print dark_files
print mask_files
sys.stdout.flush()

gains = eotestUtils.getSensorGains(sensor_id, jobname='fe55_offline')

task = sensorTest.DarkCurrentTask()
task.run(sensor_id, dark_files, mask_files, gains)
