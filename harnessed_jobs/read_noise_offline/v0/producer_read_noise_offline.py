#!/usr/bin/env python
import os
import sys
import lsst.eotest.sensor as sensorTest
import siteUtils
import eotestUtils
import vendorDataUtils

siteUtils.aggregate_job_ids()
sensor_id = siteUtils.getUnitId()

using_vendor_data \
    = os.environ['LCATR_DATACATALOG_FOLDER'].find('vendorIngest') != -1

bias_files = siteUtils.datacatalog_glob('*_fe55_bias_*.fits',
                                        testtype="FE55",
                                        imgtype="BIAS",
                                        description='Bias files:')

gains = eotestUtils.getSensorGains(jobname='fe55_offline')

if using_vendor_data and sensor_id.startswith('E2V'):
    gain_ratios = vendorDataUtils.get_e2v_gain_ratios()
    for amp in gains:
        gains[amp] /= gain_ratios[amp]

if using_vendor_data:
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
         mask_files=mask_files, use_overscan=False)
