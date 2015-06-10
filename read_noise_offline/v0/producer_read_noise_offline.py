#!/usr/bin/env python
import sys
import lsst.eotest.sensor as sensorTest
from lcatr.harness.helpers import dependency_glob
import siteUtils
import eotestUtils

sensor_id = siteUtils.getUnitId()

bias_files = siteUtils.datacatalog_glob(sensor_id, "BIAS", "FE55",
                                        pattern='*_fe55_bias_*')
system_noise_files = dependency_glob('noise_*.fits',
                                     jobname=siteUtils.getProcessName('system_noise'))
mask_files = dependency_glob('*_mask.fits')

if not system_noise_files:
    system_noise_files = None

print bias_files
print system_noise_files
print mask_files
sys.stdout.flush()

gains = eotestUtils.getSensorGains(sensor_id, jobname='fe55_offline')

task = sensorTest.ReadNoiseTask()
task.run(sensor_id, bias_files, gains,
         system_noise_files=system_noise_files, mask_files=mask_files)
