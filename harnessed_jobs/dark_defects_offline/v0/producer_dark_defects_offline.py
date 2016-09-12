#!/usr/bin/env python
import lsst.eotest.sensor as sensorTest
import siteUtils
import eotestUtils

siteUtils.aggregate_job_ids()
sensor_id = siteUtils.getUnitId()
sflat_files = siteUtils.datacatalog_glob('*_sflat_500_flat_H*.fits',
                                         testtype='SFLAT_500',
                                         imgtype='FLAT',
                                         description='Superflat files:')
bias_frame = siteUtils.dependency_glob('*_mean_bias_*.fits',
                                       jobname=siteUtils.getProcessName('fe55_offline'),
                                       description='Mean bias frame:')[0]
mask_files = eotestUtils.glob_mask_files()

task = sensorTest.DarkPixelsTask()
task.run(sensor_id, sflat_files, mask_files, bias_frame=bias_frame)
