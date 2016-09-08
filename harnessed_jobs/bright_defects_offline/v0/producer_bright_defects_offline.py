#!/usr/bin/env python
import lsst.eotest.sensor as sensorTest
import siteUtils
import eotestUtils

sensor_id = siteUtils.getUnitId()
dark_files = siteUtils.datacatalog_glob('*_dark_dark_*',
                                        testtype='DARK',
                                        imgtype='DARK',
                                        description='Dark files:')
bias_frame = siteUtils.dependency_glob('*_mean_bias_*.fits',
                                       jobname=siteUtils.getProcessName('fe55_offline'),
                                       description='Mean bias frame:')[0]
mask_files = eotestUtils.glob_mask_files()
gains = eotestUtils.getSensorGains(jobname='fe55_offline')

task = sensorTest.BrightPixelsTask()
task.run(sensor_id, dark_files, mask_files, gains, bias_frame=bias_frame)
