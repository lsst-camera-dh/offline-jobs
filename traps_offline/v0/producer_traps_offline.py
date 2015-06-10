#!/usr/bin/env python
import sys
import lsst.eotest.sensor as sensorTest
from lcatr.harness.helpers import dependency_glob
import siteUtils
import eotestUtils

sensor_id = siteUtils.getUnitId()

trap_file = siteUtils.datacatalog_glob(sensor_id, 'PPUMP', 'PPUMP',
                                       pattern='*_trap_ppump_*')[0]
mask_files = dependency_glob('*_mask.fits')

print trap_file
print mask_files
sys.stdout.flush()

gains = eotestUtils.getSensorGains(sensor_id, jobname='fe55_offline')

task = sensorTest.TrapTask()
task.run(sensor_id, trap_file, mask_files, gains)
