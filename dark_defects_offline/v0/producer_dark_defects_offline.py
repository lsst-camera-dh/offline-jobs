#!/usr/bin/env python
import sys
import lsst.eotest.sensor as sensorTest
from lcatr.harness.helpers import dependency_glob
import siteUtils

sensor_id = siteUtils.getUnitId()

sflat_files = siteUtils.datacatalog_glob(sensor_id, 'FLAT', 'SFLAT',
                                         pattern='*_superflat_500_*')
mask_files = dependency_glob('*_mask.fits')

print sflat_files
print mask_files
sys.stdout.flush()

task = sensorTest.DarkPixelsTask()
task.run(sensor_id, sflat_files, mask_files)
