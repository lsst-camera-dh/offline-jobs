#!/usr/bin/env python
import lsst.eotest.sensor as sensorTest
import siteUtils
import eotestUtils

sensor_id = siteUtils.getUnitId()
#bias_files = siteUtils.datacatalog_glob('*_fe55_bias_*.fits',
#                                        testtype="FE55",
#                                        imgtype="BIAS",
#                                        description='Bias files:')
#use_overscan = False

# Use Fe55 exposures and the overscan region instead of the bias
# frames since the vendor data are not guaranteed to have the same
# gains for the bias frames.

bias_files = siteUtils.datacatalog_glob('*_fe55_fe55_*.fits',
                                        testtype="FE55",
                                        imgtype="FE55",
                                        description='Bias files (using overscan):')
use_overscan = True

gains = eotestUtils.getSensorGains(jobname='fe55_offline')
system_noise_files = siteUtils.dependency_glob('noise_*.fits', 
                                               jobname=siteUtils.getProcessName('system_noise'))
if not system_noise_files:
    system_noise_files = None
mask_files = eotestUtils.glob_mask_files()

task = sensorTest.ReadNoiseTask()
task.run(sensor_id, bias_files, gains,
         system_noise_files=system_noise_files, mask_files=mask_files,
         use_overscan=use_overscan)
