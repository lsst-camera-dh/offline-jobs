#!/usr/bin/env python
import sys
import lsst.eotest.sensor as sensorTest
from lcatr.harness.helpers import dependency_glob
import siteUtils

sensor_id = siteUtils.getUnitId()

superflat_files = siteUtils.datacatalog_glob(sensor_id, 'FLAT', 'SFLAT',
                                             pattern='*_superflat_500_*')
mask_files = dependency_glob('*_mask.fits')

print superflat_files
print mask_files
sys.stdout.flush()

task = sensorTest.CteTask()
task.run(sensor_id, superflat_files, mask_files)
