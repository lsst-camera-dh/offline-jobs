#!/usr/bin/env python
import os
import sys
import lsst.eotest.sensor as sensorTest
import siteUtils
import eotestUtils
import vendorDataUtils

siteUtils.aggregate_job_ids()
sensor_id = siteUtils.getUnitId()

# Use Fe55 exposures and the overscan region instead of the bias
# frames since the vendor data are not guaranteed to have the same
# gains for the bias frames.
bias_files = siteUtils.datacatalog_glob('*_fe55_fe55_*.fits',
                                        testtype="FE55",
                                        imgtype="FE55",
                                        description='Bias files (using overscan):')

gains = eotestUtils.getSensorGains(jobname='fe55_offline')

if os.environ['LCATR_DATACATALOG_FOLDER'].find('vendorIngest') != -1:
    # We are analyzing vendor data, so get system noise provided by vendor.
    system_noise = vendorDataUtils.getSystemNoise(gains)
else:
    system_noise = eotestUtils.getSystemNoise(gains)

if system_noise is None:
    print
    print "WARNING: The system noise file is not found."
    print "The system noise will be set to zero for all amplifiers."
    print
    sys.stdout.flush()

mask_files = eotestUtils.glob_mask_files()

task = sensorTest.ReadNoiseTask()
task.run(sensor_id, bias_files, gains, system_noise=system_noise,
         mask_files=mask_files, use_overscan=True)
