#!/usr/bin/env python
import sys
import lsst.eotest.sensor as sensorTest
from lcatr.harness.helpers import dependency_glob
import siteUtils
import eotestUtils

sensor_id = siteUtils.getUnitId()

flat_files = siteUtils.datacatalog_glob(sensor_id, 'FLAT', 'FLAT',
                                        pattern='*_flat*flat?_*.fits')
mask_files = dependency_glob('*_mask.fits')

print flat_files
print mask_files
sys.stdout.flush()

gains = eotestUtils.getSensorGains(sensor_id, jobname='fe55_offline')

task = sensorTest.FlatPairTask()
task.run(sensor_id, flat_files, mask_files, gains)
