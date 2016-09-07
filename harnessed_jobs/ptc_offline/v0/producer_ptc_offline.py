#!/usr/bin/env python
import lsst.eotest.sensor as sensorTest
import siteUtils
import eotestUtils

sensor_id = siteUtils.getUnitId()
flat_files = siteUtils.datacatalog_glob('*_flat*flat?_*.fits',
                                        testtype='FLAT',
                                        imgtype='FLAT',
                                        description='Flat files:')
bias_frame = siteUtils.dependency_glob('*_mean_bias_*.fits',
                                       jobname=siteUtils.getProcessName('fe55_offline'),
                                       description='Mean bias frame:')[0]
mask_files = eotestUtils.glob_mask_files()
gains = eotestUtils.getSensorGains(jobname='fe55_offline')

task = sensorTest.PtcTask()
task.run(sensor_id, flat_files, mask_files, gains, bias_frame=bias_frame)
